import pickle
import sys
from pathlib import Path

from tekstherkenning_ark.utils import clear_llm_cache_files


# Add project root and tests dir to sys.path to enable importing from tests module
# Tests dir is needed so conftest.py can import from data submodule
PROJECT_ROOT = Path(__file__).parent.parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(TESTS_DIR))

from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark import constants

#
from tests.conftest import KZG_0202_TEST_DIR, KZG_0202_DOC_NAME, KZG_0202_PKL_NAME

logger = get_logger(__name__)


def sanitize_smart_document(smart_doc: SmartDocument) -> SmartDocument:
    """Sanitize the SmartDocument by removing the analyze_result and unnecessary
    sections to remove sensitive information and to reduce size for test data."""

    # Filter out relevant sections
    relevant_sections = []
    for idx, sectie in enumerate(smart_doc.sections):
        if "meettabel" in sectie.titel.lower() and sectie.tabellen:
            relevant_sections.append(idx)
        if "Constructie" in sectie.titel:
            relevant_sections.extend([idx, idx + 1, idx + 2, idx + 3])  # include next 3 sections as well

    # unique and sort and select
    relevant_sections = sorted(set(relevant_sections))
    relevant_sections = [smart_doc.sections[i] for i in relevant_sections]

    logger.info(
        f"Sanitized SmartDocument: kept {len(relevant_sections)} relevant sections out of {len(smart_doc.sections)} total sections"
    )

    return SmartDocument(document_name=smart_doc.document_name, sections=relevant_sections, analyze_result=None)


def generate_rak_cache(sanitized_doc: SmartDocument) -> None:
    """Generate the Rak cache for the sanitized SmartDocument to ensure that any LLM calls during Rak creation are cached in the test data directory."""

    # Set the cache dir to the test data dir for KZG0202 to ensure any LLM calls during Rak creation are cached there
    # This should already be the case, but we set it again here to be sure when this function is called independently.
    constants.CACHE_DIR = KZG_0202_TEST_DIR

    # Create Rak instance from sanitized SmartDocument to generate cache
    # use_cache False to ensure it generates new cache in test dir
    _ = Rak.from_smart_document(sanitized_doc, use_caching=False)


if __name__ == "__main__":

    # Load document from local data folder
    DOC_SRC_PATH = constants.DUIKRAPPORTEN_DIR / f"{KZG_0202_DOC_NAME}.pdf"
    PKL_DST_PATH = KZG_0202_TEST_DIR / KZG_0202_PKL_NAME

    # Set the cache dir to the test data dir for KZG0202 to ensure any LLM calls during Rak creation are cached there
    constants.CACHE_DIR = KZG_0202_TEST_DIR

    # Create SmartDocument instance from PDF
    logger.info(f"Creating SmartDocument from PDF: {DOC_SRC_PATH}")
    smart_doc = SmartDocument.from_pdf(DOC_SRC_PATH, use_cache=True)

    # Sanitize the SmartDocument
    logger.info("Sanitizing SmartDocument for test data")
    sanitized_doc = sanitize_smart_document(smart_doc)

    # Clear LLM cache to ensure clean state for generating Rak cache
    clear_llm_cache_files(cache_dir=KZG_0202_TEST_DIR)

    # Save the sanitized SmartDocument to the test data directory
    logger.info(f"Saving sanitized SmartDocument to {PKL_DST_PATH}")
    PKL_DST_PATH.write_bytes(pickle.dumps(sanitized_doc))

    # Generate Rak cache for the sanitized SmartDocument to ensure LLM calls are cached in test data dir
    logger.info("Generating Rak cache for sanitized SmartDocument")
    generate_rak_cache(sanitized_doc)
