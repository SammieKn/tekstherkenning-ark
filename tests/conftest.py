"""
test fixtures for module tests

tests work only local -with data dir for now- what do we want?
"""

from pathlib import Path

import pytest

from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rakdeel import Rakdeel

# Test directory constants
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"

# Import mock data creators
from data.mock_rak_with_gebreken import create_mock_rak_with_gebreken
from data.mock_rak_with_onverwachte_resultaten import create_mock_rak_with_onverwachte_resultaten
from data.mock_rak_with_scheuren import create_mock_rak_with_scheuren


@pytest.fixture()
def mock_rak_with_gebreken() -> Rak:
    """Fixture to provide a complete mock Rak object with gebreken at various levels."""

    return create_mock_rak_with_gebreken()


@pytest.fixture()
def mock_rak_with_onverwachte_resultaten() -> Rak:
    """Fixture to provide a complete mock Rak object with OnverwachtResultaat at various levels."""

    return create_mock_rak_with_onverwachte_resultaten()


@pytest.fixture()
def mock_rak_with_scheuren() -> Rak:
    """Fixture to provide a mock Rak object for testing scheur calculations."""

    return create_mock_rak_with_scheuren()


@pytest.fixture()
def mock_rakdeel(mock_rak_with_gebreken: Rak) -> Rakdeel:
    """Fixture to provide a single Rakdeel from the mock Rak with gebreken."""
    return mock_rak_with_gebreken.rakdelen[0]


@pytest.fixture()
def mock_rakdeel_with_scheuren(mock_rak_with_scheuren: Rak) -> Rakdeel:
    """Fixture to provide a single Rakdeel for testing maximaal_aantal_scheuren_per_10_m."""
    return mock_rak_with_scheuren.rakdelen[0]


@pytest.fixture()
def mock_palen(mock_rak_with_gebreken: Rak) -> list[Paal]:
    """Fixture to provide a list of Palen from the first Rakdeel of the mock Rak with gebreken."""
    return mock_rak_with_gebreken.rakdelen[0].onderbouw.palen
