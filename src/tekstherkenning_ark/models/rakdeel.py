from pydantic import BaseModel

from .bovenbouw import Bovenbouw
from .gebrek import Gebrek
from .onderbouw import Onderbouw


class Rakdeel(BaseModel):
    """Rakdeel.

    Attributes:
        bovenbouw: Object met alle eigenschappen van de bovenbouw van het rakdeel.
        constructietype: Type constructie van het rakdeel (bijvoorbeeld houten paalfundering, betonnen L-wand, etc.).
        gebreken: Lijst van gebreken in het rakdeel.
        lengte_m: Lengte van het rakdeel in meters.
        onderbouw: Object met alle eigenschappen van de onderbouw van het rakdeel.
        rakdeel_id: Unieke identificatie van het rakdeel, bijvoorbeeld 'Constructie A' of 'Constructie B'.
        bouwjaar: Bouwjaar van het rakdeel.
        opmerkingen: Eventuele aanvullende opmerkingen over het rakdeel.
    """

    bovenbouw: Bovenbouw
    # Te vinden in paragraaf 5.x, eerste alinea.
    constructietype: str

    gebreken: list[Gebrek]
    # Te vinden in paragraaf 5.x, eerste zin.
    lengte_m: float
    onderbouw: Onderbouw
    # Te vinden in paragraaf 5.x, kopregel of inhoudsopgave.
    rakdeel_id: str
    # Te vinden in paragraaf 5.1 of af te leiden uit de constructiebeschrijving.
    bouwjaar: int | None = None
    # Te vinden in de tekst van de constructiebeschrijving of samenvatting.
    opmerkingen: str | None = None
