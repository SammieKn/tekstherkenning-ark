from pydantic import BaseModel

from .paal import Paal


class PaalRij(BaseModel):
    """PaalRij.

    Attributes:
        paalrij_nummer: Uniek nummer of code van de paalrij.
        palen: Lijst van palen die tot deze paalrij behoren.
    """

    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalrij'.
    paalrij_nummer: str
    # Elke paal wordt beschreven in de meettabel funderingspalen, Bijlage 3.
    palen: list[Paal]
