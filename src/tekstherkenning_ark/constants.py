from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
DUIKRAPPORTEN_DIR = DATA_DIR / "duikrapporten"
CACHE_DIR = DATA_DIR / ".cache"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

TEST_PDF_PATH = DUIKRAPPORTEN_DIR / "HEG0801_Houtmonstername&VisueleInspectie_V1.1_20220311.pdf"

NAP_CM_HOOGTE_WATERLIJN = 40
# Constructieonderdeel mapping
CONSTRUCTIE_ONDERDELEN_VLOER = ["vloer"]
CONSTRUCTIE_ONDERDELEN_ONDERBOUW = [
    "ligger",
    "planken",
    "kesp",
    "deksloof",
    "watersloof",
    "paal",
    "palen",
    "schuifhout",
    "opsluitklos",
    "grondkerend",
]
CONSTRUCTIE_ONDERDELEN_BOVENBOUW = [
    "metsel",
    "deksteen",
    "natuursteen",
    "wand",
]
CONSTRUCTIE_ONDERDELEN_ONDERLOOPSHEIDSCHERM = ["onderloop"]
