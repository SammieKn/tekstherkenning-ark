from pydantic import BaseModel


class Gebrek(BaseModel):
    """Model representing a 'gebrek' (deficiency or issue).

    Attributes:
        locatie_meter: Locatie van het gebrek in meters.
        codering: Codering van het gebrek.
        omschrijving: Omschrijving van het gebrek.
    """
    codering: str
    omschrijving: str
    figuurnummer: list[str]


class Scheur(Gebrek):
    """Scheur (crack). 

    Attributes:
        lengte_cm: Lengte van de scheur in centimeters.
        scheurwijdte_mm: Maximale scheurwijdte in millimeters.
    """

    # Te vinden in de omschrijving van de gebrekentabel.
    lengte_cm: int
    # Te vinden in de omschrijving van de gebrekentabel, vaak als 'SW'.
    scheurwijdte_mm: int


class GrondVoerendGat(Gebrek):
    """Grondvoerend gat.

    Attributes:
        afmetingen_cm: Afmetingen van het gat in centimeters (b x h x d).
    """

    # Te vinden in de omschrijving van de gebrekentabel.
    afmetingen_cm: list[int | None]


class BuikInWand(Gebrek):
    """Buik in wand.

    Attributes:
        uitbuiging_cm: Mate van uitbuiging in centimeters.
    """

    # Te vinden in de omschrijving van de gebrekentabel.
    uitbuiking_cm: int


class Scheefstand(Gebrek):
    """Scheefstand.

    Attributes:
        hoek_graden: Hoek van de scheefstand in graden.
    """

    # Te vinden in de omschrijving van de gebrekentabel indien vermeld.
    hoek_graden: int


class LokaalVerdwenenMetselwerk(Gebrek):
    """Lokaal verdwenen metselwerk.

    Attributes:
        afmetingen_cm: Afmetingen van het verdwenen metselwerk in centimeters (b x h x d).
    """

    # Te vinden in de omschrijving van de gebrekentabel.
    afmetingen_cm: list[int | None]
