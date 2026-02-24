"""
Module to test methods related to Paal model.
"""

from tekstherkenning_ark.enums import NietBeschikbaar, SchoorStand
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.rakdeel import Rakdeel
from azure.ai.documentintelligence.models import DocumentTable


def test_get_palen_from_doc_tables_dict_dimensions(paal_tables: DocumentTable):
    """check type and dimensions"""
    palen_dict = Paal.from_doc_tables(paal_tables)
    assert isinstance(palen_dict, dict)
    assert len(palen_dict) == 10


def test_get_palen_from_doc_tables_no_onverwacht_resultaat(paal_tables: DocumentTable):
    """check no onverwacht resultaat in parsed palen"""

    palen_dict = Paal.from_doc_tables(paal_tables)

    total_onverwacht = 0
    for palen in palen_dict.values():
        for paal in palen:
            total_onverwacht += len(paal.onverwachte_resultaten)
    assert (
        len(paal.onverwachte_resultaten) == 0
    ), f"Er zijn (onverwacht !) onverwachte resultaten gevonden in de palen: {total_onverwacht}"


def test_paalrij_nummer(mock_palen: list[Paal]):
    expected_paal_nummers = ["P1.1", "P1.2", "P2.2", "P1.3"]
    expected_paalrij_nummers = [1, 1, 2, 1]

    for paal, expected_nummer, expected_rij in zip(mock_palen, expected_paal_nummers, expected_paalrij_nummers):
        assert paal.paal_nummer == expected_nummer
        assert paal.paalrij_nummer == expected_rij


def test_paal_nummer_main(mock_palen: list[Paal]):
    expected_paal_nummers = ["P1.1", "P1.2", "P2.2", "P1.3"]
    expected_paal_nummer_mains = [1, 2, 2, 3]

    for paal, expected_nummer, expected_nummer_main in zip(
        mock_palen, expected_paal_nummers, expected_paal_nummer_mains
    ):
        assert paal.paal_nummer == expected_nummer
        assert paal.paal_nummer_main == expected_nummer_main


def test_n_scheuren(mock_rakdeel_with_scheuren: Rakdeel):
    """Test the property n_scheuren"""

    palen = mock_rakdeel_with_scheuren.onderbouw.palen

    expected_scheuren_counts = [2, 1, 1, 0, 0, 0, 1, 0]

    scheuren_count = [paal.n_scheuren for paal in palen]

    assert scheuren_count == expected_scheuren_counts


def test_paal_is_ongewenste_schoorstand_neutraal(mock_palen: list[Paal]):
    paal = mock_palen[0]
    paal.schoor_richting = SchoorStand.NEUTRAAL
    assert paal.is_ongewenste_schoorstand == False


def test_paal_is_ongewenste_schoorstand_pna(mock_palen: list[Paal]):
    paal = mock_palen[0]
    paal.schoor_richting = SchoorStand.NEGATIEF
    assert paal.is_ongewenste_schoorstand == True


def test_paal_is_ongewenste_schoorstand_niet_beschikbaar(mock_palen: list[Paal]):
    paal = mock_palen[0]
    paal.schoor_richting = NietBeschikbaar.NIET_VAN_TOEPASSING
    assert paal.is_ongewenste_schoorstand is None
