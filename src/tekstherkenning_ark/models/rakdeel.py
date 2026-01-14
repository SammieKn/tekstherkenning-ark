from pydantic import BaseModel, Field

from .bovenbouw import Bovenbouw
from .gebrek import Gebrek
from .onderbouw import Onderbouw


class Rakdeel(BaseModel):
    """Rakdeel"""

    bovenbouw: Bovenbouw = Field(description="Object met alle eigenschappen van de bovenbouw van het rakdeel.")
    # Te vinden in paragraaf 5.x, eerste alinea.
    constructietype: str = Field(
        description="Type constructie van het rakdeel (bijvoorbeeld houten paalfundering, betonnen L-wand, etc.)."
    )
    gebreken: list[Gebrek]
    # Te vinden in paragraaf 5.x, eerste zin.
    lengte_m: float = Field(description="Lengte van het rakdeel in meters.")
    onderbouw: Onderbouw = Field(description="Object met alle eigenschappen van de onderbouw van het rakdeel.")
    # Te vinden in paragraaf 5.x, kopregel of inhoudsopgave.
    rakdeel_id: str = Field(
        description="Unieke identificatie van het rakdeel, bijvoorbeeld 'Constructie A' of 'Constructie B'."
    )
    # Te vinden in paragraaf 5.1 of af te leiden uit de constructiebeschrijving.
    bouwjaar: int | None = Field(default=None, description="Bouwjaar van het rakdeel.")
    # Te vinden in de tekst van de constructiebeschrijving of samenvatting.
    opmerkingen: str | None = Field(default=None, description="Eventuele aanvullende opmerkingen over het rakdeel.")
