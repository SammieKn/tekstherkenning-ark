"""
test fixtures for module tests

tests work only local -with data dir for now- what do we want?
"""

import json
import pickle
import pytest
from pathlib import Path
import importlib

from tekstherkenning_ark.smart_document import SmartDocument
from tekstherkenning_ark.models.rak import Rak

# Test directory constants
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"


@pytest.fixture
def kzg0202_from_test_cache(monkeypatch):
    # Set a new CACHE_DIR for this test
    new_cache_dir = Path(TEST_DATA_DIR / "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325")
    monkeypatch.setenv("CACHE_DIR", str(new_cache_dir))

    # Reload the constants module to reflect the updated environment variable
    import tekstherkenning_ark.constants
    importlib.reload(tekstherkenning_ark.constants)
    from tekstherkenning_ark.constants import CACHE_DIR
    assert CACHE_DIR == new_cache_dir

    return get_rak_kzg0202()


def get_rak_kzg0202():
    """Get a Rak instance for the KZG0202 test PDF from the test cache."""
    # Reload the constants module to reflect the updated environment variable
    from tekstherkenning_ark.constants import CACHE_DIR
    cached_doc_path = CACHE_DIR / "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325_docai_result.pkl"
    # load data
    doc_from_cache = pickle.loads(cached_doc_path.read_bytes())
    loaded_doc = SmartDocument(pdf_path=doc_from_cache["pdf_path"], sections=doc_from_cache["sections"],
                               analyze_result=None)
    # rak
    rak = Rak.from_smart_document(loaded_doc)
    return rak


@pytest.fixture(scope="session")
def paal_tables() -> list:
    """Fixture to provide a complete mock Rak object with gebreken at various levels."""
    cache_file = TEST_DATA_DIR / "palen_HEG0801_Houtmonstername&VisueleInspectie_V1.1_20220311.pkl"
    return pickle.loads(cache_file.read_bytes())


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


# from tekstherkenning_ark.parsed_pdf import ParsedPDF
# from tekstherkenning_ark.constants import DATA_DIR

# TEST_PDF_PATH = DATA_DIR / "HEG0801_Houtmonstername&VisueleInspectie_V1.1_20220311.pdf"


# @pytest.fixture(scope="module")
# def parsed_pdf_fixture():
#     """Fixture to provide a ParsedPDF instance for tests."""
#     return ParsedPDF.from_pdf(TEST_PDF_PATH, use_cache=True)


# @pytest.fixture(scope="module")
# def gebreken_tabel_fixture(parsed_pdf_fixture):
#     """Fixture to provide the 'GEBREKEN' table from the ParsedPDF instance."""
#     return parsed_pdf_fixture.result.tables[13]


# @pytest.fixture(scope="module")
# def palen_tabel_fixture(parsed_pdf_fixture):
#     """Fixture to provide the 'FIGUREN' table from the ParsedPDF instance."""
#     return parsed_pdf_fixture.result.tables[89]
