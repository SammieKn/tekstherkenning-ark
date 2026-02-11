"""
test fixtures for module tests

tests work only local -with data dir for now- what do we want?
"""

import json
import pickle
import pytest
from pathlib import Path

from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark import constants

# Test directory constants
TEST_DIR = Path(__file__).parent
TEST_DIR = Path(r"C:\repos\tekstherkenning-ark\tests")
TEST_DATA_DIR = TEST_DIR / "data"

constants.CACHE_DIR = Path(TEST_DATA_DIR / "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325")


@pytest.fixture
def kzg0202_from_test_cache():
    # Set a new CACHE_DIR for this test
    cached_doc_path = constants.CACHE_DIR / "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325_docai_result.pkl"

    return get_rak_kzg0202(cached_doc_path)


def get_rak_kzg0202(cached_doc_path):
    """Get a Rak instance for the KZG0202 test PDF from the test cache."""
    # load data
    doc_from_cache = pickle.loads(cached_doc_path.read_bytes())
    loaded_doc = SmartDocument(pdf_path=doc_from_cache["pdf_path"], sections=doc_from_cache["sections"],
                               analyze_result=None)
    # rak
    rak = Rak.from_smart_document(loaded_doc, use_caching=False)  # use cached LLM parts but not rak itself
    return rak


@pytest.fixture(scope="session")
def paal_tables():
    """Fixture to provide a complete mock Rak object with gebreken at various levels."""
    cached_doc_path = constants.CACHE_DIR / "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325_docai_result.pkl"
    doc_from_cache = pickle.loads(cached_doc_path.read_bytes())
    loaded_doc = SmartDocument(pdf_path=doc_from_cache["pdf_path"], sections=doc_from_cache["sections"],
                               analyze_result=None)
    paal_tables = loaded_doc.get_meettabel_fundering_paal()
    return paal_tables


@pytest.fixture(scope="session")
def mock_rak_with_gebreken() -> Rak:
    """Fixture to provide a complete mock Rak object with gebreken at various levels."""
    json_path = TEST_DATA_DIR / "mock_rak_with_gebreken.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return Rak.model_validate(data)


@pytest.fixture(scope="session")
def mock_rak_with_onverwachte_resultaten() -> Rak:
    """Fixture to provide a complete mock Rak object with OnverwachtResultaat at various levels."""
    json_path = TEST_DATA_DIR / "mock_rak_with_onverwachte_resultaten.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return Rak.model_validate(data)
