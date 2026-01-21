from pydantic import BaseModel

from tekstherkenning_ark.models.rakdeel import Rakdeel


class Rak(BaseModel):
    """Rak.

    Attributes:
        rakdelen: Lijst van rakdelen waaruit het rak is opgebouwd.
        raknaam: Naam of code van het rak.
        totale_lengte_m: Totale lengte van het rak in meters.
        opmerkingen: Eventuele aanvullende opmerkingen over het gehele rak.
    """

    # Elk rakdeel heeft een eigen constructietype.
    rakdelen: list[Rakdeel]
    # Te vinden in de rapporttitel, projectgegevens of paragraaf 2.2.1 (paspoortgegevens).
    raknaam: str
    # Te vinden in paragraaf 2.2.1 (paspoortgegevens) en/of de constructiebeschrijving (eerste zin van paragraaf 5.x).
    totale_lengte_m: float
    # Te vinden in de samenvatting, inleiding of slotbeschouwing van het rapport.
    opmerkingen: str = ""
