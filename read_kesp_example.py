"""
- Use azure document intelligence to get the data of the attributes of the different data models
- In ./data there are the reports that need to be read. loop over them
- we work on a first poc, start small
- parse the document so we can analyse the results
- use ./.env for the environment variables
"""

from pathlib import Path

from src.tekstherkenning_ark.parsed_pdf import ParsedPDF
from tekstherkenning_ark.constants import DATA_DIR
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.models.paal import Paal

TEST_PDF_PATH = DATA_DIR / "HEG0801_Houtmonstername&VisueleInspectie_V1.1_20220311.pdf"


def main():
    """Main function to process documents using Azure Document Intelligence."""
    print(f"\nProcessing: {TEST_PDF_PATH.name}")

    # Create ParsedPDF instance from PDF file
    parsed_pdf = ParsedPDF.from_pdf(TEST_PDF_PATH, use_cache=True)

    # Print results to console
    # parsed_pdf.print()

    # Save results to JSON
    # parsed_pdf.to_json()

    # Save full results to PDF
    # parsed_pdf.to_pdf()

    tables = parsed_pdf.result.tables[94:100]  # Kespen tables
    kesp_dict = Kesp.from_doc_tables(tables)

    for constructie, kespen in kesp_dict.items():
        print(f"\nConstructie ID: {constructie}")
        for kesp in kespen:
            print(kesp.kespnummer)


if __name__ == "__main__":
    main()
