"""
test fixtures for module tests

tests work only local -with data dir for now- what do we want?
"""

import json
from pathlib import Path

import pytest

from tekstherkenning_ark.models.rak import Rak

# Test directory constants
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"


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
