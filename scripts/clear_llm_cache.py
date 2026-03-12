from tekstherkenning_ark import utils
from tekstherkenning_ark.logger import get_logger


logger = get_logger(__name__)


if __name__ == "__main__":
    utils.clear_llm_cache_files()
