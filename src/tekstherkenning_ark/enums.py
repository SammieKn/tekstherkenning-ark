from enum import Enum


class FlexibeleEnum(Enum):
    """Base class voor enums die case-insensitive matching en input opschoning ondersteunen."""

    @classmethod
    def _missing_(cls, value: object):
        """Wordt aangeroepen als de standaard lookup faalt.

        Probeert de waarde te matchen na opschoning en case-insensitive vergelijking.
        """
        if not isinstance(value, str):
            return None

        # Opschonen: strip whitespace
        schone_waarde = value.strip()

        # Probeer exacte match na strip
        for member in cls:
            if member.value == schone_waarde:
                return member

        # Probeer case-insensitive match
        schone_waarde_lower = schone_waarde.lower()
        for member in cls:
            if member.value.lower() == schone_waarde_lower:
                return member

        # Probeer ook op naam (bijv. "HOUT" -> MateriaalFundering.HOUT)
        schone_waarde_upper = schone_waarde.upper()
        for member in cls:
            if member.name == schone_waarde_upper:
                return member

        return None


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


class AansluitingStatus(FlexibeleEnum):
    """Status van de aansluiting paal-kesp of paal-vloer. Te vinden in de meettabel
    funderingspalen, Bijlage 3, kolom 'Aansluiting'.
    """

    GOED = "G"
    NIET_MEETBAAR = "NM"
    SLECHT = "S"
