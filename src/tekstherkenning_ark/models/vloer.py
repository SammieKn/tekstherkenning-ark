from pydantic import BaseModel, Field

from .gebrek import Gebrek


class Vloer(BaseModel):
    """Vloer"""

    # Te vinden in de gebrekentabel (paragraaf 2.3 of 5.3.3) als 'algemeen' gebrek.
    is_beschadigd: bool = Field(description="Indicatie of de vloer beschadigd of kierend is.")
    gebreken: list[Gebrek]
    # Af te leiden uit de constructiebeschrijving (paragraaf 5.x) of doorsnedetekening.
    materiaal: str = Field(description="Materiaal van de vloer (bijvoorbeeld hout, beton).")
    # Te vinden in de constructiebeschrijving (paragraaf 5.x) of af te leiden uit de doorsnedetekening.
    bovenkant_deksteen_cm_tov_nap: float | None = Field(
        default=None,
        description="Hoogte van de bovenkant van de deksteen ten opzichte van NAP, in centimeters.",
    )
    # Te vinden in de constructiebeschrijving (paragraaf 5.x) of af te leiden uit de doorsnedetekening.
    bovenkant_vloer_cm_tov_nap: float | None = Field(
        default=None,
        description="Hoogte van de bovenkant van de vloer ten opzichte van NAP, in centimeters.",
    )
    # Te vinden in de uitleg bij het algemene gebrek in de gebrekentabel (paragraaf 2.3 of 5.3.3).
    is_meerdere_locaties: bool | None = Field(
        default=None,
        description="Indicatie of de schade aan de vloer op meerdere locaties voorkomt.",
    )
    # Te vinden in de tekst van de constructiebeschrijving of de gebrekentabel.
    opmerkingen: str | None = Field(default=None, description="Eventuele aanvullende opmerkingen over de vloer.")
