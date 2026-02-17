from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.rakdeel import Rakdeel


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
