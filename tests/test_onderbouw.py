from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat, OnverwachtResultaatType
from tekstherkenning_ark.enums import AansluitingStatus


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


def test_get_next_paal_normal_case(mock_rakdeel: Rakdeel):
    """Test dat get_next_paal de volgende paal in de reeks correct teruggeeft."""
    onderbouw = mock_rakdeel.onderbouw

    # Test P1.1 -> P1.2
    p1_1 = onderbouw.palen[0]  # P1.1
    next_paal = onderbouw.get_next_paal(p1_1)

    assert isinstance(next_paal, Paal)
    assert next_paal.paal_nummer == "P1.2"

    # Test P1.2 -> P1.3 (volgens mock data verwijst P1.3 naar P1.2)
    next_paal = onderbouw.get_next_paal(next_paal)

    assert isinstance(next_paal, Paal)
    assert next_paal.paal_nummer == "P1.3"


def test_get_next_paal_no_next_paal(mock_rakdeel: Rakdeel):
    """Test dat get_next_paal None teruggeeft als er geen volgende paal is."""
    onderbouw = mock_rakdeel.onderbouw

    # P1.3 heeft geen volgende paal in de mock data
    p1_3 = next(paal for paal in onderbouw.palen if paal.paal_nummer == "P1.3")
    next_paal = onderbouw.get_next_paal(p1_3)

    assert next_paal is None


def test_get_next_paal_multiple_references_error(mock_rakdeel: Rakdeel):
    """Test dat get_next_paal een OnverwachtResultaat teruggeeft bij meerdere verwijzingen naar dezelfde paal."""
    onderbouw = mock_rakdeel.onderbouw

    # Creëer een nieuwe paal die ook verwijst naar P1.2 (naast P1.3 die al naar P1.2 verwijst in mock data)
    duplicate_paal = Paal(
        paal_nummer="P1.4",
        hoh_paalnummer="P1.2",  # Dupliceert de verwijzing
        diameter_haaks=150,
        diameter_parallel=150,
        diameter_gemiddeld=150,
        hoh_afstand_cm=100,
        schoor_graden=5,
        schoor_richting="PNV",
        afstand_frontwand_cm=25,
        is_scheefstand=False,
        is_paalbreuk=False,
        is_aantasting=False,
        aansluiting_status=AansluitingStatus.GOED,
        positionering_aansluiting_cm="0",
    )
    onderbouw.palen.append(duplicate_paal)

    p1_2 = next(paal for paal in onderbouw.palen if paal.paal_nummer == "P1.2")
    result = onderbouw.get_next_paal(p1_2)

    assert isinstance(result, OnverwachtResultaat)
    assert result.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    assert "Meerdere palen verwijzen naar hetzelfde hoh_paalnummer" in result.details


def test_get_consecutive_palen_normal_case(mock_rakdeel: Rakdeel):
    """Test dat get_consecutive_palen de palen in de juiste volgorde teruggeeft."""
    onderbouw = mock_rakdeel.onderbouw

    result = onderbouw.get_consecutive_palen()

    assert isinstance(result, list)
    assert len(result) == len(onderbouw.eerste_rij_palen)

    # Controleer de volgorde: P1.1 -> P1.2 -> P1.3
    assert result[0].paal_nummer == "P1.1"
    assert result[1].paal_nummer == "P1.2"
    assert result[2].paal_nummer == "P1.3"


def test_get_consecutive_palen_empty_eerste_rij(mock_rakdeel: Rakdeel):
    """Test dat get_consecutive_palen een lege lijst teruggeeft als er geen eerste rij palen zijn."""
    onderbouw = mock_rakdeel.onderbouw

    # Verwijder alle eerste rij palen
    onderbouw.palen = [paal for paal in onderbouw.palen if paal.paalrij_nummer != 1]

    result = onderbouw.get_consecutive_palen()

    assert isinstance(result, list)
    assert len(result) == 0


def test_get_consecutive_palen_cyclical_reference_error(mock_rakdeel: Rakdeel):
    """Test dat get_consecutive_palen een OnverwachtResultaat teruggeeft bij cyclische verwijzingen."""
    onderbouw = mock_rakdeel.onderbouw

    # Create a circular reference by setting hoh_paalnummer to create a loop
    mock_rakdeel.onderbouw.palen[0].hoh_paalnummer = "P1.3"

    result = onderbouw.get_consecutive_palen()

    assert isinstance(result, OnverwachtResultaat)
    assert result.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    assert "Cyclische paalreferenties gedetecteerd" in result.details


def test_get_consecutive_palen_incomplete_chain_error(mock_rakdeel: Rakdeel):
    """Test dat get_consecutive_palen een OnverwachtResultaat teruggeeft bij onvolledige verwerking."""
    onderbouw = mock_rakdeel.onderbouw

    # Voeg een extra eerste rij paal toe die niet in de keten zit
    extra_paal = Paal(
        paal_nummer="P1.4",
        hoh_paalnummer="",  # Geen verwijzing - orphaned paal
        diameter_haaks=150,
        diameter_parallel=150,
        diameter_gemiddeld=150,
        hoh_afstand_cm=100,
        schoor_graden=5,
        schoor_richting="PNV",
        afstand_frontwand_cm=25,
        is_scheefstand=False,
        is_paalbreuk=False,
        is_aantasting=False,
        aansluiting_status=AansluitingStatus.GOED,
        positionering_aansluiting_cm="0",
    )
    onderbouw.palen.append(extra_paal)

    result = onderbouw.get_consecutive_palen()

    assert isinstance(result, OnverwachtResultaat)
    assert result.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    assert "Onvolledige verwerking van palen" in result.details


def test_get_consecutive_palen_propagates_get_next_paal_error(mock_rakdeel: Rakdeel):
    """Test dat get_consecutive_palen errors van get_next_paal correct doorgeeft."""
    onderbouw = mock_rakdeel.onderbouw

    # Creëer situatie waarbij get_next_paal een error geeft (meerdere verwijzingen)
    duplicate_paal = Paal(
        paal_nummer="P1.4",
        hoh_paalnummer="P1.2",  # Dupliceert verwijzing naar P1.2
        diameter_haaks=150,
        diameter_parallel=150,
        diameter_gemiddeld=150,
        hoh_afstand_cm=100,
        schoor_graden=5,
        schoor_richting="PNV",
        afstand_frontwand_cm=25,
        is_scheefstand=False,
        is_paalbreuk=False,
        is_aantasting=False,
        aansluiting_status=AansluitingStatus.GOED,
        positionering_aansluiting_cm="0",
    )
    onderbouw.palen.append(duplicate_paal)

    result = onderbouw.get_consecutive_palen()

    assert isinstance(result, OnverwachtResultaat)
    assert result.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    assert "Meerdere palen verwijzen naar hetzelfde hoh_paalnummer" in result.details
