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
from tekstherkenning_ark.document.smart_document import SmartDocument


def main():
    """Hoofdfunctie voor het exporteren van Rak data naar Excel."""
    pdf_rapporten = [file for file in (constants.DATA_DIR / "duikrapporten").glob("*.pdf")]

    for file in pdf_rapporten:
        if not "boor" in file.stem.lower():

            doc = SmartDocument.from_pdf(file)
            print(f"Genereren van Rak object voor {doc.document_name}...")
            rak = Rak.from_smart_document(doc, use_caching=False)
            print("Exporteren naar Excel...")
            export_pad = rak.to_excel()
            print(f"Klaar! Bestand opgeslagen: {export_pad}")


if __name__ == "__main__":
    main()
