from tekstherkenning_ark.constants import DATA_DIR
from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat
from tekstherkenning_ark.models.rak import Rak

import pandas as pd

CSV_DIR = DATA_DIR / "csv"
CSV_DIR.mkdir(exist_ok=True)

HOUTMONSTER_TABLE_NAME = "houtmonsters"
PALEN_TABLE_NAME = "palen"
KESPEN_TABLE_NAME = "kespen"
GEBREKEN_TABLE_NAME = "gebreken"

logger = get_logger(__name__)

if __name__ == "__main__":

    pdf_rapporten = [file for file in (DATA_DIR / "duikrapporten").glob("*.pdf")]

    # Columns: rak id, rakdeel details
    rakdeel_rows = []

    # Columns: rak id, rakdeel id, paal id, houtmonster details
    houtmonster_rows = []

    # Columns:rak id, rakdeel id, paal details, afstand van startrak, main paal id, paalrij
    palen_rows = []

    # Columns: rak id, rakdeel id, kesp details, main kesp id
    kespen_rows = []

    # gebreken
    # Columns: rak id, rakdeel id, gebrek details
    gebreken_rows = []

    # Gebreken per type: pad, gebrek details, verwijzing naar id in gebreken_rows (FK)
    gebreken_rows_per_type: dict[str, list] = {}

    for file in pdf_rapporten:
        if not "boor" in file.stem.lower():

            doc = SmartDocument.from_pdf(file)
            print(f"Genereren van Rak object voor {doc.pdf_path.name}...")
            rak = Rak.from_smart_document(doc, use_caching=True)

            # Rakdeel data
            for rakdeel in rak.rakdelen:
                rakdeel_row = {
                    "rak_id": rak.raknaam,
                    **rakdeel.model_dump(),
                }
                rakdeel_rows.append(rakdeel_row)

            # Houtmonster table data
            houtmonsters = rak.alle_houtmonsters
            for rakdeel_id, paal_id, houtmonster in houtmonsters:
                houtmonster_row = {
                    "rak_id": rak.raknaam,
                    "rakdeel_id": rakdeel_id,
                    "paal_nummer": paal_id,
                    **houtmonster.model_dump(),
                }
                houtmonster_rows.append(houtmonster_row)

            # Kesp table data
            for rakdeel_id, kesp in rak.alle_kespen:
                kesp_row = {
                    "rak_id": rak.raknaam,
                    "rakdeel_id": rakdeel_id,
                    "main_kesp_id": kesp.kesp_nummer_main,
                    **kesp.model_dump(),
                }
                kespen_rows.append(kesp_row)

            # Paal table data
            for rakdeel in rak.rakdelen:
                afstand_van_startrak_cm = 0

                for paal in rakdeel.onderbouw.palen:
                    paal_row = {
                        "rak_id": rak.raknaam,
                        "rakdeel_id": rakdeel.rakdeel_id,
                        "paal_nummer": paal.paal_nummer,
                        "afstand_van_startrak_cm": afstand_van_startrak_cm,
                        "afstand_op_paalrij_cm": paal.hoh_afstand_cm if paal.paalrij_nummer == 2 else 0,
                        "paal_nummer_main": paal.paal_nummer_main,
                        "paalrij_nummer": paal.paalrij_nummer,
                        **paal.model_dump(),
                    }
                    palen_rows.append(paal_row)

                    if paal.paalrij_nummer == 1 and not afstand_van_startrak_cm is None:
                        afstand_van_startrak_cm = (
                            (afstand_van_startrak_cm + paal.hoh_afstand_cm) if paal.hoh_afstand_cm else None
                        )

            # Gebreken data
            for pad, gebrek in rak.alle_gebreken:
                rakdeel_id = pad.split("/")[1]

                gebrek_type = type(gebrek).__name__
                gebrek_row = {
                    "rak_id": rak.raknaam,
                    "rakdeel_id": rakdeel_id,
                    "pad": pad,
                    "gebrek_type": gebrek_type,
                    **gebrek.model_dump(),
                }

                # Voeg toe aan algemene gebreken tabel
                gebreken_rows.append(gebrek_row)

                # Voeg toe aan gebreken per type tabel, met verwijzing naar algemene gebreken tabel
                if gebrek_type not in gebreken_rows_per_type:
                    gebreken_rows_per_type[gebrek_type] = []

                gebreken_rows_per_type[gebrek_type].append({**gebrek_row, "gebrek_id": len(gebreken_rows) - 1})

    # Filter out all OnverwachtResultaat values
    n_onverwacht = 0

    for rows in [
        rakdeel_rows,
        houtmonster_rows,
        palen_rows,
        kespen_rows,
        gebreken_rows,
        *list(gebreken_rows_per_type.values()),
    ]:
        for row in rows:
            for key, value in row.items():
                if isinstance(value, OnverwachtResultaat):
                    n_onverwacht += 1
                    row[key] = value.waarde

    logger.info(f"{n_onverwacht} onverwachte resultaten gevonden en omgezet naar hun waarde in de CSV export.")

    # Zet om naar DataFrames en exporteer naar CSV

    csv_args = {"index": True, "sep": ";", "index_label": "id"}

    logger.info(f"Exporteer {len(rakdeel_rows)} rakdelen naar CSV")
    rakdeel_df = pd.DataFrame(rakdeel_rows).replace("\n", " ", regex=True)
    rakdeel_df.to_csv(CSV_DIR / "rakdelen.csv", **csv_args)

    logger.info(f"Exporteer {len(houtmonster_rows)} houtmonsters naar CSV")
    houtmonsters_df = pd.DataFrame(houtmonster_rows).replace("\n", " ", regex=True)
    houtmonsters_df.to_csv(CSV_DIR / f"{HOUTMONSTER_TABLE_NAME}.csv", **csv_args)

    logger.info(f"Exporteer {len(palen_rows)} palen naar CSV")
    palen_df = pd.DataFrame(palen_rows).replace("\n", " ", regex=True)
    palen_df.to_csv(CSV_DIR / f"{PALEN_TABLE_NAME}.csv", **csv_args)

    logger.info(f"Exporteer {len(kespen_rows)} kespen naar CSV")
    kespen_df = pd.DataFrame(kespen_rows).replace("\n", " ", regex=True)
    kespen_df.to_csv(CSV_DIR / f"{KESPEN_TABLE_NAME}.csv", **csv_args)

    logger.info(f"Exporteer {len(gebreken_rows)} gebreken naar CSV")
    gebreken_df = pd.DataFrame(gebreken_rows).replace("\n", " ", regex=True)
    gebreken_df.to_csv(CSV_DIR / f"{GEBREKEN_TABLE_NAME}.csv", **csv_args)

    for gebrek_type, rows in gebreken_rows_per_type.items():
        logger.info(f"Exporteer {len(rows)} gebreken van type {gebrek_type} naar CSV")
        df = pd.DataFrame(rows).replace("\n", " ", regex=True)
        df.to_csv(CSV_DIR / f"{GEBREKEN_TABLE_NAME}_{gebrek_type}.csv", **csv_args)
