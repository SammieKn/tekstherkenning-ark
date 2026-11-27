"""Compare two Excel exports while retaining the ground-truth workbook.

Run with ``uv run python scripts\\compare_excel_exports.py GT.xlsx NV.xlsx --output diff.xlsx``.
"""

from __future__ import annotations

import argparse
import os
import re
from collections import defaultdict, deque
from contextlib import ExitStack
from copy import copy
from enum import Enum
from pathlib import Path
from tempfile import NamedTemporaryFile

from openpyxl import load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet
from pydantic import BaseModel

from tekstherkenning_ark.constants import DATA_DIR
from tekstherkenning_ark.document.structured_table import TableType
from tekstherkenning_ark.enums import (
    AansluitingStatus,
    MateriaalBovenbouw,
    MateriaalFundering,
    MateriaalOnderbouw,
    MateriaalVloer,
    NietBeschikbaar,
    SchoorStand,
)
from tekstherkenning_ark.export_utils import (
    BOVENBOUW_TABLE_NAME,
    GEBREKEN_TABLE_NAME,
    HOUTMONSTER_TABLE_NAME,
    KESPEN_TABLE_NAME,
    ONDERBOUW_TABLE_NAME,
    PALEN_TABLE_NAME,
    RAK_TABLE_NAME,
    RAKDEEL_TABLE_NAME,
    TOESTANDBEPALINGEN_TABLE_NAME,
)
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaatType

VALUE_SEPARATOR = "/"
ADDED_FILL = PatternFill(fill_type="solid", fgColor="C6EFCE")
DELETED_FILL = PatternFill(fill_type="solid", fgColor="FFC7CE")
CHANGED_FILL = PatternFill(fill_type="solid", fgColor="FFEB9C")
SUMMARY_SHEET_NAME = "Samenvatting"
MISMATCHED_COLUMNS_SHEET_NAME = "mismatched columns"
IGNORED_SHEET_NAMES = {"onverwachte_resultaten"}
IGNORED_SHEET_PREFIXES = ("gebreken_",)
ENUM_PATTERN = re.compile(r"^(?P<class>[A-Za-z_]\w*)\.(?P<member>[A-Za-z_]\w*)$")
REPOSITORY_ENUM_TYPES: tuple[type[Enum], ...] = (
    MateriaalFundering,
    MateriaalOnderbouw,
    MateriaalBovenbouw,
    MateriaalVloer,
    SchoorStand,
    NietBeschikbaar,
    AansluitingStatus,
    TableType,
    OnverwachtResultaatType,
)

logger = get_logger(__name__)

SHEET_ID_COLS = {
    RAK_TABLE_NAME: ["raknaam"],
    RAKDEEL_TABLE_NAME: ["rak_id", "rakdeel_id"],
    BOVENBOUW_TABLE_NAME: ["rak_id", "rakdeel_id"],
    ONDERBOUW_TABLE_NAME: ["rak_id", "rakdeel_id"],
    HOUTMONSTER_TABLE_NAME: ["codering"],
    PALEN_TABLE_NAME: ["paal_nummer"],
    KESPEN_TABLE_NAME: ["kesp_nummer"],
    TOESTANDBEPALINGEN_TABLE_NAME: ["rak_id", "rakdeel_id", "onderdeel"],
    GEBREKEN_TABLE_NAME: ["codering"],
}


class SheetSummary(BaseModel):
    """Store comparison counts for one worksheet.

    Attributes
    ----------
    sheet_name : str
        Compared worksheet name.
    new_rows, deleted_rows, changed_cells, gt_cells : int
        Row changes, yellow cells, and original GT data-cell count.
    """

    sheet_name: str
    new_rows: int = 0
    deleted_rows: int = 0
    changed_cells: int = 0
    gt_cells: int = 0


class ColumnMismatch(BaseModel):
    """Describe a column that occurs in only one workbook's version of a sheet."""

    sheet_name: str
    column_name: str
    source: str


def _is_ignored_sheet(sheet_name: str) -> bool:
    """Return whether a sheet is intentionally excluded from comparison output."""
    return sheet_name in IGNORED_SHEET_NAMES or sheet_name.startswith(IGNORED_SHEET_PREFIXES)


def _headers(sheet: Worksheet, source: str) -> dict[str, int]:
    """Return column positions by header, rejecting ambiguous headers."""
    if sheet.max_row == 1 and all(cell.value is None for cell in sheet[1]):
        return {}
    headers: dict[str, int] = {}
    for cell in sheet[1]:
        name = cell.value
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{source} {sheet.title}!{cell.coordinate}: blank or non-text column header")
        if name in headers:
            raise ValueError(f"{source} {sheet.title}!{cell.coordinate}: duplicate column header {name!r}")
        headers[name] = cell.column
    return headers


def _comparison_text(value: object) -> str:
    """Convert a cell value to trimmed text for displayed-value comparisons."""
    return "" if value is None else str(value).strip().lower()


def _cell_value_is_empty(value: object) -> bool:
    """Return whether a cell has no non-whitespace text."""
    return not _comparison_text(value)


def _enum_members(value: object) -> tuple[Enum, ...]:
    """Return repository enum members represented by a cell value."""
    if isinstance(value, Enum):
        return (value,)

    text = "" if value is None else str(value).strip()
    pattern = ENUM_PATTERN.fullmatch(text)
    if pattern:
        class_name = pattern.group("class").casefold()
        member_name = pattern.group("member").casefold()
        return tuple(
            enum_type.__members__[name]
            for enum_type in REPOSITORY_ENUM_TYPES
            if enum_type.__name__.casefold() == class_name
            for name in enum_type.__members__
            if name.casefold() == member_name
        )

    members: list[Enum] = []
    for enum_type in REPOSITORY_ENUM_TYPES:
        try:
            members.append(enum_type(value))
        except (TypeError, ValueError):
            normalized = text.casefold()
            members.extend(
                member
                for member in enum_type
                if member.name.casefold() == normalized or str(member.value).strip().casefold() == normalized
            )
    return tuple(members)


def _cell_values_equal(left: object, right: object) -> bool:
    """Compare trimmed text, then compare matching repository enum members."""
    if _comparison_text(left) == _comparison_text(right):
        return True
    if not any(
        isinstance(value, Enum) or isinstance(value, str) and ENUM_PATTERN.fullmatch(value.strip())
        for value in (left, right)
    ):
        return False
    left_members = _enum_members(left)
    right_members = _enum_members(right)
    return any(left_member == right_member for left_member in left_members for right_member in right_members)


def _index_rows(
    sheet: Worksheet, headers: dict[str, int], id_columns: list[str], columns: list[str], source: str
) -> dict[tuple[str, ...], deque[int]]:
    """Index data-row positions by configured IDs or complete row values."""

    missing = [name for name in id_columns if name not in headers]
    if headers and missing:
        raise ValueError(f"{source} {sheet.title}: missing ID columns {missing}")
    index: dict[tuple[str, ...], deque[int]] = defaultdict(deque)
    if not headers:
        return index
    for row in range(2, sheet.max_row + 1):
        if all(sheet.cell(row, column).value is None for column in headers.values()):
            continue
        values = tuple(
            sheet.cell(row, headers[name]).value if name in headers else None for name in id_columns or columns
        )
        if id_columns and any(value is None or isinstance(value, str) and not value.strip() for value in values):
            raise ValueError(f"{source} {sheet.title}: blank ID in row {row}")
        key = tuple(_comparison_text(value) for value in values)
        if id_columns and key in index:
            logger.warning(
                "%s %s: repeated ID %r in rows %s and %s; pairing occurrences in worksheet order",
                source,
                sheet.title,
                values,
                list(index[key]),
                row,
            )
        index[key].append(row)
    return index


def _copy_cell(source: Cell, target: Cell) -> None:
    """Copy a cell's value and supported formatting without sharing mutable styles."""
    target.value = source.value
    target.data_type = source.data_type
    target.font = copy(source.font)
    target.fill = copy(source.fill)
    target.border = copy(source.border)
    target.alignment = copy(source.alignment)
    target.number_format = source.number_format
    target.protection = copy(source.protection)
    target.hyperlink = copy(source.hyperlink)
    target.comment = copy(source.comment)


def _paint_row(sheet: Worksheet, row: int, fill: PatternFill) -> None:
    """Color every cell within the worksheet width for one data row."""
    for cell in sheet[row]:
        cell.fill = fill


def _copy_new_sheet(source: Worksheet, target: Worksheet) -> None:
    """Copy an NV-only sheet between workbooks using public openpyxl attributes."""
    for row in source:
        for cell in row:
            _copy_cell(cell, target.cell(cell.row, cell.column))
    for name, dimension in source.column_dimensions.items():
        target.column_dimensions[name] = copy(dimension)
    for number, dimension in source.row_dimensions.items():
        target.row_dimensions[number] = copy(dimension)
    target.sheet_format = copy(source.sheet_format)
    target.sheet_properties = copy(source.sheet_properties)
    target.freeze_panes = source.freeze_panes
    target.auto_filter = copy(source.auto_filter)


def _annotate_common_sheet(gt: Worksheet, nv: Worksheet, id_columns: list[str]) -> SheetSummary:
    """Match rows, annotate cell changes, and append NV-only rows in source order."""
    gt_headers, nv_headers = _headers(gt, "GT"), _headers(nv, "NV")
    columns = list(gt_headers) + [name for name in nv_headers if name not in gt_headers]
    gt_index = _index_rows(gt, gt_headers, id_columns, columns, "GT")
    nv_index = _index_rows(nv, nv_headers, id_columns, columns, "NV")
    summary = SheetSummary(sheet_name=gt.title, gt_cells=max(gt.max_row - 1, 0) * len(gt_headers))
    output_headers = {name: position for position, name in enumerate(columns, start=1)}

    for name in nv_headers.keys() - gt_headers.keys():
        column = output_headers[name]
        _copy_cell(nv.cell(1, nv_headers[name]), gt.cell(1, column))
        letter = get_column_letter(column)
        dimension = copy(nv.column_dimensions[get_column_letter(nv_headers[name])])
        dimension.index = letter
        dimension.min = dimension.max = column
        gt.column_dimensions[letter] = dimension

    for key, rows in gt_index.items():
        for row in rows:
            if not nv_index.get(key):
                summary.deleted_rows += 1
                _paint_row(gt, row, DELETED_FILL)
                continue
            nv_row = nv_index[key].popleft()
            for name in nv_headers:
                target = gt.cell(row, output_headers[name])
                source = nv.cell(nv_row, nv_headers[name])
                if name not in gt_headers:
                    _copy_cell(source, target)
                elif not _cell_values_equal(target.value, source.value):
                    summary.changed_cells += 1
                    if _cell_value_is_empty(target.value):
                        target.value = source.value
                        target.data_type = source.data_type
                        target.fill = ADDED_FILL
                    elif _cell_value_is_empty(source.value):
                        target.fill = DELETED_FILL
                    else:
                        target.value = f"{target.value}{VALUE_SEPARATOR}{source.value}"
                        target.data_type = "s"
                        target.fill = CHANGED_FILL

    for nv_row in sorted(row for rows in nv_index.values() for row in rows):
        row = gt.max_row + 1
        for name, column in nv_headers.items():
            _copy_cell(nv.cell(nv_row, column), gt.cell(row, output_headers[name]))
        dimension = copy(nv.row_dimensions[nv_row])
        dimension.index = row
        gt.row_dimensions[row] = dimension
        _paint_row(gt, row, ADDED_FILL)
        summary.new_rows += 1

    # Apply structural column colors last, overriding conflicting row colors.
    for name, column in output_headers.items():
        if name not in gt_headers or name not in nv_headers:
            fill = ADDED_FILL if name not in gt_headers else DELETED_FILL
            for row in gt.iter_rows(min_col=column, max_col=column):
                row[0].fill = fill
    return summary


def _add_summary(sheet: Worksheet, summaries: list[SheetSummary], gt_path: Path, nv_path: Path) -> None:
    """Write the per-sheet results, input paths, and color legend."""
    sheet.append(["Werkblad", "Nieuwe rijen", "Verwijderde rijen", "Gewijzigde cellen", "GT-cellen", "Gewijzigd (%)"])
    for summary in summaries:
        percentage = summary.changed_cells / summary.gt_cells if summary.gt_cells else 0
        sheet.append(
            [
                summary.sheet_name,
                summary.new_rows,
                summary.deleted_rows,
                summary.changed_cells,
                summary.gt_cells,
                percentage,
            ]
        )
        sheet.cell(sheet.max_row, 6).number_format = "0.00%"
    for cell in sheet[1][:6]:
        cell.font = Font(bold=True)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:F{len(summaries) + 1}"
    for letter in "ABCDEF":
        sheet.column_dimensions[letter].width = 24
    for row, (label, fill) in enumerate(
        [("Nieuw (NV)", ADDED_FILL), ("Verwijderd (GT)", DELETED_FILL), ("GT/NV", CHANGED_FILL)], start=2
    ):
        sheet.cell(row, 9, label).fill = fill
    sheet.cell(6, 9, "GT")
    sheet.cell(6, 10, str(gt_path))
    sheet.cell(7, 9, "NV")
    sheet.cell(7, 10, str(nv_path))
    sheet.cell(9, 9, "Percentage: gele cellen / GT-cellen, exclusief koprij.")
    sheet.cell(10, 9, "Kolomkleuren hebben voorrang op rijkleuren.")
    sheet.column_dimensions["I"].width = 28


def _add_column_mismatches(sheet: Worksheet, mismatches: list[ColumnMismatch]) -> None:
    """Write one colored row for each GT-only or NV-only column."""
    sheet.append(["Werkblad", "Kolom", "Aanwezig in"])
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for mismatch in mismatches:
        sheet.append([mismatch.sheet_name, mismatch.column_name, f"Alleen {mismatch.source}"])
        sheet.cell(sheet.max_row, 2).fill = DELETED_FILL if mismatch.source == "GT" else ADDED_FILL
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:C{len(mismatches) + 1}"
    sheet.column_dimensions["A"].width = 30
    sheet.column_dimensions["B"].width = 40
    sheet.column_dimensions["C"].width = 20


def compare_excel_exports(
    gt_path: Path, nv_path: Path, output_path: Path, overwrite: bool = False
) -> list[SheetSummary]:
    """Save an annotated comparison without modifying either input.

    Parameters
    ----------
    gt_path, nv_path : Path
        Existing ground-truth and new-version Excel exports.
    output_path : Path
        Output file; existing files are rejected unless ``overwrite`` is true.
    overwrite : bool, default=False
        Atomically replace an existing output after successfully saving the comparison.

    Returns
    -------
    list[SheetSummary]
        Comparison counts for mapped sheets present in either input.

    Raises
    ------
    ValueError
        Input/output paths overlap or headers/row identifiers are ambiguous.
    FileExistsError
        The requested output file already exists.
    """
    gt_path, nv_path = gt_path.resolve(strict=True), nv_path.resolve(strict=True)
    output_path = output_path.resolve()
    if output_path in (gt_path, nv_path):
        raise ValueError("Output must be different from both input files")
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}")
    logger.info("Starting Excel comparison: GT=%s | NV=%s | output=%s", gt_path, nv_path, output_path)
    with ExitStack() as stack:
        gt_book = load_workbook(gt_path)
        stack.callback(gt_book.close)
        logger.info("Loaded GT workbook with worksheets: %s", gt_book.sheetnames)
        nv_book = load_workbook(nv_path)
        stack.callback(nv_book.close)
        logger.info("Loaded NV workbook with worksheets: %s", nv_book.sheetnames)
        reserved_sheets = {SUMMARY_SHEET_NAME, MISMATCHED_COLUMNS_SHEET_NAME}
        existing_reserved_sheets = reserved_sheets.intersection(gt_book.sheetnames)
        if existing_reserved_sheets:
            raise ValueError(f"GT contains reserved worksheets {sorted(existing_reserved_sheets)}")
        for sheet_name in tuple(gt_book.sheetnames):
            if _is_ignored_sheet(sheet_name):
                del gt_book[sheet_name]
                logger.info("Excluded ignored GT worksheet from comparison output: %s", sheet_name)
        summaries: list[SheetSummary] = []
        mismatched_columns: list[ColumnMismatch] = []
        names = list(gt_book.sheetnames) + [name for name in nv_book.sheetnames if name not in gt_book.sheetnames]
        for name in names:
            if _is_ignored_sheet(name) or name not in SHEET_ID_COLS:
                continue
            gt_headers = _headers(gt_book[name], "GT") if name in gt_book.sheetnames else {}
            nv_headers = _headers(nv_book[name], "NV") if name in nv_book.sheetnames else {}
            mismatched_columns.extend(
                ColumnMismatch(sheet_name=name, column_name=column, source="GT")
                for column in gt_headers
                if column not in nv_headers
            )
            mismatched_columns.extend(
                ColumnMismatch(sheet_name=name, column_name=column, source="NV")
                for column in nv_headers
                if column not in gt_headers
            )
            id_columns = SHEET_ID_COLS[name]
            if name in gt_book.sheetnames and name in nv_book.sheetnames:
                summary = _annotate_common_sheet(gt_book[name], nv_book[name], id_columns)
            else:
                source = gt_book[name] if name in gt_book.sheetnames else nv_book[name]
                label = "GT" if name in gt_book.sheetnames else "NV"
                headers = _headers(source, label)
                index = _index_rows(source, headers, id_columns, list(headers), label)
                count = sum(len(rows) for rows in index.values())
                summary = SheetSummary(sheet_name=name)
                if name in gt_book.sheetnames:
                    target, fill = gt_book[name], DELETED_FILL
                    summary.deleted_rows = count
                    summary.gt_cells = max(target.max_row - 1, 0) * len(headers)
                else:
                    target, fill = gt_book.create_sheet(name), ADDED_FILL
                    _copy_new_sheet(source, target)
                    summary.new_rows = count
                for row in range(2, target.max_row + 1):
                    _paint_row(target, row, fill)
            summaries.append(summary)
            logger.info(
                f"{name}: {summary.new_rows} new rows, {summary.deleted_rows} deleted rows, "
                f"{summary.changed_cells} changed cells"
            )
        _add_summary(gt_book.create_sheet(SUMMARY_SHEET_NAME), summaries, gt_path, nv_path)
        _add_column_mismatches(gt_book.create_sheet(MISMATCHED_COLUMNS_SHEET_NAME), mismatched_columns)
        if overwrite:
            temporary_path: Path | None = None
            try:
                with NamedTemporaryFile(
                    mode="w+b",
                    prefix=f".{output_path.stem}.",
                    suffix=output_path.suffix,
                    dir=output_path.parent,
                    delete=False,
                ) as output:
                    temporary_path = Path(output.name)
                    gt_book.save(output)
                os.replace(temporary_path, output_path)
            finally:
                if temporary_path is not None and temporary_path.exists():
                    temporary_path.unlink()
        else:
            with output_path.open("xb") as output:
                gt_book.save(output)
    logger.info(f"Excel comparison saved: {output_path}")
    return summaries


def main() -> None:
    """Parse file paths and create the Excel comparison."""

    parser = argparse.ArgumentParser(
        description="Vergelijk twee Excel-exports en markeer verschillen ten opzichte van GT."
    )
    parser.add_argument(
        "gt",
        nargs="?",
        type=Path,
        default=DATA_DIR / "excel_exports" / "table_export_261117_1703.xlsx",  # table_export_261117_1703
        help="Ground-truth Excel-export",
    )
    parser.add_argument(
        "nv",
        nargs="?",
        type=Path,
        default=DATA_DIR
        / "nomic_output"
        / "HEG0201_duikrapport_extractie_WF2.xlsx",  # HEG0201_duikrapport_extractie_WF2
        help="Nieuwe Excel-export",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DATA_DIR / "nomic_output" / "diff.xlsx",
        help="Excel-bestand voor de vergelijking",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Vervang een bestaand uitvoerbestand atomair na een geslaagde vergelijking",
        default=True,
    )
    args = parser.parse_args()
    try:
        compare_excel_exports(args.gt, args.nv, args.output, overwrite=args.overwrite)
    except Exception:
        logger.exception("Excel comparison failed: GT=%s | NV=%s | output=%s", args.gt, args.nv, args.output)
        raise


if __name__ == "__main__":
    main()
