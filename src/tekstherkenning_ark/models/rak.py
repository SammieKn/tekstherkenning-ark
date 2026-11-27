from __future__ import annotations

import asyncio
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ConfigDict, computed_field

from tekstherkenning_ark import constants
from tekstherkenning_ark.constants import DATA_DIR
from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.export_utils import (
    NOMIC_DOCUMENT_TABLE_NAME,
    NOMIC_SAMENVATTING_TABLE_NAME,
    NOMIC_WIJZIGINGEN_TABLE_NAME,
    haal_rakdeel_id_en_model_pad,
    remove_collection_fields,
    remove_onverwacht_resultaat_from_table_rows,
    remove_unsafe_values_for_excel,
    waarde_naar_excel,
)
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.models.boorweerstandsmeting import Boorweerstandsmeting
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.houtmonster import Houtmonster
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.models.nomic_record import NomicRecord
from tekstherkenning_ark.models.onderbouw import Onderbouw
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.rak_base_model import RakBaseModel
from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.models.toestand_onderdeel import ToestandOnderdeel

logger = get_logger(__name__)


class Rak(RakBaseModel):
    """Rak.

    Attributes:
        rakdelen: Lijst van rakdelen waaruit het rak is opgebouwd.
        raknaam: Naam of code van het rak.
        totale_lengte_m: Totale lengte van het rak in meters.
        unassigned_palen: Palen die niet aan een specifiek rakdeel zijn toegewezen.
        unassigned_kespen: Kespen die niet aan een specifiek rakdeel zijn toegewezen.
        unassigned_houtmonsters: Houtmonsters die niet aan een specifieke paal zijn toegewezen.
        boorweerstandsmetingen: Boorweerstandsmetingen uit de aanvullende Nomic CSV.
        nomic_document: Rijen uit de aanvullende document.csv.
        nomic_samenvattingen: Rijen uit de aanvullende samenvatting.csv.
        nomic_wijzigingen: Rijen uit de aanvullende wijzigingen.csv.
        opmerkingen: Eventuele opmerkingen (inherited from RakBaseModel).

    Properties (berekend):
        aantal_rakdelen: Totaal aantal rakdelen in dit rak.
        alle_palen: Verzameling van alle palen uit alle rakdelen.
        alle_kespen: Verzameling van alle kespen uit alle rakdelen.
        alle_houtmonsters: Verzameling van alle houtmonsters uit alle palen.
    """

    model_config = ConfigDict(
        use_enum_values=True,
    )
    # Elk rakdeel heeft een eigen constructietype.
    rakdelen: list[Rakdeel]
    # Te vinden in de rapporttitel, projectgegevens of paragraaf 2.2.1 (paspoortgegevens).
    raknaam: str
    # Te vinden in paragraaf 2.2.1 (paspoortgegevens) en/of de constructiebeschrijving (eerste zin van paragraaf 5.x).
    totale_lengte_m: float

    unassigned_palen: list[Paal] = []
    unassigned_kespen: list[Kesp] = []
    unassigned_houtmonsters: list[Houtmonster] = []
    boorweerstandsmetingen: list[Boorweerstandsmeting] = []
    nomic_document: list[NomicRecord] = []
    nomic_samenvattingen: list[NomicRecord] = []
    nomic_wijzigingen: list[NomicRecord] = []

    @classmethod
    def from_nomic_df(cls, frame: pd.DataFrame) -> list[Rak]:
        """Create Rak metadata objects from the Nomic rak table.

        Parameters
        ----------
        frame : pandas.DataFrame
            Rows from ``rakken.csv``.

        Returns
        -------
        list[Rak]
            Rak metadata objects in source row order.
        """
        fields = ("raknaam", "totale_lengte_m", "opmerkingen")
        cls._require_nomic_columns(frame, fields)
        rakken = []
        for row in frame.to_dict(orient="records"):
            values = cls.nomic_model_values(row, fields)
            rakken.append(cls(rakdelen=[], **values))
        return rakken

    @classmethod
    def from_nomic_csvs(cls, csv_dir: Path) -> Rak:
        """Load Nomic tables through their model parsers and assemble one Rak hierarchy."""

        parsers = {
            "Rak": cls.from_nomic_df,
            "Rakdeel": Rakdeel.from_nomic_df,
            "Boorweerstandsmeting": Boorweerstandsmeting.from_nomic_df,
            "Paal": Paal.from_nomic_df,
            "Kesp": Kesp.from_nomic_df,
            "Gebrek": Gebrek.from_nomic_df,
            "ToestandOnderdeel": ToestandOnderdeel.from_nomic_df,
            "Houtmonster": Houtmonster.from_nomic_df,
            "NomicDocument": NomicRecord.from_nomic_df,
            "NomicSamenvatting": NomicRecord.from_nomic_df,
            "NomicWijziging": NomicRecord.from_nomic_df,
        }

        # Load all CSV data and parse objects
        parsed: dict[str, Any] = {}
        for class_name, file_name in constants.NOMIC_CSV_FILES.items():
            path = csv_dir / file_name
            if not path.is_file():
                if class_name in constants.OPTIONAL_NOMIC_CSV_CLASSES:
                    frame = pd.DataFrame()
                else:
                    raise FileNotFoundError(f"Required Nomic CSV file not found: {path}")
            else:
                logger.info(f"Reading {path}")
                frame = pd.read_csv(path, keep_default_na=False)
            parsed[class_name] = parsers[class_name](frame)

        rak_objects = parsed["Rak"]
        if len(rak_objects) != 1:
            rak_path = csv_dir / constants.NOMIC_CSV_FILES["Rak"]
            raise ValueError(f"Expected exactly one rak record in {rak_path}")

        rak = rak_objects[0]
        rak.boorweerstandsmetingen = parsed["Boorweerstandsmeting"]
        rak.nomic_document = parsed["NomicDocument"]
        rak.nomic_samenvattingen = parsed["NomicSamenvatting"]
        rak.nomic_wijzigingen = parsed["NomicWijziging"]
        if not rak.raknaam.strip():
            raise ValueError(f"The raknaam in {csv_dir / constants.NOMIC_CSV_FILES['Rak']} must not be empty")
        rakdelen: list[Rakdeel] = parsed["Rakdeel"]
        rakdeel_by_id = {rakdeel.rakdeel_id: rakdeel for rakdeel in rakdelen}
        if len(rakdeel_by_id) != len(rakdelen):
            raise ValueError("rakdelen.csv contains duplicate rakdeel IDs")
        for rakdeel in rakdelen:
            rakdeel.bovenbouw = Bovenbouw()
            rakdeel.onderbouw = Onderbouw(palen=[], kespen=[])
        rak.rakdelen = rakdelen

        palen_by_id: dict[str, list[Paal]] = parsed["Paal"]
        kespen_by_id: dict[str, list[Kesp]] = parsed["Kesp"]
        paal_count = sum(len(palen) for palen in palen_by_id.values())
        kesp_count = sum(len(kespen) for kespen in kespen_by_id.values())
        # if paal_count != sum(len(set(paal.paal_nummer for paal in palen)) for palen in palen_by_id.values()):
        #     raise ValueError("palen.csv contains duplicate paal numbers within a rakdeel")
        # if kesp_count != sum(len(set(kesp.kesp_nummer for kesp in kespen)) for kespen in kespen_by_id.values()):
        #     raise ValueError("kespen.csv contains duplicate kesp numbers within a rakdeel")
        for rakdeel_id, palen in palen_by_id.items():
            if rakdeel_id in rakdeel_by_id:
                rakdeel_by_id[rakdeel_id].onderbouw.palen = palen
            else:
                rak.unassigned_palen.extend(palen)
        for rakdeel_id, kespen in kespen_by_id.items():
            if rakdeel_id in rakdeel_by_id:
                rakdeel_by_id[rakdeel_id].onderbouw.kespen = kespen
            else:
                rak.unassigned_kespen.extend(kespen)

        paal_by_key = {
            (rakdeel_id, paal.paal_nummer): paal for rakdeel_id, palen in palen_by_id.items() for paal in palen
        }
        houtmonsters_by_paal: dict[tuple[str, str], list[Houtmonster]] = parsed["Houtmonster"]
        for key, houtmonsters in houtmonsters_by_paal.items():
            paal = paal_by_key.get(key)
            if paal is None:
                rak.unassigned_houtmonsters.extend(houtmonsters)
            else:
                paal.houtmonsters.extend(houtmonsters)

        toestanden_by_id: dict[str, list[ToestandOnderdeel]] = parsed["ToestandOnderdeel"]
        for rakdeel_id, toestanden in toestanden_by_id.items():
            rakdeel = rakdeel_by_id.get(rakdeel_id)
            if rakdeel is None:
                rak.toestand_onderdelen.extend(toestanden)
                continue
            rakdeel.toestand_onderdelen.extend(toestanden)
            rakdeel.assign_toestandsbepalingen_to_children()

        gebreken_by_target: dict[tuple[str, str, str], list[Gebrek]] = parsed["Gebrek"]
        for (rakdeel_id, model_pad, component_id), gebreken in gebreken_by_target.items():
            rakdeel = rakdeel_by_id.get(rakdeel_id)
            if rakdeel is None:
                rak.gebreken.extend(gebreken)
                if rakdeel_id:
                    logger.warning(f"Gebreken refer to unknown rakdeel {rakdeel_id!r}; assigned to Rak")
                continue
            if model_pad in {"", "rakdeel"}:
                rakdeel.gebreken.extend(gebreken)
            elif model_pad == "bovenbouw":
                rakdeel.bovenbouw.gebreken.extend(gebreken)
            elif model_pad == "onderbouw":
                rakdeel.onderbouw.gebreken.extend(gebreken)
            elif model_pad == "onderbouw/vloer" and rakdeel.onderbouw.vloer is not None:
                rakdeel.onderbouw.vloer.gebreken.extend(gebreken)
            elif model_pad == "onderbouw/onderloopsheidscherm" and rakdeel.onderbouw.onderloopsheidscherm is not None:
                rakdeel.onderbouw.onderloopsheidscherm.gebreken.extend(gebreken)
            elif model_pad == "onderbouw/palen":
                paal = paal_by_key.get((rakdeel_id, component_id))
                (paal.gebreken if paal else rakdeel.gebreken).extend(gebreken)
            elif model_pad == "onderbouw/kespen":
                kesp = next(
                    (item for item in rakdeel.onderbouw.kespen if item.kesp_nummer == component_id),
                    None,
                )
                (kesp.gebreken if kesp else rakdeel.gebreken).extend(gebreken)
            else:
                rakdeel.gebreken.extend(gebreken)
                logger.warning(f"Unknown model_pad {model_pad!r}; assigned defects to rakdeel {rakdeel_id!r}")

        return rak

    @property
    def identifier(self) -> str:
        """Return a string that uniquely identifies this Rak instance."""
        return str(self.raknaam)

    @computed_field
    @property
    def aantal_rakdelen(self) -> int:
        """Totaal aantal rakdelen in dit rak."""
        return len(self.rakdelen)

    @property
    def alle_palen(self) -> list[tuple[str, Paal]]:
        """Verzamel alle palen uit alle rakdelen.

        Returns
        -------
        list[tuple[str, Paal]]
            Lijst van tuples met (rakdeel_id, paal).
        """
        resultaat: list[tuple[str, Paal]] = []
        for rakdeel in self.rakdelen:
            for paal in rakdeel.onderbouw.palen:
                resultaat.append((rakdeel.rakdeel_id, paal))

        # Add unassigned palen
        for paal in self.unassigned_palen:
            resultaat.append(("unassigned", paal))
        return resultaat

    @property
    def alle_kespen(self) -> list[tuple[str, Kesp]]:
        """Verzamel alle kespen uit alle rakdelen.

        Returns
        -------
        list[tuple[str, Kesp]]
            Lijst van tuples met (rakdeel_id, kesp).
        """
        resultaat: list[tuple[str, Kesp]] = []
        for rakdeel in self.rakdelen:
            for kesp in rakdeel.onderbouw.kespen:
                resultaat.append((rakdeel.rakdeel_id, kesp))

        # Add unassigned kespen
        for kesp in self.unassigned_kespen:
            resultaat.append(("unassigned", kesp))
        return resultaat

    @property
    def alle_houtmonsters(self) -> list[tuple[str, Houtmonster]]:
        """Verzamel alle houtmonsters uit alle palen in alle rakdelen.

        Returns
        -------
        list[tuple[str, Houtmonster]]
            Lijst van tuples met (rakdeel_id, houtmonster).
        """
        resultaat: list[tuple[str, Houtmonster]] = []
        for rakdeel in self.rakdelen:
            for paal in rakdeel.onderbouw.palen:
                for houtmonster in paal.houtmonsters:
                    resultaat.append((rakdeel.rakdeel_id, houtmonster))

        # Add unassigned houtmonsters
        for houtmonster in self.unassigned_houtmonsters:
            resultaat.append(("unassigned", houtmonster))
        return resultaat

    def to_excel(self, export_dir: Path | None = None) -> Path:
        """Exporteer alle data van dit Rak naar een Excel-bestand.

        Maakt de volgende sheets:
        - Per gebrek-type een sheet met alle gebreken van dat type
        - Onderdeel_Aantasting: toestandsbepaling per rakdeel
        - Kespen: alle kespen met rakdeel referentie
        - Palen: alle palen met rakdeel referentie
        - Houtmonsters: alle houtmonsters met paal en rakdeel referentie
        - Boorweerstandsmetingen: alle metingen met rakdeel en paal referentie

        Parameters
        ----------
        export_dir : Path, optioneel
            Directory voor export. Standaard DATA_DIR / 'excel_exports'.

        Returns
        -------
        Path
            Pad naar het gegenereerde Excel-bestand.
        """
        if export_dir is None:
            export_dir = DATA_DIR / "excel_exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        raknaam_safe = self.raknaam.replace("/", "_").replace("\\", "_") or "onbekend_rak"
        bestandsnaam = f"{raknaam_safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        export_pad = export_dir / bestandsnaam

        with pd.ExcelWriter(export_pad, engine="openpyxl") as writer:
            sheets_geschreven = 0

            for sheet_name, dataframe in (
                ("Rak", self._get_rak_df()),
                ("Rakdelen", self._get_rakdeel_df()),
                ("Bovenbouw", self._get_bovenbouw_df()),
                ("Onderbouw", self._get_onderbouw_df()),
            ):
                if not dataframe.empty:
                    remove_unsafe_values_for_excel(dataframe).to_excel(writer, sheet_name=sheet_name, index=False)
                    sheets_geschreven += 1

            # Sheet: Gebreken per type
            gebreken_per_type: dict[str, list[dict]] = {}
            for rakdeel_id, gebrek in self.alle_gebreken:
                type_naam = type(gebrek).__name__
                if type_naam not in gebreken_per_type:
                    gebreken_per_type[type_naam] = []
                gebrek_dict = gebrek.model_dump()
                gebrek_dict["rakdeel_id"] = rakdeel_id
                gebreken_per_type[type_naam].append(gebrek_dict)

            for type_naam, gebreken_list in gebreken_per_type.items():
                df = pd.DataFrame(gebreken_list)
                # Zet rakdeel_id als eerste kolom
                kolommen = ["rakdeel_id"] + [k for k in df.columns if k != "rakdeel_id"]
                df = df[kolommen]
                sheet_naam = f"Gebreken_{type_naam}"[:31]  # Excel max 31 chars
                remove_unsafe_values_for_excel(df).to_excel(writer, sheet_name=sheet_naam, index=False)
                sheets_geschreven += 1

            # Sheet: Onderdeel Aantasting (hiërarchisch)
            aantasting_rows = []
            for pad, toestandonderdeel in self.alle_toestandsbepalingen:
                rakdeel_id, model_pad = haal_rakdeel_id_en_model_pad(pad)
                aantasting_rows.append(
                    {
                        "rakdeel_id": rakdeel_id,
                        "model_pad": model_pad,
                        "onderdeel": toestandonderdeel.constructie_onderdeel,
                        "aangetast": waarde_naar_excel(toestandonderdeel.aangetast),
                        **toestandonderdeel.model_dump(
                            mode="python",
                            exclude={"constructie_onderdeel", "aangetast"},
                        ),
                    }
                )

            if aantasting_rows:
                df_aantasting = pd.DataFrame(aantasting_rows)
                remove_unsafe_values_for_excel(df_aantasting).to_excel(
                    writer, sheet_name="Onderdeel_Aantasting", index=False
                )
                sheets_geschreven += 1

            # Sheet: Kespen
            kespen_rows = []
            for rakdeel_id, kesp in self.alle_kespen:
                kesp_dict = kesp.model_dump(exclude={"gebreken"})
                kesp_dict["rakdeel_id"] = rakdeel_id
                kespen_rows.append(kesp_dict)
            if kespen_rows:
                df_kespen = pd.DataFrame(kespen_rows)
                kolommen = ["rakdeel_id"] + [k for k in df_kespen.columns if k != "rakdeel_id"]
                df_kespen = df_kespen[kolommen]
                remove_unsafe_values_for_excel(df_kespen).to_excel(writer, sheet_name="Kespen", index=False)
                sheets_geschreven += 1

            # Sheet: Palen
            palen_rows = []
            for rakdeel_id, paal in self.alle_palen:
                paal_dict = paal.model_dump(exclude={"gebreken", "houtmonsters"})
                paal_dict["rakdeel_id"] = rakdeel_id
                palen_rows.append(paal_dict)
            if palen_rows:
                df_palen = pd.DataFrame(palen_rows)
                kolommen = ["rakdeel_id"] + [k for k in df_palen.columns if k != "rakdeel_id"]
                df_palen = df_palen[kolommen]
                remove_unsafe_values_for_excel(df_palen).to_excel(writer, sheet_name="Palen", index=False)
                sheets_geschreven += 1

            # Sheet: Houtmonsters
            houtmonster_rows = []
            for rakdeel_id, houtmonster in self.alle_houtmonsters:
                hm_dict = houtmonster.model_dump()
                hm_dict["rakdeel_id"] = rakdeel_id
                hm_dict["paal_nummer_ref"] = houtmonster.paal_nummer
                houtmonster_rows.append(hm_dict)
            if houtmonster_rows:
                df_houtmonsters = pd.DataFrame(houtmonster_rows)
                kolommen = ["rakdeel_id", "paal_nummer_ref"] + [
                    k for k in df_houtmonsters.columns if k not in ["rakdeel_id", "paal_nummer_ref"]
                ]
                df_houtmonsters = df_houtmonsters[kolommen]
                remove_unsafe_values_for_excel(df_houtmonsters).to_excel(
                    writer, sheet_name="Houtmonsters", index=False
                )
                sheets_geschreven += 1

            # Sheet: Boorweerstandsmetingen
            df_boorweerstandsmetingen = self._get_boorweerstandsmetingen_df()
            if not df_boorweerstandsmetingen.empty:
                remove_unsafe_values_for_excel(df_boorweerstandsmetingen).to_excel(
                    writer, sheet_name="Boorweerstandsmetingen", index=False
                )
                sheets_geschreven += 1

            for sheet_name, dataframe in (
                ("Document", self._get_nomic_document_df()),
                ("Samenvatting", self._get_nomic_samenvatting_df()),
                ("Wijzigingen", self._get_nomic_wijzigingen_df()),
            ):
                if not dataframe.empty:
                    remove_unsafe_values_for_excel(dataframe).to_excel(writer, sheet_name=sheet_name, index=False)
                    sheets_geschreven += 1

            # Fallback: als er geen data is, maak een lege info sheet
            if sheets_geschreven == 0:
                df_info = pd.DataFrame(
                    {
                        "info": [
                            f"Rak: {self.raknaam}",
                            f"Totale lengte: {self.totale_lengte_m} m",
                            f"Aantal rakdelen: {len(self.rakdelen)}",
                            "Geen gedetailleerde data beschikbaar.",
                        ]
                    }
                )
                df_info.to_excel(writer, sheet_name="Info", index=False)

        print(f"Excel geëxporteerd naar: {export_pad}")
        return export_pad

    @classmethod
    def from_smart_document(cls, doc: SmartDocument, use_caching: bool = True) -> Rak:
        """Maak een Rak-object en alle bijbehorende subobjecten aan vanuit een SmartDocument."""

        cache_file = constants.CACHE_DIR / f"rak_{doc.document_name}.pkl"
        if cache_file.exists() and use_caching:
            logger.info(f"Loading cached Rak from {cache_file}")
            rak_instance = pickle.loads(cache_file.read_bytes())
            return rak_instance

        raknaam = doc.get_raknaam()

        # Laad palen, kespen en houtmonsters uit tabellen
        paal_structured_table = doc.get_meettabel_fundering_paal()
        palen_dict = Paal.from_doc_tables(paal_structured_table)

        kesp_structured_table = doc.get_meettabel_fundering_kesp()
        kespen_dict = Kesp.from_doc_tables(kesp_structured_table)

        houtmonster_structured_table = doc.get_meettabel_houtmonsters()
        houtmonsters = Houtmonster.from_doc_tables(houtmonster_structured_table)

        cls.assign_houtmonsters_to_palen(palen_dict=palen_dict, houtmonsters=houtmonsters)

        # Maak rakdelen aan (parallel via async)
        rakdeel_sections = doc.get_rakdeel_secties()

        async def maak_rakdelen_async():
            rakdeel_taken = [
                Rakdeel.from_smart_doc_section(
                    section=section,
                    palen_dict=palen_dict,
                    kespen_dict=kespen_dict,
                )
                for section in rakdeel_sections
            ]
            return await asyncio.gather(*rakdeel_taken)

        rakdelen = asyncio.run(maak_rakdelen_async())

        # raknaam = doc.get_raknaam()
        # totale_lengte_m = doc.get_rak_totale_lengte_m()
        # opmerkingen = doc.get_rak_opmerkingen()

        # Validate all constructie ids in palen and kespen are present in rakdelen, otherwise log a warning
        rakdeel_ids = sorted([rd.rakdeel_id for rd in rakdelen])
        gevonden_constructie_ids = sorted(list(set(list(palen_dict.keys()) + list(kespen_dict.keys()))))
        for constructie_id in gevonden_constructie_ids:
            if constructie_id and not any(
                constructie_id.lower().startswith(rakdeel_id.lower()) for rakdeel_id in rakdeel_ids
            ):
                logger.warning(f"Constructie ID '{constructie_id}' found in palen/kespen but not in rakdelen")

        # Create rak instance
        rak_instance = cls(
            rakdelen=list(rakdelen),
            raknaam=raknaam,
            totale_lengte_m=0.0,  # TODO
            opmerkingen="",
        )

        # Check if all palen, kespen and houtmonsters are correctly assigned to rakdelen
        rak_instance.check_assigned_objects(palen_dict=palen_dict, kespen_dict=kespen_dict, houtmonsters=houtmonsters)

        # Cache the created Rak instance
        cache_file.write_bytes(pickle.dumps(rak_instance))

        return rak_instance

    @staticmethod
    def assign_houtmonsters_to_palen(palen_dict: dict[str, list[Paal]], houtmonsters: list[Houtmonster]):
        """Plaats houtmonsters onder juiste palen op basis van paal_nummer of codering."""

        processed_houtmonsters: set[Houtmonster] = set()
        for _, palen in palen_dict.items():
            for paal in palen:
                paal.houtmonsters = [
                    hm
                    for hm in houtmonsters
                    if paal.paal_nummer == hm.paal_nummer or paal.paal_nummer == hm.codering.split("/")[2]
                ]
                if paal.houtmonsters:
                    processed_houtmonsters.update(set(paal.houtmonsters))

    def check_assigned_objects(
        self, palen_dict: dict[str, list[Paal]], kespen_dict: dict[str, list[Kesp]], houtmonsters: list[Houtmonster]
    ):
        """Controleer of alle palen, kespen en houtmonsters correct zijn toegewezen aan rakdelen.
        Indien niet, sla de niet toegewezen objecten op in het rak en log een waarschuwing."""

        # Get assigned objects from rak object
        assigned_palen = [p for _, p in self.alle_palen]
        assigned_kespen = [k for _, k in self.alle_kespen]
        assigned_houtmonsters = [hm for _, hm in self.alle_houtmonsters]

        # Check for unassigned palen
        unassigned_palen = []
        for palen in palen_dict.values():
            unassigned_palen.extend([p for p in palen if not p in assigned_palen])

        # Check for unassigned kespen
        unassigned_kespen = []
        for kespen in kespen_dict.values():
            unassigned_kespen.extend([k for k in kespen if not k in assigned_kespen])

        # Check for unassigned houtmonsters
        unassigned_houtmonsters = [hm for hm in houtmonsters if hm not in assigned_houtmonsters]

        # Log warnings for unassigned objects
        if unassigned_palen:
            logger.warning(
                f"{len(unassigned_palen)} palen could not be assigned to any rakdeel. Storing them in `unassigned_palen` list in Rak."
            )
            self.unassigned_palen = unassigned_palen

        if unassigned_kespen:
            logger.warning(
                f"{len(unassigned_kespen)} kespen could not be assigned to any rakdeel. Storing them in `unassigned_kespen` list in Rak."
            )
            self.unassigned_kespen = unassigned_kespen

        if unassigned_houtmonsters:
            logger.warning(
                f"{len(unassigned_houtmonsters)} houtmonsters could not be assigned to any paal. Storing them in `unassigned_houtmonsters` list in Rak."
            )
            self.unassigned_houtmonsters = unassigned_houtmonsters

    def _get_rak_df(self) -> pd.DataFrame:
        """Genereer een DataFrame tabel met rak data"""

        rows = [remove_collection_fields(self.model_dump(mode="python"))]
        rows = remove_onverwacht_resultaat_from_table_rows(rows)
        return pd.DataFrame(rows).replace("\n", " ", regex=True)

    def _get_rakdeel_df(self) -> pd.DataFrame:
        """Genereer een DataFrame tabel met rakdeel data"""

        rows = []
        for rakdeel in self.rakdelen:
            rakdeel_row = {
                "rak_id": self.raknaam,
                **remove_collection_fields(rakdeel.model_dump(mode="python")),
            }
            rows.append(rakdeel_row)

        rows = remove_onverwacht_resultaat_from_table_rows(rows)
        return pd.DataFrame(rows).replace("\n", " ", regex=True)

    def _get_houtmonsters_df(self) -> pd.DataFrame:
        """Genereer een DataFrame tabel met houtmonster data"""

        rows = []
        for rakdeel_id, houtmonster in self.alle_houtmonsters:
            houtmonster_row = {
                "rak_id": self.raknaam,
                "rakdeel_id": rakdeel_id,
                **remove_collection_fields(houtmonster.model_dump(mode="python")),
            }
            rows.append(houtmonster_row)

        rows = remove_onverwacht_resultaat_from_table_rows(rows)
        return pd.DataFrame(rows).replace("\n", " ", regex=True)

    def _get_boorweerstandsmetingen_df(self) -> pd.DataFrame:
        """Genereer een DataFrame tabel met boorweerstandsmetingen."""
        rows = [
            {
                "rak_id": self.raknaam,
                **remove_collection_fields(meting.model_dump(mode="python")),
            }
            for meting in self.boorweerstandsmetingen
        ]
        rows = remove_onverwacht_resultaat_from_table_rows(rows)
        return pd.DataFrame(rows).replace("\n", " ", regex=True)

    def _get_nomic_document_df(self) -> pd.DataFrame:
        """Build a dataframe from the document.csv rows."""
        return pd.DataFrame([record.model_dump(mode="python") for record in self.nomic_document])

    def _get_nomic_samenvatting_df(self) -> pd.DataFrame:
        """Build a dataframe from the samenvatting.csv rows."""
        return pd.DataFrame([record.model_dump(mode="python") for record in self.nomic_samenvattingen])

    def _get_nomic_wijzigingen_df(self) -> pd.DataFrame:
        """Build a dataframe from the wijzigingen.csv rows."""
        return pd.DataFrame([record.model_dump(mode="python") for record in self.nomic_wijzigingen])

    def _get_palen_df(self) -> pd.DataFrame:
        """Genereer een DataFrame tabel met paal data"""

        rows = []
        for rakdeel in self.rakdelen:
            afstand_van_startrak_cm = rakdeel.lengte_m * 100 if isinstance(rakdeel.lengte_m, (int, float)) else None

            for paal in rakdeel.onderbouw.palen:
                paal_row = {
                    "rak_id": self.raknaam,
                    "rakdeel_id": rakdeel.rakdeel_id,
                    "afstand_van_startrak_cm": afstand_van_startrak_cm,
                    **remove_collection_fields(paal.model_dump(mode="python")),
                }
                rows.append(paal_row)

                if paal.paal_nummer_main == 1 and afstand_van_startrak_cm is not None:
                    afstand_van_startrak_cm = (
                        (afstand_van_startrak_cm + paal.hoh_afstand_cm) if paal.hoh_afstand_cm else None
                    )

        rows = remove_onverwacht_resultaat_from_table_rows(rows)
        return pd.DataFrame(rows).replace("\n", " ", regex=True)

    def _get_kespen_df(self) -> pd.DataFrame:
        """Genereer een DataFrame tabel met kesp data"""

        rows = []
        for rakdeel_id, kesp in self.alle_kespen:
            kesp_row = {
                "rak_id": self.raknaam,
                "rakdeel_id": rakdeel_id,
                **remove_collection_fields(kesp.model_dump(mode="python")),
            }
            rows.append(kesp_row)

        rows = remove_onverwacht_resultaat_from_table_rows(rows)
        return pd.DataFrame(rows).replace("\n", " ", regex=True)

    def _get_gebreken_df(self) -> pd.DataFrame:
        """Genereer een DataFrame tabel met gebrek data"""

        rows = []
        for pad, gebrek in self.alle_gebreken:
            rakdeel_id, model_pad = haal_rakdeel_id_en_model_pad(pad)
            gebrek_type = type(gebrek).__name__
            gebrek_row = {
                "rak_id": self.raknaam,
                "rakdeel_id": rakdeel_id,
                "model_pad": model_pad,
                "gebrek_type": gebrek_type,
                **remove_collection_fields(gebrek.model_dump(mode="python")),
            }
            rows.append(gebrek_row)

        rows = remove_onverwacht_resultaat_from_table_rows(rows)
        return pd.DataFrame(rows).replace("\n", " ", regex=True)

    def _get_gebreken_per_type_dfs(self) -> dict[str, pd.DataFrame]:
        """Genereer DataFrame tabellen per gebrek type"""

        gebreken_per_type: dict[str, list[dict]] = {}
        for pad, gebrek in self.alle_gebreken:
            rakdeel_id, model_pad = haal_rakdeel_id_en_model_pad(pad)
            gebrek_type = type(gebrek).__name__
            gebrek_row = {
                "rak_id": self.raknaam,
                "rakdeel_id": rakdeel_id,
                "model_pad": model_pad,
                **remove_collection_fields(gebrek.model_dump(mode="python")),
            }

            if gebrek_type not in gebreken_per_type:
                gebreken_per_type[gebrek_type] = []
            gebreken_per_type[gebrek_type].append(gebrek_row)

        # Converteer naar DataFrames
        gebreken_dfs = {}
        for gebrek_type, rows in gebreken_per_type.items():
            df = pd.DataFrame(rows).replace("\n", " ", regex=True)
            gebreken_dfs[gebrek_type] = df

        return gebreken_dfs

    def _get_toestandsbepalingen_df(self) -> pd.DataFrame:
        """Genereer een DataFrame tabel met toestandsbepalingen data"""

        rows = []
        for pad, toestandonderdeel in self.alle_toestandsbepalingen:
            rakdeel_id, model_pad = haal_rakdeel_id_en_model_pad(pad)
            row = {
                "rak_id": self.raknaam,
                "rakdeel_id": rakdeel_id,
                "model_pad": model_pad,
                "onderdeel": toestandonderdeel.constructie_onderdeel,
                "aangetast": waarde_naar_excel(toestandonderdeel.aangetast),
                **toestandonderdeel.model_dump(mode="python", exclude={"constructie_onderdeel", "aangetast"}),
            }
            rows.append(row)

        rows = remove_onverwacht_resultaat_from_table_rows(rows)
        return pd.DataFrame(rows).replace("\n", " ", regex=True)

    def _get_onverwacht_resultaten_df(self) -> pd.DataFrame:
        """Genereer een DataFrame tabel met onverwacht resultaat data"""

        rows = []
        for pad, onverwacht in self.alle_onverwachte_resultaten:
            rakdeel_id, model_pad = haal_rakdeel_id_en_model_pad(pad)
            row = {
                "rak_id": self.raknaam,
                "rakdeel_id": rakdeel_id,
                "model_pad": model_pad,
                **remove_collection_fields(onverwacht.model_dump(mode="python")),
            }
            rows.append(row)

        rows = remove_onverwacht_resultaat_from_table_rows(rows)
        return pd.DataFrame(rows).replace("\n", " ", regex=True)

    def _get_onderbouw_df(self) -> pd.DataFrame:
        """Genereer een DataFrame tabel met onderbouw data"""

        rows = []
        for rakdeel in self.rakdelen:
            onderbouw_row = {
                "rak_id": self.raknaam,
                "rakdeel_id": rakdeel.rakdeel_id,
                **remove_collection_fields(rakdeel.onderbouw.model_dump(mode="python")),
            }
            rows.append(onderbouw_row)

        rows = remove_onverwacht_resultaat_from_table_rows(rows)
        return pd.DataFrame(rows).replace("\n", " ", regex=True)

    def _get_bovenbouw_df(self) -> pd.DataFrame:
        """Genereer een DataFrame tabel met bovenbouw data"""

        rows = []
        for rakdeel in self.rakdelen:
            bovenbouw_row = {
                "rak_id": self.raknaam,
                "rakdeel_id": rakdeel.rakdeel_id,
                **remove_collection_fields(rakdeel.bovenbouw.model_dump(mode="python")),
            }
            rows.append(bovenbouw_row)

        rows = remove_onverwacht_resultaat_from_table_rows(rows)
        return pd.DataFrame(rows).replace("\n", " ", regex=True)


if __name__ == "__main__":

    doc = SmartDocument.from_pdf(constants.TEST_PDF_PATH)

    rak = Rak.from_smart_document(doc, use_caching=False)

    for rd in rak.rakdelen:
        print(rd.rakdeel_id)
        for p in [p for p in rd.onderbouw.palen if p.gebreken]:
            print(f"  Paal: {p.paal_nummer}")
            for gebrek in p.gebreken:
                print(f"    Gebrek: {gebrek.codering}")

        for kesp in [k for k in rd.onderbouw.kespen if k.gebreken]:
            print(f"  Kesp: {kesp.kesp_nummer}")
            for gebrek in kesp.gebreken:
                print(f"    Gebrek: {gebrek.codering}")

        if rd.bovenbouw.gebreken:
            print(f"  Metselwerk gebreken:")
            for gebrek in rd.bovenbouw.gebreken:
                print(f"    Gebrek: {gebrek.codering}")

        for gebrek in rd.gebreken:
            print(f"  Rakdeel gebrek: {gebrek.codering}")
