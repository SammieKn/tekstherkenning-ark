from pydantic import BaseModel

from tekstherkenning_ark.enums import MateriaalOnderbouw, MateriaalVloer, NietBeschikbaar
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.models.onderloopsheidscherm import Onderloopsheidscherm
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.vloer import Vloer
from tekstherkenning_ark.models.gebrek import Gebrek


class Onderbouw(BaseModel):
    """Object met alle eigenschappen van de onderbouw van het rakdeel.

    Attributes:
        kespen: Lijst van onderzochte kespen onder het rakdeel.
        onderloopsheidscherm: Onderloopsheidscherm van de onderbouw.
        palen: Lijst van palen onder het rakdeel.
        vloer: Vloer van de onderbouw.
        materiaal: Materiaal van de onderbouw (bijvoorbeeld hout, beton, staal).
    """

    # Te vinden in de meettabel kespen (Bijlage 3).
    kespen: list[Kesp]
    # Elke paalrij bevat de bijbehorende palen. Te vinden in de meettabel funderingspalen (Bijlage 3).
    palen: list[Paal]

    vloer: Vloer | None = None
    onderloopsheidscherm: Onderloopsheidscherm | None = None

    # Af te leiden uit de constructiebeschrijving (paragraaf 5.x) of doorsnedetekening.
    materiaal: MateriaalOnderbouw | NietBeschikbaar = NietBeschikbaar.LEEG

    @property
    def alle_gebreken(self) -> list[Gebrek]:
        """Verzamelt alle gebreken uit de onderbouw onderdelen.

        Returns:
            list[Gebrek]: Lijst van alle gebreken in de onderbouw.
        """
        gebreken = []

        for paal in self.palen:
            gebreken.extend(paal.gebreken)

        for kesp in self.kespen:
            gebreken.extend(kesp.gebreken)

        if self.vloer:
            gebreken.extend(self.vloer.gebreken)

        if self.onderloopsheidscherm:
            gebreken.extend(self.onderloopsheidscherm.gebreken)

        return gebreken
