from enum import Enum


class AansluitingStatus(Enum):
    """Status van de aansluiting paal-kesp of paal-vloer. Te vinden in de meettabel
    funderingspalen, Bijlage 3, kolom 'Aansluiting'.
    """

    GOED = "GOED"
    NIET_MEETBAAR = "NIET_MEETBAAR"
    SLECHT = "SLECHT"
