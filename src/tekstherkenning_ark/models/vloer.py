from __future__ import annotations

from tekstherkenning_ark.enums import MateriaalVloer, NietBeschikbaar
from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.rak_base_model import RakBaseModel

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving


class Vloer(RakBaseModel):
    """Vloer.

    Attributes:
        is_beschadigd: Indicatie of de vloer beschadigd is.
        materiaal: Materiaal van de vloer (bijvoorbeeld hout, beton).
        bovenkant_vloer_cm_tov_nap: Hoogte van de bovenkant van de vloer ten opzichte van NAP, in centimeters.
        is_meerdere_locaties: Indicatie of de schade aan de vloer op meerdere locaties voorkomt.
        gebreken: Lijst van gebreken (inherited from RakBaseModel).
        opmerkingen: Eventuele opmerkingen (inherited from RakBaseModel).
    """

    # Af te leiden uit de constructiebeschrijving (paragraaf 5.x) of doorsnedetekening.
    materiaal: MateriaalVloer | NietBeschikbaar
    # Te vinden in de constructiebeschrijving (paragraaf 5.x) of af te leiden uit de doorsnedetekening.
    bovenkant_vloer_cm_tov_nap: float | None = None
    # Te vinden in de uitleg bij het algemene gebrek in de gebrekentabel (paragraaf 2.3 of 5.3.3).
    is_meerdere_locaties: bool | None = None

    @property
    def is_beschadigd(self) -> bool:
        heeft_gebrek = bool(self.gebreken)
        is_beschadigd = any(toestand.aangetast for toestand in self.toestand_onderdelen)
        return heeft_gebrek or is_beschadigd

    @property
    def identifier(self) -> str:
        """Return a string that uniquely identifies this Vloer instance."""
        return "vloer"

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
