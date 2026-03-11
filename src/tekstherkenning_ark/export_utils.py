from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from tekstherkenning_ark.document.smart_document import SmartDocument
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat

from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.logger import get_logger

logger = get_logger(__name__)

RAK_TABLE_NAME = "rakken"
RAKDEEL_TABLE_NAME = "rakdelen"
HOUTMONSTER_TABLE_NAME = "houtmonsters"
PALEN_TABLE_NAME = "palen"
KESPEN_TABLE_NAME = "kespen"
GEBREKEN_TABLE_NAME = "gebreken"
TOESTANDBEPALINGEN_TABLE_NAME = "toestandsbepalingen"
ONVERWACHT_RESULTATEN_TABLE_NAME = "onverwachte_resultaten"


def remove_collection_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Verwijder alle velden uit een dictionary waarvan de waarde een list is of een dict instance.

    Dit is nodig voor Excel export omdat geneste lijsten en geneste objecten niet goed
    geserialiseerd kunnen worden naar Excel.

    Parameters
    ----------
    data : dict[str, Any]
        Dictionary met mogelijk list-waarden of dict instances

    Returns
    -------
    dict[str, Any]
        Dictionary zonder list-waarden en dict instances
    """

    cleaned_data = {key: value for key, value in data.items() if not isinstance(value, (list, dict))}
    return cleaned_data


def get_dfs_from_pdfs(pdf_rapporten: list[Path]) -> dict[str, pd.DataFrame]:
    """Get a list of dataframe tables for a set of duikrapport pdfs"""
    from tekstherkenning_ark.models.rak import Rak

    smartdocs = [SmartDocument.from_pdf(file) for file in pdf_rapporten if not "boor" in file.stem.lower()]
    rakken = [Rak.from_smart_document(doc, use_caching=False) for doc in smartdocs]

    rak_df = pd.concat([rak._get_rak_df() for rak in rakken])
    rakdeel_df = pd.concat([rak._get_rakdeel_df() for rak in rakken])
    houtmonster_df = pd.concat([rak._get_houtmonsters_df() for rak in rakken])
    kespen_df = pd.concat([rak._get_kespen_df() for rak in rakken])
    palen_df = pd.concat([rak._get_palen_df() for rak in rakken])
    gebreken_df = pd.concat([rak._get_gebreken_df() for rak in rakken])

    gebreken_dfs_per_type: dict[str, list[pd.DataFrame]] = {}
    for rak in rakken:
        df_dict = rak._get_gebreken_per_type_dfs()
        for k, v in df_dict.items():
            if not k in gebreken_dfs_per_type:
                gebreken_dfs_per_type[k] = []
            gebreken_dfs_per_type[k].append(v)

    gebreken_df_per_type: dict[str, pd.DataFrame] = {}
    for k, v in gebreken_dfs_per_type.items():
        gebreken_df_per_type[k] = pd.concat(v)

    toestandsbepalingen_df = pd.concat([rak._get_toestandsbepalingen_df() for rak in rakken])
    onverwacht_resultaten_df = pd.concat([rak._get_onverwacht_resultaten_df() for rak in rakken])

    return {
        RAK_TABLE_NAME: rak_df,
        RAKDEEL_TABLE_NAME: rakdeel_df,
        HOUTMONSTER_TABLE_NAME: houtmonster_df,
        PALEN_TABLE_NAME: palen_df,
        KESPEN_TABLE_NAME: kespen_df,
        GEBREKEN_TABLE_NAME: gebreken_df,
        **{f"{GEBREKEN_TABLE_NAME}_{k}": v for k, v in gebreken_df_per_type.items()},
        TOESTANDBEPALINGEN_TABLE_NAME: toestandsbepalingen_df,
        ONVERWACHT_RESULTATEN_TABLE_NAME: onverwacht_resultaten_df,
    }


def remove_onverwacht_resultaat_from_table_rows(
    table_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Replace any OnverwachtResultaat values in the table rows with their waarde, and log how many were found."""

    from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat

    n_onverwacht = 0

    for row in table_rows:
        for key, value in row.items():
            if isinstance(value, OnverwachtResultaat):
                n_onverwacht += 1
                row[key] = value.waarde

    logger.info(f"{n_onverwacht} onverwachte resultaten gevonden en omgezet naar hun waarde in de tabel.")

    return table_rows


def waarde_naar_excel(waarde: bool | NietBeschikbaar | OnverwachtResultaat):
    """Converteer toestandwaarde naar een Excel-vriendelijk type."""
    if isinstance(waarde, bool):
        return waarde

    if hasattr(waarde, "model_dump"):
        try:
            return waarde.model_dump()
        except Exception:
            return str(waarde)

    if hasattr(waarde, "value"):
        return waarde.value

    return str(waarde)


def haal_rakdeel_id_en_model_pad(pad: str) -> tuple[str, str]:
    """Haal `rakdeel_id` en `model_pad` uit hiërarchisch pad."""
    delen = [deel for deel in pad.split("/") if deel]
    if len(delen) < 2:
        return "", ""

    rakdeel_id = delen[1]
    model_pad = "/".join(delen[2:]) if len(delen) > 2 else "rakdeel"
    return rakdeel_id, model_pad
