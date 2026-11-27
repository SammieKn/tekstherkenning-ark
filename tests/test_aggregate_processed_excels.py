from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from scripts.aggregate_processed_excels import aggregate_processed_excels


def _write_workbook(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    """Write a small multi-sheet workbook fixture."""
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, dataframe in sheets.items():
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)


def test_aggregate_processed_excels_tags_and_combines_each_sheet(tmp_path: Path) -> None:
    """Add the source Rak code to all sheets and combine sheets by name."""
    _write_workbook(
        tmp_path / "HEG0201.xlsx",
        {
            "rakken": pd.DataFrame({"rak_id": ["HEG0201"]}),
            "palen": pd.DataFrame({"paal_nummer": ["P1.1"]}),
            "empty": pd.DataFrame({"source_value": pd.Series(dtype=str)}),
        },
    )
    _write_workbook(
        tmp_path / "LYG0201.xlsx",
        {
            "rakken": pd.DataFrame({"rak_code": ["incorrect"], "rak_id": ["LYG0201"]}),
            "palen": pd.DataFrame({"paal_nummer": ["P2.1"]}),
        },
    )

    output_path = aggregate_processed_excels(tmp_path)

    assert output_path == tmp_path / "all_rakken.xlsx"
    with pd.ExcelFile(output_path) as workbook:
        assert set(workbook.sheet_names) == {"rakken", "palen", "empty"}
        rakken = pd.read_excel(workbook, sheet_name="rakken")
        palen = pd.read_excel(workbook, sheet_name="palen")
        empty = pd.read_excel(workbook, sheet_name="empty")

    assert rakken["rak_code"].tolist() == ["HEG0201", "LYG0201"]
    assert palen["rak_code"].tolist() == ["HEG0201", "LYG0201"]
    assert empty.columns.tolist() == ["rak_code", "source_value"]
    assert empty.empty


def test_aggregate_processed_excels_excludes_its_previous_output(tmp_path: Path) -> None:
    """Do not append an existing aggregate workbook as another source."""
    _write_workbook(tmp_path / "HEG0201.xlsx", {"rakken": pd.DataFrame({"raknaam": ["HEG0201"]})})

    output_path = aggregate_processed_excels(tmp_path)
    aggregate_processed_excels(tmp_path)

    with pd.ExcelFile(output_path) as workbook:
        rakken = pd.read_excel(workbook, sheet_name="rakken")
    assert rakken["rak_code"].tolist() == ["HEG0201"]


def test_aggregate_processed_excels_requires_source_workbooks(tmp_path: Path) -> None:
    """Report an explicit error when no source workbooks exist."""
    with pytest.raises(ValueError, match="No Rak workbooks"):
        aggregate_processed_excels(tmp_path)
