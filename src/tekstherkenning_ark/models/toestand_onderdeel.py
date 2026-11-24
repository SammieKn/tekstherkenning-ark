from __future__ import annotations

import pandas as pd
from pydantic import BaseModel, ConfigDict, model_validator

from tekstherkenning_ark import constants, utils
from tekstherkenning_ark.document.structured_table import StructuredTable
from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat

logger = get_logger(__name__)


class ToestandOnderdeel(BaseModel):
    model_config = ConfigDict(extra="allow")

    constructie_onderdeel: str
    aangetast: bool | NietBeschikbaar | OnverwachtResultaat

    @classmethod
    def from_nomic_df(cls, frame: pd.DataFrame) -> dict[str, list[ToestandOnderdeel]]:
        """Create condition records grouped by rakdeel ID.

        Parameters
        ----------
        frame : pandas.DataFrame
            Rows from ``toestandsbepalingen.csv``.

        Returns
        -------
        dict[str, list[ToestandOnderdeel]]
            Condition records keyed by rakdeel ID.
        """
        columns = ("rakdeel_id", "onderdeel", "aangetast")
        missing_columns = set(columns) - set(frame.columns)
        if missing_columns:
            raise ValueError(
                f"toestandsbepalingen.csv is missing required columns: {', '.join(sorted(missing_columns))}"
            )

        grouped: dict[str, list[ToestandOnderdeel]] = {}
        for row in frame.to_dict(orient="records"):
            aangetast = row["aangetast"]
            if isinstance(aangetast, str):
                normalized = aangetast.strip().lower()
                if normalized in {"true", "ja", "yes", "1"}:
                    aangetast = True
                elif normalized in {"false", "nee", "no", "0"}:
                    aangetast = False
                elif not normalized:
                    aangetast = NietBeschikbaar.LEEG
                else:
                    aangetast = utils.parse_ja_nee(aangetast)
            elif pd.isna(aangetast):
                aangetast = NietBeschikbaar.LEEG
            elif isinstance(aangetast, (int, float)):
                aangetast = bool(aangetast)
            onderdeel = "" if pd.isna(row["onderdeel"]) else str(row["onderdeel"]).strip()
            toestand = cls(
                constructie_onderdeel=onderdeel,
                aangetast=aangetast,
                **{key: value for key, value in row.items() if key not in cls.model_fields},
            )
            rakdeel_id = "" if pd.isna(row["rakdeel_id"]) else str(row["rakdeel_id"]).strip()
            grouped.setdefault(rakdeel_id, []).append(toestand)
        return grouped

    @model_validator(mode="after")
    def validate_single_classification(self) -> ToestandOnderdeel:
        """Validate that only one classification applies to this constructie_onderdeel."""

        classifications = []
        if self.is_vloer():
            classifications.append("vloer")
        if self.is_onderbouw():
            classifications.append("onderbouw")
        if self.is_bovenbouw():
            classifications.append("bovenbouw")
        if self.is_onderloopsheidscherm():
            classifications.append("onderloopsheidscherm")

        if len(classifications) > 1:
            logger.warning(
                f"Constructie onderdeel '{self.constructie_onderdeel}' heeft meerdere classificaties: {', '.join(classifications)}"
            )

        return self

    @classmethod
    def from_toestandbepaling_table(cls, structured_table: StructuredTable | None) -> list[ToestandOnderdeel]:
        """Parse toestandsbepaling table from structured table.

        Parameters
        ----------
        structured_table : StructuredTable | None
            Structured table containing toestandsbepaling data.

        Returns
        -------
        list[ToestandOnderdeel]
            List of ToestandOnderdeel instances representing the condition status of construction components.
        """

        if structured_table is None:
            logger.warning("Geen toestandsbepaling tabel gevonden")
            return []

        # Get columns
        constructieonderdeel_col = structured_table.get_column(header_in="Constructieonderdeel")
        aangetast_col = structured_table.get_column(header_in="Aangetast")

        if constructieonderdeel_col is None or aangetast_col is None:
            logger.error("Could not find required columns in toestandsbepaling table")
            return []

        toestandsbepaling_list: list[ToestandOnderdeel] = []

        num_rows = len(constructieonderdeel_col.values)

        for row_idx in range(num_rows):
            constructieonderdeel = utils.clean_string(constructieonderdeel_col.values[row_idx])
            aangetast = utils.clean_string(aangetast_col.values[row_idx])

            if constructieonderdeel:  # Skip empty rows
                aangetast_clean = utils.parse_ja_nee(aangetast)

                if isinstance(aangetast_clean, (bool, NietBeschikbaar, OnverwachtResultaat)):
                    toestand_onderdeel = cls(
                        constructie_onderdeel=constructieonderdeel,
                        aangetast=aangetast_clean,
                    )
                    toestandsbepaling_list.append(toestand_onderdeel)
                else:
                    logger.warning(
                        f"Onverwacht resultaat '{aangetast_clean}' voor '{constructieonderdeel}', wordt overgeslagen."
                    )

        return toestandsbepaling_list

    def is_vloer(self) -> bool:
        """Check if this ToestandOnderdeel is classified as a 'vloer' based on its constructie_onderdeel."""

        return any(patroon in self.constructie_onderdeel for patroon in constants.CONSTRUCTIE_ONDERDELEN_VLOER)

    def is_onderbouw(self) -> bool:
        """Check if this ToestandOnderdeel is classified as 'onderbouw' based on its constructie_onderdeel."""

        return any(patroon in self.constructie_onderdeel for patroon in constants.CONSTRUCTIE_ONDERDELEN_ONDERBOUW)

    def is_bovenbouw(self) -> bool:
        """Check if this ToestandOnderdeel is classified as 'bovenbouw' based on its constructie_onderdeel."""

        return any(patroon in self.constructie_onderdeel for patroon in constants.CONSTRUCTIE_ONDERDELEN_BOVENBOUW)

    def is_onderloopsheidscherm(self) -> bool:
        """Check if this ToestandOnderdeel is classified as 'onderloopsheidscherm' based on its constructie_onderdeel."""

        return any(
            patroon in self.constructie_onderdeel for patroon in constants.CONSTRUCTIE_ONDERDELEN_ONDERLOOPSHEIDSCHERM
        )
