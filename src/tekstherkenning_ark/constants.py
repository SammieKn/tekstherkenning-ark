"""
Constants - but they can be sneakily overruled if os.environ has the same variable name. This is useful for testing.
"""

import os
from pathlib import Path

ROOT_DIR = Path(os.getenv("ROOT_DIR", Path(__file__).parent.parent.parent))
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT_DIR / "data"))
CACHE_DIR = Path(os.getenv("CACHE_DIR", DATA_DIR / ".cache"))

CACHE_DIR.mkdir(parents=True, exist_ok=True)

TEST_PDF_PATH = Path(
    os.getenv("TEST_PDF_PATH", DATA_DIR / "HEG0801_Houtmonstername&VisueleInspectie_V1.1_20220311.pdf")
)
