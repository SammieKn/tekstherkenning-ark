from tekstherkenning_ark.models.onderbouw import Onderbouw
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat, OnverwachtResultaatType
from tekstherkenning_ark.enums import AansluitingStatus, SchoorStand, NietBeschikbaar


def test_percentage_ongewenste_schoorstand_geen(mock_onderbouw: Onderbouw):
    """Test dat percentage_ongewenste_schoorstand 0% geeft als geen enkele paal PNA heeft."""
    # Alle mock palen hebben schoor_richting="PNV" (geen ongewenste schoorstand)
    assert mock_onderbouw.percentage_ongewenste_schoorstand == 0.0


def test_aantal_palen_dwars(mock_onderbouw: Onderbouw):
    """Test dat aantal_palen_dwars de hoogste paalrij in de onderbouw teruggeeft."""
    assert mock_onderbouw.aantal_palen_dwars == 2


def test_aantal_palen_dwars_geen_palen(mock_onderbouw: Onderbouw):
    """Test dat aantal_palen_dwars 0 is als er geen palen zijn."""
    mock_onderbouw.palen = []

    assert mock_onderbouw.aantal_palen_dwars == 0


def test_percentage_ongewenste_schoorstand_een_paal(mock_onderbouw: Onderbouw):
    """Test dat percentage_ongewenste_schoorstand correct berekent als één eerste-rij paal PNA heeft."""
    # Zet P1.1 (eerste rij) op ongewenste schoorstand
    p1_1 = next(paal for paal in mock_onderbouw.palen if paal.paal_nummer == "P1.1")
    p1_1.schoor_richting = SchoorStand.NEGATIEF

    # 1 van 4 palen = 25.0%
    assert mock_onderbouw.percentage_ongewenste_schoorstand == 25.0


def test_percentage_ongewenste_schoorstand_alle_eerste_rij(mock_onderbouw: Onderbouw):
    """Test dat percentage_ongewenste_schoorstand correct berekent als alle eerste-rij palen PNA hebben."""
    # Zet alle eerste-rij palen (P1.1, P1.2, P1.3) op ongewenste schoorstand
    for paal in mock_onderbouw.palen:
        if paal.paal_nummer_main == 1:
            paal.schoor_richting = SchoorStand.NEGATIEF

    # 3 van 4 palen = 75.0%
    assert mock_onderbouw.percentage_ongewenste_schoorstand == 75.0


def test_percentage_ongewenste_schoorstand_tweede_rij_telt_niet_mee(mock_onderbouw: Onderbouw):
    """Test dat palen buiten de eerste rij niet meetellen bij ongewenste schoorstand."""
    # Zet alleen P2.2 (tweede rij) op ongewenste schoorstand
    p2_2 = next(paal for paal in mock_onderbouw.palen if paal.paal_nummer == "P2.2")
    p2_2.schoor_richting = SchoorStand.NEGATIEF

    # Tweede-rij palen tellen niet mee → 0%
    assert mock_onderbouw.percentage_ongewenste_schoorstand == 0.0


def test_percentage_ongewenste_schoorstand_geen_palen(mock_onderbouw: Onderbouw):
    """Test dat percentage_ongewenste_schoorstand None geeft als er geen palen zijn."""
    mock_onderbouw.palen = []

    assert mock_onderbouw.percentage_ongewenste_schoorstand is None


def test_get_eerste_paal_met_aansluitende_statussen_vindt_vijfde_paal(mock_onderbouw: Onderbouw, maak_paal_rij_1):
    """Test dat de helper de paal retourneert waarop de aaneengesloten reeks van vijf wordt bereikt."""
    extra_palen = [
        maak_paal_rij_1("P1.4", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.5", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.6", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.7", AansluitingStatus.SLECHT),
    ]
    mock_onderbouw.palen.extend(extra_palen)

    for paal_nummer in ["P1.1", "P1.2", "P1.3"]:
        leading_paal = next(p for p in mock_onderbouw.palen if p.paal_nummer == paal_nummer)
        leading_paal.aansluiting_status = AansluitingStatus.SLECHT

    resultaat = mock_onderbouw.get_eerste_paal_met_aansluitende_statussen((AansluitingStatus.SLECHT,))

    assert isinstance(resultaat, Paal)
    assert resultaat.paal_nummer == "P1.5"


def test_get_eerste_paal_met_aansluitende_statussen_none_bij_onderbroken_reeks(
    mock_onderbouw: Onderbouw, maak_paal_rij_1
):
    """Test dat de helper None teruggeeft als er geen vijf aaneengesloten matchende statussen zijn."""
    extra_palen = [
        maak_paal_rij_1("P1.4", AansluitingStatus.GOED),
        maak_paal_rij_1("P1.5", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.6", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.7", AansluitingStatus.GOED),
        maak_paal_rij_1("P1.8", AansluitingStatus.SLECHT),
    ]
    mock_onderbouw.palen.extend(extra_palen)

    for paal_nummer in ["P1.1", "P1.2", "P1.3"]:
        leading_paal = next(p for p in mock_onderbouw.palen if p.paal_nummer == paal_nummer)
        leading_paal.aansluiting_status = AansluitingStatus.SLECHT

    resultaat = mock_onderbouw.get_eerste_paal_met_aansluitende_statussen((AansluitingStatus.SLECHT,))

    assert resultaat is None


def test_get_eerste_paal_met_aansluitende_statussen_met_onverwacht_resultaat(
    mock_onderbouw: Onderbouw, maak_paal_rij_1
):
    """Test dat OnverwachtResultaat meetelt als include_onverwacht_resultaat=True."""
    onverwacht = OnverwachtResultaat(
        waarde=None,
        onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
        details="Test onverwacht resultaat",
    )

    mock_onderbouw.palen = [
        maak_paal_rij_1("P1.1", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.2", AansluitingStatus.NIET_MEETBAAR),
        maak_paal_rij_1("P1.3", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.4", onverwacht),
        maak_paal_rij_1("P1.5", AansluitingStatus.SLECHT),
    ]

    resultaat = mock_onderbouw.get_eerste_paal_met_aansluitende_statussen(
        [AansluitingStatus.SLECHT, AansluitingStatus.NIET_MEETBAAR],
        include_onverwacht_resultaat=True,
    )

    assert isinstance(resultaat, Paal)
    assert resultaat.paal_nummer == "P1.5"


def test_is_vijf_aansluitende_slechte_paal_kesp_verbinding_in_rij_true(mock_onderbouw: Onderbouw, maak_paal_rij_1):
    """Test dat de property True is bij vijf aaneengesloten slechte aansluitingen."""
    mock_onderbouw.palen = [
        maak_paal_rij_1("P1.1", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.2", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.3", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.4", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.5", AansluitingStatus.SLECHT),
    ]
    assert mock_onderbouw.is_vijf_aansluitende_slechte_paal_kesp_verbinding_in_rij


def test_is_vijf_aansluitende_slechte_paal_kesp_verbinding_in_rij_onverwacht_resultaat(
    mock_onderbouw: Onderbouw,
    maak_paal_rij_1,
):
    """Test dat de property een OnverwachtResultaat teruggeeft bij reeks met NM/OnverwachtResultaat."""
    onverwacht = OnverwachtResultaat(
        waarde=None,
        onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
        details="Test onverwacht resultaat",
    )

    mock_onderbouw.palen = [
        maak_paal_rij_1("P1.1", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.2", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.3", AansluitingStatus.NIET_MEETBAAR),
        maak_paal_rij_1("P1.4", onverwacht),
        maak_paal_rij_1("P1.5", AansluitingStatus.SLECHT),
    ]

    resultaat = mock_onderbouw.is_vijf_aansluitende_slechte_paal_kesp_verbinding_in_rij

    assert isinstance(resultaat, OnverwachtResultaat)
    assert resultaat.waarde is True
    assert resultaat.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT


def test_is_vijf_aansluitende_slechte_paal_kesp_verbinding_in_rij_false_bij_niet_aaneengesloten(
    mock_onderbouw: Onderbouw,
    maak_paal_rij_1,
):
    """Test dat de property False is bij vijf slechte verbindingen die niet aaneengesloten zijn."""
    mock_onderbouw.palen = [
        maak_paal_rij_1("P1.1", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.2", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.3", AansluitingStatus.GOED),
        maak_paal_rij_1("P1.4", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.5", AansluitingStatus.SLECHT),
        maak_paal_rij_1("P1.6", AansluitingStatus.SLECHT),
    ]

    assert mock_onderbouw.is_vijf_aansluitende_slechte_paal_kesp_verbinding_in_rij is False


def test_aantal_schoorpalen(mock_onderbouw: Onderbouw):
    """Test dat aantal_schoorpalen alleen PNV/PNA meetelt."""
    mock_onderbouw.palen[0].schoor_richting = SchoorStand.POSITIEF
    mock_onderbouw.palen[1].schoor_richting = SchoorStand.NEGATIEF
    mock_onderbouw.palen[2].schoor_richting = SchoorStand.NEUTRAAL
    mock_onderbouw.palen[3].schoor_richting = NietBeschikbaar.NIET_VAN_TOEPASSING

    assert mock_onderbouw.aantal_schoorpalen == 2


def test_is_schoorpalen_in_een_richting_true(mock_onderbouw: Onderbouw):
    """Test dat is_schoorpalen_in_een_richting True is als alle schoorpalen dezelfde richting hebben."""
    for paal in mock_onderbouw.palen:
        paal.schoor_richting = SchoorStand.POSITIEF

    assert mock_onderbouw.is_schoorpalen_in_een_richting


def test_is_schoorpalen_in_een_richting_false(mock_onderbouw: Onderbouw):
    """Test dat is_schoorpalen_in_een_richting False is bij gemengde PNV/PNA richtingen."""
    mock_onderbouw.palen[0].schoor_richting = SchoorStand.POSITIEF
    mock_onderbouw.palen[1].schoor_richting = SchoorStand.NEGATIEF

    assert not mock_onderbouw.is_schoorpalen_in_een_richting


def test_is_schoorpalen_in_een_richting_niet_van_toepassing(mock_onderbouw: Onderbouw):
    """Test dat is_schoorpalen_in_een_richting NVT teruggeeft als er geen schoorpalen zijn."""
    for paal in mock_onderbouw.palen:
        paal.schoor_richting = SchoorStand.NEUTRAAL

    assert mock_onderbouw.is_schoorpalen_in_een_richting is NietBeschikbaar.NIET_VAN_TOEPASSING


def test_eerste_rij_palen(mock_onderbouw: Onderbouw):
    """Test dat de eerste rij palen correct wordt geïdentificeerd en gesorteerd."""
    eerste_rij_palen = mock_onderbouw.p1_palen

    assert len(eerste_rij_palen) == 3
    assert eerste_rij_palen[0].paal_nummer == "P1.1"
    assert eerste_rij_palen[1].paal_nummer == "P1.2"
    assert eerste_rij_palen[2].paal_nummer == "P1.3"


def test_p1_palen_wrong_order(mock_onderbouw: Onderbouw):
    """Test dat de eerste rij palen correct wordt geïdentificeerd en gesorteerd."""
    # Change the order of palen
    mock_onderbouw.palen = [
        mock_onderbouw.palen[1],
        mock_onderbouw.palen[0],
        mock_onderbouw.palen[3],
        mock_onderbouw.palen[2],
    ]

    eerste_rij_palen = mock_onderbouw.p1_palen

    assert len(eerste_rij_palen) == 3
    assert eerste_rij_palen[0].paal_nummer == "P1.1"
    assert eerste_rij_palen[1].paal_nummer == "P1.2"
    assert eerste_rij_palen[2].paal_nummer == "P1.3"


def test_eerste_rij_palen_missing(mock_onderbouw: Onderbouw):
    """Test dat de eerste rij palen correct wordt geïdentificeerd en gesorteerd, ook als er een paal ontbreekt."""
    # Remove one of the palen from the first rij
    mock_onderbouw.palen = [paal for paal in mock_onderbouw.palen if paal.paal_nummer != "P1.2"]

    eerste_rij_palen = mock_onderbouw.p1_palen

    assert len(eerste_rij_palen) == 2
    assert eerste_rij_palen[0].paal_nummer == "P1.1"
    assert eerste_rij_palen[1].paal_nummer == "P1.3"


def test_get_next_paal_normal_case(mock_onderbouw: Onderbouw):
    """Test dat get_next_paal de volgende paal in de reeks correct teruggeeft."""
    # Test P1.1 -> P1.2
    p1_1 = mock_onderbouw.palen[0]  # P1.1
    next_paal = mock_onderbouw.get_next_paal(p1_1)

    assert isinstance(next_paal, Paal)
    assert next_paal.paal_nummer == "P1.2"

    # Test P1.2 -> P1.3 (volgens mock data verwijst P1.3 naar P1.2)
    next_paal = mock_onderbouw.get_next_paal(next_paal)

    assert isinstance(next_paal, Paal)
    assert next_paal.paal_nummer == "P1.3"


def test_get_next_paal_no_next_paal(mock_onderbouw: Onderbouw):
    """Test dat get_next_paal None teruggeeft als er geen volgende paal is."""
    # P1.3 heeft geen volgende paal in de mock data
    p1_3 = next(paal for paal in mock_onderbouw.palen if paal.paal_nummer == "P1.3")
    next_paal = mock_onderbouw.get_next_paal(p1_3)

    assert next_paal is None


def test_get_next_paal_multiple_references_error(mock_onderbouw: Onderbouw):
    """Test dat get_next_paal een OnverwachtResultaat teruggeeft bij meerdere verwijzingen naar dezelfde paal."""
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
    mock_onderbouw.palen.append(duplicate_paal)

    p1_2 = next(paal for paal in mock_onderbouw.palen if paal.paal_nummer == "P1.2")
    result = mock_onderbouw.get_next_paal(p1_2)

    assert isinstance(result, OnverwachtResultaat)
    assert result.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    assert "Meerdere palen verwijzen naar hetzelfde hoh_paalnummer" in result.details


def test_get_consecutive_palen_normal_case(mock_onderbouw: Onderbouw):
    """Test dat get_consecutive_palen de palen in de juiste volgorde teruggeeft."""
    result = mock_onderbouw.get_consecutive_palen()

    assert isinstance(result, list)
    assert len(result) == len(mock_onderbouw.p1_palen)

    # Controleer de volgorde: P1.1 -> P1.2 -> P1.3
    assert result[0].paal_nummer == "P1.1"
    assert result[1].paal_nummer == "P1.2"
    assert result[2].paal_nummer == "P1.3"


def test_get_consecutive_palen_empty_eerste_rij(mock_onderbouw: Onderbouw):
    """Test dat get_consecutive_palen een lege lijst teruggeeft als er geen eerste rij palen zijn."""
    # Verwijder alle eerste rij palen
    mock_onderbouw.palen = [paal for paal in mock_onderbouw.palen if paal.paal_nummer_main != 1]

    result = mock_onderbouw.get_consecutive_palen()

    assert isinstance(result, list)
    assert len(result) == 0


def test_get_consecutive_palen_cyclical_reference_error(mock_onderbouw: Onderbouw):
    """Test dat get_consecutive_palen een OnverwachtResultaat teruggeeft bij cyclische verwijzingen."""
    # Create a circular reference by setting hoh_paalnummer to create a loop
    mock_onderbouw.palen[0].hoh_paalnummer = "P1.3"

    result = mock_onderbouw.get_consecutive_palen()

    assert isinstance(result, OnverwachtResultaat)
    assert result.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    assert "Cyclische paalreferenties gedetecteerd" in result.details


def test_get_consecutive_palen_incomplete_chain_error(mock_onderbouw: Onderbouw):
    """Test dat get_consecutive_palen een OnverwachtResultaat teruggeeft bij onvolledige verwerking."""
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
    mock_onderbouw.palen.append(extra_paal)

    result = mock_onderbouw.get_consecutive_palen()

    assert isinstance(result, OnverwachtResultaat)
    assert result.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT


def test_get_consecutive_palen_propagates_get_next_paal_error(mock_onderbouw: Onderbouw):
    """Test dat get_consecutive_palen errors van get_next_paal correct doorgeeft."""
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
    mock_onderbouw.palen.append(duplicate_paal)

    result = mock_onderbouw.get_consecutive_palen()

    assert isinstance(result, OnverwachtResultaat)
    assert result.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    assert "Meerdere palen verwijzen naar hetzelfde hoh_paalnummer" in result.details


def test_get_consecutive_palen_no_hoh_afstand_cm(mock_onderbouw: Onderbouw):
    """Test dat get_consecutive_palen een OnverwachtResultaat teruggeeft als een paal geen hoh_afstand_cm heeft."""
    # Verwijder hoh_afstand_cm van een paal
    mock_onderbouw.palen[1].hoh_afstand_cm = None

    result = mock_onderbouw.get_consecutive_palen()

    assert isinstance(result, OnverwachtResultaat)
    assert result.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    assert "Ontbrekende hoh_afstand_cm voor paal" in result.details


def test_aantal_paalrijen(mock_onderbouw: Onderbouw):
    """Test dat aantal_paalrijen het aantal unieke paalrijen teruggeeft."""
    # Mock data heeft palen in rij 1 (P1.1, P1.2, P1.3) en rij 2 (P2.2)
    assert mock_onderbouw.aantal_paalrijen == 3


def test_aantal_paalrijen_geen_palen(mock_onderbouw: Onderbouw):
    """Test dat aantal_paalrijen 0 is als er geen palen zijn."""
    mock_onderbouw.palen = []

    assert mock_onderbouw.aantal_paalrijen == 0


def test_aantal_palen_per_rij(mock_onderbouw: Onderbouw):
    """Test dat aantal_palen_per_rij een correct overzicht geeft van palen per rij."""
    # Mock data heeft 3 palen in rij 1 en 1 paal in rij 2
    assert mock_onderbouw.aantal_palen_per_rij == {1: 1, 2: 2, 3: 1}
    assert mock_onderbouw.max_aantal_palen_per_rij == 2


def test_aantal_palen_per_rij_extra_paal(mock_onderbouw: Onderbouw, maak_paal_rij_1):
    """Test dat aantal_palen_per_rij correct update bij het toevoegen van palen."""
    # Voeg extra paal toe aan rij 1
    extra_paal = maak_paal_rij_1("P1.4", AansluitingStatus.GOED)
    mock_onderbouw.palen.append(extra_paal)

    assert mock_onderbouw.aantal_palen_per_rij == {1: 1, 2: 2, 3: 1, 4: 1}
    assert mock_onderbouw.max_aantal_palen_per_rij == 2


def test_aantal_palen_per_rij_meerdere_rijen(mock_onderbouw: Onderbouw):
    """Test dat aantal_palen_per_rij correct werkt met meerdere paalrijen."""
    # Voeg palen toe aan een derde rij
    paal_rij_3_1 = Paal(
        paal_nummer="P3.1",
        paalrij_nummer=3,
        hoh_paalnummer="",
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
    paal_rij_3_2 = Paal(
        paal_nummer="P3.2",
        paalrij_nummer=3,
        hoh_paalnummer="P3.1",
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
    mock_onderbouw.palen.extend([paal_rij_3_1, paal_rij_3_2])

    assert mock_onderbouw.aantal_palen_per_rij == {1: 2, 2: 3, 3: 1}
    assert mock_onderbouw.max_aantal_palen_per_rij == 3


def test_aantal_ongewenst_schoor(mock_onderbouw: Onderbouw):
    """Test dat aantal_ongewenst_schoor alleen eerste-rij palen met negatieve schoorstand telt."""
    # Alle palen hebben standaard PNV (positief), dus aantal_ongewenst_schoor moet 0 zijn
    assert mock_onderbouw.aantal_ongewenst_schoor == 0


def test_aantal_ongewenst_schoor_een_paal(mock_onderbouw: Onderbouw):
    """Test dat aantal_ongewenst_schoor correct telt bij één paal met ongewenste schoorstand."""
    # Zet P1.1 (eerste rij) op negatieve schoorstand
    p1_1 = next(paal for paal in mock_onderbouw.palen if paal.paal_nummer == "P1.1")
    p1_1.schoor_richting = SchoorStand.NEGATIEF

    assert mock_onderbouw.aantal_ongewenst_schoor == 1


def test_aantal_ongewenst_schoor_meerdere_palen(mock_onderbouw: Onderbouw):
    """Test dat aantal_ongewenst_schoor correct telt bij meerdere palen met ongewenste schoorstand."""
    # Zet alle eerste-rij palen op negatieve schoorstand
    for paal in mock_onderbouw.palen:
        if paal.paal_nummer_main == 1:
            paal.schoor_richting = SchoorStand.NEGATIEF

    assert mock_onderbouw.aantal_ongewenst_schoor == 3


def test_aantal_ongewenst_schoor_tweede_rij_telt_niet_mee(mock_onderbouw: Onderbouw):
    """Test dat aantal_ongewenst_schoor alleen eerste-rij palen meetelt."""
    # Zet alleen P2.2 (tweede rij) op negatieve schoorstand
    p2_2 = next(paal for paal in mock_onderbouw.palen if paal.paal_nummer == "P2.2")
    p2_2.schoor_richting = SchoorStand.NEGATIEF

    # Tweede-rij palen meetellen niet
    assert mock_onderbouw.aantal_ongewenst_schoor == 0


def test_totaal_aantal_kespen(mock_onderbouw: Onderbouw):
    """Test dat totaal_aantal_kespen het juiste aantal kespen teruggeeft."""
    # Mock data heeft 7 kespen (K1 t/m K7)
    assert mock_onderbouw.totaal_aantal_kespen == 7


def test_totaal_aantal_kespen_geen_kespen(mock_onderbouw: Onderbouw):
    """Test dat totaal_aantal_kespen 0 is als er geen kespen zijn."""
    mock_onderbouw.kespen = []

    assert mock_onderbouw.totaal_aantal_kespen == 0


def test_aantal_beschadigde_kespen(mock_onderbouw: Onderbouw):
    """Test dat aantal_beschadigde_kespen kespen met vervorming of aantasting telt."""
    # Mock data heeft 5 kespen met is_aangetast=True (K2 t/m K6)
    assert mock_onderbouw.aantal_beschadigde_kespen == 5


def test_aantal_beschadigde_kespen_met_vervorming(mock_onderbouw: Onderbouw):
    """Test dat aantal_beschadigde_kespen ook vervormde kespen meetelt."""
    # Zet K1 (niet aangetast) op vervormd
    mock_onderbouw.kespen[0].is_vervormd = True

    # Nu zijn er 6 beschadigde kespen: K1 (vervormd) en K2-K6 (aangetast)
    assert mock_onderbouw.aantal_beschadigde_kespen == 6


def test_aantal_beschadigde_kespen_geen_kespen(mock_onderbouw: Onderbouw):
    """Test dat aantal_beschadigde_kespen 0 is als er geen kespen zijn."""
    mock_onderbouw.kespen = []

    assert mock_onderbouw.aantal_beschadigde_kespen == 0


def test_aantal_aansluitingen(mock_onderbouw: Onderbouw):
    """Test dat aantal_aansluitingen palen met status GOED of SLECHT telt."""
    # Mock data heeft 4 palen, allemaal met aansluiting_status GOED
    assert mock_onderbouw.aantal_aansluitingen == 4


def test_aantal_aansluitingen_gemengd(mock_onderbouw: Onderbouw):
    """Test dat aantal_aansluitingen zowel GOED als SLECHT aansluitingen telt."""
    # Zet enkele palen op SLECHT
    mock_onderbouw.palen[0].aansluiting_status = AansluitingStatus.SLECHT
    mock_onderbouw.palen[1].aansluiting_status = AansluitingStatus.SLECHT

    # Nog steeds 4 aansluitingen (2 GOED + 2 SLECHT)
    assert mock_onderbouw.aantal_aansluitingen == 4


def test_aantal_aansluitingen_met_niet_meetbaar(mock_onderbouw: Onderbouw):
    """Test dat aantal_aansluitingen palen met status NIET_MEETBAAR niet meetelt."""
    # Zet enkele palen op NIET_MEETBAAR
    mock_onderbouw.palen[0].aansluiting_status = AansluitingStatus.NIET_MEETBAAR
    mock_onderbouw.palen[1].aansluiting_status = AansluitingStatus.NIET_MEETBAAR

    # Alleen 2 aansluitingen (de palen met status GOED)
    assert mock_onderbouw.aantal_aansluitingen == 2


def test_aantal_slechte_aansluitingen(mock_onderbouw: Onderbouw):
    """Test dat aantal_slechte_aansluitingen alleen palen met status SLECHT telt."""
    # Mock data heeft 4 palen, allemaal met aansluiting_status GOED
    assert mock_onderbouw.aantal_slechte_aansluitingen == 0


def test_aantal_slechte_aansluitingen_enkele_slechte(mock_onderbouw: Onderbouw):
    """Test dat aantal_slechte_aansluitingen correct telt bij enkele slechte aansluitingen."""
    # Zet twee palen op SLECHT
    mock_onderbouw.palen[0].aansluiting_status = AansluitingStatus.SLECHT
    mock_onderbouw.palen[1].aansluiting_status = AansluitingStatus.SLECHT

    assert mock_onderbouw.aantal_slechte_aansluitingen == 2


def test_aantal_slechte_aansluitingen_alle_slecht(mock_onderbouw: Onderbouw):
    """Test dat aantal_slechte_aansluitingen correct telt als alle aansluitingen slecht zijn."""
    # Zet alle palen op SLECHT
    for paal in mock_onderbouw.palen:
        paal.aansluiting_status = AansluitingStatus.SLECHT

    assert mock_onderbouw.aantal_slechte_aansluitingen == 4
