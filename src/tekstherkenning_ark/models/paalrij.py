from pydantic import BaseModel, Field

from .paal import Paal


class PaalRij(BaseModel):
    """PaalRij"""

    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalrij'.
    paalrij_nummer: str = Field(description="Uniek nummer of code van de paalrij.")
    # Elke paal wordt beschreven in de meettabel funderingspalen, Bijlage 3.
    palen: list[Paal] = Field(description="Lijst van palen die tot deze paalrij behoren.")
