from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
DUIKRAPPORTEN_DIR = DATA_DIR / "duikrapporten"
CACHE_DIR = DATA_DIR / ".cache"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

TEST_PDF_PATH = DUIKRAPPORTEN_DIR / "HEG0801_Houtmonstername&VisueleInspectie_V1.1_20220311.pdf"

CONSTRUCTIEONDERDEEL_MAPPING = {
    "onderbouw.vloer": [
        r"vloer",
    ],
    "onderbouw": [
        r"ligger",
        r"planken",
        r"kesp",
        r"deksloof",
        r"watersloof",
        r"paal",
        r"palen",
        r"schuifhout",
        r"opsluitklos",
        r"grondkerend",
    ],
    "bovenbouw": [
        r"metsel",
        r"deksteen",
        r"natuursteen",
        r"wand",
    ],
    "onderbouw.onderloopsheidscherm": [
        r"onderloop",
    ],
}
