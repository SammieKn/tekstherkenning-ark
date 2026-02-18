from tekstherkenning_ark.models.rakdeel import Rakdeel


def test_eerste_rij_palen(mock_rakdeel: Rakdeel):
    """Test dat de eerste rij palen correct wordt geïdentificeerd en gesorteerd."""

    eerste_rij_palen = mock_rakdeel.onderbouw.eerste_rij_palen

    assert len(eerste_rij_palen) == 3
    assert eerste_rij_palen[0].paal_nummer == "P1.1"
    assert eerste_rij_palen[1].paal_nummer == "P1.2"
    assert eerste_rij_palen[2].paal_nummer == "P1.3"


def test_eerste_rij_palen_wrong_order(mock_rakdeel: Rakdeel):
    """Test dat de eerste rij palen correct wordt geïdentificeerd en gesorteerd."""

    # Change the order of palen
    mock_rakdeel.onderbouw.palen = [
        mock_rakdeel.onderbouw.palen[1],
        mock_rakdeel.onderbouw.palen[0],
        mock_rakdeel.onderbouw.palen[3],
        mock_rakdeel.onderbouw.palen[2],
    ]

    eerste_rij_palen = mock_rakdeel.onderbouw.eerste_rij_palen

    assert len(eerste_rij_palen) == 3
    assert eerste_rij_palen[0].paal_nummer == "P1.1"
    assert eerste_rij_palen[1].paal_nummer == "P1.2"
    assert eerste_rij_palen[2].paal_nummer == "P1.3"


def test_eerste_rij_palen_missing(mock_rakdeel: Rakdeel):
    """Test dat de eerste rij palen correct wordt geïdentificeerd en gesorteerd, ook als er een paal ontbreekt."""

    # Remove one of the palen from the first rij
    mock_rakdeel.onderbouw.palen = [paal for paal in mock_rakdeel.onderbouw.palen if paal.paal_nummer != "P1.2"]

    eerste_rij_palen = mock_rakdeel.onderbouw.eerste_rij_palen

    assert len(eerste_rij_palen) == 2
    assert eerste_rij_palen[0].paal_nummer == "P1.1"
    assert eerste_rij_palen[1].paal_nummer == "P1.3"
