from pydantic import BaseModel

from .gebrek import Gebrek


class Vloer(BaseModel):
    """Vloer.

    Attributes:
        is_beschadigd: Indicatie of de vloer beschadigd of kierend is.
        gebreken: Lijst van gebreken in de vloer.
        materiaal: Materiaal van de vloer (bijvoorbeeld hout, beton).
        bovenkant_deksteen_cm_tov_nap: Hoogte van de bovenkant van de deksteen ten opzichte van NAP, in centimeters.
        bovenkant_vloer_cm_tov_nap: Hoogte van de bovenkant van de vloer ten opzichte van NAP, in centimeters.
        is_meerdere_locaties: Indicatie of de schade aan de vloer op meerdere locaties voorkomt.
        opmerkingen: Eventuele aanvullende opmerkingen over de vloer.
    """

    # Te vinden in de gebrekentabel (paragraaf 2.3 of 5.3.3) als 'algemeen' gebrek.
    is_beschadigd: bool
    gebreken: list[Gebrek]
    # Af te leiden uit de constructiebeschrijving (paragraaf 5.x) of doorsnedetekening.
    materiaal: str

    # Te vinden in de constructiebeschrijving (paragraaf 5.x) of af te leiden uit de doorsnedetekening.
    bovenkant_vloer_cm_tov_nap: float | None = None
    # Te vinden in de uitleg bij het algemene gebrek in de gebrekentabel (paragraaf 2.3 of 5.3.3).
    is_meerdere_locaties: bool | None = None
    # Te vinden in de tekst van de constructiebeschrijving of de gebrekentabel.
    opmerkingen: str | None = None
