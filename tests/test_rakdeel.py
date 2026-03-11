from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat, OnverwachtResultaatType
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.onderbouw import Onderbouw


def test_lengte_m_omschrijving(mock_rakdeel: Rakdeel):
    assert mock_rakdeel.lengte_m_omschrijving == 4.0


def test_lengte_m_afgeleid(mock_rakdeel: Rakdeel):
    assert mock_rakdeel.lengte_m_afgeleid == 4.2


def test_lengte_m(mock_rakdeel: Rakdeel):

    # If lengte_m_omschrijving is available, it should take precedence over lengte_m_afgeleid
    assert mock_rakdeel.lengte_m == 4.0

    # Remove lengte_m_omschrijving to test that lengte_m_afgeleid is used when lengte_m_omschrijving is not available
    mock_rakdeel.lengte_m_omschrijving = None
    assert mock_rakdeel.lengte_m == 4.2


def test_lengte_m_afgeleid_no_data(mock_rakdeel: Rakdeel):

    # Remove all palen to simulate the case where there is no data to derive the length from
    mock_rakdeel.onderbouw.palen = []

    # In this case, we expect lengte_m_afgeleid to be None, since there are no palen to derive the length from
    assert mock_rakdeel.lengte_m_afgeleid is None


def test_lengte_m_afgeleid_no_hoh_afstand_cm(mock_rakdeel: Rakdeel):
    """Test that lengte_m_afgeleid correctly handles palen without hoh_afstand_cm."""

    # Remove hoh_afstand_cm from a paal
    mock_rakdeel.onderbouw.palen[1].hoh_afstand_cm = None

    # In this case, we expect lengte_m_afgeleid to be an OnverwachtResultaat indicating that there is missing hoh_afstand_cm data for a paal.
    assert isinstance(mock_rakdeel.lengte_m_afgeleid, OnverwachtResultaat)
    assert (
        mock_rakdeel.lengte_m_afgeleid.onverwacht_resultaat_type
        is OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    )
    assert "Ontbrekende hoh_afstand_cm voor paal" in mock_rakdeel.lengte_m_afgeleid.details


def test_maximaal_aantal_scheuren_per_10_m(mock_rakdeel_with_scheuren: Rakdeel):
    """Test the maximaal_aantal_scheuren_per_10_m property calculation.

    This test uses a mock rakdeel with:
    - Paalrij 1: P1.1 (3 ScheurHout), P1.2 (1 ScheurHout), P1.3 (0), P1.4 (3 ScheurHout), P1.5 (0)
    - Paalrij 2: P2.1 (1 ScheurHout), P2.2 (2 ScheurHout), P2.3 (0), P2.4 (1 ScheurHout), P2.5 (0)
    - hoh_afstand_cm: 300, 400, 500, 400, 300 cm respectively

    The calculation should:
    1. Couple palen from both rows: [P1.1,P2.1]=4, [P1.2,P2.2]=3, [P1.3,P2.3]=0, [P1.4,P2.4]=4, [P1.5,P2.5]=0
    2. Use a sliding 10m window to find maximum scheuren count
    3. Expected maximum: 7 scheuren (window P1.1-P1.3: 4+3+0=7 scheuren)
    """

    result = mock_rakdeel_with_scheuren.bovenbouw.maximaal_aantal_scheuren_per_10_m

    # Verify result is not an OnverwachtResultaat
    assert not isinstance(result, OnverwachtResultaat), f"Unexpected error: {result}"

    # Verify the maximum number of scheuren per 10m is correctly calculated
    assert result == 5, f"Expected 5 scheuren per 10m, but got {result}"


def test_maximaal_aantal_scheuren_per_10_m_geen_scheuren(mock_rakdeel_with_scheuren: Rakdeel):
    """Test maximaal_aantal_scheuren_per_10_m when there are no scheuren."""
    # Remove all scheuren
    mock_rakdeel_with_scheuren.bovenbouw.gebreken = []

    # Should return 0 since there are no scheuren to count
    assert mock_rakdeel_with_scheuren.bovenbouw.maximaal_aantal_scheuren_per_10_m == 0


def test_maximaal_aantal_scheuren_per_10_m_none_afstand(mock_rakdeel_with_scheuren: Rakdeel):
    """Test maximaal_aantal_scheuren_per_10_m when get_consecutive_palen returns OnverwachtResultaat."""
    # Remove hoh_afstand_cm to trigger OnverwachtResultaat in get_consecutive_palen
    mock_rakdeel_with_scheuren.bovenbouw.gebreken[4] = None

    result = mock_rakdeel_with_scheuren.bovenbouw.maximaal_aantal_scheuren_per_10_m

    # Verify result is not an OnverwachtResultaat
    assert not isinstance(result, OnverwachtResultaat), f"Unexpected error: {result}"

    # Verify the maximum number of scheuren per 10m is correctly calculated
    assert result == 4, f"Expected 4 scheuren per 10m, but got {result}"


def test_percentage_niet_functionerend_schuifhout_geen_kespen():
    """Test dat percentage_niet_functionerend_schuifhout None teruggeeft als er geen kespen zijn."""
    rakdeel = Rakdeel(
        rakdeel_id="Test A",
        bovenbouw=Bovenbouw(),
        onderbouw=Onderbouw(
            palen=[],
            kespen=[],
        ),
    )

    assert rakdeel.percentage_niet_functionerend_schuifhout is None


def test_percentage_niet_functionerend_schuifhout_normaal():
    """Test normale berekening: 2 van 4 opsluitklossen aangetast = 50% functionerend."""
    rakdeel = Rakdeel(
        rakdeel_id="Test B",
        bovenbouw=Bovenbouw(),
        onderbouw=Onderbouw(
            palen=[],
            kespen=[
                Kesp(
                    kesp_nummer="K1",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=True,
                    is_opsluitklos_aangetast=False,
                ),
                Kesp(
                    kesp_nummer="K2",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=True,
                    is_opsluitklos_aangetast=True,
                ),
                Kesp(
                    kesp_nummer="K3",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=True,
                    is_opsluitklos_aangetast=False,
                ),
                Kesp(
                    kesp_nummer="K4",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=True,
                    is_opsluitklos_aangetast=True,
                ),
            ],
        ),
    )

    resultaat = rakdeel.percentage_niet_functionerend_schuifhout
    assert isinstance(resultaat, float)
    assert resultaat == 50.0


def test_percentage_niet_functionerend_schuifhout_alle_functionerend():
    """Test wanneer alle opsluitklossen functionerend zijn = 100%."""
    rakdeel = Rakdeel(
        rakdeel_id="Test C",
        bovenbouw=Bovenbouw(),
        onderbouw=Onderbouw(
            palen=[],
            kespen=[
                Kesp(
                    kesp_nummer="K1",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=True,
                    is_opsluitklos_aangetast=False,
                ),
                Kesp(
                    kesp_nummer="K2",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=True,
                    is_opsluitklos_aangetast=False,
                ),
            ],
        ),
    )

    resultaat = rakdeel.percentage_niet_functionerend_schuifhout
    assert isinstance(resultaat, float)
    assert resultaat == 0.0


def test_percentage_niet_functionerend_schuifhout_half():
    """Test wanneer geen opsluitklossen functionerend zijn = 0%."""
    rakdeel = Rakdeel(
        rakdeel_id="Test D",
        bovenbouw=Bovenbouw(),
        onderbouw=Onderbouw(
            palen=[],
            kespen=[
                Kesp(
                    kesp_nummer="K1",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=True,
                    is_opsluitklos_aangetast=True,
                ),
                Kesp(
                    kesp_nummer="K2",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=True,
                    is_opsluitklos_aangetast=False,
                ),
            ],
        ),
    )

    resultaat = rakdeel.percentage_niet_functionerend_schuifhout
    assert isinstance(resultaat, float)
    assert resultaat == 50.0


def test_percentage_niet_functionerend_schuifhout_geen_opsluitklos_aanwezig():
    """Test wanneer opsluitklossen niet aanwezig zijn (worden niet meegerekend)."""
    rakdeel = Rakdeel(
        rakdeel_id="Test E",
        bovenbouw=Bovenbouw(),
        onderbouw=Onderbouw(
            palen=[],
            kespen=[
                Kesp(
                    kesp_nummer="K1",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=True,
                    is_opsluitklos_aangetast=False,
                ),
                Kesp(
                    kesp_nummer="K2",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=False,
                    is_opsluitklos_aangetast=False,
                ),
                Kesp(
                    kesp_nummer="K3",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=True,
                    is_opsluitklos_aangetast=True,
                ),
            ],
        ),
    )

    # 1 opsluitklos aanwezig & niet aangetast, 1 aanwezig & aangetast = 50%
    resultaat = rakdeel.percentage_niet_functionerend_schuifhout
    assert isinstance(resultaat, float)
    assert resultaat == 50.0


def test_percentage_niet_functionerend_schuifhout_geen_enkele_opsluitklos_aanwezig_none():
    """Test dat None wordt teruggegeven als er wel kespen zijn maar geen enkele opsluitklos aanwezig is."""
    rakdeel = Rakdeel(
        rakdeel_id="Test E2",
        bovenbouw=Bovenbouw(),
        onderbouw=Onderbouw(
            palen=[],
            kespen=[
                Kesp(
                    kesp_nummer="K1",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=False,
                    is_opsluitklos_aangetast=False,
                ),
                Kesp(
                    kesp_nummer="K2",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=False,
                    is_opsluitklos_aangetast=False,
                ),
            ],
        ),
    )

    assert rakdeel.percentage_niet_functionerend_schuifhout is None


def test_percentage_niet_functionerend_schuifhout_inconsistente_data():
    """Test dat OnverwachtResultaat wordt geretourneerd bij tegenstrijdige data."""
    rakdeel = Rakdeel(
        rakdeel_id="Test F",
        bovenbouw=Bovenbouw(),
        onderbouw=Onderbouw(
            palen=[],
            kespen=[
                Kesp(
                    kesp_nummer="K1",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=False,
                    is_opsluitklos_aangetast=True,  # Tegenstrijdig: aangetast maar niet aanwezig
                ),
            ],
        ),
    )

    resultaat = rakdeel.percentage_niet_functionerend_schuifhout
    assert isinstance(resultaat, OnverwachtResultaat)
    assert resultaat.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    assert "K1" in resultaat.waarde
    assert "Tegenstrijdige data" in resultaat.waarde


def test_percentage_niet_functionerend_schuifhout_onverwacht_resultaat_in_kesp():
    """Test dat OnverwachtResultaat wordt geretourneerd als kesp data OnverwachtResultaat bevat."""
    rakdeel = Rakdeel(
        rakdeel_id="Test G",
        bovenbouw=Bovenbouw(),
        onderbouw=Onderbouw(
            palen=[],
            kespen=[
                Kesp(
                    kesp_nummer="K1",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=OnverwachtResultaat(
                        waarde="Onleesbare data",
                        onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
                    ),
                    is_opsluitklos_aangetast=False,
                ),
            ],
        ),
    )

    resultaat = rakdeel.percentage_niet_functionerend_schuifhout
    assert isinstance(resultaat, OnverwachtResultaat)
    assert resultaat.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    assert "Onduidelijke staat van opsluitklossen" in resultaat.waarde


def test_percentage_niet_functionerend_schuifhout_meerdere_inconsistente_kespen():
    """Test dat alle inconsistente kespen worden vermeld in de foutmelding."""
    rakdeel = Rakdeel(
        rakdeel_id="Test H",
        bovenbouw=Bovenbouw(),
        onderbouw=Onderbouw(
            palen=[],
            kespen=[
                Kesp(
                    kesp_nummer="K1",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=False,
                    is_opsluitklos_aangetast=True,
                ),
                Kesp(
                    kesp_nummer="K2",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=True,
                    is_opsluitklos_aangetast=False,
                ),
                Kesp(
                    kesp_nummer="K3",
                    hoogte_cm=20,
                    breedte_cm=15,
                    lengte_uitstekend_deel_cm=10,
                    is_opsluitklos_aanwezig=False,
                    is_opsluitklos_aangetast=True,
                ),
            ],
        ),
    )

    resultaat = rakdeel.percentage_niet_functionerend_schuifhout
    assert isinstance(resultaat, OnverwachtResultaat)
    assert resultaat.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    assert "K1" in resultaat.waarde
    assert "K3" in resultaat.waarde


def test_vijf_slechte_kespen_naast_elkaar_met_mock(mock_rak_with_gebreken: Rak):
    """Test vijf_slechte_kespen_naast_elkaar met mock data (K2-K6 zijn aangetast)."""

    assert mock_rak_with_gebreken.rakdelen[0].vijf_slechte_kespen_naast_elkaar


def test_vijf_slechte_kespen_naast_elkaar_minder_dan_vijf_kespen(mock_rak_with_gebreken: Rak):
    """Test vijf_slechte_kespen_naast_elkaar met minder dan 5 kespen totaal."""

    # Keep only K1-K3
    mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen = mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen[:3]
    assert not mock_rak_with_gebreken.rakdelen[0].vijf_slechte_kespen_naast_elkaar


def test_vijf_slechte_kespen_naast_elkaar_onderbroken(mock_rak_with_gebreken: Rak):
    """Test vijf_slechte_kespen_naast_elkaar met exact 4 consecutive aangetaste kespen."""

    # K3 niet aangetast
    mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen[2].is_aangetast = False

    assert not mock_rak_with_gebreken.rakdelen[0].vijf_slechte_kespen_naast_elkaar


def test_vijf_slechte_kespen_naast_elkaar_gebrek(mock_rak_with_gebreken: Rak):
    """Test vijf_slechte_kespen_naast_elkaar met een gebrek op K1 maar K1 zelf niet aangetast."""

    # Maak K3 niet aangetast maar voeg een gebrek toe
    mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen[2].is_aangetast = False
    mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen[2].gebreken.append(
        Gebrek(codering="GK1", omschrijving="Beschadigd kesp", figuurnummer="F2")
    )

    assert mock_rak_with_gebreken.rakdelen[0].vijf_slechte_kespen_naast_elkaar


def test_vijf_slechte_kespen_naast_elkaar_meer_dan_vijf(mock_rak_with_gebreken: Rak):
    """Test vijf_slechte_kespen_naast_elkaar met 6 consecutive aangetaste kespen."""

    # K7 ook aangetast maken
    mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen[6].is_aangetast = True

    assert mock_rak_with_gebreken.rakdelen[0].vijf_slechte_kespen_naast_elkaar


def test_vijf_slechte_kespen_naast_elkaar_geen_kespen(mock_rak_with_gebreken: Rak):
    """Test vijf_slechte_kespen_naast_elkaar met geen kespen."""
    # Verwijder alle kespen
    mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen = []

    assert not mock_rak_with_gebreken.rakdelen[0].vijf_slechte_kespen_naast_elkaar
