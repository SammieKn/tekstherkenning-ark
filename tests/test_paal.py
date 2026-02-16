from tekstherkenning_ark.models.paal import Paal


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
