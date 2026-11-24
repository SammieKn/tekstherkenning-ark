"""Build and enrich a Rak from Nomic CSV exports, then export it to Excel.

Usage
-----
    uv run python scripts/nomic_csv_to_excel.py HEG0201
    uv run python scripts/nomic_csv_to_excel.py --rak-code LYG0201
    uv run python scripts/nomic_csv_to_excel.py --csv-dir data/nomic/csv/HEG0201 --output-dir data/excel_exports
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Iterator
from pathlib import Path

import pandas as pd

from tekstherkenning_ark import constants
from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.export_utils import (
    BOORWEERSTANDSMETINGEN_TABLE_NAME,
    BOVENBOUW_TABLE_NAME,
    GEBREKEN_TABLE_NAME,
    HOUTMONSTER_TABLE_NAME,
    KESPEN_TABLE_NAME,
    ONDERBOUW_TABLE_NAME,
    ONVERWACHT_RESULTATEN_TABLE_NAME,
    PALEN_TABLE_NAME,
    RAK_TABLE_NAME,
    RAKDEEL_TABLE_NAME,
    TOESTANDBEPALINGEN_TABLE_NAME,
    remove_unsafe_values_for_excel,
)
from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rak_base_model import RakBaseModel
from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.models.vloer import Vloer

logger = get_logger(__name__)


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


def _resolve_paths(rak_code: str | None, csv_dir: Path | None, output_dir: Path | None) -> tuple[Path, Path | None]:
    """Resolve CSV and Excel directories from a rak code or explicit paths.

    Parameters
    ----------
    rak_code : str | None
        Rak code used to derive paths under ``NOMIC_DIR``.
    csv_dir : Path | None
        Explicit CSV directory, used when no rak code is given.
    output_dir : Path | None
        Explicit export directory, if supplied.

    Returns
    -------
    tuple[Path, Path | None]
        Resolved input CSV directory and export directory. With a rak code,
        the defaults are ``NOMIC_DIR/csv/<rak_code>`` and
        ``NOMIC_DIR/processed``.
    """
    if rak_code:
        return (
            constants.NOMIC_DIR / "csv" / rak_code,
            output_dir if output_dir is not None else constants.NOMIC_DIR / "processed",
        )
    if csv_dir is None:
        raise ValueError("Provide either a rak code or a CSV directory.")
    return csv_dir, output_dir


def _get_rak_dataframes(rak: Rak) -> dict[str, pd.DataFrame]:
    """Build the Excel export sheets from a processed Rak.

    Parameters
    ----------
    rak : Rak
        Rak to export.

    Returns
    -------
    dict[str, pandas.DataFrame]
        Table dataframes using the same tables as the PDF-to-Excel export.
    """
    dataframes = {
        RAK_TABLE_NAME: rak._get_rak_df(),
        RAKDEEL_TABLE_NAME: rak._get_rakdeel_df(),
        BOVENBOUW_TABLE_NAME: rak._get_bovenbouw_df(),
        ONDERBOUW_TABLE_NAME: rak._get_onderbouw_df(),
        HOUTMONSTER_TABLE_NAME: rak._get_houtmonsters_df(),
        BOORWEERSTANDSMETINGEN_TABLE_NAME: rak._get_boorweerstandsmetingen_df(),
        PALEN_TABLE_NAME: rak._get_palen_df(),
        KESPEN_TABLE_NAME: rak._get_kespen_df(),
        TOESTANDBEPALINGEN_TABLE_NAME: rak._get_toestandsbepalingen_df(),
        ONVERWACHT_RESULTATEN_TABLE_NAME: rak._get_onverwacht_resultaten_df(),
        GEBREKEN_TABLE_NAME: rak._get_gebreken_df(),
    }
    dataframes.update(
        {
            f"{GEBREKEN_TABLE_NAME}_{gebrek_type}": dataframe
            for gebrek_type, dataframe in rak._get_gebreken_per_type_dfs().items()
        }
    )
    return dataframes


def export_rak_to_excel(rak: Rak, output_dir: Path | None) -> Path:
    """Export Rak dataframes using the multi-sheet Excel writer workflow.

    Parameters
    ----------
    rak : Rak
        Processed Rak to export.
    output_dir : Path | None
        Output folder. If omitted, use ``data/excel_exports``.

    Returns
    -------
    Path
        Path to the generated Excel workbook.
    """
    export_dir = output_dir if output_dir is not None else constants.DATA_DIR / "excel_exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    excel_path = export_dir / f"{rak.raknaam}.xlsx"
    dataframes = _get_rak_dataframes(rak)

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for name, dataframe in dataframes.items():
            logger.info(f"Exporting {len(dataframe)} rows from {name} to Excel sheet")
            dataframe = remove_unsafe_values_for_excel(dataframe)
            sheet_name = name[:30]
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)

            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = max((len(str(cell.value)) for cell in column if cell.value), default=0)
                column_letter = column[0].column_letter
                worksheet.column_dimensions[column_letter].width = min(max_length + 2, 50)

    logger.info(f"Excel file saved: {excel_path}")
    return excel_path


def main() -> None:
    """Load, enrich, classify, and export a Rak from Nomic CSV files."""
    parser = argparse.ArgumentParser(description="Exporteer Nomic CSV-data naar een verrijkte Rak Excel-export.")
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--rak-code", help="Rakcode, bijvoorbeeld HEG0201.")
    input_group.add_argument("--csv-dir", type=Path, help="Map met Nomic CSV-bestanden voor één Rak.")
    parser.add_argument("rak_code_positional", nargs="?", help="Rakcode als positioneel argument.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Uitvoermap voor Excel (standaard met --rak-code: data/nomic/processed).",
    )
    args = parser.parse_args()

    if args.rak_code_positional and (args.rak_code or args.csv_dir):
        parser.error("Use a positional rak code, --rak-code, or --csv-dir, not more than one.")
    rak_code = args.rak_code or args.rak_code_positional

    if bool(rak_code) == bool(args.csv_dir):
        parser.error("Provide exactly one of a rak code or --csv-dir.")
    csv_dir, output_dir = _resolve_paths(rak_code, args.csv_dir, args.output_dir)

    logger.info(f"Loading Nomic CSV files from {csv_dir}")
    rak = Rak.from_nomic_csvs(csv_dir)
    logger.info(f"Loaded Rak {rak.raknaam} with {len(rak.rakdelen)} rakdelen")

    logger.info("Enriching rakdelen and classifying generic defects")
    asyncio.run(process_rak(rak))

    export_path = export_rak_to_excel(rak, output_dir)
    logger.info(f"Processed Rak exported to {export_path}")


if __name__ == "__main__":
    main()
