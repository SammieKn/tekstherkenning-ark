from enum import Enum


class Materiaal(Enum):
    """Materiaaltype"""

    HOUT = "hout"
    BETON = "beton"
    STAAL = "staal"


class BovenbouwMateriaal(Enum):
    """Materiaaltype voor bovenbouw"""

    MESTELWERK = "Metselwerk"
    BASALT = "Basalt"
    BETON_MESTELWERK = "Beton+Metselwerk"
    BETON_BASALT = "Beton+Basalt"
    BETON = "Beton"
