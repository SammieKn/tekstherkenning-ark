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
