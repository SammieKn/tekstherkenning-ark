from pydantic import BaseModel, Field

from .gebrek import Gebrek


class Metselwerk(BaseModel):
    """Metselwerk, Object met alle eigenschappen van het metselwerk. Gegevens uit de
    constructiebeschrijving, toestandstabel en gebrekentabel.
    """

    gebreken: list[Gebrek]
    # Te vinden in de constructiebeschrijving of doorsnedetekening.
    is_banden_aanwezig: bool | None = Field(
        default=None,
        description="Indicatie of er banden (bijvoorbeeld natuursteen banden) in het metselwerk aanwezig zijn.",
    )
    # Te vinden in de constructiebeschrijving of doorsnedetekening.
    dikte_cm: float | None = Field(default=None, description="Dikte van het metselwerk in centimeters.")
    # Te vinden in de constructiebeschrijving of doorsnedetekening.
    hoogte_cm: float | None = Field(default=None, description="Hoogte van het metselwerk in centimeters.")
    # Te vinden in de tekst van de constructiebeschrijving of de gebrekentabel.
    opmerkingen: str | None = Field(default=None, description="Eventuele aanvullende opmerkingen over het metselwerk.")
    # Af te leiden uit de constructiebeschrijving of doorsnedetekening.
    type_metselwerk: str | None = Field(
        default=None,
        description="Type metselwerk (bijvoorbeeld halfsteens, kruisverband, etc.).",
    )
