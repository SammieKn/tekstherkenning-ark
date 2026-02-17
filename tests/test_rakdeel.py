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
