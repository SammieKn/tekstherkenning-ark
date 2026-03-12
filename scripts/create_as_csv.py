from tekstherkenning_ark.export_utils import get_dfs_from_pdfs
from tekstherkenning_ark.constants import DATA_DIR
from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat
from tekstherkenning_ark.models.rak import Rak

import pandas as pd

CSV_DIR = DATA_DIR / "csv"
CSV_DIR.mkdir(exist_ok=True)

logger = get_logger(__name__)

if __name__ == "__main__":

    pdf_rapporten = [file for file in (DATA_DIR / "duikrapporten").glob("*.pdf")]
    df_dict = get_dfs_from_pdfs(pdf_rapporten)

    # Zet om naar DataFrames en exporteer naar CSV
    for name, df in df_dict.items():
        logger.info(f"Exporteer {len(df)} rijen van {name} naar CSV")
        df.to_csv(CSV_DIR / f"{name}.csv", index=False, sep=";")
