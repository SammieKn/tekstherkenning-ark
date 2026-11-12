"""Maak documentfixtures lokaal, zonder LLM-calls of het wissen van bestaande caches."""

import argparse
import pickle
import sys
from copy import deepcopy
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "tests"))

from conftest import KZG_0202_DOC_NAME, KZG_0202_PKL_NAME, KZG_0202_TEST_DIR

from tekstherkenning_ark import constants
from tekstherkenning_ark.document.sectie import Paragraaf, Sectie
from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.document.structured_table import DocumentTabel, TabelCel


def migreer_historische_fixture(bron_pad: Path) -> SmartDocument:
    """Kopieer uitsluitend de vertrouwde historische tekst en cellen naar eigen typen.

    Parameters
    ----------
    bron_pad : Path
        Vertrouwde oude pickle; eenmalig uit te voeren in de oude SDK-omgeving.

    Returns
    -------
    SmartDocument
        SDK-vrije referentiedata, nadrukkelijk geen nieuwe PyMuPDF-extractie.
    """
    historisch = pickle.loads(bron_pad.read_bytes())
    document = SmartDocument(document_name=historisch.document_name)
    for sectie_index, oude_sectie in enumerate(historisch.sections):
        sectie = Sectie(oude_sectie.titel, heading_offset=oude_sectie.heading_offset, id=f"sectie-{sectie_index}")
        document.sections.append(sectie)
        for paragraaf_index, paragraaf in enumerate(oude_sectie.inhoud):
            document.registreer_element(
                sectie,
                Paragraaf(
                    paragraaf.content,
                    id=f"s{sectie_index}-p{paragraaf_index}",
                    leesvolgorde=len(document.elementen),
                    rol=str(paragraaf.role or "text"),
                ),
            )
        for tabel_index, tabel in enumerate(oude_sectie.tabellen):
            document.registreer_element(
                sectie,
                DocumentTabel(
                    tabel.row_count,
                    tabel.column_count,
                    cells=tuple(
                        TabelCel(
                            cel.content,
                            cel.row_index,
                            cel.column_index,
                            row_span=cel.row_span or 1,
                            column_span=cel.column_span or 1,
                        )
                        for cel in tabel.cells
                    ),
                    id=f"s{sectie_index}-t{tabel_index}",
                    leesvolgorde=len(document.elementen),
                    herkomst="historische_fixture",
                ),
            )
    return document


def sanitize_smart_document(smart_doc: SmartDocument) -> SmartDocument:
    """Behoud relevante secties en hun canonieke registratie in een onafhankelijke kopie.

    Parameters
    ----------
    smart_doc : SmartDocument
        Nieuw lokaal geextraheerd document.

    Returns
    -------
    SmartDocument
        Document zonder analyseobject en zonder ongerelateerde sectie-inhoud.
    """
    document = deepcopy(smart_doc)
    behouden = set()
    for index, sectie in enumerate(document.sections):
        if "meettabel" in sectie.titel.lower() and sectie.tabellen:
            behouden.add(index)
        if "Constructie" in sectie.titel:
            behouden.update(range(index, min(index + 4, len(document.sections))))
    document.sections = [sectie for index, sectie in enumerate(document.sections) if index in behouden]
    sectie_ids = {sectie.id for sectie in document.sections}
    element_ids = {element_id for sectie in document.sections for element_id in sectie.element_ids}
    document.elementen = {
        element_id: element for element_id, element in document.elementen.items() if element_id in element_ids
    }
    for sectie in document.sections:
        sectie._elementen = document.elementen
        if sectie.ouder_id not in sectie_ids:
            sectie.ouder_id = None
    document.analyze_result = None
    return document


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--migreer-historisch", action="store_true", help="Behoud de historische referentiewaarden.")
    parser.add_argument("--overschrijven", action="store_true", help="Overschrijf uitsluitend de eigen documentfixture.")
    opties = parser.parse_args()
    doel_pad = KZG_0202_TEST_DIR / KZG_0202_PKL_NAME
    if doel_pad.exists() and not opties.overschrijven:
        parser.error("De eigen documentfixture bestaat al; gebruik alleen bewust --overschrijven.")
    if opties.migreer_historisch:
        document = migreer_historische_fixture(
            KZG_0202_TEST_DIR / f"{KZG_0202_DOC_NAME}_smart_document_sanitized.pkl"
        )
    else:
        document = sanitize_smart_document(
            SmartDocument.from_pdf(constants.DUIKRAPPORTEN_DIR / f"{KZG_0202_DOC_NAME}.pdf")
        )
    doel_pad.write_bytes(pickle.dumps(document))
    print(f"Eigen documentfixture geschreven: {doel_pad.name}; {len(document.elementen)} elementen.")
