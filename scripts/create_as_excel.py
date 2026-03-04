from datetime import datetime

from tekstherkenning_ark.export_utils import get_dfs_from_pdfs
from tekstherkenning_ark.constants import DATA_DIR
from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat
from tekstherkenning_ark.models.rak import Rak

import pandas as pd

EXCEL_EXPORT_DIR = DATA_DIR / "excel_exports"
EXCEL_EXPORT_DIR.mkdir(exist_ok=True)

logger = get_logger(__name__)

if __name__ == "__main__":

    pdf_rapporten = [file for file in (DATA_DIR / "duikrapporten").glob("*.pdf")]
    df_dict = get_dfs_from_pdfs(pdf_rapporten)

    # Zet om naar DataFrames en exporteer naar Excel met meerdere sheets
    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    excel_path = EXCEL_EXPORT_DIR / f"export_{timestamp}.xlsx"

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for name, df in df_dict.items():
            logger.info(f"Exporteer {len(df)} rijen van {name} naar Excel sheet")
            df.to_excel(writer, sheet_name=name, index=False)

    logger.info(f"Excel bestand opgeslagen: {excel_path}")
