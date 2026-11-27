from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pandas as pd
import pytest

from scripts.nomic_csv_to_excel import (
    _get_all_rak_csv_dirs,
    _resolve_paths,
    export_rak_to_excel,
    main,
    process_rak,
)
from tekstherkenning_ark.enums import AansluitingStatus, MateriaalBovenbouw, NietBeschikbaar
from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving
from tekstherkenning_ark.models.boorweerstandsmeting import Boorweerstandsmeting
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.gebrek import Gebrek, ScheurHout
from tekstherkenning_ark.models.nomic_record import NomicRecord
from tekstherkenning_ark.models.onderbouw import Onderbouw
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rakdeel import Rakdeel


def test_resolve_paths_from_rak_code_uses_nomic_directories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Derive CSV and processed output folders from the configured Nomic root."""
    nomic_dir = tmp_path / "nomic"
    monkeypatch.setattr("scripts.nomic_csv_to_excel.constants.NOMIC_DIR", nomic_dir)

    csv_dir, output_dir = _resolve_paths("HEG0201", None, None)

    assert csv_dir == nomic_dir / "csv" / "HEG0201"
    assert output_dir == nomic_dir / "processed"


def test_resolve_paths_keeps_explicit_directories(tmp_path: Path) -> None:
    """Honor explicitly supplied CSV and output directories."""
    csv_dir = tmp_path / "csv"
    output_dir = tmp_path / "excel"

    assert _resolve_paths(None, csv_dir, output_dir) == (csv_dir, output_dir)


def test_get_all_rak_csv_dirs_filters_by_name_and_sorts(tmp_path: Path) -> None:
    """Select immediate child folders with seven-character names and no underscores."""
    csv_root = tmp_path / "csv"
    csv_root.mkdir()
    (csv_root / "LYG0201").mkdir()
    (csv_root / "HEG0201").mkdir()
    (csv_root / "ABC_DEF").mkdir()
    (csv_root / "TOOLONG8").mkdir()
    (csv_root / "NESTED00").mkdir()
    (csv_root / "NESTED00" / "ABC1234").mkdir()
    (csv_root / "BAD0001").write_text("not a folder", encoding="utf-8")

    assert _get_all_rak_csv_dirs(csv_root) == [csv_root / "HEG0201", csv_root / "LYG0201"]


def test_main_all_processes_matching_folders_with_processed_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Process each matching folder in sorted order using the default processed folder."""
    nomic_dir = tmp_path / "nomic"
    csv_root = nomic_dir / "csv"
    (csv_root / "LYG0201").mkdir(parents=True)
    (csv_root / "HEG0201").mkdir()
    (csv_root / "ABC_DEF").mkdir()
    monkeypatch.setattr("scripts.nomic_csv_to_excel.constants.NOMIC_DIR", nomic_dir)

    calls: list[tuple[Path, Path | None]] = []
    monkeypatch.setattr(
        "scripts.nomic_csv_to_excel._process_and_export_rak",
        lambda csv_dir, output_dir: calls.append((csv_dir, output_dir)),
    )
    monkeypatch.setattr(sys, "argv", ["nomic_csv_to_excel.py", "--all"])

    main()

    assert calls == [
        (csv_root / "HEG0201", nomic_dir / "processed"),
        (csv_root / "LYG0201", nomic_dir / "processed"),
    ]


def test_export_rak_to_excel_writes_table_sheets(tmp_path: Path) -> None:
    """Write Rak table dataframes to a multi-sheet Excel workbook."""
    rak = Rak(
        rakdelen=[
            Rakdeel(
                rakdeel_id="Constructie A",
                bovenbouw=Bovenbouw(),
                onderbouw=Onderbouw(palen=[], kespen=[]),
            )
        ],
        raknaam="TESTRAK",
        totale_lengte_m=12.0,
        nomic_samenvattingen=[NomicRecord(tabel="rakken", toelichting="Summary row")],
        boorweerstandsmetingen=[
            Boorweerstandsmeting(
                rakdeel_id="Constructie A",
                codering="TESTRAK/Con.A/P1.1/BM",
                rak_code="TESTRAK",
                paal_nummer="P1.1",
                bma_nummer="18",
                diameter_paal_mm=240,
                hoogte_onder_nap_cm=108,
                hoogte_tov_onderzijde_fundering_cm=15,
                datum_meting="2025-01-15",
                resultaat_tekst="",
                pagina=28,
                bron="source",
                bron_rij="source row",
            )
        ],
    )
    rakdeel = rak.rakdelen[0]
    rakdeel.bovenbouw.materiaal = MateriaalBovenbouw.METSELWERK
    rakdeel.onderbouw.palen.append(
        Paal(
            paal_nummer="P1",
            diameter_haaks=NietBeschikbaar.LEEG,
            diameter_parallel=NietBeschikbaar.LEEG,
            diameter_gemiddeld=NietBeschikbaar.LEEG,
            hoh_afstand_cm=NietBeschikbaar.LEEG,
            hoh_paalnummer="",
            schoor_graden=NietBeschikbaar.LEEG,
            schoor_richting=NietBeschikbaar.LEEG,
            afstand_frontwand_cm=NietBeschikbaar.LEEG,
            is_scheefstand=NietBeschikbaar.LEEG,
            is_paalbreuk=NietBeschikbaar.LEEG,
            is_aantasting=NietBeschikbaar.LEEG,
            aansluiting_status=AansluitingStatus.GOED,
            positionering_aansluiting_cm=NietBeschikbaar.LEEG,
        )
    )

    excel_path = export_rak_to_excel(rak, tmp_path)

    assert excel_path.parent == tmp_path
    assert excel_path.name == "TESTRAK.xlsx"
    with pd.ExcelFile(excel_path) as workbook:
        assert {
            "rakken",
            "rakdelen",
            "bovenbouw",
            "onderbouw",
            "boorweerstandsmetingen",
            "samenvatting",
            "gebreken",
        }.issubset(workbook.sheet_names)
        exported_summary = pd.read_excel(workbook, sheet_name="samenvatting")
        exported_bovenbouw = pd.read_excel(workbook, sheet_name="bovenbouw")
        exported_palen = pd.read_excel(workbook, sheet_name="palen")
    assert exported_summary.loc[0, "toelichting"] == "Summary row"
    assert exported_bovenbouw.loc[0, "materiaal"] == "Metselwerk"
    assert pd.isna(exported_palen.loc[0, "diameter_haaks"])

    model_excel_path = rak.to_excel(tmp_path)
    with pd.ExcelFile(model_excel_path) as workbook:
        assert "Boorweerstandsmetingen" in workbook.sheet_names
        assert "Samenvatting" in workbook.sheet_names


def test_process_rak_enriches_missing_fields_and_classifies_generic_defects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enrich empty Nomic fields without overwriting CSV data and classify generic defects."""
    rakdeel = Rakdeel(
        rakdeel_id="Constructie A",
        omschrijving="Houten onderbouw uit 1990.",
        bouwjaar=1990,
        bovenbouw=Bovenbouw(),
        onderbouw=Onderbouw(palen=[], kespen=[]),
        gebreken=[Gebrek(codering="GB1", omschrijving="Een scheur.", figuurnummer="")],
    )
    rak = Rak(rakdelen=[rakdeel], raknaam="TESTRAK", totale_lengte_m=12.0)

    async def classify_defect(defect: Gebrek) -> list[Gebrek]:
        return [ScheurHout(**defect.model_dump())]

    monkeypatch.setattr(
        RakdeelOmschrijving,
        "classificeer_omschrijving",
        AsyncMock(return_value=RakdeelOmschrijving(bouwjaar=2000, lengte_rakdeel=10.5)),
    )
    monkeypatch.setattr(Gebrek, "classify_gebrek", AsyncMock(side_effect=classify_defect))

    asyncio.run(process_rak(rak))

    assert rakdeel.bouwjaar == 1990
    assert rakdeel.lengte_m_omschrijving == 10.5
    assert isinstance(rakdeel.gebreken[0], ScheurHout)
    assert rakdeel.onderbouw.materiaal is NietBeschikbaar.LEEG
