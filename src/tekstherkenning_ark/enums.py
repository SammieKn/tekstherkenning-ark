from typing import Literal
from tekstherkenning_ark.flexibele_enum import FlexibeleEnum


class MateriaalFundering(FlexibeleEnum):
    """Afkomstig uit `ark-automatiseren/app/Segment/segment_parametrization.py`"""

    HOUT = "Hout"
    STAAL = "Staal"
    BETON = "Beton"


class MateriaalOnderbouw(FlexibeleEnum):
    """Afkomstig uit `ark-automatiseren/app/Segment/segment_parametrization.py`"""

    HOUT = "Hout"
    STAAL = "Staal"
    BETON = "Beton"


class MateriaalBovenbouw(FlexibeleEnum):
    """Afkomstig uit `ark-automatiseren/app/Segment/segment_parametrization.py`"""

    METSELWERK = "Metselwerk"
    BASALT = "Basalt"
    BETON_METSELWERK = "Beton+Metselwerk"
    BETON_BASALT = "Beton+Basalt"
    BETON = "Beton"


class MateriaalVloer(FlexibeleEnum):
    """Afkomstig uit `ark-automatiseren/app/Segment/segment_parametrization.py`"""

    ONBEKEND = "Onbekend"
    HOUT = "Hout"
    BETON = "Beton"


class SchoorStand(FlexibeleEnum):
    POSITIEF = "PNV"
    NEGATIEF = "PNA"
    NEUTRAAL = "LR"
    TO_DO_REMOVE_PNL = "PNL"  # TODO Verwijderen indien niet meer gebruikt


class NietBeschikbaar(FlexibeleEnum):
    NIET_VAN_TOEPASSING = "NVT"
    NIET_MEETBAAR = "NM"
    LEEG = ""

    def __bool__(self):
        """Niet beschikbaar waarden worden als False beschouwd in een boolean context, net als None, lege string, etc."""
        return False

    def default_comparison_behavior(self, other) -> bool:
        """Vergelijkingen met float altijd True maken om validatie van velden mogelijk te maken"""

        if isinstance(other, (int, float)):
            return True  # NietBeschikbaar wordt als gelijk aan elke meetbare waarde beschouwd
        return False  # Voor andere types, gebruik de standaard vergelijking

    def __gt__(self, other):
        return self.default_comparison_behavior(other)

    def __lt__(self, other):
        return self.default_comparison_behavior(other)

    def __ge__(self, other):
        return self.default_comparison_behavior(other)

    def __le__(self, other):
        return self.default_comparison_behavior(other)


class AansluitingStatus(FlexibeleEnum):
    """Status van de aansluiting paal-kesp of paal-vloer. Te vinden in de meettabel
    funderingspalen, Bijlage 3, kolom 'Aansluiting'.
    """

    GOED = "G"
    NIET_MEETBAAR = "NM"
    SLECHT = "S"
