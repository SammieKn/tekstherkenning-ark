from pydantic import BaseModel
from tekstherkenning_ark.models.gebrek import Gebrek, Scheur, GrondVoerendGat, BuikInWand


class Metselwerk(BaseModel):
    """Metselwerk, Object met alle eigenschappen van het metselwerk.

    Gegevens uit de constructiebeschrijving, toestandstabel en gebrekentabel.

    Attributes:
        gebreken: Lijst van gebreken in het metselwerk.
        dikte_cm: Dikte van het metselwerk in centimeters.
        hoogte_cm: Hoogte van het metselwerk in centimeters.
        opmerkingen: Eventuele aanvullende opmerkingen over het metselwerk.
    """

    gebreken: list[Gebrek] = []
    # Te vinden in de constructiebeschrijving of doorsnedetekening.
    dikte_cm: float | None = None
    # Te vinden in de constructiebeschrijving of doorsnedetekening.
    hoogte_cm: float | None = None
    # Te vinden in de tekst van de constructiebeschrijving of de gebrekentabel.
    opmerkingen: str | None = None
