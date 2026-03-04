from tekstherkenning_ark.constants import CACHE_DIR
from tekstherkenning_ark.logger import get_logger


logger = get_logger(__name__)


def clear_llm_cache_files():
    """Clear all llm cache files in the .cache directory."""

    files = [file for file in CACHE_DIR.glob("*.pkl") if not "_docai_result" in file.stem]
    for file in files:
        try:
            file.unlink()
            logger.info(f"Deleted cache file: {file}")
        except Exception as e:
            logger.error(f"Error deleting cache file {file}: {e}")


if __name__ == "__main__":
    clear_llm_cache_files()
