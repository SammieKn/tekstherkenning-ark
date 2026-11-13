"""Exporteer één of meerdere Rak duikinspecties naar JSON.

Gebruik
-------
Enkele rak via rakcode (zoekt PDF automatisch in DUIKRAPPORTEN_DIR)::

    uv run python scripts/rak_to_json.py --rakcode HEG0201

Alle PDF bestanden in een map verwerken::

    uv run python scripts/rak_to_json.py --map data/duikrapporten

Uitvoermap opgeven (standaard: data/json_exports)::

    uv run python scripts/rak_to_json.py --rakcode HEG0201 --uitvoermap pad/naar/map
    uv run python scripts/rak_to_json.py --map data/duikrapporten --uitvoermap pad/naar/map

Opmerking
---------
De bestandsnaam van de uitvoer is altijd: `<rak_id>_<JJMMDD_HHMM>.json`
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


def exporteer_pdf(pdf_pad: Path, uitvoermap: Path | None = None) -> None:
    """Verwerk één PDF en schrijf de JSON export.

    Parameters
    ----------
    pdf_pad : Path
        Pad naar het PDF bestand.
    uitvoermap : Path | None
        Map waar de JSON wordt opgeslagen. Standaard `data/json_exports`.
    """
    rak_id = get_rak_id(pdf_pad.stem) or pdf_pad.stem
    print(f"Rapport gevonden: {pdf_pad.name}")
    doc = SmartDocument.from_pdf(pdf_pad)
    rak = Rak.from_smart_document(doc, use_caching=False)

    export_dir = uitvoermap if uitvoermap is not None else DATA_DIR / "json_exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    export_pad = export_dir / f"{rak_id}_{timestamp}.json"

    export_pad.write_text(rak.model_dump_json(indent=2), encoding="utf-8")
    print(f"JSON opgeslagen naar: {export_pad}")


def main() -> None:
    """Start script en exporteer gekozen rak(ken) naar JSON."""
    parser = argparse.ArgumentParser(description="Exporteer een Rak duikrapport naar JSON.")
    groep = parser.add_mutually_exclusive_group(required=True)
    groep.add_argument("--rakcode", help="Rakcode, bijvoorbeeld HEG0201")
    groep.add_argument("--map", type=Path, help="Map met PDF bestanden om allemaal te verwerken")
    parser.add_argument(
        "--uitvoermap",
        type=Path,
        default=None,
        help="Map waar JSON bestanden worden opgeslagen (standaard: data/json_exports)",
    )
    args = parser.parse_args()

    if args.rakcode:
        _, pdf_pad = vind_duikrapport_pad(args.rakcode)
        exporteer_pdf(pdf_pad, uitvoermap=args.uitvoermap)
    else:
        pdf_bestanden = list(args.map.glob("*.pdf"))
        if not pdf_bestanden:
            print(f"Geen PDF bestanden gevonden in {args.map}")
            return
        print(f"{len(pdf_bestanden)} PDF bestanden gevonden in {args.map}")
        for pdf_pad in pdf_bestanden:
            exporteer_pdf(pdf_pad, uitvoermap=args.uitvoermap)


if __name__ == "__main__":
    main()
