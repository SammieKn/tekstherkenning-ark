"""Offline tests for annotated Excel-export comparisons."""

import sys
from contextlib import closing
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

# Pytest prepends tests/, which also contains a scripts/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.compare_excel_exports import (
    ADDED_FILL,
    CHANGED_FILL,
    DELETED_FILL,
    MISMATCHED_COLUMNS_SHEET_NAME,
    SHEET_ID_COLS,
    SUMMARY_SHEET_NAME,
    compare_excel_exports,
    main,
)

ExcelValue = str | int | float | bool | None


def _write_workbook(path: Path, sheets: dict[str, list[list[ExcelValue]]]) -> None:
    """Write small synthetic export sheets to a temporary workbook."""
    with closing(Workbook()) as workbook:
        workbook.remove(workbook.worksheets[0])
        for name, rows in sheets.items():
            sheet = workbook.create_sheet(name)
            for row in rows:
                sheet.append(row)
        workbook.save(path)


@pytest.fixture
def paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Provide separate temporary GT, NV, and output paths."""
    return tmp_path / "gt.xlsx", tmp_path / "nv.xlsx", tmp_path / "diff.xlsx"


def test_matches_composite_ids_preserves_gt_and_reports_exact_percentage(paths: tuple[Path, Path, Path]) -> None:
    """Reordered rows/headers must not affect matching, formatting, or the GT denominator."""
    gt_path, nv_path, output_path = paths
    _write_workbook(
        gt_path,
        {
            "rakdelen": [
                ["rak_id", "rakdeel_id", "waarde", "leeg", "aantal"],
                ["R", "D1", "=oud", None, 0],
                ["R", "D2", "verwijderd", None, 4],
                ["R", "D3", "gelijk", None, 7],
            ]
        },
    )
    with closing(load_workbook(gt_path)) as workbook:
        sheet = workbook["rakdelen"]
        sheet.column_dimensions["C"].width = 38
        sheet["C4"].font = Font(bold=True)
        sheet["E4"].number_format = "0.00"
        sheet.freeze_panes = "C2"
        workbook.save(gt_path)
    _write_workbook(
        nv_path,
        {
            "rakdelen": [
                ["aantal", "rakdeel_id", "leeg", "waarde", "rak_id"],
                [12, "D4", None, "toegevoegd", "R"],
                [7, "D3", None, "gelijk", "R"],
                [0, "D1", "nu", "=nieuw", "R"],
            ]
        },
    )
    gt_bytes, nv_bytes = gt_path.read_bytes(), nv_path.read_bytes()

    summaries = compare_excel_exports(gt_path, nv_path, output_path)

    assert gt_path.read_bytes() == gt_bytes
    assert nv_path.read_bytes() == nv_bytes
    assert summaries[0].new_rows == 1
    assert summaries[0].deleted_rows == 1
    assert summaries[0].changed_cells == 2
    with closing(load_workbook(output_path)) as workbook:
        sheet = workbook["rakdelen"]
        assert [sheet.cell(row, 2).value for row in range(2, 6)] == ["D1", "D2", "D3", "D4"]
        assert sheet["C2"].value == "=oud/=nieuw"
        assert sheet["C2"].data_type == "s"
        assert sheet["D2"].value == "nu"
        assert sheet["C2"].fill == CHANGED_FILL
        assert sheet["D2"].fill == ADDED_FILL
        assert all(cell.fill == DELETED_FILL for cell in sheet[3])
        assert all(cell.fill == ADDED_FILL for cell in sheet[5])
        assert sheet["C4"].value == "gelijk"
        assert sheet["C4"].font.bold
        assert sheet["E4"].value == 7
        assert isinstance(sheet["E4"].value, int)
        assert sheet["E4"].number_format == "0.00"
        assert sheet.column_dimensions["C"].width == 38
        assert sheet.freeze_panes == "C2"
        summary = workbook[SUMMARY_SHEET_NAME]
        assert [cell.value for cell in summary[2][:5]] == ["rakdelen", 1, 1, 2, 15]
        assert summary["F2"].value == pytest.approx(2 / 15)
        assert summary["F2"].number_format == "0.00%"
        assert workbook.sheetnames[-2:] == [SUMMARY_SHEET_NAME, MISMATCHED_COLUMNS_SHEET_NAME]
        assert workbook[MISMATCHED_COLUMNS_SHEET_NAME].max_row == 1


def test_column_colors_override_row_colors_and_preserve_column_order(paths: tuple[Path, Path, Path]) -> None:
    """Added/deleted columns include headers and override conflicting red/green rows."""
    gt_path, nv_path, output_path = paths
    _write_workbook(
        gt_path, {"rakken": [["raknaam", "oud", "gedeeld"], ["A", "oud-A", "zelfde"], ["B", "oud-B", "weg"]]}
    )
    _write_workbook(
        nv_path, {"rakken": [["nieuw", "gedeeld", "raknaam"], ["nieuw-A", "zelfde", "A"], ["nieuw-C", "erbij", "C"]]}
    )
    with closing(load_workbook(nv_path)) as workbook:
        workbook["rakken"].column_dimensions["A"].width = 42
        workbook.save(nv_path)

    compare_excel_exports(gt_path, nv_path, output_path)

    with closing(load_workbook(output_path)) as workbook:
        sheet = workbook["rakken"]
        assert [cell.value for cell in sheet[1]] == ["raknaam", "oud", "gedeeld", "nieuw"]
        assert all(cell.fill == DELETED_FILL for cell in sheet["B"])
        assert all(cell.fill == ADDED_FILL for cell in sheet["D"])
        assert sheet["A3"].fill == DELETED_FILL
        assert sheet["D3"].fill == ADDED_FILL
        assert sheet["A4"].fill == ADDED_FILL
        assert sheet["B4"].fill == DELETED_FILL
        assert sheet["B2"].value == "oud-A"
        assert sheet["D2"].value == "nieuw-A"
        assert sheet["D3"].value is None
        assert sheet["B4"].value is None
        assert sheet["D4"].value == "nieuw-C"
        assert sheet.column_dimensions["D"].width == 42
        assert [cell.value for cell in workbook[SUMMARY_SHEET_NAME][2][:6]] == ["rakken", 1, 1, 0, 6, 0]
        mismatches = workbook[MISMATCHED_COLUMNS_SHEET_NAME]
        assert [row[:3] for row in mismatches.iter_rows(min_row=1, max_row=3, values_only=True)] == [
            ("Werkblad", "Kolom", "Aanwezig in"),
            ("rakken", "oud", "Alleen GT"),
            ("rakken", "nieuw", "Alleen NV"),
        ]
        assert mismatches["B2"].fill == DELETED_FILL
        assert mismatches["B3"].fill == ADDED_FILL


def test_no_id_sheet_matches_complete_rows_and_counts_duplicate_occurrences(
    paths: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Full-row matching consumes duplicate rows once and treats edits as delete/add."""
    monkeypatch.setitem(SHEET_ID_COLS, "toestandsbepalingen", [])
    gt_path, nv_path, output_path = paths
    _write_workbook(
        gt_path, {"toestandsbepalingen": [["eigenschap", "waarde"], ["a", 1], ["a", 1], ["b", 2], ["c", 3]]}
    )
    _write_workbook(
        nv_path, {"toestandsbepalingen": [["waarde", "eigenschap"], [3, "c"], [1, "a"], [4, "b"], [5, "d"]]}
    )

    compare_excel_exports(gt_path, nv_path, output_path)

    with closing(load_workbook(output_path)) as workbook:
        sheet = workbook["toestandsbepalingen"]
        assert sheet["A2"].fill.patternType is None
        assert all(cell.fill == DELETED_FILL for cell in sheet[3])
        assert all(cell.fill == DELETED_FILL for cell in sheet[4])
        assert sheet["A5"].fill.patternType is None
        assert [cell.value for cell in sheet[6]] == ["b", 4]
        assert [cell.value for cell in sheet[7]] == ["d", 5]
        assert all(cell.fill == ADDED_FILL for cell in sheet[6])
        assert all(cell.fill == ADDED_FILL for cell in sheet[7])
        assert [cell.value for cell in workbook[SUMMARY_SHEET_NAME][2][:6]] == ["toestandsbepalingen", 2, 2, 0, 8, 0]


def test_duplicate_configured_ids_are_paired_in_row_order(
    paths: tuple[Path, Path, Path], caplog: pytest.LogCaptureFixture
) -> None:
    """Repeated configured IDs are paired FIFO and emit an explicit warning."""
    gt_path, nv_path, output_path = paths
    _write_workbook(gt_path, {"rakken": [["raknaam", "waarde"], ["R", "eerste"], ["R", "tweede"]]})
    _write_workbook(nv_path, {"rakken": [["raknaam", "waarde"], ["R", "eerste"], ["R", "aangepast"]]})

    compare_excel_exports(gt_path, nv_path, output_path)

    with closing(load_workbook(output_path)) as workbook:
        sheet = workbook["rakken"]
        assert sheet["B2"].value == "eerste"
        assert sheet["B2"].fill.patternType is None
        assert sheet["B3"].value == "tweede/aangepast"
        assert sheet["B3"].fill == CHANGED_FILL
        assert workbook[SUMMARY_SHEET_NAME]["D2"].value == 1
    assert "pairing occurrences in worksheet order" in caplog.text


def test_one_sided_mapped_sheets_and_ignored_sheets(paths: tuple[Path, Path, Path]) -> None:
    """Compare mapped sheets and omit ignored unexpected-result and defect-type worksheets."""
    gt_path, nv_path, output_path = paths
    _write_workbook(
        gt_path,
        {
            "rakken": [["raknaam", "waarde"], ["R", 1]],
            "onverwachte_resultaten": [["notitie"], ["GT behouden"]],
            "gebreken_scheur": [["codering"], ["GT scheur"]],
        },
    )
    _write_workbook(
        nv_path,
        {
            "rakdelen": [["rak_id", "rakdeel_id"], ["R", "D1"], ["R", "D2"]],
            "onverwachte_resultaten": [["notitie"], ["NV negeren"]],
            "gebreken_scheur": [["codering"], ["NV scheur"]],
            "gebreken_scheefstand": [["codering"], ["niet kopieren"]],
        },
    )
    with closing(load_workbook(nv_path)) as workbook:
        sheet = workbook["rakdelen"]
        sheet.column_dimensions["A"].width = 31
        sheet.row_dimensions[2].height = 25
        sheet["A1"].font = Font(bold=True)
        sheet.freeze_panes = "A2"
        workbook.save(nv_path)

    compare_excel_exports(gt_path, nv_path, output_path)

    with closing(load_workbook(output_path)) as workbook:
        assert workbook.sheetnames == [
            "rakken",
            "rakdelen",
            SUMMARY_SHEET_NAME,
            MISMATCHED_COLUMNS_SHEET_NAME,
        ]
        assert all(cell.fill == DELETED_FILL for cell in workbook["rakken"][2])
        assert all(cell.fill == ADDED_FILL for cell in workbook["rakdelen"][2])
        assert all(cell.fill == ADDED_FILL for cell in workbook["rakdelen"][3])
        assert "onverwachte_resultaten" not in workbook.sheetnames
        assert "gebreken_scheur" not in workbook.sheetnames
        assert "gebreken_scheefstand" not in workbook.sheetnames
        assert workbook["rakdelen"]["A1"].font.bold
        assert workbook["rakdelen"].column_dimensions["A"].width == 31
        assert workbook["rakdelen"].row_dimensions[2].height == 25
        assert workbook["rakdelen"].freeze_panes == "A2"
        results = list(workbook[SUMMARY_SHEET_NAME].iter_rows(min_row=2, max_row=3, max_col=6, values_only=True))
        assert results == [("rakken", 0, 1, 0, 2, 0), ("rakdelen", 2, 0, 0, 0, 0)]
        mismatches = list(workbook[MISMATCHED_COLUMNS_SHEET_NAME].iter_rows(min_row=2, values_only=True))
        assert mismatches == [
            ("rakken", "raknaam", "Alleen GT"),
            ("rakken", "waarde", "Alleen GT"),
            ("rakdelen", "rak_id", "Alleen NV"),
            ("rakdelen", "rakdeel_id", "Alleen NV"),
        ]
        assert workbook[MISMATCHED_COLUMNS_SHEET_NAME]["B2"].fill == DELETED_FILL
        assert workbook[MISMATCHED_COLUMNS_SHEET_NAME]["B4"].fill == ADDED_FILL


@pytest.mark.parametrize(
    ("gt_rows", "nv_rows", "new_rows", "deleted_rows", "gt_cells"),
    [
        ([], [], 0, 0, 0),
        ([["raknaam"]], [["raknaam"]], 0, 0, 0),
        ([], [["raknaam"], ["R"]], 1, 0, 0),
        ([["raknaam"], ["R"]], [], 0, 1, 1),
    ],
)
def test_empty_sheets_have_valid_zero_percentages(
    paths: tuple[Path, Path, Path],
    gt_rows: list[list[ExcelValue]],
    nv_rows: list[list[ExcelValue]],
    new_rows: int,
    deleted_rows: int,
    gt_cells: int,
) -> None:
    """Headerless and header-only exports must not fail or divide by zero."""
    gt_path, nv_path, output_path = paths
    _write_workbook(gt_path, {"rakken": gt_rows})
    _write_workbook(nv_path, {"rakken": nv_rows})

    compare_excel_exports(gt_path, nv_path, output_path)

    with closing(load_workbook(output_path)) as workbook:
        assert [cell.value for cell in workbook[SUMMARY_SHEET_NAME][2][:6]] == [
            "rakken",
            new_rows,
            deleted_rows,
            0,
            gt_cells,
            0,
        ]


@pytest.mark.parametrize(
    ("old", "new", "expected", "changed", "fill"),
    [
        (None, "nieuw", "nieuw", True, ADDED_FILL),
        ("  ", "nieuw", "nieuw", True, ADDED_FILL),
        ("oud", None, "oud", True, DELETED_FILL),
        ("oud", " ", "oud", True, DELETED_FILL),
        ("links", "rechts", "links/rechts", True, CHANGED_FILL),
        (" 90 ", 90, " 90 ", False, None),
        (90, "90", 90, False, None),
        (False, 0, "False/0", True, CHANGED_FILL),
    ],
)
def test_changed_values_preserve_empty_sides_and_scalar_distinctions(
    paths: tuple[Path, Path, Path],
    old: ExcelValue,
    new: ExcelValue,
    expected: str,
    changed: bool,
    fill: object,
) -> None:
    """Empty-side differences use red/green fills; other differences remain yellow."""
    gt_path, nv_path, output_path = paths
    _write_workbook(gt_path, {"rakken": [["raknaam", "waarde"], ["R", old]]})
    _write_workbook(nv_path, {"rakken": [["raknaam", "waarde"], ["R", new]]})

    compare_excel_exports(gt_path, nv_path, output_path)

    with closing(load_workbook(output_path)) as workbook:
        if changed:
            assert workbook["rakken"]["B2"].value == expected
            assert workbook["rakken"]["B2"].fill == fill
            assert workbook[SUMMARY_SHEET_NAME]["F2"].value == 0.5
        else:
            assert workbook["rakken"]["B2"].value == old
            assert workbook["rakken"]["B2"].fill.patternType is None
            assert workbook[SUMMARY_SHEET_NAME]["D2"].value == 0


def test_full_row_matching_uses_trimmed_string_values(
    paths: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A no-ID sheet treats numeric and trimmed text representations as the same row."""
    monkeypatch.setitem(SHEET_ID_COLS, "toestandsbepalingen", [])
    gt_path, nv_path, output_path = paths
    _write_workbook(gt_path, {"toestandsbepalingen": [["eigenschap", "waarde"], ["hoek", 90]]})
    _write_workbook(nv_path, {"toestandsbepalingen": [["waarde", "eigenschap"], [" 90 ", "hoek"]]})

    compare_excel_exports(gt_path, nv_path, output_path)

    with closing(load_workbook(output_path)) as workbook:
        sheet = workbook["toestandsbepalingen"]
        assert sheet.max_row == 2
        assert [cell.value for cell in sheet[2]] == ["hoek", 90]
        assert all(cell.fill.patternType is None for cell in sheet[2])
        assert [cell.value for cell in workbook[SUMMARY_SHEET_NAME][2][:6]] == [
            "toestandsbepalingen",
            0,
            0,
            0,
            2,
            0,
        ]


def test_configured_ids_match_as_trimmed_strings(paths: tuple[Path, Path, Path]) -> None:
    """Configured IDs with surrounding whitespace still identify the same row."""
    gt_path, nv_path, output_path = paths
    _write_workbook(gt_path, {"rakken": [["raknaam", "waarde"], [" R ", 90]]})
    _write_workbook(nv_path, {"rakken": [["raknaam", "waarde"], ["R", "90"]]})

    compare_excel_exports(gt_path, nv_path, output_path)

    with closing(load_workbook(output_path)) as workbook:
        sheet = workbook["rakken"]
        assert sheet.max_row == 2
        assert sheet["B2"].value == 90
        assert sheet["B2"].fill.patternType is None
        assert [cell.value for cell in workbook[SUMMARY_SHEET_NAME][2][:6]] == ["rakken", 0, 0, 0, 2, 0]


def test_qualified_enum_and_enum_value_are_equal(paths: tuple[Path, Path, Path]) -> None:
    """A qualified enum member matches its value using the matching repository enum."""
    gt_path, nv_path, output_path = paths
    _write_workbook(
        gt_path,
        {"rakken": [["raknaam", "materiaal"], ["R", "MateriaalBovenbouw.METSELWERK"]]},
    )
    _write_workbook(nv_path, {"rakken": [["raknaam", "materiaal"], ["R", "Metselwerk"]]})

    compare_excel_exports(gt_path, nv_path, output_path)

    with closing(load_workbook(output_path)) as workbook:
        sheet = workbook["rakken"]
        assert sheet["B2"].value == "MateriaalBovenbouw.METSELWERK"
        assert sheet["B2"].fill.patternType is None
        assert workbook[SUMMARY_SHEET_NAME]["D2"].value == 0


def test_different_enum_types_do_not_match_shared_member_names(paths: tuple[Path, Path, Path]) -> None:
    """Equal member names or values from different enum classes are not interchangeable."""
    gt_path, nv_path, output_path = paths
    _write_workbook(gt_path, {"rakken": [["raknaam", "materiaal"], ["R", "MateriaalFundering.HOUT"]]})
    _write_workbook(nv_path, {"rakken": [["raknaam", "materiaal"], ["R", "MateriaalBovenbouw.HOUT"]]})

    compare_excel_exports(gt_path, nv_path, output_path)

    with closing(load_workbook(output_path)) as workbook:
        sheet = workbook["rakken"]
        assert sheet["B2"].value == "MateriaalFundering.HOUT/MateriaalBovenbouw.HOUT"
        assert sheet["B2"].fill == CHANGED_FILL
        assert workbook[SUMMARY_SHEET_NAME]["D2"].value == 1


@pytest.mark.parametrize("invalid_input", ["GT", "NV"])
@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ([["waarde"], [1]], "missing ID columns"),
        ([["raknaam", None], ["R", 1]], "blank or non-text column header"),
        ([["raknaam", "raknaam"], ["R", "R"]], "duplicate column header"),
        ([["raknaam", "waarde"], [None, 1]], "blank ID"),
    ],
)
def test_invalid_headers_and_ids_fail_without_creating_output(
    paths: tuple[Path, Path, Path], invalid_input: str, rows: list[list[ExcelValue]], message: str
) -> None:
    """Ambiguous keys/headers must identify the offending input and sheet explicitly."""
    gt_path, nv_path, output_path = paths
    valid_rows: list[list[ExcelValue]] = [["raknaam", "waarde"], ["R", 1]]
    _write_workbook(gt_path, {"rakken": rows if invalid_input == "GT" else valid_rows})
    _write_workbook(nv_path, {"rakken": rows if invalid_input == "NV" else valid_rows})

    with pytest.raises(ValueError, match=f"{invalid_input} rakken.*{message}"):
        compare_excel_exports(gt_path, nv_path, output_path)

    assert not output_path.exists()


def test_rejects_reserved_summary_name_without_replacing_it(paths: tuple[Path, Path, Path]) -> None:
    """Never silently replace an existing GT summary worksheet."""
    gt_path, nv_path, output_path = paths
    _write_workbook(gt_path, {"rakken": [["raknaam"]], SUMMARY_SHEET_NAME: [["behouden"]]})
    _write_workbook(nv_path, {"rakken": [["raknaam"]]})

    with pytest.raises(ValueError, match="reserved worksheet"):
        compare_excel_exports(gt_path, nv_path, output_path)

    assert not output_path.exists()


def test_rejects_input_overwrites_and_existing_outputs(paths: tuple[Path, Path, Path]) -> None:
    """An explicit output must still never overwrite an existing file."""
    gt_path, nv_path, output_path = paths
    _write_workbook(gt_path, {"rakken": [["raknaam"], ["R"]]})
    _write_workbook(nv_path, {"rakken": [["raknaam"], ["R"]]})
    gt_bytes, nv_bytes = gt_path.read_bytes(), nv_path.read_bytes()
    for path in (gt_path, nv_path):
        with pytest.raises(ValueError, match="different from both"):
            compare_excel_exports(gt_path, nv_path, path)
    output_path.write_bytes(b"existing output")

    with pytest.raises(FileExistsError, match="already exists"):
        compare_excel_exports(gt_path, nv_path, output_path)

    assert output_path.read_bytes() == b"existing output"
    assert gt_path.read_bytes() == gt_bytes
    assert nv_path.read_bytes() == nv_bytes


def test_overwrite_replaces_existing_output_only_after_comparison_succeeds(paths: tuple[Path, Path, Path]) -> None:
    """Explicit overwrite atomically replaces an old output with a readable workbook."""
    gt_path, nv_path, output_path = paths
    _write_workbook(gt_path, {"rakken": [["raknaam", "waarde"], ["R", 1]]})
    _write_workbook(nv_path, {"rakken": [["raknaam", "waarde"], ["R", 2]]})
    output_path.write_bytes(b"old output")

    compare_excel_exports(gt_path, nv_path, output_path, overwrite=True)

    with closing(load_workbook(output_path)) as workbook:
        assert workbook["rakken"]["B2"].value == "1/2"
    assert list(output_path.parent.glob(f".{output_path.stem}.*{output_path.suffix}")) == []


def test_cli_creates_the_requested_workbook(paths: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI must pass the two input paths and explicit output through to comparison."""
    gt_path, nv_path, output_path = paths
    _write_workbook(gt_path, {"rakken": [["raknaam", "waarde"], ["R", 1]]})
    _write_workbook(nv_path, {"rakken": [["raknaam", "waarde"], ["R", 2]]})
    monkeypatch.setattr(
        "sys.argv", ["compare_excel_exports", str(gt_path), str(nv_path), "--output", str(output_path)]
    )

    main()

    with closing(load_workbook(output_path)) as workbook:
        assert workbook["rakken"]["B2"].value == "1/2"
