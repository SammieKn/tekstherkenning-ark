"""
In dit script, converteren we `Rak` objects naar Excel-bestanden.

Gebruik:
    python scripts/rak_to_excel.py [--pdf PAD_NAAR_PDF] [--output OUTPUT_DIR]

Het script laadt een Rak uit een PDF en exporteert de data naar Excel met:
- Per gebrek-type een sheet met alle gebreken van dat type
- Onderdeel_Aantasting: toestandsbepaling per rakdeel
- Kespen: alle kespen met rakdeel referentie
- Palen: alle palen met rakdeel referentie
- Houtmonsters: alle houtmonsters met paal en rakdeel referentie
"""

import argparse
from pathlib import Path

from tekstherkenning_ark import constants
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.smart_document import SmartDocument


def main():
    """Hoofdfunctie voor het exporteren van Rak data naar Excel."""
    doc = SmartDocument.from_pdf(constants.TEST_PDF_PATH)

    rak = Rak.from_smart_document(doc)
    # parser = argparse.ArgumentParser(description="Exporteer Rak data naar Excel")
    # parser.add_argument(
    #     "--pdf",
    #     type=Path,
    #     default=constants.TEST_PDF_PATH,
    #     help="Pad naar de PDF om te verwerken",
    # )
    # parser.add_argument(
    #     "--output",
    #     type=Path,
    #     default=None,
    #     help="Output directory voor Excel-bestanden (standaard: data/excel_exports)",
    # )
    # args = parser.parse_args()

    # print(f"Laden van PDF: {args.pdf}")
    # doc = SmartDocument.from_pdf(args.pdf)

    # print("Genereren van Rak object...")
    # rak = Rak.from_smart_document(doc)

    print("Exporteren naar Excel...")
    export_pad = rak.to_excel()

    print(f"Klaar! Bestand opgeslagen: {export_pad}")


if __name__ == "__main__":
    main()
