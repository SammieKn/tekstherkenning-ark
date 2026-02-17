from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat, OnverwachtResultaatType
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rakdeel import Rakdeel


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

    result = mock_rakdeel_with_scheuren.maximaal_aantal_scheuren_per_10_m

    # Verify result is not an OnverwachtResultaat
    assert not isinstance(result, OnverwachtResultaat), f"Unexpected error: {result}"

    # Verify the maximum number of scheuren per 10m is correctly calculated
    assert result == 4, f"Expected 4 scheuren per 10m, but got {result}"


def test_maximaal_aantal_scheuren_per_10_m_geen_palen(mock_rakdeel_with_scheuren: Rakdeel):
    """Test maximaal_aantal_scheuren_per_10_m when there are no palen."""
    # Remove all palen
    mock_rakdeel_with_scheuren.onderbouw.palen = []

    # Should return 0 since there are no palen to count scheuren from
    assert mock_rakdeel_with_scheuren.maximaal_aantal_scheuren_per_10_m == 0


def test_maximaal_aantal_scheuren_per_10_m_onverwacht_resultaat(mock_rakdeel_with_scheuren: Rakdeel):
    """Test maximaal_aantal_scheuren_per_10_m when get_consecutive_palen returns OnverwachtResultaat."""
    # Remove hoh_afstand_cm to trigger OnverwachtResultaat in get_consecutive_palen
    mock_rakdeel_with_scheuren.onderbouw.palen[1].hoh_afstand_cm = None

    result = mock_rakdeel_with_scheuren.maximaal_aantal_scheuren_per_10_m
    assert isinstance(result, OnverwachtResultaat)
    assert result.onverwacht_resultaat_type == OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
