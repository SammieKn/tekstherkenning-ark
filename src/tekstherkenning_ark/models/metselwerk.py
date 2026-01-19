from pydantic import BaseModel

from .gebrek import Gebrek


class Metselwerk(BaseModel):
    """Metselwerk, Object met alle eigenschappen van het metselwerk.

    Gegevens uit de constructiebeschrijving, toestandstabel en gebrekentabel.

    Attributes:
        gebreken: Lijst van gebreken in het metselwerk.
        is_banden_aanwezig: Indicatie of er banden (bijvoorbeeld natuursteen banden) in het metselwerk aanwezig zijn.
        dikte_cm: Dikte van het metselwerk in centimeters.
        hoogte_cm: Hoogte van het metselwerk in centimeters.
        opmerkingen: Eventuele aanvullende opmerkingen over het metselwerk.
        type_metselwerk: Type metselwerk (bijvoorbeeld halfsteens, kruisverband, etc.).
    """

    gebreken: list[Gebrek]
    # Te vinden in de constructiebeschrijving of doorsnedetekening.
    is_banden_aanwezig: bool | None = None
    # Te vinden in de constructiebeschrijving of doorsnedetekening.
    dikte_cm: float | None = None
    # Te vinden in de constructiebeschrijving of doorsnedetekening.
    hoogte_cm: float | None = None
    # Te vinden in de tekst van de constructiebeschrijving of de gebrekentabel.
    opmerkingen: str | None = None
    # Af te leiden uit de constructiebeschrijving of doorsnedetekening.
    type_metselwerk: str | None = None
