from enum import Enum

class MateriaalFundering(Enum):
    """Afkomstig uit `ark-automatiseren/app/Segment/segment_parametrization.py`"""
    HOUT = "Hout"
    STAAL = "Staal"
    BETON = "Beton"

class MateriaalOnderbouw(Enum):
    """Afkomstig uit `ark-automatiseren/app/Segment/segment_parametrization.py`"""
    HOUT = "Hout"
    STAAL = "Staal"
    BETON = "Beton"

class MateriaalBovenbouw(Enum):
    """Afkomstig uit `ark-automatiseren/app/Segment/segment_parametrization.py`"""
    METSELWERK = "Metselwerk"
    BASALT = "Basalt"
    BETON_METSELWERK = "Beton+Metselwerk"
    BETON_BASALT = "Beton+Basalt"
    BETON = "Beton"

class MateriaalVloer(Enum):
    """Afkomstig uit `ark-automatiseren/app/Segment/segment_parametrization.py`"""
    ONBEKEND = "Onbekend"
    HOUT = "Hout"
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
