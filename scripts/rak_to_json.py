"""Eenvoudig script om een Rak te exporteren naar JSON.

Gebruik:
        uv run python scripts/rak_to_json.py --rakcode HEG0201

Het script zoekt een PDF in `DUIKRAPPORTEN_DIR` op basis van de opgegeven rakcode,
bouwt een `Rak` model en schrijft de JSON export naar:
`data/json_exports/<rak_id>_<YYMMDD_HHMM>.json`
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from tekstherkenning_ark.constants import DATA_DIR, DUIKRAPPORTEN_DIR
from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.utils import get_rak_id


def vind_duikrapport_pad(rakcode: str) -> tuple[str, Path]:
    """Zoek het PDF-pad van een duikrapport op basis van rakcode.

    Parameters
    ----------
    rakcode : str
            Door gebruiker opgegeven rakcode (bijv. HEG0201).

    Returns
    -------
    tuple[str, Path]
            Gevonden rak_id en bijbehorend PDF pad.

    Raises
    ------
    ValueError
            Als de rakcode ongeldig is of geen bijpassend rapport is gevonden.
    """
    rak_id = get_rak_id(rakcode)
    if rak_id is None:
        raise ValueError(f"Ongeldige rakcode: '{rakcode}'")

    for pdf_pad in DUIKRAPPORTEN_DIR.glob("*.pdf"):
        if get_rak_id(pdf_pad.stem) == rak_id:
            return rak_id, pdf_pad

    raise ValueError(f"Geen duikrapport gevonden voor rakcode '{rak_id}' in {DUIKRAPPORTEN_DIR}")


def main() -> None:
    """Start script en exporteer gekozen rak naar JSON."""
    parser = argparse.ArgumentParser(description="Exporteer een Rak duikrapport naar JSON.")
    parser.add_argument("--rakcode", required=True, help="Rakcode, bijvoorbeeld HEG0201")
    args = parser.parse_args()

    rak_id, pdf_pad = vind_duikrapport_pad(args.rakcode)

    print(f"Rapport gevonden: {pdf_pad.name}")
    doc = SmartDocument.from_pdf(pdf_pad)
    rak = Rak.from_smart_document(doc, use_caching=True)

    export_dir = DATA_DIR / "json_exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    export_pad = export_dir / f"{rak_id}_{timestamp}.json"

    export_pad.write_text(rak.model_dump_json(indent=2), encoding="utf-8")
    print(f"JSON opgeslagen naar: {export_pad}")


if __name__ == "__main__":
    main()
