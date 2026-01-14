from pydantic import BaseModel


class Gebrek(BaseModel):
    """Model representing a 'gebrek' (deficiency or issue)."""

    locatie_meter: int
    codering: str
    omschrijving: str
