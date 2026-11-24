"""Aggregate the processed Rak workbooks into one workbook."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from tekstherkenning_ark import constants
from tekstherkenning_ark.export_utils import remove_unsafe_values_for_excel
from tekstherkenning_ark.logger import get_logger

logger = get_logger(__name__)
RAK_CODE_COLUMN = "rak_code"
DEFAULT_OUTPUT_NAME = "all_rakken.xlsx"


def aggregate_processed_excels(processed_dir: Path, output_path: Path | None = None) -> Path:
    """Combine sheets from processed Rak workbooks and add a Rak code to every row.

    Parameters
    ----------
    processed_dir : pathlib.Path
        Directory containing the per-Rak Excel workbooks.
    output_path : pathlib.Path | None, optional
        Destination workbook. Defaults to ``processed_dir/all_rakken.xlsx``.

    Returns
    -------
    pathlib.Path
        Path to the combined workbook.
    """
    if not processed_dir.is_dir():
        raise FileNotFoundError(f"Processed workbook directory not found: {processed_dir}")

    aggregate_path = output_path or processed_dir / DEFAULT_OUTPUT_NAME
    aggregate_path.parent.mkdir(parents=True, exist_ok=True)
    workbooks = sorted(
        path
        for path in processed_dir.glob("*.xlsx")
        if path.is_file() and path.resolve() != aggregate_path.resolve() and not path.name.startswith("~$")
    )
    if not workbooks:
        raise ValueError(f"No Rak workbooks found in {processed_dir}")

    dataframes_by_sheet: dict[str, list[pd.DataFrame]] = {}
    for workbook_path in workbooks:
        rak_code = workbook_path.stem
        with pd.ExcelFile(workbook_path, engine="openpyxl") as workbook:
            for sheet_name in workbook.sheet_names:
                dataframe = pd.read_excel(workbook, sheet_name=sheet_name)
                if RAK_CODE_COLUMN in dataframe.columns:
                    dataframe = dataframe.drop(columns=[RAK_CODE_COLUMN])
                dataframe.insert(0, RAK_CODE_COLUMN, rak_code)
                dataframes_by_sheet.setdefault(sheet_name, []).append(dataframe)
                logger.info(f"Read {len(dataframe)} rows from {workbook_path.name}, sheet {sheet_name}")

    with pd.ExcelWriter(aggregate_path, engine="openpyxl") as writer:
        for sheet_name, dataframes in dataframes_by_sheet.items():
            combined = pd.concat(dataframes, ignore_index=True, sort=False)
            combined = remove_unsafe_values_for_excel(combined)
            combined.to_excel(writer, sheet_name=sheet_name, index=False)
            logger.info(f"Wrote {len(combined)} rows to aggregate sheet {sheet_name}")

    logger.info(f"Aggregated workbook saved to {aggregate_path}")
    return aggregate_path


def main() -> None:
    """Aggregate the workbooks under ``NOMIC_DIR/processed``."""
    parser = argparse.ArgumentParser(description="Combine processed Nomic Rak workbooks.")
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=constants.NOMIC_DIR / "processed",
        help="Directory containing Rak workbooks (default: data/nomic/processed).",
    )
    parser.add_argument("--output", type=Path, default=None, help="Output workbook path.")
    args = parser.parse_args()

    aggregate_processed_excels(args.processed_dir, args.output)


if __name__ == "__main__":
    main()
