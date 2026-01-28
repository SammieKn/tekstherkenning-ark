from __future__ import annotations

from pydantic import BaseModel

from tekstherkenning_ark.enums import MateriaalVloer
from tekstherkenning_ark.models.gebrek import Gebrek

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving


class Vloer(BaseModel):
    """Vloer.

    Attributes:
        is_beschadigd: Indicatie of de vloer beschadigd of kierend is.
        gebreken: Lijst van gebreken in de vloer.
        materiaal: Materiaal van de vloer (bijvoorbeeld hout, beton).
        bovenkant_vloer_cm_tov_nap: Hoogte van de bovenkant van de vloer ten opzichte van NAP, in centimeters.
        is_meerdere_locaties: Indicatie of de schade aan de vloer op meerdere locaties voorkomt.
        opmerkingen: Eventuele aanvullende opmerkingen over de vloer.
    """

    # Te vinden in de gebrekentabel (paragraaf 2.3 of 5.3.3) als 'algemeen' gebrek.
    is_beschadigd: bool | None = None
    gebreken: list[Gebrek] = []

    # Af te leiden uit de constructiebeschrijving (paragraaf 5.x) of doorsnedetekening.
    materiaal: MateriaalVloer

    # Te vinden in de constructiebeschrijving (paragraaf 5.x) of af te leiden uit de doorsnedetekening.
    bovenkant_vloer_cm_tov_nap: float | None = None
    # Te vinden in de uitleg bij het algemene gebrek in de gebrekentabel (paragraaf 2.3 of 5.3.3).
    is_meerdere_locaties: bool | None = None

    # Te vinden in de tekst van de constructiebeschrijving of de gebrekentabel.
    opmerkingen: str = ""

    @classmethod
    def from_rakdeel_omschrijving(cls, omschrijving: RakdeelOmschrijving) -> Vloer:
        """Genereer een Vloer model vanuit een RakdeelOmschrijving model.

        Args:
            omschrijving (RakdeelOmschrijving): Het RakdeelOmschrijving model.

        Returns:
            Vloer: Het gegenereerde Vloer model.
        """
        return cls(
            materiaal=omschrijving.materiaal_vloer,
            bovenkant_vloer_cm_tov_nap=omschrijving.bovenkant_vloer_cm,
        )
