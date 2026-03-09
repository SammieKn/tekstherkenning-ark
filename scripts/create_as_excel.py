from datetime import datetime

from tekstherkenning_ark.export_utils import get_dfs_from_pdfs
from tekstherkenning_ark.constants import DATA_DIR
from tekstherkenning_ark.logger import get_logger

import pandas as pd

EXCEL_EXPORT_DIR = DATA_DIR / "excel_exports"
EXCEL_EXPORT_DIR.mkdir(exist_ok=True)

logger = get_logger(__name__)

if __name__ == "__main__":

    pdf_rapporten = [file for file in (DATA_DIR / "duikrapporten").glob("*.pdf")]
    df_dict = get_dfs_from_pdfs(pdf_rapporten)

    # Zet om naar DataFrames en exporteer naar Excel met meerdere sheets
    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    excel_path = EXCEL_EXPORT_DIR / f"table_export_{timestamp}.xlsx"

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for name, df in df_dict.items():
            logger.info(f"Exporteer {len(df)} rijen van {name} naar Excel sheet")
            sheet_name = name[:30]
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Autofit kolommen
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Max 50 voor leesbaarheid
                worksheet.column_dimensions[column_letter].width = adjusted_width

    logger.info(f"Excel bestand opgeslagen: {excel_path}")
