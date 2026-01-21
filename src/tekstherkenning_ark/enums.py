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


class SchoorStand(Enum):
    POSITIEF = "PNV"
    NEGATIEF = "PNA"
    NEUTRAAL = "LR"


class NietBeschikbaar(Enum):
    NIET_VAN_TOEPASSING = "NVT"
    NIET_MEETBAAR = "NM"
    LEEG = ""


class AansluitingStatus(Enum):
    """Status van de aansluiting paal-kesp of paal-vloer. Te vinden in de meettabel
    funderingspalen, Bijlage 3, kolom 'Aansluiting'.
    """

    GOED = "G"
    NIET_MEETBAAR = "NM"
    SLECHT = "S"
