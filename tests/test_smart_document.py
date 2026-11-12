"""Contracttests voor lokale PDF-extractie voorafgaand aan de SmartDocument-migratie."""

import json
import pickle
import re
import shutil
import socket
import subprocess
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace
from typing import NoReturn
from unittest.mock import patch

import pymupdf
import pytest

from tekstherkenning_ark import constants
from tekstherkenning_ark.document.rakdeelsectie import RakdeelSectie
from tekstherkenning_ark.document.sectie import Afbeelding, BronLocatie, Paragraaf, Sectie
from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.document.structured_table import DocumentTabel, StructuredTable, TabelCel, TableType
from tekstherkenning_ark.utils import get_paal_id, get_table_content, is_table_type_by_id_func
from tekstherkenning_ark.utils import get_kesp_id


def test_structuur_export_is_verplaatsbaar_en_behoudt_gemengde_elementen(tmp_path: Path) -> None:
    """Schrijf alleen een canonieke registratie en relatieve, bestaande PNG-paden.

    Parameters
    ----------
    tmp_path : Path
        Tijdelijke bron-, export- en verplaatsingsmap.
    """
    locatie = BronLocatie(1, (20, 40, 100, 80))
    sectie = Sectie("1 Resultaten", id="sectie-1", koplocatie=locatie)
    subsectie = Sectie("1.1 Details", id="sectie-2", kopniveau=2, ouder_id=sectie.id, koplocatie=locatie)
    document = SmartDocument(
        "KZG0202",
        sections=[sectie, subsectie],
        bron_hash="bron",
        pagina_afmetingen={1: (595, 842)},
        bookmarks=[(1, "1 Resultaten", 1)],
    )
    document.extractie_metadata = document._extractie_configuratie()
    bron_png = tmp_path / "bron.png"
    with pymupdf.open() as pdf:
        pagina = pdf.new_page(width=100, height=100)
        pagina.draw_rect((10, 10, 90, 90), fill=(0.2, 0.6, 0.4))
        pagina.get_pixmap().save(bron_png)
    for element in (
        Paragraaf("Native tekst", "tekst-1", bronlocaties=(locatie,)),
        DocumentTabel(
            2,
            3,
            (
                TabelCel("Diameter", 0, 0, column_span=2, bronlocaties=(locatie,)),
                TabelCel("P2.39", 0, 2, row_span=2),
                TabelCel("230", 1, 0),
                TabelCel("", 1, 1),
            ),
            id="tabel-1",
            bronlocaties=(locatie,),
        ),
        Afbeelding("figuur-1", bron_png, (locatie,)),
    ):
        document.registreer_element(sectie, element)
    document.registreer_element(subsectie, Paragraaf("Detail\nzonder tekstnormalisatie", "tekst-2"))

    manifest_pad = document.exporteer_structuur(tmp_path / "export")
    shutil.move(str(manifest_pad.parent), tmp_path / "verplaatst")
    gegevens = json.loads((tmp_path / "verplaatst" / "structuur.json").read_text(encoding="utf-8"))

    assert gegevens["documentvingerafdruk"] == document.documentvingerafdruk
    assert gegevens["secties"][0]["element_ids"] == ["tekst-1", "tabel-1", "figuur-1"]
    assert [element["soort"] for element in gegevens["elementen"]] == ["paragraaf", "tabel", "afbeelding", "paragraaf"]
    assert gegevens["elementen"][1]["cells"][1]["content"] == "P2.39"
    asset_pad = Path(gegevens["elementen"][2]["bestand"])
    assert not asset_pad.is_absolute()
    assert (tmp_path / "verplaatst" / asset_pad).is_file()
    assert "_elementen" not in gegevens["secties"][0]
    assert document.elementen["figuur-1"].bestand == bron_png
    hersteld = SmartDocument._lees_structuur(tmp_path / "verplaatst" / "structuur.json", document.documentvingerafdruk)
    assert hersteld.sections[0].full_text() == "Native tekst"
    assert hersteld.sections[0].tabellen[0].matrix == (("Diameter", None, "P2.39"), ("230", "", None))
    assert hersteld.elementen["tabel-1"] == document.elementen["tabel-1"]
    assert hersteld.sections[1].ouder_id == hersteld.sections[0].id
    assert hersteld.sections[1].kopniveau == 2
    assert hersteld.sections[1].koplocatie == locatie
    assert hersteld.sections[1].full_text() == "Detail\nzonder tekstnormalisatie"
    assert hersteld.bookmarks == document.bookmarks
    assert hersteld.pagina_afmetingen == document.pagina_afmetingen
    assert hersteld.get_elementen(hersteld.sections[0])[1] is hersteld.elementen["tabel-1"]
    assert hersteld.sections[0].afbeeldingen[0].bestand.is_relative_to(tmp_path / "verplaatst")


def test_structuur_export_behoudt_documentvolgorde_buiten_sectiegroepering(tmp_path: Path) -> None:
    """Herstel document- en sectievolgorde afzonderlijk met dezelfde geregistreerde objecten.

    Parameters
    ----------
    tmp_path : Path
        Tijdelijke exportmap.
    """
    eerste_sectie = Sectie("Eerste", id="sectie-1")
    tweede_sectie = Sectie("Tweede", id="sectie-2")
    document = SmartDocument(
        "proef", sections=[eerste_sectie, tweede_sectie], bron_hash="bron", pagina_afmetingen={1: (595, 842)},
        extractie_metadata=SmartDocument._extractie_configuratie(),
    )
    document.registreer_element(tweede_sectie, Paragraaf("Eerder in document", "tekst-1", leesvolgorde=0))
    document.registreer_element(eerste_sectie, Paragraaf("Later in document", "tekst-2", leesvolgorde=1))

    hersteld = SmartDocument._lees_structuur(document.exporteer_structuur(tmp_path), document.documentvingerafdruk)

    assert list(hersteld.elementen) == ["tekst-1", "tekst-2"]
    assert [sectie.element_ids for sectie in hersteld.sections] == [["tekst-2"], ["tekst-1"]]
    assert all(sectie._elementen is hersteld.elementen for sectie in hersteld.sections)


def test_structuur_export_publiceert_geen_manifest_met_ontbrekende_asset(tmp_path: Path) -> None:
    """Faalt expliciet in plaats van een JSON met gebroken figuurverwijzingen te publiceren.

    Parameters
    ----------
    tmp_path : Path
        Tijdelijke exportmap zonder de vereiste PNG.
    """
    sectie = Sectie("Resultaten", id="sectie-1")
    document = SmartDocument("KZG0202", sections=[sectie])
    document.registreer_element(sectie, Afbeelding("figuur-1", tmp_path / "ontbreekt.png", ()))

    with pytest.raises(ValueError, match="figuurasset"):
        document.exporteer_structuur(tmp_path / "export")

    assert not (tmp_path / "export" / "structuur.json").exists()


@pytest.fixture
def document_met_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, blokkeer_ocr_en_netwerk: Callable[..., NoReturn]
) -> tuple[Path, SmartDocument]:
    """Maak een geisoleerde echte PDF met native tekst, rasterfiguur en geldige cache.

    Parameters
    ----------
    tmp_path : Path
        Tijdelijke invoer- en cachemap.
    monkeypatch : pytest.MonkeyPatch
        Isoleert de cachemap.
    blokkeer_ocr_en_netwerk : Callable[..., NoReturn]
        Blokkeert OCR en netwerk gedurende de gehele proef.

    Returns
    -------
    tuple[Path, SmartDocument]
        Bron-PDF en eenmaal lokaal geextraheerd document.
    """
    monkeypatch.setattr(constants, "CACHE_DIR", tmp_path / "cache")
    pdf_pad = tmp_path / "KZG0202_cache.pdf"
    with pymupdf.open() as figuur, pymupdf.open() as pdf:
        tekening = figuur.new_page(width=400, height=240)
        tekening.draw_rect((10, 10, 390, 230), fill=(0.9, 0.95, 1))
        for index, hoogte in enumerate((50, 90, 130, 110, 150)):
            links = 65 + index * 55
            tekening.draw_rect((links, 200 - hoogte, links + 30, 200), fill=(0.2, 0.6, 0.4))
        pagina = pdf.new_page()
        pagina.insert_text((72, 72), "1 Inspectieresultaten", fontsize=18)
        pagina.insert_text((72, 120), "Native tekst voor cachecontrole.")
        pagina.insert_image((72, 160, 472, 400), stream=tekening.get_pixmap().tobytes("png"))
        pagina.insert_text((72, 420), "Figuur 1.1: Meting.", fontsize=10)
        pdf.save(pdf_pad)

    document = SmartDocument.from_pdf(pdf_pad, use_cache=False)
    assert any(isinstance(element, Afbeelding) for element in document.elementen.values())
    return pdf_pad, document


def test_documentcache_hit_slaat_pdf_extractie_over(
    document_met_cache: tuple[Path, SmartDocument],
    monkeypatch: pytest.MonkeyPatch,
    blokkeer_ocr_en_netwerk: Callable[..., NoReturn],
) -> None:
    """Lees dezelfde inhoud, ook onder een andere naam, zonder de PDF opnieuw te openen.

    Parameters
    ----------
    document_met_cache : tuple[Path, SmartDocument]
        PDF met bestaande lokale structuurcache.
    monkeypatch : pytest.MonkeyPatch
        Verbiedt iedere volgende PDF-opening.
    blokkeer_ocr_en_netwerk : Callable[..., NoReturn]
        Verboden bewerking die als PDF-openingsblokkade dient.
    """
    pdf_pad, eerste = document_met_cache
    monkeypatch.setattr(pymupdf, "open", blokkeer_ocr_en_netwerk)
    tweede = SmartDocument.from_pdf(pdf_pad)

    assert tweede.documentvingerafdruk == eerste.documentvingerafdruk
    assert [sectie.full_text() for sectie in tweede.sections] == [sectie.full_text() for sectie in eerste.sections]
    assert tweede.sections[0]._elementen is tweede.elementen
    assert tweede.bron_bestandsnaam == pdf_pad.name
    cache_map = constants.CACHE_DIR / "pymupdf_extractie" / eerste.documentvingerafdruk
    assert {pad.name for pad in cache_map.iterdir()} == {"structuur.json", "afbeeldingen"}
    ander_pad = pdf_pad.with_name("HEG0201_andere_naam.pdf")
    shutil.copyfile(pdf_pad, ander_pad)
    hernoemd = SmartDocument.from_pdf(ander_pad)
    assert hernoemd.documentvingerafdruk == eerste.documentvingerafdruk
    assert hernoemd.document_name == ander_pad.stem
    assert hernoemd.bron_bestandsnaam == ander_pad.name
    with pytest.raises(pytest.fail.Exception):
        SmartDocument.from_pdf(pdf_pad, use_cache=False)


@pytest.mark.parametrize(
    "defect",
    [
        "json",
        "schema",
        "vingerafdruk",
        "ontbrekend_veld",
        "lege_cache",
        "dubbel_element",
        "onbekend_element",
        "dubbele_toewijzing",
        "niet_toegewezen",
        "cyclische_ouder",
        "ontbrekende_asset",
        "beschadigde_asset",
        "andere_geldige_png",
        "absoluut_assetpad",
        "buiten_assetpad",
        "ongeldige_tekst",
    ],
)
def test_documentcache_herstelt_ongeldig_manifest_of_asset(
    defect: str, document_met_cache: tuple[Path, SmartDocument]
) -> None:
    """Een onvolledige of gewijzigde cache moet opnieuw lokaal worden geextraheerd.

    Parameters
    ----------
    defect : str
        Beschadiging van het manifest of een bijbehorende figuur.
    document_met_cache : tuple[Path, SmartDocument]
        Bestaande, geldige PDF-cache met figuurasset.
    """
    pdf_pad, document = document_met_cache
    manifest_pad = constants.CACHE_DIR / "pymupdf_extractie" / document.documentvingerafdruk / "structuur.json"
    gegevens = json.loads(manifest_pad.read_text(encoding="utf-8"))
    figuur = next(element for element in gegevens["elementen"] if element["soort"] == "afbeelding")
    asset_pad = manifest_pad.parent / figuur["bestand"]
    if defect == "schema":
        gegevens["schema_versie"] += 1
    elif defect == "vingerafdruk":
        gegevens["documentvingerafdruk"] = "verkeerd"
    elif defect == "ontbrekend_veld":
        del gegevens["secties"]
    elif defect == "lege_cache":
        gegevens["secties"] = []
        gegevens["elementen"] = []
    elif defect == "dubbel_element":
        gegevens["elementen"].append(gegevens["elementen"][0])
    elif defect == "onbekend_element":
        gegevens["secties"][0]["element_ids"].append("onbekend")
    elif defect == "dubbele_toewijzing":
        sectie = next(sectie for sectie in gegevens["secties"] if sectie["element_ids"])
        sectie["element_ids"].append(sectie["element_ids"][0])
    elif defect == "niet_toegewezen":
        next(sectie for sectie in gegevens["secties"] if sectie["element_ids"])["element_ids"].pop()
    elif defect == "cyclische_ouder":
        gegevens["secties"][0]["ouder_id"] = gegevens["secties"][0]["id"]
    elif defect == "ontbrekende_asset":
        asset_pad.unlink()
    elif defect == "beschadigde_asset":
        asset_pad.write_bytes(b"geen PNG")
    elif defect == "andere_geldige_png":
        with pymupdf.open() as pdf:
            pdf.new_page(width=20, height=20).get_pixmap().save(asset_pad)
    elif defect == "absoluut_assetpad":
        figuur["bestand"] = str(asset_pad.resolve())
    elif defect == "buiten_assetpad":
        figuur["bestand"] = "../buiten.png"
    elif defect == "ongeldige_tekst":
        next(element for element in gegevens["elementen"] if element["soort"] == "paragraaf")["content"] = None
    manifest_pad.write_text("{" if defect == "json" else json.dumps(gegevens), encoding="utf-8")

    with patch.object(pymupdf.Document, "to_json", autospec=True, side_effect=pymupdf.Document.to_json) as extractie:
        hersteld = SmartDocument.from_pdf(pdf_pad)
    assert extractie.call_count == 1
    assert hersteld.documentvingerafdruk == document.documentvingerafdruk
    assert [sectie.full_text() for sectie in hersteld.sections] == [sectie.full_text() for sectie in document.sections]
    assert all(
        element.bestand.is_file() for element in hersteld.elementen.values() if isinstance(element, Afbeelding)
    )


@pytest.mark.parametrize(
    ("veld", "waarde"),
    [("schema_versie", 2), ("extractor_versie", 999), ("pymupdf_versie", "andere-versie"), ("image_dpi", 100)],
)
def test_documentcache_scheidt_extractie_instellingen(
    veld: str, waarde: int | str, document_met_cache: tuple[Path, SmartDocument], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Elke uitvoerbepalende versie of renderinstelling krijgt een afzonderlijke cache.

    Parameters
    ----------
    veld : str
        Te wijzigen extractieoptie.
    waarde : int | str
        Gesimuleerde andere versie of DPI.
    document_met_cache : tuple[Path, SmartDocument]
        Bestaande extractie onder de oorspronkelijke instellingen.
    monkeypatch : pytest.MonkeyPatch
        Vervangt uitsluitend de nieuwe extractieconfiguratie.
    """
    pdf_pad, eerste = document_met_cache
    instellingen = dict(eerste.extractie_metadata, **{veld: waarde})
    monkeypatch.setattr(SmartDocument, "_extractie_configuratie", staticmethod(lambda: instellingen))
    with patch.object(pymupdf.Document, "to_json", autospec=True, side_effect=pymupdf.Document.to_json) as extractie:
        tweede = SmartDocument.from_pdf(pdf_pad)
    assert extractie.call_count == 1
    assert tweede.documentvingerafdruk != eerste.documentvingerafdruk
    assert eerste.extractie_metadata[veld] != tweede.extractie_metadata[veld]
    for document in (eerste, tweede):
        assert (constants.CACHE_DIR / "pymupdf_extractie" / document.documentvingerafdruk / "structuur.json").is_file()


def test_documentcache_scheidt_andere_bron_met_dezelfde_bestandsnaam(
    document_met_cache: tuple[Path, SmartDocument]
) -> None:
    """Verwar verschillende PDF-inhoud onder dezelfde bestandsnaam nooit met een cachehit.

    Parameters
    ----------
    document_met_cache : tuple[Path, SmartDocument]
        Eerste bron en cache voor de gelijknamige tweede PDF.
    """
    pdf_pad, eerste = document_met_cache
    ander_pad = pdf_pad.parent / "andere_map" / pdf_pad.name
    ander_pad.parent.mkdir()
    with pymupdf.open() as pdf:
        pagina = pdf.new_page()
        pagina.insert_text((72, 72), "1 Andere inspectie", fontsize=18)
        pagina.insert_text((72, 120), "Dit is inhoud uit een andere bron.")
        pdf.save(ander_pad)
    tweede = SmartDocument.from_pdf(ander_pad)
    assert tweede.bron_hash != eerste.bron_hash
    assert tweede.documentvingerafdruk != eerste.documentvingerafdruk
    assert tweede.document_name == eerste.document_name
    assert "Dit is inhoud uit een andere bron." in " ".join(sectie.full_text() for sectie in tweede.sections)


def test_documentcache_behoudt_native_meettabellen_uit_echt_rapport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, blokkeer_ocr_en_netwerk: Callable[..., NoReturn]
) -> None:
    """Toets echte brede en smallere vervolgtabellen na export en een PDF-vrije cachehit.

    Parameters
    ----------
    tmp_path : Path
        Tijdelijke selectie van meetpagina's en cache.
    monkeypatch : pytest.MonkeyPatch
        Isoleert de cache en blokkeert PDF-opening op de tweede aanroep.
    blokkeer_ocr_en_netwerk : Callable[..., NoReturn]
        Verbiedt OCR, netwerk en later iedere PDF-opening.
    """
    bron_pad = next((Path(__file__).resolve().parents[1] / "data" / "duikrapporten").glob("KZG0202_*.pdf"), None)
    if bron_pad is None:
        pytest.skip("Lokaal proefrapport KZG0202 ontbreekt.")
    monkeypatch.setattr(constants, "CACHE_DIR", tmp_path / "cache")
    pdf_pad = tmp_path / "KZG0202_meetpagina.pdf"
    with pymupdf.open(bron_pad) as bron, pymupdf.open() as selectie:
        for pagina in (52, 55, 56, 57):
            selectie.insert_pdf(bron, from_page=pagina - 1, to_page=pagina - 1)
        selectie.save(pdf_pad)
    eerste = SmartDocument.from_pdf(pdf_pad, use_cache=False)
    tabellen = [element for element in eerste.elementen.values() if isinstance(element, DocumentTabel)]
    assert any(cel.content == "P2.39" for tabel in tabellen for cel in tabel.cells)
    assert {14, 18} <= {tabel.column_count for tabel in tabellen}
    monkeypatch.setattr(pymupdf, "open", blokkeer_ocr_en_netwerk)
    tweede = SmartDocument.from_pdf(pdf_pad)
    assert tweede.elementen == eerste.elementen
    assert [sectie.element_ids for sectie in tweede.sections] == [sectie.element_ids for sectie in eerste.sections]


def test_documentcontract_sectie_behoudt_native_tekst_en_hierarchie() -> None:
    """Behoud bestaande teksttoegang naast expliciete bron- en hierarchiegegevens."""
    locatie = BronLocatie(pagina=3, bbox=(72, 100, 500, 140))
    paragraaf = Paragraaf("Paal P2.39\nDiameter 230 mm", id="tekst-1", bronlocaties=(locatie,))
    sectie = Sectie(
        "5.1 Constructie A",
        inhoud=[paragraaf],
        id="sectie-2",
        kopniveau=2,
        ouder_id="sectie-1",
        koplocatie=locatie,
        element_ids=[paragraaf.id],
    )

    assert sectie.full_text() == "Paal P2.39\nDiameter 230 mm"
    assert sectie.inhoud[0] is paragraaf
    assert sectie.koplocatie == locatie
    assert sectie.ouder_id == "sectie-1"
    assert sectie.kopniveau == 2
    assert Sectie("Losse sectie").element_ids == []


def test_documentcontract_afbeelding_bewaart_plaatsing_en_bijschrift() -> None:
    """Bewaar een PNG-verwijzing zonder de native bijschrifttekst in de figuur te dupliceren."""
    locatie = BronLocatie(pagina=4, bbox=(72, 160, 472, 400))
    afbeelding = Afbeelding(
        id="figuur-1",
        bestand=Path("afbeeldingen/figuur-1.png"),
        bronlocaties=(locatie,),
        leesvolgorde=3,
        bijschrift_id="tekst-2",
    )

    assert afbeelding.bestand.as_posix() == "afbeeldingen/figuur-1.png"
    assert afbeelding.bronlocaties == (locatie,)
    assert afbeelding.bijschrift_id == "tekst-2"
    assert afbeelding.leesvolgorde == 3


def test_documentcontract_tabel_behoudt_samenvoegingen_en_brongebieden() -> None:
    """Bewaar ruwe celspans en segmenten zonder waarden of lege posities door te vullen."""
    eerste_locatie = BronLocatie(3, (20, 40, 100, 60))
    tweede_locatie = BronLocatie(4, (20, 40, 100, 60))
    samengevoegde_cel = TabelCel("Diameter", 0, 0, column_span=2, bronlocaties=(eerste_locatie,))
    tabel = DocumentTabel(
        row_count=2,
        column_count=2,
        cells=(samengevoegde_cel, TabelCel("P2.39", 1, 0), TabelCel("230", 1, 1)),
        bronlocaties=(eerste_locatie, tweede_locatie),
    )

    assert tabel.matrix == (("Diameter", None), ("P2.39", "230"))
    assert get_table_content(tabel) == [["Diameter", ""], ["P2.39", "230"]]
    assert samengevoegde_cel.column_span == 2
    assert samengevoegde_cel.bronlocaties == (eerste_locatie,)
    assert tabel.bronlocaties == (eerste_locatie, tweede_locatie)


def test_documentcontract_tabel_werkt_met_bestaande_id_selectie() -> None:
    """Gebruik bestaande tabelclassificatie zonder Azure-objecten of tekstcorrecties."""
    tabel = DocumentTabel(
        row_count=3,
        column_count=2,
        cells=(TabelCel("P2.39", 0, 0), TabelCel("P2.40", 1, 0), TabelCel("P2.41", 2, 0)),
    )

    assert is_table_type_by_id_func(tabel, get_paal_id)
    assert get_table_content(tabel)[0][0] == "P2.39"


def test_native_tabelconversie_verzint_geen_kolom_bij_kortere_rechterrand() -> None:
    """Behoud het native 2x3-raster wanneer een laatste cel een kortere rechterrand heeft."""
    tabel = SimpleNamespace(
        row_count=2,
        col_count=3,
        bbox=(0, 0, 300, 40),
        rows=[
            SimpleNamespace(cells=[(0, 0, 100, 20), (100, 0, 200, 20), (200, 0, 300, 20)]),
            SimpleNamespace(cells=[None, None, (200, 20, 250, 40)]),
        ],
        extract=lambda: [["A", "B", "C"], [None, None, "D"]],
    )
    document_tabel = DocumentTabel.from_pymupdf(tabel, pagina=1, id="tabel-1")
    assert document_tabel.matrix == (("A", "B", "C"), (None, None, "D"))
    assert all(cel.column_index + cel.column_span <= 3 for cel in document_tabel.cells)
    assert all(cel.column_span == 1 for cel in document_tabel.cells)


def test_native_tabelconversie_behoudt_samenvoeging_en_lege_cel() -> None:
    """Kopieer native celgeometrie en tekst voordat de PDF wordt gesloten."""
    with pymupdf.open() as pdf:
        pagina = pdf.new_page()
        pagina.draw_rect((50, 50, 250, 140))
        pagina.draw_line((50, 80), (250, 80))
        pagina.draw_line((50, 110), (250, 110))
        pagina.draw_line((150, 80), (150, 140))
        pagina.insert_text((60, 70), "Diameter")
        pagina.insert_text((60, 100), "P2.39")
        pagina.insert_text((160, 100), "230")
        pagina.insert_text((60, 130), "P2.40")
        # Ook find_tables gebruikt standaard layout; schakel dat voor native celrasters expliciet uit.
        gevonden = pagina.find_tables(use_layout=False).tables
        assert len(gevonden) == 1
        tabel = DocumentTabel.from_pymupdf(gevonden[0], pagina=1, id="tabel-1")

    assert tabel.matrix == (("Diameter", None), ("P2.39", "230"), ("P2.40", ""))
    assert tabel.cells[0].column_span == 2
    assert tabel.cells[0].row_span == 1
    assert tabel.bronlocaties[0].pagina == 1
    assert all(cel.bronlocaties for cel in tabel.cells)


@pytest.mark.parametrize("eenhedenrij", ["ontbreekt", "leeg"])
@pytest.mark.parametrize("afwijkende_subkop", [False, True])
@pytest.mark.parametrize("veel_legenda", [False, True])
def test_native_meettabellen_behouden_smaller_vervolg_en_verwijderen_bevestigde_kop(
    eenhedenrij: str, afwijkende_subkop: bool, veel_legenda: bool
) -> None:
    """Combineer gelijke domeinkolommen zonder fysieke rasterbreedtes gelijk te veronderstellen.

    Parameters
    ----------
    eenhedenrij : str
        Een vervolg zonder eenhedenrij of met een lege eenhedenrij.
    afwijkende_subkop : bool
        Of het vervolg een andere subkop heeft en dus niet gecombineerd mag worden.
    veel_legenda : bool
        Of legenda's de ID-fractie onder de oude 50%-drempel brengen.
    """
    tabellen = []
    for segment in range(2):
        breed = segment == 0
        rijen = [
            ["", "Diameter", "Schades"],
            ["Paalnummer", "Gemiddelde", "Aantasting"],
            ["[Px.y]", "[mm]", ""],
        ] + [[f"P2.{segment * 4 + index}", "230", "Nee"] for index in range(1, 5)]
        if segment == 1 and afwijkende_subkop:
            rijen[1][1] = "Andere betekenis"
        if breed:
            rijen = [rij[:2] + [None] + rij[2:] for rij in rijen]
        else:
            # De echte KZG0202-vervolgpagina's herhalen de koppen zonder eenhedenrij.
            if eenhedenrij == "ontbreekt":
                rijen.pop(2)
            else:
                rijen[2] = ["", "", ""]
        if veel_legenda:
            rijen.extend([["Legenda"] + [""] * (len(rijen[0]) - 1) for _ in range(10)])
        tabel = DocumentTabel(
            len(rijen),
            4 if breed else 3,
            cells=tuple(
                TabelCel(tekst, rij_index, kolom_index, column_span=2 if breed and kolom_index == 1 else 1)
                for rij_index, rij in enumerate(rijen)
                for kolom_index, tekst in enumerate(rij)
                if tekst is not None
            ),
        )
        tabellen.append(tabel)

    if afwijkende_subkop:
        with pytest.raises(ValueError, match="Onverenigbare native tabelkoppen"):
            StructuredTable.from_doc_table(tabellen, TableType.PALEN)
        return

    gestructureerd = StructuredTable.from_doc_table(tabellen, TableType.PALEN)

    assert gestructureerd is not None
    assert gestructureerd.num_rows == 8
    assert gestructureerd.columns[0].values == [f"P2.{index}" for index in range(1, 9)]
    assert gestructureerd.get_value("Diameter", "Gemiddelde", index=7) == "230"
    assert tabellen[0].matrix[3] == ("P2.1", "230", None, "Nee")


def test_documentcontract_tabel_werkt_met_bestaande_kopinterpretatie() -> None:
    """Behoud de StructuredTable-route voor eigen ruwe tabellen."""
    rijen = (("Constructieonderdeel", "Aangetast"), ("Fundering", "Nee"))
    tabel = DocumentTabel(
        row_count=2,
        column_count=2,
        cells=tuple(
            TabelCel(tekst, rij_index, kolom_index)
            for rij_index, rij in enumerate(rijen)
            for kolom_index, tekst in enumerate(rij)
        ),
    )

    gestructureerd = StructuredTable.from_doc_table([tabel], TableType.TOESTANDSBEPALING)

    assert gestructureerd is not None
    assert gestructureerd.get_value(header_in="Constructieonderdeel") == "Fundering"
    assert gestructureerd.get_value(header_in="Aangetast") == "Nee"


def test_documentcontract_registratie_bewaart_tekst_tabel_en_figuur_in_volgorde() -> None:
    """Laat secties dezelfde canonieke objecten raadplegen zonder Azure-analyseresultaat."""
    sectie = Sectie("Constructie A", id="sectie-1")
    document = SmartDocument("KZG0202", sections=[sectie])
    paragraaf = Paragraaf("Native beschrijving", id="tekst-1", leesvolgorde=1)
    tabel = DocumentTabel(0, 0, id="tabel-1", leesvolgorde=2)
    afbeelding = Afbeelding("figuur-1", Path("figuur.png"), (), leesvolgorde=3)

    for element in (paragraaf, tabel, afbeelding):
        document.registreer_element(sectie, element)

    elementen = document.get_elementen(sectie)
    assert document.analyze_result is None
    assert sectie.element_ids == ["tekst-1", "tabel-1", "figuur-1"]
    assert elementen[0] is paragraaf
    assert elementen[1] is tabel
    assert elementen[2] is afbeelding
    assert document.elementen["tabel-1"] is tabel
    assert sectie.full_text() == "Native beschrijving"
    assert tuple(sectie.inhoud) == (paragraaf,)
    assert tuple(sectie.tabellen) == (tabel,)
    assert sectie.afbeeldingen == (afbeelding,)
    assert SmartDocument("Ander document").elementen == {}


def test_documentcontract_registratie_weigert_dubbele_element_id() -> None:
    """Voorkom dat een tweede element dezelfde bronidentiteit overschrijft."""
    sectie = Sectie("Constructie A")
    document = SmartDocument("KZG0202", sections=[sectie])
    origineel = Paragraaf("Origineel", id="tekst-1")
    document.registreer_element(sectie, origineel)

    with pytest.raises(ValueError, match="al geregistreerd"):
        document.registreer_element(sectie, Paragraaf("Anders", id="tekst-1"))

    assert document.elementen["tekst-1"] is origineel
    assert sectie.element_ids == ["tekst-1"]


def test_documentcontract_registratie_weigert_lege_id_en_vreemde_sectie() -> None:
    """Verander registratie en sectieverwijzingen niet bij ongeldige koppelingen."""
    sectie = Sectie("Constructie A")
    document = SmartDocument("KZG0202", sections=[sectie])

    with pytest.raises(ValueError, match="leeg"):
        document.registreer_element(sectie, Paragraaf("Zonder identiteit"))
    with pytest.raises(ValueError, match="sectie hoort niet"):
        document.registreer_element(Sectie("Constructie A"), Paragraaf("Andere sectie", id="tekst-1"))

    assert document.elementen == {}
    assert sectie.element_ids == []


def test_documentcontract_fixture_gebruikt_eigen_typen(
    kzg0202_smart_document: SmartDocument,
    blokkeer_ocr_en_netwerk: Callable[..., NoReturn],
) -> None:
    """Laad historische referentiewaarden zonder SDK-objecten of verborgen extractie.

    Parameters
    ----------
    kzg0202_smart_document : SmartDocument
        Gemigreerde eigen documentfixture.
    blokkeer_ocr_en_netwerk : Callable[..., NoReturn]
        Blokkeert OCR en netwerk tijdens het lezen en gebruiken van de fixture.
    """
    document = kzg0202_smart_document

    assert document.elementen
    assert document.sections
    assert all(isinstance(element, (Paragraaf, DocumentTabel)) for element in document.elementen.values())
    assert all(sectie._elementen is document.elementen for sectie in document.sections)
    assert b"azure.ai.documentintelligence" not in pickle.dumps(document)
    assert document.get_meettabel_fundering_paal() is not None


def test_documentcontract_pickle_behoudt_nieuwe_elementverwijzingen() -> None:
    """Laat herstel van standaardvelden bestaande nieuwe registraties ongemoeid."""
    sectie = Sectie("Constructie A", id="sectie-1")
    document = SmartDocument("KZG0202", sections=[sectie])
    document.registreer_element(sectie, Paragraaf("Native beschrijving", id="tekst-1"))

    hersteld = pickle.loads(pickle.dumps(document))

    assert hersteld.sections[0].element_ids == ["tekst-1"]
    assert hersteld.get_elementen(hersteld.sections[0])[0] is hersteld.elementen["tekst-1"]


def test_documentcontract_import_en_fixture_zonder_azure_sdk() -> None:
    """Bewijs in een vers proces dat productie-import en fixture geen Azure SDK nodig hebben."""
    code = """
import importlib.abc
import sys
from pathlib import Path

class VerbiedAzure(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'azure' or fullname.startswith('azure.'):
            raise ModuleNotFoundError('Azure SDK is niet beschikbaar')

sys.meta_path.insert(0, VerbiedAzure())
sys.path.insert(0, str(Path.cwd() / 'tests'))
from conftest import load_kzg0202_smart_document
from tekstherkenning_ark.cli import main
document = load_kzg0202_smart_document()
assert document.elementen
assert document.get_meettabel_fundering_paal() is not None
assert not any(naam == 'azure' or naam.startswith('azure.') for naam in sys.modules)
"""
    resultaat = subprocess.run(
        ["uv", "run", "--no-sync", "--offline", "python", "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultaat.returncode == 0, resultaat.stderr


@pytest.mark.parametrize(
    "rapport_pad",
    sorted((Path(__file__).resolve().parents[1] / "data" / "duikrapporten").glob("*.pdf")),
    ids=lambda pad: pad.stem,
)
def test_native_corpus_behoudt_broncellen_en_meetrecords(
    rapport_pad: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    """Vergelijk broncellen en palen-/kesprecords onafhankelijk met lokale PDF-pagina's.

    Parameters
    ----------
    rapport_pad : Path
        Lokaal rapport; niet afhankelijk van historische Azure-uitkomsten.
    tmp_path : Path
        Tijdelijke document- en assetcache.
    monkeypatch : pytest.MonkeyPatch
        Isoleert de cache van bestaande gebruikersdata.
    request : pytest.FixtureRequest
        Activeert de relatief dure controle uitsluitend met --pdf-corpus.
    """
    if not request.config.getoption("--pdf-corpus"):
        pytest.skip("Gebruik --pdf-corpus voor de volledige lokale broncontrole.")
    monkeypatch.setattr(constants, "CACHE_DIR", tmp_path / "cache")
    begin = perf_counter()
    brontabellen = {}
    bron_ids = {TableType.PALEN: Counter(), TableType.KESPEN: Counter()}
    vorige_meettype = None
    vorige_meetpagina = -2
    with pymupdf.open(rapport_pad) as bron:
        assert any(pagina.get_text().strip() for pagina in bron), "Bron-PDF heeft geen selecteerbare tekst."
        for pagina in bron:
            pagina.remove_rotation()
            # Native tekstvoorbereiding voorkomt verouderde tabeltekst na layout van een eerder document.
            pagina.get_text("dict", sort=True)
            for index, tabel in enumerate(pagina.find_tables(use_layout=False).tables):
                matrix = tabel.extract()
                tabel_id = f"p{pagina.number + 1}-t{index}"
                brontabellen[tabel_id] = tuple(
                    tuple(
                        (matrix[rij_index][kolom_index] or "") if gebied is not None else None
                        for kolom_index, gebied in enumerate(rij.cells)
                    )
                    for rij_index, rij in enumerate(tabel.rows)
                )
                eerste_kolom = [
                    matrix[rij_index][0] or ""
                    for rij_index, rij in enumerate(tabel.rows)
                    if rij.cells[0] is not None
                ]
                for tabeltype, herken_id in ((TableType.PALEN, get_paal_id), (TableType.KESPEN, get_kesp_id)):
                    gevonden = [herken_id(waarde) for waarde in eerste_kolom if herken_id(waarde) is not None]
                    meetkop = "paalnummer" if tabeltype == TableType.PALEN else "kespnummer"
                    heeft_meetkop = any("".join(waarde.lower().split()) == meetkop for waarde in eerste_kolom)
                    koploos_vervolg = (
                        vorige_meettype == tabeltype
                        and pagina.number <= vorige_meetpagina + 1
                        and eerste_kolom
                        and len(gevonden) / len(eerste_kolom) > 0.5
                    )
                    if heeft_meetkop or koploos_vervolg:
                        bron_ids[tabeltype].update(gevonden)
                        vorige_meettype, vorige_meetpagina = tabeltype, pagina.number
    # Leg bronwaarden vast voordat layoutanalyse native extractie-instellingen kan beinvloeden.
    document = SmartDocument.from_pdf(rapport_pad, use_cache=False)
    geextraheerd = {
        element.id.removeprefix(f"{document.bron_hash[:12]}-"): element.matrix
        for element in document.elementen.values() if isinstance(element, DocumentTabel)
    }
    verschillen = [
        (tabel_id, rij, kolom, " ".join(waarde.split()) == " ".join(brontabellen[tabel_id][rij][kolom].split()))
        for tabel_id, matrix in geextraheerd.items()
        for rij, waarden in enumerate(matrix)
        for kolom, waarde in enumerate(waarden)
        if waarde is not None and brontabellen[tabel_id][rij][kolom] is not None
        and waarde != brontabellen[tabel_id][rij][kolom]
    ]
    assert geextraheerd == brontabellen, f"Tabel/rij/kolom/alleen_regelindeling: {verschillen}"
    for tabeltype, tabel in (
        (TableType.PALEN, document.get_meettabel_fundering_paal()),
        (TableType.KESPEN, document.get_meettabel_fundering_kesp()),
    ):
        herken_id = get_paal_id if tabeltype == TableType.PALEN else get_kesp_id
        werkelijk = Counter(herken_id(waarde) for waarde in tabel.columns[0].values) if tabel else Counter()
        assert werkelijk == bron_ids[tabeltype], f"{rapport_pad.stem}: verschil in {tabeltype}-meetrecords"
    assert all(
        element.bestand.is_file() for element in document.elementen.values() if isinstance(element, Afbeelding)
    )
    print(
        f"{rapport_pad.stem}: {len(document.pagina_afmetingen)} pagina's, {len(brontabellen)} tabellen, "
        f"{sum(bron_ids[TableType.PALEN].values())} paalrijen, "
        f"{sum(bron_ids[TableType.KESPEN].values())} kesprijen, {perf_counter() - begin:.2f} s"
    )


def test_from_pdf_behoudt_hierarchie_en_native_tabel_zonder_azure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, blokkeer_ocr_en_netwerk: Callable[..., NoReturn]
) -> None:
    """Lees meerdere secties en een eigen tabel via de publieke PDF-route.

    Parameters
    ----------
    tmp_path : Path
        Tijdelijke PDF- en assetmap.
    monkeypatch : pytest.MonkeyPatch
        Isoleert caches en verbiedt iedere OCR-fallback.
    blokkeer_ocr_en_netwerk : Callable[..., NoReturn]
        Netwerk- en OCR-blokkade.
    """
    monkeypatch.setattr(constants, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(pymupdf.Page, "get_textpage_ocr", blokkeer_ocr_en_netwerk)
    pdf_pad = tmp_path / "KZG0202_proef.pdf"
    with pymupdf.open() as pdf:
        pagina = pdf.new_page()
        pagina.insert_text((72, 72), "1 Resultaten", fontsize=18)
        pagina.insert_text((72, 105), "Algemene native beschrijving.")
        pagina.insert_text((72, 155), "1.1 Constructie A", fontsize=15)
        pagina.insert_text((72, 190), "De paal is onderzocht zonder beeldherkenning.")
        pagina.insert_text((72, 240), "1.1.1 Toestandbepaling", fontsize=13)
        pagina.draw_rect((72, 270, 450, 330))
        pagina.draw_line((72, 300), (450, 300))
        pagina.draw_line((300, 270), (300, 330))
        pagina.insert_text((80, 290), "Constructieonderdeel")
        pagina.insert_text((310, 290), "Aangetast")
        pagina.insert_text((80, 320), "Fundering")
        pagina.insert_text((310, 320), "Nee")
        pagina = pdf.new_page()
        pagina.insert_text((72, 72), "Vervolg binnen dezelfde toestandsectie.")
        pagina.insert_text((72, 160), "1.2 Constructie B", fontsize=15)
        pagina.insert_text((72, 200), "Deze beschrijving hoort uitsluitend bij constructie B.")
        pdf.save(pdf_pad)

    # Een oude entry mag de nieuwe lokale route niet onzichtbaar omzeilen.
    constants.CACHE_DIR.mkdir(parents=True)
    oud_cachepad = constants.CACHE_DIR / f"{pdf_pad.stem}_docai_result.pkl"
    oud_cachepad.write_bytes(b"geen geldige oude cache")
    document = SmartDocument.from_pdf(pdf_pad)

    assert document.analyze_result is None
    assert document.get_raknaam() == "KZG0202"
    hoofdstuk = next(sectie for sectie in document.sections if sectie.titel == "1 Resultaten")
    constructie = next(sectie for sectie in document.sections if sectie.titel == "1.1 Constructie A")
    toestand = next(sectie for sectie in document.sections if sectie.titel == "1.1.1 Toestandbepaling")
    assert constructie.ouder_id == hoofdstuk.id
    assert toestand.ouder_id == constructie.id
    assert toestand.kopniveau == 3
    assert len(toestand.tabellen) == 1
    assert toestand.tabellen[0].matrix == (("Constructieonderdeel", "Aangetast"), ("Fundering", "Nee"))
    assert "Fundering" not in toestand.full_text()
    assert "Vervolg binnen dezelfde toestandsectie." in toestand.full_text()
    assert len(document.get_rakdeel_secties()) == 2
    assert oud_cachepad.read_bytes() == b"geen geldige oude cache"
    assert all(element.bronlocaties for element in document.elementen.values())
    assert len({element_id for sectie in document.sections for element_id in sectie.element_ids}) == len(
        document.elementen
    )


@pytest.mark.parametrize("soort", ["beschadigd", "versleuteld", "zonder_tekst"])
def test_from_pdf_meldt_ongeschikte_invoer_zonder_ocr(
    soort: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, blokkeer_ocr_en_netwerk: Callable[..., NoReturn]
) -> None:
    """Geef een gerichte fout zonder OCR- of cloudfallback.

    Parameters
    ----------
    soort : str
        Afwijkend PDF-geval.
    tmp_path : Path
        Tijdelijke invoer- en assetmap.
    monkeypatch : pytest.MonkeyPatch
        Isoleert de uitvoer van de bestaande caches.
    blokkeer_ocr_en_netwerk : Callable[..., NoReturn]
        Netwerk- en OCR-blokkade.
    """
    monkeypatch.setattr(constants, "CACHE_DIR", tmp_path / "cache")
    pdf_pad = tmp_path / "invoer.pdf"
    if soort == "beschadigd":
        pdf_pad.write_bytes(b"ongeldig PDF-bestand")
        melding = "Onleesbare PDF"
    else:
        with pymupdf.open() as pdf:
            pagina = pdf.new_page()
            if soort == "versleuteld":
                pagina.insert_text((72, 72), "Native tekst")
                pdf.save(pdf_pad, encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="test", user_pw="test")
                melding = "Versleutelde PDF"
            else:
                pdf.save(pdf_pad)
                melding = "geen selecteerbare tekst"

    with pytest.raises(ValueError, match=melding):
        SmartDocument.from_pdf(pdf_pad, use_cache=False)


def test_rakdeelsectie_leest_geen_toestand_uit_volgende_constructie() -> None:
    """Begrens ook directe sectieconversie als een constructie zijn tabellen mist."""
    tabel = DocumentTabel(
        2,
        2,
        cells=(
            TabelCel("Constructieonderdeel", 0, 0), TabelCel("Aangetast", 0, 1),
            TabelCel("Fundering", 1, 0), TabelCel("Nee", 1, 1),
        ),
    )
    secties = [
        Sectie("5.1 Constructie A", inhoud=[Paragraaf("Alleen beschrijving A")]),
        Sectie("5.2 Constructie B"),
        Sectie("5.2.1 Toestandbepaling", tabellen=[tabel]),
    ]

    rakdeel = RakdeelSectie.from_smart_document(secties)

    assert rakdeel.toestand_tabel is None
    assert rakdeel.gebreken_tabel is None


def test_sectieparser_verwart_inhoudsopgave_en_bijschriften_niet_met_hoofdstukken() -> None:
    """Houd appendixverwijzingen en verkeerd geclassificeerde bijschriften bij hun huidige sectie."""
    locatie = BronLocatie(2, (72, 72, 500, 100))
    document = SmartDocument("KZG0202", bron_hash="bron")
    elementen = [
        Paragraaf(tekst, id=f"tekst-{index}", bronlocaties=(locatie,), rol=rol)
        for index, (tekst, rol) in enumerate(
            [
                ("INHOUDSOPGAVE", "section-header"),
                ("Bijlage 1 Meettabel houtmonsters", "text"),
                ("Bijlage 3 Meettabel fundering", "section-header"),
                ("1 INLEIDING", "section-header"),
                ("Tabel 2.1: Paspoortgegevens.", "section-header"),
            ]
        )
    ]

    document._parse_document(elementen)

    assert [sectie.titel for sectie in document.sections] == ["INHOUDSOPGAVE", "1 INLEIDING"]
    assert "Bijlage 3" in document.sections[0].full_text()
    assert "Tabel 2.1" in document.sections[1].full_text()


def test_from_pdf_behoudt_native_tekst_op_geroteerde_pagina(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, blokkeer_ocr_en_netwerk: Callable[..., NoReturn]
) -> None:
    """Behoud native inhoud en paginametadata bij PDF-rotatie.

    Parameters
    ----------
    tmp_path : Path
        Tijdelijke invoer- en assetmap.
    monkeypatch : pytest.MonkeyPatch
        Isoleert de uitvoer van de productie-extractor.
    blokkeer_ocr_en_netwerk : Callable[..., NoReturn]
        Netwerk- en OCR-blokkade.
    """
    monkeypatch.setattr(constants, "CACHE_DIR", tmp_path / "cache")
    pdf_pad = tmp_path / "geroteerd.pdf"
    with pymupdf.open() as pdf:
        pagina = pdf.new_page()
        pagina.insert_text((100, 150), "Native_rotatietekst", fontsize=12)
        pagina.set_rotation(90)
        pdf.save(pdf_pad)

    document = SmartDocument.from_pdf(pdf_pad, use_cache=False)

    assert any(
        "Native_rotatietekst" in element.content
        for element in document.elementen.values()
        if isinstance(element, Paragraaf)
    )
    assert document.pagina_afmetingen[1][0] > document.pagina_afmetingen[1][1]


def test_layoutvolgorde_behoudt_kolommen_en_plaatst_ongeclassificeerde_tekst_lokaal() -> None:
    """Behoud de boxvolgorde in plaats van de hele pagina op y/x te sorteren."""
    document = SmartDocument("volgorde", bron_hash="bron")
    layout = {
        "pages": [{"page_number": 1, "boxes": [
            {"boxclass": "text", "x0": 300, "y0": 10, "x1": 500, "y1": 30},
            {"boxclass": "text", "x0": 50, "y0": 50, "x1": 250, "y1": 70},
        ]}],
    }
    regels = {1: [
        {"bbox": (60, 10, 200, 30), "spans": [{"text": "Ongeclassificeerd links"}]},
        {"bbox": (310, 10, 480, 30), "spans": [{"text": "Rechterkolom eerst"}]},
        {"bbox": (60, 50, 200, 70), "spans": [{"text": "Linkerkolom daarna"}]},
    ]}

    elementen = document._lees_layout(layout, {1: []}, regels)

    assert [element.content for element in elementen] == [
        "Rechterkolom eerst", "Ongeclassificeerd links", "Linkerkolom daarna",
    ]
    assert [element.leesvolgorde for element in elementen] == [0, 1, 2]


@pytest.fixture
def blokkeer_ocr_en_netwerk(monkeypatch: pytest.MonkeyPatch) -> Callable[..., NoReturn]:
    """Laat de extractieproef falen zodra OCR of een netwerkverbinding wordt gestart.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Herstelt de geblokkeerde functies na iedere test.

    Returns
    -------
    Callable[..., NoReturn]
        Ook als expliciete OCR-callback bruikbare blokkade voor de layoutextractor.
    """

    def verboden_aanroep(*args: object, **kwargs: object) -> NoReturn:
        """Meld een ongewenste OCR- of netwerkaanroep tijdens lokale extractie."""
        pytest.fail("Lokale PDF-extractie mag geen OCR of netwerkverbinding starten.")

    # Een toevallige OCR-fallback of cloudcall moet de proef zichtbaar laten falen.
    monkeypatch.setattr(pymupdf.Page, "get_textpage_ocr", verboden_aanroep)
    monkeypatch.setattr(socket.socket, "connect", verboden_aanroep)
    monkeypatch.setattr(socket, "create_connection", verboden_aanroep)
    return verboden_aanroep


def test_pymupdf_json_behoudt_native_tekst_zonder_ocr(
    tmp_path: Path, blokkeer_ocr_en_netwerk: Callable[..., NoReturn]
) -> None:
    """Verifieer het JSON-contract van de geinstalleerde PyMuPDF-API.

    Parameters
    ----------
    tmp_path : Path
        Tijdelijke uitvoermap voor eventuele figuurassets.
    blokkeer_ocr_en_netwerk : Callable[..., NoReturn]
        Blokkeert OCR en netwerkverkeer gedurende deze test.
    """
    with pymupdf.open() as document:
        pagina = document.new_page()
        pagina.insert_text((72, 72), "1 Inspectieresultaten", fontsize=18)
        pagina.insert_text((72, 120), "Deze selecteerbare tekst komt rechtstreeks uit de PDF.", fontsize=11)

        # force_ocr=False voorkomt automatische OCR niet; use_ocr=False doet dat wel.
        resultaat = document.to_json(
            use_ocr=False,
            ocr_function=blokkeer_ocr_en_netwerk,
            force_text=True,
            write_images=True,
            embed_images=False,
            image_dpi=150,
            image_path=str(tmp_path),
        )

    assert isinstance(resultaat, str)
    gegevens = json.loads(resultaat)
    assert gegevens["page_count"] == 1
    assert gegevens["use_ocr"] == 0
    pagina_gegevens = gegevens["pages"][0]
    assert pagina_gegevens["page_number"] == 1
    assert pagina_gegevens["full_ocred"] is False

    tekst = " ".join(
        span["text"]
        for blok in pagina_gegevens["boxes"]
        for regel in (blok.get("textlines") or [])
        for span in regel["spans"]
    )
    assert "1 Inspectieresultaten" in tekst
    assert "Deze selecteerbare tekst komt rechtstreeks uit de PDF." in tekst


@pytest.mark.parametrize("beeldsoort", ["raster", "vector"])
def test_pymupdf_behoudt_native_figuurlabel_zonder_pixeltekst_te_herkennen(
    beeldsoort: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, blokkeer_ocr_en_netwerk: Callable[..., NoReturn]
) -> None:
    """Behoud selecteerbare figuurtekst en exporteer de figuur zonder nieuwe OCR.

    Parameters
    ----------
    beeldsoort : str
        Een rasterfiguur met native tekstlaag of een volledig vectorgebaseerde figuur.
    tmp_path : Path
        Tijdelijke uitvoermap voor de figuur-PNG.
    monkeypatch : pytest.MonkeyPatch
        Isoleert de uitvoer van de productie-extractor.
    blokkeer_ocr_en_netwerk : Callable[..., NoReturn]
        Laat iedere OCR- of netwerkaanroep falen.
    """
    monkeypatch.setattr(constants, "CACHE_DIR", tmp_path / "cache")
    pdf_pad = tmp_path / "figuur.pdf"
    with pymupdf.open() as figuur, pymupdf.open() as document:
        tekening = figuur.new_page(width=400, height=240)
        tekening.draw_rect((10, 10, 390, 230), color=(0, 0, 0), fill=(0.9, 0.95, 1))
        tekening.draw_line((40, 200), (370, 200), width=2)
        tekening.draw_line((40, 200), (40, 30), width=2)
        for index, hoogte in enumerate((50, 90, 130, 110, 150)):
            links = 65 + index * 55
            tekening.draw_rect((links, 200 - hoogte, links + 30, 200), color=(0, 0, 0), fill=(0.2, 0.6, 0.4))
        if beeldsoort == "raster":
            tekening.insert_text((70, 30), "Alleen_pixeltekst", fontsize=12)

        pagina = document.new_page()
        pagina.insert_text((72, 72), "1 Inspectieresultaten", fontsize=18)
        figuurgebied = pymupdf.Rect(72, 160, 472, 400)
        if beeldsoort == "raster":
            pagina.insert_image(figuurgebied, stream=tekening.get_pixmap().tobytes("png"))
        else:
            pagina.show_pdf_page(figuurgebied, figuur, 0)
        pagina.insert_text((140, 280), "Native_figuurlabel", fontsize=12)
        pagina.insert_text((72, 420), "Figuur 1.1: Meting.", fontsize=10)
        document.save(pdf_pad)

    document = SmartDocument.from_pdf(pdf_pad, use_cache=False)
    tekst = " ".join(element.content for element in document.elementen.values() if isinstance(element, Paragraaf))
    assert document.analyze_result is None
    assert "Native_figuurlabel" in tekst
    assert "Alleen_pixeltekst" not in tekst
    figuren = [element for element in document.elementen.values() if isinstance(element, Afbeelding)]
    assert figuren
    assert any(
        pymupdf.Rect(afbeelding.bronlocaties[0].bbox).contains(pymupdf.Point(150, 275)) for afbeelding in figuren
    )
    for afbeelding in figuren:
        assert afbeelding.bestand.is_file()
        assert afbeelding.bestand.is_relative_to(tmp_path)
    bijschrift = next(
        element for element in document.elementen.values()
        if isinstance(element, Paragraaf) and element.content.startswith("Figuur 1.1:")
    )
    assert any(afbeelding.bijschrift_id == bijschrift.id for afbeelding in figuren)


@pytest.mark.parametrize(
    ("rapport_prefix", "paginanummers", "verwachte_meetrij"),
    [
        ("KZG0202", (1, 6, 10, 11, 30, 31, 52, 53, 55), ("P2.39", "230", "230", "230", "70", "P1.39")),
        ("HEG0201", (1, 6, 10, 11, 23, 24, 40, 41, 42), ()),
        ("HEG0801", (1, 6, 10, 11, 27, 28, 49, 50, 54), ("P2.36", "200", "200", "200", "50", "P1.36")),
    ],
    ids=["KZG0202", "HEG0201", "HEG0801"],
)
def test_pymupdf_behoudt_rapportstructuur_en_figuren(
    rapport_prefix: str,
    paginanummers: tuple[int, ...],
    verwachte_meetrij: tuple[str, ...],
    tmp_path: Path,
    blokkeer_ocr_en_netwerk: Callable[..., NoReturn],
) -> None:
    """Beproef koppen, tabelsegmenten, native meet-IDs en figuren op lokale rapporten.

    Parameters
    ----------
    rapport_prefix : str
        Bestandsnaamprefix van het lokale proefrapport.
    paginanummers : tuple[int, ...]
        Representatieve, eengebaseerde pagina's inclusief tabelvervolgen.
    verwachte_meetrij : tuple[str, ...]
        Eerste zes brongeverifieerde cellen van een eerder beschadigde meetrij, indien van toepassing.
    tmp_path : Path
        Tijdelijke uitvoermap, los van bestaande document- en domeincaches.
    blokkeer_ocr_en_netwerk : Callable[..., NoReturn]
        Blokkeert ook de eigen OCR-callback van de layoutextractor.
    """
    map_rapporten = Path(__file__).resolve().parents[1] / "data" / "duikrapporten"
    pdf_pad = next(map_rapporten.glob(f"{rapport_prefix}_*.pdf"), None)
    if pdf_pad is None:
        pytest.skip(f"Lokaal proefrapport {rapport_prefix} ontbreekt.")

    with pymupdf.open(pdf_pad) as document:
        bron_bookmarks = document.get_toc()
        # Vergelijk met de PDF zelf, niet met mogelijk foutieve oude Azure-resultaten.
        bron_ids = {
            nummer: set(re.findall(r"\b(?:P\d+\.\d+|K\d+)\b", document[nummer - 1].get_text()))
            for nummer in paginanummers
        }
        start = perf_counter()
        # Native celmatrices voorkomen de puntverwijdering en rijsamenvoeging van de JSON-nabewerking.
        native_tabellen = {
            nummer: [tabel.extract() for tabel in document[nummer - 1].find_tables().tables]
            for nummer in paginanummers
        }
        gegevens = json.loads(
            document.to_json(
                pages=[nummer - 1 for nummer in paginanummers],
                use_ocr=False,
                ocr_function=blokkeer_ocr_en_netwerk,
                force_text=True,
                write_images=True,
                embed_images=False,
                image_dpi=150,
                image_format="png",
                image_path=str(tmp_path),
            )
        )
        duur = perf_counter() - start

    assert gegevens["toc"] == bron_bookmarks
    assert gegevens["use_ocr"] == 0
    assert gegevens["force_text"] is True
    assert gegevens["image_dpi"] == 150
    assert [pagina["page_number"] for pagina in gegevens["pages"]] == list(paginanummers)

    paalrijen = [rij for matrix in native_tabellen[paginanummers[-3]] for rij in matrix]
    assert any(rij[:4] == ["Paalnummer", "Haaks", "Parrallel", "Gemiddelde"] for rij in paalrijen)
    kesprijen = [rij for matrix in native_tabellen[paginanummers[-1]] for rij in matrix]
    assert any(rij[:3] == ["Kespnummer", "Hoogte", "Breedte"] for rij in kesprijen)

    if verwachte_meetrij:
        meetrijen = [
            rij
            for matrix in native_tabellen[paginanummers[-3]]
            for rij in matrix
            if rij[0] == verwachte_meetrij[0]
        ]
        assert len(meetrijen) == 1
        assert tuple(meetrijen[0][:6]) == verwachte_meetrij

    koppen = []
    aantal_tabellen = 0
    aantal_figuren = 0
    for pagina in gegevens["pages"]:
        assert pagina["full_ocred"] is False
        tabeltekst = [
            cel or ""
            for matrix in native_tabellen[pagina["page_number"]]
            for rij in matrix
            for cel in rij
        ]
        for blok in pagina["boxes"]:
            assert blok["x0"] < blok["x1"]
            assert blok["y0"] < blok["y1"]
            tekst = " ".join(
                span["text"] for regel in (blok.get("textlines") or []) for span in regel["spans"]
            )
            if blok["boxclass"] in {"title", "section-header"}:
                koppen.append(tekst)
            if blok.get("table"):
                tabel = blok["table"]
                assert len(tabel["extract"]) == tabel["row_count"]
                assert all(len(rij) == tabel["col_count"] for rij in tabel["extract"])
                aantal_tabellen += 1
            if blok["boxclass"] == "picture":
                afbeelding_pad = Path(blok["image"]).resolve()
                assert afbeelding_pad.is_relative_to(tmp_path.resolve())
                assert afbeelding_pad.suffix == ".png"
                assert afbeelding_pad.is_file()
                afbeelding = pymupdf.Pixmap(str(afbeelding_pad))
                assert afbeelding.width > 0 and afbeelding.height > 0
                aantal_figuren += 1

        if pagina["page_number"] >= paginanummers[-3]:
            gevonden_ids = set(re.findall(r"\b(?:P\d+\.\d+|K\d+)\b", " ".join(tabeltekst)))
            assert bron_ids[pagina["page_number"]]
            ontbrekende_ids = bron_ids[pagina["page_number"]] - gevonden_ids
            assert not ontbrekende_ids, f"{rapport_prefix}, pagina {pagina['page_number']}: {ontbrekende_ids}"

    assert any("Constructie A" in kop for kop in koppen)
    assert aantal_tabellen >= 3
    assert aantal_figuren >= 3
    print(
        f"{rapport_prefix}: {len(paginanummers)} pagina's, {aantal_tabellen} tabelsegmenten, "
        f"{aantal_figuren} PNG-figuren, {duur:.2f} s (native tabellen, layout en figuurexport samen)."
    )