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

    tables = parsed_pdf.result.tables[89:94]
    paal_dict = Paal.from_doc_tables(tables)

    for constructie, palen in paal_dict.items():
        print(f"\nConstructie ID: {constructie}")
        for paal in palen:
            print(paal)


if __name__ == "__main__":
    main()
