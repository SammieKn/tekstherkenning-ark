"""
test fixtures for module tests

tests work only local -with data dir for now- what do we want?
"""

from functools import cache
import json
import pickle
import pytest
from pathlib import Path

from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark import constants
from pathlib import Path

from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rakdeel import Rakdeel
from azure.ai.documentintelligence.models import DocumentTable


# Import mock data creators
from data.mock_rak_with_gebreken import create_mock_rak_with_gebreken
from data.mock_rak_with_onverwachte_resultaten import create_mock_rak_with_onverwachte_resultaten
from data.mock_rak_with_scheuren import create_mock_rak_with_scheuren

# Test directory constants
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"

KZG_0202_DOC_NAME = "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325"
KZG_0202_PKL_NAME = f"{KZG_0202_DOC_NAME}_smart_document_sanitized.pkl"
KZG_0202_TEST_DIR = TEST_DATA_DIR / "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325"

# Set the CACHE_DIR to the test directory for KZG0202
constants.CACHE_DIR = KZG_0202_TEST_DIR


@cache
def load_kzg0202_smart_document() -> SmartDocument:
    """Load the SmartDocument for the KZG0202 test PDF from the test cache."""

    doc_pkl_path = KZG_0202_TEST_DIR / f"{KZG_0202_DOC_NAME}_smart_document_sanitized.pkl"
    smart_doc = pickle.loads(doc_pkl_path.read_bytes())

    return smart_doc


@pytest.fixture(scope="session")
def kzg0202_rak() -> Rak:

    smart_doc = load_kzg0202_smart_document()

    # rak
    rak = Rak.from_smart_document(smart_doc, use_caching=False)  # use cached LLM parts but not rak itself
    return rak


@pytest.fixture(scope="session")
def paal_tables() -> DocumentTable:
    """Fixture to provide a complete mock Rak object with gebreken at various levels."""
    loaded_doc = load_kzg0202_smart_document()

    paal_tables = loaded_doc.get_meettabel_fundering_paal()

    return paal_tables


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


@pytest.fixture()
def mock_rak_with_scheuren_json() -> str:
    """Fixture to provide a JSON string of a mock Rak with scheuren for testing JSON serialization."""

    mock_rak_with_scheuren_json_path = TEST_DATA_DIR / "mock_rak_with_scheuren.json"
    return mock_rak_with_scheuren_json_path.read_text()
