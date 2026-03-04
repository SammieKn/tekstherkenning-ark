from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat, OnverwachtResultaatType
from tekstherkenning_ark.enums import AansluitingStatus, SchoorStand, NietBeschikbaar


def test_percentage_ongewenste_schoorstand_geen(mock_rakdeel: Rakdeel):
    """Test dat percentage_ongewenste_schoorstand 0% geeft als geen enkele paal PNA heeft."""
    # Alle mock palen hebben schoor_richting="PNV" (geen ongewenste schoorstand)
    assert mock_rakdeel.onderbouw.percentage_ongewenste_schoorstand == 0.0


def test_aantal_palen_dwars(mock_rakdeel: Rakdeel):
    """Test dat aantal_palen_dwars de hoogste paalrij in de onderbouw teruggeeft."""
    onderbouw = mock_rakdeel.onderbouw

    assert onderbouw.aantal_palen_dwars == 2


def test_aantal_palen_dwars_geen_palen(mock_rakdeel: Rakdeel):
    """Test dat aantal_palen_dwars 0 is als er geen palen zijn."""
    mock_rakdeel.onderbouw.palen = []

    assert mock_rakdeel.onderbouw.aantal_palen_dwars == 0


def test_percentage_ongewenste_schoorstand_een_paal(mock_rakdeel: Rakdeel):
    """Test dat percentage_ongewenste_schoorstand correct berekent als één eerste-rij paal PNA heeft."""
    onderbouw = mock_rakdeel.onderbouw

    # Zet P1.1 (eerste rij) op ongewenste schoorstand
    p1_1 = next(paal for paal in onderbouw.palen if paal.paal_nummer == "P1.1")
    p1_1.schoor_richting = SchoorStand.NEGATIEF

    # 1 van 4 palen = 25.0%
    assert onderbouw.percentage_ongewenste_schoorstand == 25.0


def test_percentage_ongewenste_schoorstand_alle_eerste_rij(mock_rakdeel: Rakdeel):
    """Test dat percentage_ongewenste_schoorstand correct berekent als alle eerste-rij palen PNA hebben."""
    onderbouw = mock_rakdeel.onderbouw

    # Zet alle eerste-rij palen (P1.1, P1.2, P1.3) op ongewenste schoorstand
    for paal in onderbouw.palen:
        if paal.paalrij_nummer == 1:
            paal.schoor_richting = SchoorStand.NEGATIEF

    # 3 van 4 palen = 75.0%
    assert onderbouw.percentage_ongewenste_schoorstand == 75.0


def test_percentage_ongewenste_schoorstand_tweede_rij_telt_niet_mee(mock_rakdeel: Rakdeel):
    """Test dat palen buiten de eerste rij niet meetellen bij ongewenste schoorstand."""
    onderbouw = mock_rakdeel.onderbouw

    # Zet alleen P2.2 (tweede rij) op ongewenste schoorstand
    p2_2 = next(paal for paal in onderbouw.palen if paal.paal_nummer == "P2.2")
    p2_2.schoor_richting = SchoorStand.NEGATIEF

    # Tweede-rij palen tellen niet mee → 0%
    assert onderbouw.percentage_ongewenste_schoorstand == 0.0


def test_percentage_ongewenste_schoorstand_geen_palen(mock_rakdeel: Rakdeel):
    """Test dat percentage_ongewenste_schoorstand None geeft als er geen palen zijn."""
    mock_rakdeel.onderbouw.palen = []

    assert mock_rakdeel.onderbouw.percentage_ongewenste_schoorstand is None


def test_get_eerste_paal_met_aansluitende_statussen_vindt_vijfde_paal(mock_rakdeel: Rakdeel, maak_paal_rij_1):
    """Test dat de helper de paal retourneert waarop de aaneengesloten reeks van vijf wordt bereikt."""
    onderbouw = mock_rakdeel.onderbouw

    extra_palen = [
        maak_paal_rij_1("P1.4", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.5", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.6", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.7", AansluitingStatus.SLECHT),
    ]
    onderbouw.palen.extend(extra_palen)

    for paal_nummer in ["P1.1", "P1.2", "P1.3"]:
        leading_paal = next(p for p in onderbouw.palen if p.paal_nummer == paal_nummer)
        leading_paal.aansluiting_status = AansluitingStatus.SLECHT

    resultaat = onderbouw.get_eerste_paal_met_aansluitende_statussen((AansluitingStatus.SLECHT,))

    assert isinstance(resultaat, Paal)
    assert resultaat.paal_nummer == "P1.5"


def test_get_eerste_paal_met_aansluitende_statussen_none_bij_onderbroken_reeks(mock_rakdeel: Rakdeel, maak_paal_rij_1):
    """Test dat de helper None teruggeeft als er geen vijf aaneengesloten matchende statussen zijn."""
    onderbouw = mock_rakdeel.onderbouw

    extra_palen = [
        maak_paal_rij_1("P1.4", AansluitingStatus.GOED),
        maak_paal_rij_1("P1.5", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.6", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.7", AansluitingStatus.GOED),
        maak_paal_rij_1("P1.8", AansluitingStatus.SLECHT),
    ]
    onderbouw.palen.extend(extra_palen)

    for paal_nummer in ["P1.1", "P1.2", "P1.3"]:
        leading_paal = next(p for p in onderbouw.palen if p.paal_nummer == paal_nummer)
        leading_paal.aansluiting_status = AansluitingStatus.SLECHT

    resultaat = onderbouw.get_eerste_paal_met_aansluitende_statussen((AansluitingStatus.SLECHT,))

    assert resultaat is None


def test_get_eerste_paal_met_aansluitende_statussen_met_onverwacht_resultaat(mock_rakdeel: Rakdeel, maak_paal_rij_1):
    """Test dat OnverwachtResultaat meetelt als include_onverwacht_resultaat=True."""
    onderbouw = mock_rakdeel.onderbouw

    onverwacht = OnverwachtResultaat(
        waarde=None,
        onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
        details="Test onverwacht resultaat",
    )

    onderbouw.palen = [
        maak_paal_rij_1("P1.1", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.2", AansluitingStatus.NIET_MEETBAAR),
        maak_paal_rij_1("P1.3", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.4", onverwacht),
        maak_paal_rij_1("P1.5", AansluitingStatus.SLECHT),
    ]

    resultaat = onderbouw.get_eerste_paal_met_aansluitende_statussen(
        [AansluitingStatus.SLECHT, AansluitingStatus.NIET_MEETBAAR],
        include_onverwacht_resultaat=True,
    )

    assert isinstance(resultaat, Paal)
    assert resultaat.paal_nummer == "P1.5"


def test_is_vijf_aansluitende_slechte_paal_kesp_verbinding_in_rij_true(mock_rakdeel: Rakdeel, maak_paal_rij_1):
    """Test dat de property True is bij vijf aaneengesloten slechte aansluitingen."""
    onderbouw = mock_rakdeel.onderbouw

    onderbouw.palen = [
        maak_paal_rij_1("P1.1", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.2", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.3", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.4", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.5", AansluitingStatus.SLECHT),
    ]
    assert onderbouw.is_vijf_aansluitende_slechte_paal_kesp_verbinding_in_rij


def test_is_vijf_aansluitende_slechte_paal_kesp_verbinding_in_rij_onverwacht_resultaat(
    mock_rakdeel: Rakdeel,
    maak_paal_rij_1,
):
    """Test dat de property een OnverwachtResultaat teruggeeft bij reeks met NM/OnverwachtResultaat."""
    onderbouw = mock_rakdeel.onderbouw

    onverwacht = OnverwachtResultaat(
        waarde=None,
        onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
        details="Test onverwacht resultaat",
    )

    onderbouw.palen = [
        maak_paal_rij_1("P1.1", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.2", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.3", AansluitingStatus.NIET_MEETBAAR),
        maak_paal_rij_1("P1.4", onverwacht),
        maak_paal_rij_1("P1.5", AansluitingStatus.SLECHT),
    ]

    resultaat = onderbouw.is_vijf_aansluitende_slechte_paal_kesp_verbinding_in_rij

    assert isinstance(resultaat, OnverwachtResultaat)
    assert resultaat.waarde is True
    assert resultaat.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT


def test_is_vijf_aansluitende_slechte_paal_kesp_verbinding_in_rij_false_bij_niet_aaneengesloten(
    mock_rakdeel: Rakdeel,
    maak_paal_rij_1,
):
    """Test dat de property False is bij vijf slechte verbindingen die niet aaneengesloten zijn."""
    onderbouw = mock_rakdeel.onderbouw

    onderbouw.palen = [
        maak_paal_rij_1("P1.1", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.2", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.3", AansluitingStatus.GOED),
        maak_paal_rij_1("P1.4", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.5", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.6", AansluitingStatus.SLECHT),
    ]

    assert onderbouw.is_vijf_aansluitende_slechte_paal_kesp_verbinding_in_rij is False


def test_aantal_schoorpalen(mock_rakdeel: Rakdeel):
    """Test dat aantal_schoorpalen alleen PNV/PNA meetelt."""
    onderbouw = mock_rakdeel.onderbouw

    onderbouw.palen[0].schoor_richting = SchoorStand.POSITIEF
    onderbouw.palen[1].schoor_richting = SchoorStand.NEGATIEF
    onderbouw.palen[2].schoor_richting = SchoorStand.NEUTRAAL
    onderbouw.palen[3].schoor_richting = NietBeschikbaar.NIET_VAN_TOEPASSING

    assert onderbouw.aantal_schoorpalen == 2


def test_is_schoorpalen_in_een_richting_true(mock_rakdeel: Rakdeel):
    """Test dat is_schoorpalen_in_een_richting True is als alle schoorpalen dezelfde richting hebben."""
    onderbouw = mock_rakdeel.onderbouw

    for paal in onderbouw.palen:
        paal.schoor_richting = SchoorStand.POSITIEF

    assert onderbouw.is_schoorpalen_in_een_richting


def test_is_schoorpalen_in_een_richting_false(mock_rakdeel: Rakdeel):
    """Test dat is_schoorpalen_in_een_richting False is bij gemengde PNV/PNA richtingen."""
    onderbouw = mock_rakdeel.onderbouw

    onderbouw.palen[0].schoor_richting = SchoorStand.POSITIEF
    onderbouw.palen[1].schoor_richting = SchoorStand.NEGATIEF

    assert not onderbouw.is_schoorpalen_in_een_richting


def test_is_schoorpalen_in_een_richting_niet_van_toepassing(mock_rakdeel: Rakdeel):
    """Test dat is_schoorpalen_in_een_richting NVT teruggeeft als er geen schoorpalen zijn."""
    onderbouw = mock_rakdeel.onderbouw

    for paal in onderbouw.palen:
        paal.schoor_richting = SchoorStand.NEUTRAAL

    assert onderbouw.is_schoorpalen_in_een_richting is NietBeschikbaar.NIET_VAN_TOEPASSING


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


def test_get_consecutive_palen_no_hoh_afstand_cm(mock_rakdeel: Rakdeel):
    """Test dat get_consecutive_palen een OnverwachtResultaat teruggeeft als een paal geen hoh_afstand_cm heeft."""
    onderbouw = mock_rakdeel.onderbouw

    # Verwijder hoh_afstand_cm van een paal
    onderbouw.palen[1].hoh_afstand_cm = None

    result = onderbouw.get_consecutive_palen()

    assert isinstance(result, OnverwachtResultaat)
    assert result.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    assert "Ontbrekende hoh_afstand_cm voor paal" in result.details
