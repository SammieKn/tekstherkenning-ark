from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.rak_base_model import RakBaseModel


class Metselwerk(RakBaseModel):
    """Metselwerk, Object met alle eigenschappen van het metselwerk.

    Gegevens uit de constructiebeschrijving, toestandstabel en gebrekentabel.

    Attributes:
        dikte_cm: Dikte van het metselwerk in centimeters.
        hoogte_cm: Hoogte van het metselwerk in centimeters.
        gebreken: Lijst van gebreken (inherited from RakBaseModel).
        opmerkingen: Eventuele opmerkingen (inherited from RakBaseModel).
    """

    # Te vinden in de constructiebeschrijving of doorsnedetekening.
    dikte_cm: float | None = None
    # Te vinden in de constructiebeschrijving of doorsnedetekening.
    hoogte_cm: float | None = None

    @property
    def identifier(self) -> str:
        """Return a string that uniquely identifies this Metselwerk instance."""
        return "metselwerk"
