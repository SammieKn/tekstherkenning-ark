from pathlib import Path


ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = DATA_DIR / ".cache"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

TEST_PDF_PATH = DATA_DIR / "HEG0801_Houtmonstername&VisueleInspectie_V1.1_20220311.pdf"
