"""Build and enrich a Rak from Nomic CSV exports, then export it to Excel.

Usage
-----
    uv run python scripts/nomic_csv_to_excel.py --csv-dir data/nomic_output/csv/LYG0201
    uv run python scripts/nomic_csv_to_excel.py --csv-dir data/nomic_output/csv/HEG0201 --output-dir data/excel_exports
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Iterator
from pathlib import Path

from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving
from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rak_base_model import RakBaseModel
from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.models.vloer import Vloer


def _walk_models(model: RakBaseModel) -> Iterator[RakBaseModel]:
    """Yield a model and all nested RakBaseModel children.

    Parameters
    ----------
    model : RakBaseModel
        Root model to traverse.

    Yields
    ------
    RakBaseModel
        The root and each nested model.
    """
    yield model
    for child in model.children:
        yield from _walk_models(child)


def _is_empty(value: object) -> bool:
    """Return whether a model field is unset or marked as empty."""
    return value is None or value is NietBeschikbaar.LEEG


def _apply_description(rakdeel: Rakdeel, description: RakdeelOmschrijving) -> None:
    """Fill missing Rakdeel fields from a classified description.

    Parameters
    ----------
    rakdeel : Rakdeel
        Rakdeel instance to enrich.
    description : RakdeelOmschrijving
        Values extracted from the Rakdeel description.

    Notes
    -----
    Existing CSV values remain authoritative. The description only fills unset
    values and does not change component-presence decisions made from CSV data.
    """
    if rakdeel.bouwjaar is None and isinstance(description.bouwjaar, int):
        rakdeel.bouwjaar = description.bouwjaar
    if _is_empty(rakdeel.lengte_m_omschrijving) and isinstance(description.lengte_rakdeel, (float, int)):
        rakdeel.lengte_m_omschrijving = float(description.lengte_rakdeel)

    if _is_empty(rakdeel.onderbouw.materiaal) and description.materiaal_onderbouw is not NietBeschikbaar.LEEG:
        rakdeel.onderbouw.materiaal = description.materiaal_onderbouw
    if (
        _is_empty(rakdeel.onderbouw.materiaal_fundering)
        and description.materiaal_fundering is not NietBeschikbaar.LEEG
    ):
        rakdeel.onderbouw.materiaal_fundering = description.materiaal_fundering
    if _is_empty(rakdeel.bovenbouw.materiaal) and description.materiaal_bovenbouw is not NietBeschikbaar.LEEG:
        rakdeel.bovenbouw.materiaal = description.materiaal_bovenbouw
    if rakdeel.bovenbouw.bovenkant_deksteen_cm_tov_nap is None and description.bovenkant_deksteen_cm is not None:
        rakdeel.bovenbouw.bovenkant_deksteen_cm_tov_nap = description.bovenkant_deksteen_cm

    vloer_hoogte = description.bovenkant_vloer_cm
    vloer_materiaal = description.materiaal_vloer
    if rakdeel.onderbouw.vloer is None and (
        not isinstance(vloer_materiaal, NietBeschikbaar) or vloer_hoogte is not None
    ):
        rakdeel.onderbouw.vloer = Vloer(
            materiaal=vloer_materiaal,
            bovenkant_vloer_cm_tov_nap=vloer_hoogte,
        )
    elif rakdeel.onderbouw.vloer is not None:
        if _is_empty(rakdeel.onderbouw.vloer.materiaal) and vloer_materiaal is not NietBeschikbaar.LEEG:
            rakdeel.onderbouw.vloer.materiaal = vloer_materiaal
        if rakdeel.onderbouw.vloer.bovenkant_vloer_cm_tov_nap is None and vloer_hoogte is not None:
            rakdeel.onderbouw.vloer.bovenkant_vloer_cm_tov_nap = vloer_hoogte


async def _expand_rakdeel(rakdeel: Rakdeel) -> None:
    """Classify a Rakdeel description and fill fields not supplied by CSV.

    Parameters
    ----------
    rakdeel : Rakdeel
        Rakdeel to enrich.
    """
    if not rakdeel.omschrijving.strip():
        return
    description = await RakdeelOmschrijving.classificeer_omschrijving(rakdeel.omschrijving)
    _apply_description(rakdeel, description)


async def _classify_generic_defects(rak: Rak) -> None:
    """Replace generic defects throughout the Rak hierarchy with classified results.

    Parameters
    ----------
    rak : Rak
        Rak whose generic defects should be classified.
    """
    owners = list(_walk_models(rak))
    generic_defects = [(owner, gebrek) for owner in owners for gebrek in owner.gebreken if type(gebrek) is Gebrek]
    if not generic_defects:
        return

    classified = await asyncio.gather(*(Gebrek.classify_gebrek(gebrek) for _, gebrek in generic_defects))
    replacements = {id(gebrek): result for (_, gebrek), result in zip(generic_defects, classified)}
    for owner in owners:
        owner.gebreken = [
            replacement for gebrek in owner.gebreken for replacement in replacements.get(id(gebrek), [gebrek])
        ]


async def process_rak(rak: Rak) -> None:
    """Enrich Rakdelen from descriptions and classify generic defects.

    Parameters
    ----------
    rak : Rak
        Rak loaded from Nomic CSV files.
    """
    await asyncio.gather(*(_expand_rakdeel(rakdeel) for rakdeel in rak.rakdelen))
    await _classify_generic_defects(rak)


def main() -> None:
    """Load, enrich, classify, and export a Rak from Nomic CSV files."""
    parser = argparse.ArgumentParser(description="Exporteer Nomic CSV-data naar een verrijkte Rak Excel-export.")
    parser.add_argument("--csv-dir", type=Path, required=True, help="Map met Nomic CSV-bestanden voor één Rak.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Uitvoermap voor Excel (standaard: data/excel_exports).",
    )
    args = parser.parse_args()

    rak = Rak.from_nomic_csvs(args.csv_dir)
    asyncio.run(process_rak(rak))
    export_path = rak.to_excel(args.output_dir)
    print(f"Verrijkte Rak geëxporteerd naar: {export_path}")


if __name__ == "__main__":
    main()
