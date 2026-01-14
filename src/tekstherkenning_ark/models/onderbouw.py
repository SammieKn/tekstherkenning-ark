from pydantic import BaseModel

from tekstherkenning_ark.models.paal import Paal

from .kesp import Kesp
from .onderloopsheidscherm import Onderloopsheidscherm
from .vloer import Vloer


class Onderbouw(BaseModel):
    """Object met alle eigenschappen van de onderbouw van het rakdeel.

    Attributes:
        kespen: Lijst van onderzochte kespen onder het rakdeel.
        onderloopsheidscherm: Onderloopsheidscherm van de onderbouw.
        paalrijen: Lijst van paalrijen onder het rakdeel.
        vloer: Vloer van de onderbouw.
        materiaal: Materiaal van de onderbouw (bijvoorbeeld hout, beton, staal).
    """

    # Te vinden in de meettabel kespen (Bijlage 3).
    kespen: list[Kesp]
    onderloopsheidscherm: Onderloopsheidscherm
    # Elke paalrij bevat de bijbehorende palen. Te vinden in de meettabel funderingspalen (Bijlage 3).
    palen: list[Paal]
    vloer: Vloer
    # Af te leiden uit de constructiebeschrijving (paragraaf 5.x) of doorsnedetekening.
    materiaal: str | None = None
