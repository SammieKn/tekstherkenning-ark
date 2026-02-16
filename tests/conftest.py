"""
test fixtures for module tests

tests work only local -with data dir for now- what do we want?
"""

from functools import cache
import json
from pathlib import Path

import pytest

from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rakdeel import Rakdeel

# Test directory constants
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"


@cache
def load_from_json(json_file: Path) -> Rak:
    """Helper function to load a Rak object from a JSON file."""
    data = json_file.read_text(encoding="utf-8")
    return Rak.model_validate(json.loads(data))


@pytest.fixture()
def mock_rak_with_gebreken() -> Rak:
    """Fixture to provide a complete mock Rak object with gebreken at various levels."""

    return load_from_json(TEST_DATA_DIR / "mock_rak_with_gebreken.json").model_copy(deep=True)


@pytest.fixture()
def mock_rak_with_onverwachte_resultaten() -> Rak:
    """Fixture to provide a complete mock Rak object with OnverwachtResultaat at various levels."""

    return load_from_json(TEST_DATA_DIR / "mock_rak_with_onverwachte_resultaten.json").model_copy(deep=True)


@pytest.fixture()
def mock_rakdeel(mock_rak_with_gebreken: Rak) -> Rakdeel:
    """Fixture to provide a single Rakdeel from the mock Rak with gebreken."""
    return mock_rak_with_gebreken.rakdelen[0]


@pytest.fixture()
def mock_palen(mock_rak_with_gebreken: Rak) -> list[Paal]:
    """Fixture to provide a list of Palen from the first Rakdeel of the mock Rak with gebreken."""
    return mock_rak_with_gebreken.rakdelen[0].onderbouw.palen


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
