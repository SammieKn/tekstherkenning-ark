"""
test fixtures for module tests

tests work only local -with data dir for now- what do we want?
"""

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

KZG_0202_TEST_DIR = TEST_DATA_DIR / "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325"

# Set the CACHE_DIR to the test directory for KZG0202
constants.CACHE_DIR = KZG_0202_TEST_DIR


@pytest.fixture
def kzg0202_rak() -> Rak:
    doc_pkl_path = KZG_0202_TEST_DIR / "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325_docai_result.pkl"
    return get_rak_kzg0202(doc_pkl_path)


def get_rak_kzg0202(doc_pkl_path: Path) -> Rak:
    """Get a Rak instance for the KZG0202 test PDF from the test cache."""
    # load data
    doc_from_cache = pickle.loads(doc_pkl_path.read_bytes())

    loaded_doc = SmartDocument(
        pdf_path=doc_from_cache["pdf_path"], sections=doc_from_cache["sections"], analyze_result=None
    )
    # rak
    rak = Rak.from_smart_document(loaded_doc, use_caching=False)  # use cached LLM parts but not rak itself
    return rak


@pytest.fixture(scope="session")
def paal_tables() -> DocumentTable:
    """Fixture to provide a complete mock Rak object with gebreken at various levels."""
    doc_pkl_path = KZG_0202_TEST_DIR / "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325_docai_result.pkl"
    doc_from_cache = pickle.loads(doc_pkl_path.read_bytes())

    loaded_doc = SmartDocument(
        pdf_path=doc_from_cache["pdf_path"], sections=doc_from_cache["sections"], analyze_result=None
    )
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
