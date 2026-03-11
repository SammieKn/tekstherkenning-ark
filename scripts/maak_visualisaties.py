"""Genereer Plotly-visualisaties voor alle rakdelen in een JSON-exportbestand.

Gebruik:
    uv run python scripts/maak_visualisaties.py <json_bestand>
    uv run python scripts/maak_visualisaties.py <json_bestand> --uitvoer <map>

Zonder --uitvoer worden de HTML-bestanden opgeslagen in
`visuals/output/<rakdeel_id>/` naast de projectroot.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Zorg dat de projectroot op het pad staat zodat `visuals` gevonden wordt
# ongeacht vanuit welke werkmap het script wordt gestart.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from visuals.rakdeelvisualiseerder import RakdeelVisualiseerder, laad_rak_uit_json, sla_figuren_op


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genereer Plotly-visualisaties voor alle rakdelen in een JSON-exportbestand."
    )
    parser.add_argument(
        "invoer",
        type=Path,
        help="Pad naar het JSON-exportbestand (bijv. data/json_exports/HEG0201_260311_1343.json).",
    )
    parser.add_argument(
        "--uitvoer",
        type=Path,
        default=None,
        help="Map voor de HTML-uitvoer. Standaard: visuals/output/<rakdeel_id>/.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if not args.invoer.exists():
        raise SystemExit(f"Bestand niet gevonden: {args.invoer}")

    rak = laad_rak_uit_json(args.invoer)
    raknaam = rak.get("raknaam", args.invoer.stem)
    rakdelen = rak.get("rakdelen", [])

    print(f"Rak geladen: {raknaam} | {len(rakdelen)} rakdelen")

    for rakdeel in rakdelen:
        rid = rakdeel.get("rakdeel_id", "onbekend")
        uitvoer_map = args.uitvoer / rid if args.uitvoer else Path("visuals/output") / rid
        vis = RakdeelVisualiseerder(rakdeel)
        sla_figuren_op(vis.alle_figuren, uitvoer_map)
        print(f"  {rid} → {uitvoer_map}")

    print("Klaar.")


if __name__ == "__main__":
    main()
