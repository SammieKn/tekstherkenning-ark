from enum import Enum

class SchoorStand(Enum):
    POSITIEF = "PNV"
    NEGATIEF = "PNA"
    NEUTRAAL = "LR"

class NietBeschikbaar(Enum):
    NIET_VAN_TOEPASSING = "NVT"
    NIET_MEETBAAR = "NMB"