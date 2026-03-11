"""Command-line interface voor tekstherkenning-ark.

Gebruik:
    uv run tekstherkenning-ark -i <input_pdf_path> [-o <output_directory>]

Voorbeeld:
    uv run tekstherkenning-ark -i data/duikrapporten/HEG0201.pdf
    uv run tekstherkenning-ark -i data/duikrapporten/HEG0201.pdf -o data/json_exports
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.utils import get_rak_id

logger = get_logger(__name__)


def valideer_input_bestand(input_path: Path) -> Path:
    """Valideer het input PDF bestand.

    Parameters
    ----------
    input_path : Path
        Pad naar het input PDF bestand.

    Raises
    ------
    ValueError
        Als het bestand niet bestaat, geen PDF is, of "boorweestand" in de naam bevat.
    """
    if not input_path.exists():
        raise ValueError(f"Input bestand bestaat niet: {input_path}")

    if input_path.suffix.lower() != ".pdf":
        raise ValueError(f"Input bestand moet een PDF zijn, kreeg: {input_path.suffix}")

    if "boorweestand" in input_path.name.lower():
        raise ValueError(
            f"Het bestand '{input_path.name}' bevat 'boorweestand' in de naam. "
            "Dit type rapport wordt niet ondersteund door tekstherkenning-ark."
        )

    return input_path


def valideer_output_directory(output_dir: Path) -> Path:
    """Valideer en maak de output directory aan.

    Parameters
    ----------
    output_dir : Path
        Pad naar de output directory.

    Returns
    -------
    Path
        De gevalideerde output directory.
    """
    # Zorg ervoor dat de output directory bestaat
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir


def genereer_output_bestandsnaam(input_path: Path, output_dir: Path) -> Path:
    """Genereer de output bestandsnaam op basis van de input en timestamp.

    Parameters
    ----------
    input_path : Path
        Pad naar het input PDF bestand.
    output_dir : Path
        Directory waar het JSON bestand opgeslagen moet worden.

    Returns
    -------
    Path
        Volledig pad naar het output JSON bestand.

    Raises
    ------
    ValueError
        Als geen geldige rakcode gevonden kan worden in de bestandsnaam.
    """
    rak_id = get_rak_id(input_path.stem)

    if rak_id is None:
        raise ValueError(
            f"Kan geen geldige rakcode vinden in bestandsnaam: '{input_path.name}'. "
            f"Verwacht een code zoals HEG0201 of AMS0601."
        )

    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    filename = f"{rak_id}_{timestamp}.json"

    return output_dir / filename


def main() -> None:
    """Hoofdfunctie voor de CLI."""
    parser = argparse.ArgumentParser(
        description="Verwerk een duikrapport PDF en exporteer naar JSON.",
        prog="tekstherkenning-ark",
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=Path,
        help="Pad naar het input PDF bestand",
        metavar="INPUT_PDF",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("."),
        help="Output directory voor het JSON bestand (default: huidige directory)",
        metavar="OUTPUT_DIR",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Gebruik geen cache voor Rak",
    )

    args = parser.parse_args()

    try:
        # Valideer input
        input_path = valideer_input_bestand(args.input)

        # Valideer en maak output directory aan
        output_dir = valideer_output_directory(args.output)

        # Genereer output bestandsnaam
        output_path = genereer_output_bestandsnaam(input_path, output_dir)

        logger.info(f"Verwerken van: {input_path}")

        # Verwerk het PDF bestand
        use_cache = not args.no_cache
        doc = SmartDocument.from_pdf(input_path)
        rak = Rak.from_smart_document(doc, use_caching=use_cache)

        # Exporteer naar JSON
        json_content = rak.model_dump_json(indent=2)
        output_path.write_text(json_content, encoding="utf-8")

        logger.info(f"JSON succesvol opgeslagen naar: {output_path}")
        print(f"✓ Verwerking voltooid: {output_path}")

    except ValueError as e:
        logger.error(f"Validatiefout: {e}")
        print(f"Fout: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Onverwachte fout tijdens verwerking: {e}", exc_info=True)
        print(f"Fout tijdens verwerking: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
