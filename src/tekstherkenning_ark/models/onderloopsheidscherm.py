from pydantic import BaseModel

from tekstherkenning_ark.models.gebrek import Gebrek


class Onderloopsheidscherm(BaseModel):
    """Onderloopsheidscherm.

    Attributes:
        is_aanwezig: Indicatie of er een onderloopsheidscherm aanwezig is.
        gebrek: Gebrek aan het onderloopsheidscherm.
        is_beschadigd: Indicatie of het onderloopsheidscherm beschadigd is (op meerdere plekken).
        is_meerdere_locaties: Indicatie of de schade aan het onderloopsheidscherm op meerdere locaties voorkomt.
        opmerkingen: Eventuele aanvullende opmerkingen over het onderloopsheidscherm.
    """

    # Te vinden in de constructiebeschrijving (paragraaf 5.x) of op de archieftekening.
    is_aanwezig: bool
    gebreken: list[Gebrek] = []
    # Te vinden in de toestandstabel (figuur 1.11) of als 'algemeen' gebrek in de gebrekentabel (paragraaf 2.3 of 5.3.3).
    is_beschadigd: bool | None = None
    # Te vinden in de uitleg bij het algemene gebrek in de gebrekentabel (paragraaf 2.3 of 5.3.3).
    is_meerdere_locaties: bool | None = None
    # Te vinden in de tekst van de constructiebeschrijving of de gebrekentabel.
    opmerkingen: str = ""
