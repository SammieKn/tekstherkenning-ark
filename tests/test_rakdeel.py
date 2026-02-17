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


def test_lengte_m_afgeleid_circular_reference(mock_rakdeel: Rakdeel):
    """Test that lengte_m_afgeleid correctly detects a circular reference in hoh_paalnummer."""

    # Create a circular reference by setting hoh_paalnummer to create a loop
    mock_rakdeel.onderbouw.palen[0].hoh_paalnummer = "P1.3"

    # In this case, we expect lengte_m_afgeleid to be an OnverwachtResultaat indicating that there is a circular reference in the paal references.
    assert isinstance(mock_rakdeel.lengte_m_afgeleid, OnverwachtResultaat)
    assert (
        mock_rakdeel.lengte_m_afgeleid.onverwacht_resultaat_type
        is OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    )
    assert "Cyclische paalreferenties gedetecteerd bij Rakdeel" in mock_rakdeel.lengte_m_afgeleid.details


def test_lengte_m_afgeleid_duplicate_reference(mock_rakdeel: Rakdeel):
    """Test that lengte_m_afgeleid correctly detects a duplicate reference in hoh_paalnummer."""

    # Create a duplicate reference by setting hoh_paalnummer to the same value for multiple palen
    mock_rakdeel.onderbouw.palen[0].hoh_paalnummer = "P1.2"

    # In this case, we expect lengte_m_afgeleid to be an OnverwachtResultaat indicating that there are multiple palen referencing the same hoh_paalnummer.
    assert isinstance(mock_rakdeel.lengte_m_afgeleid, OnverwachtResultaat)
    assert (
        mock_rakdeel.lengte_m_afgeleid.onverwacht_resultaat_type
        is OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    )
    assert "Meerdere palen verwijzen naar hetzelfde hoh_paalnummer" in mock_rakdeel.lengte_m_afgeleid.details


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


def test_lengte_m_afgeleid_not_all_palen_processed(mock_rakdeel: Rakdeel):
    """Test that lengte_m_afgeleid correctly handles the case where the reference chain is interrupted
    and thus not alle palen have been processed."""

    # The last paal is missing a reference and will thus not be found in the chain of references,
    # which should lead to an OnverwachtResultaat indicating that not all palen have been processed.
    mock_rakdeel.onderbouw.palen[3].hoh_paalnummer = ""

    # In this case, we expect lengte_m_afgeleid to be an OnverwachtResultaat indicating that there is an incomplete processing of palen for the Rakdeel.
    assert isinstance(mock_rakdeel.lengte_m_afgeleid, OnverwachtResultaat)
    assert (
        mock_rakdeel.lengte_m_afgeleid.onverwacht_resultaat_type
        is OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT
    )
    assert "Onvolledige verwerking van palen bij Rakdeel" in mock_rakdeel.lengte_m_afgeleid.details
