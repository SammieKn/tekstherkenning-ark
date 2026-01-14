from pydantic import BaseModel, Field

from .rakdeel import Rakdeel


class Rak(BaseModel):
    """Rak"""

    # Elk rakdeel heeft een eigen constructietype.
    rakdelen: list[Rakdeel] = Field(description="Lijst van rakdelen waaruit het rak is opgebouwd.")
    # Te vinden in de rapporttitel, projectgegevens of paragraaf 2.2.1 (paspoortgegevens).
    raknaam: str = Field(description="Naam of code van het rak.")
    # Te vinden in paragraaf 2.2.1 (paspoortgegevens) en/of de constructiebeschrijving (eerste zin van paragraaf 5.x).
    totale_lengte_m: float = Field(description="Totale lengte van het rak in meters.")
    # Te vinden in de samenvatting, inleiding of slotbeschouwing van het rapport.
    opmerkingen: str | None = Field(
        default=None,
        description="Eventuele aanvullende opmerkingen over het gehele rak.",
    )
