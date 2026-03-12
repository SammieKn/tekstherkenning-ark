from __future__ import annotations

from pydantic import computed_field

from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.rak_base_model import RakBaseModel

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving


class Onderloopsheidscherm(RakBaseModel):
    """Onderloopsheidscherm.

    Attributes:
        is_meerdere_locaties: Indicatie of de schade aan het onderloopsheidscherm op meerdere locaties voorkomt.
        gebreken: Lijst van gebreken (inherited from RakBaseModel).
        opmerkingen: Eventuele opmerkingen (inherited from RakBaseModel).

    Properties (berekend):
        is_beschadigd: Indicatie of het onderloopsheidscherm beschadigd is.
    """

    # Te vinden in de uitleg bij het algemene gebrek in de gebrekentabel (paragraaf 2.3 of 5.3.3).
    is_meerdere_locaties: bool | None = None  # TODO

    @computed_field
    @property
    def is_beschadigd(self) -> bool:
        heeft_gebrek = bool(self.gebreken)
        is_beschadigd = any(toestand.aangetast for toestand in self.toestand_onderdelen)
        return heeft_gebrek or is_beschadigd

    @property
    def identifier(self) -> str:
        """Return a string that uniquely identifies this Onderloopsheidscherm instance."""
        return "onderloopsheidscherm"

    @classmethod
    def from_rakdeel_omschrijving(cls, omschrijving: RakdeelOmschrijving) -> Onderloopsheidscherm | None:
        """Genereer een Onderloopsheidscherm model vanuit een RakdeelOmschrijving model.

        Args:
            omschrijving (RakdeelOmschrijving): Het RakdeelOmschrijving model.

        Returns:
            Onderloopsheidscherm | None: Een leeg Onderloopsheidscherm model, of None als er geen onderloopsheidscherm is.
        """

        if omschrijving.onderloopsheidscherm:
            return cls()

        return None
