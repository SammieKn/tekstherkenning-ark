"""
test fixtures for module tests

tests work only local -with data dir for now- what do we want?
"""
import pytest

from tekstherkenning_ark.parsed_pdf import ParsedPDF
from tekstherkenning_ark.constants import DATA_DIR

TEST_PDF_PATH = DATA_DIR / "HEG0801_Houtmonstername&VisueleInspectie_V1.1_20220311.pdf"


@pytest.fixture(scope="module")
def parsed_pdf_fixture():
    """Fixture to provide a ParsedPDF instance for tests."""
    return ParsedPDF.from_pdf(TEST_PDF_PATH, use_cache=True)


@pytest.fixture(scope="module")
def gebreken_tabel_fixture(parsed_pdf_fixture):
    """Fixture to provide the 'GEBREKEN' table from the ParsedPDF instance."""
    return parsed_pdf_fixture.result.tables[13]


@pytest.fixture(scope="module")
def palen_tabel_fixture(parsed_pdf_fixture):
    """Fixture to provide the 'FIGUREN' table from the ParsedPDF instance."""
    return parsed_pdf_fixture.result.tables[89]
