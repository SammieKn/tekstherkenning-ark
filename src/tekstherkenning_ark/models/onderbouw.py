from pydantic import BaseModel, Field

from .kesp import Kesp
from .onderloopsheidscherm import Onderloopsheidscherm
from .paalrij import PaalRij
from .vloer import Vloer


class Onderbouw(BaseModel):
    """Object met alle eigenschappen van de onderbouw van het rakdeel.

    Onderbouw
    """

    # Te vinden in de meettabel kespen (Bijlage 3).
    kespen: list[Kesp] = Field(description="Lijst van onderzochte kespen onder het rakdeel.")
    onderloopsheidscherm: Onderloopsheidscherm
    # Elke paalrij bevat de bijbehorende palen. Te vinden in de meettabel funderingspalen (Bijlage 3).
    paalrijen: list[PaalRij] = Field(description="Lijst van paalrijen onder het rakdeel.")
    vloer: Vloer
    # Af te leiden uit de constructiebeschrijving (paragraaf 5.x) of doorsnedetekening.
    materiaal: str | None = Field(
        default=None,
        description="Materiaal van de onderbouw (bijvoorbeeld hout, beton, staal).",
    )
    # Te vinden in de tekst van de constructiebeschrijving, meettabellen of gebrekentabel.
    opmerkingen: str | None = Field(default=None, description="Eventuele aanvullende opmerkingen over de onderbouw.")
