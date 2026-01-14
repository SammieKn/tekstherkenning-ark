from pydantic import BaseModel, Field

from .gebrek import Gebrek


class Onderloopsheidscherm(BaseModel):
    """Onderloopsheidscherm"""

    # Te vinden in de constructiebeschrijving (paragraaf 5.x) of op de archieftekening.
    is_aanwezig: bool = Field(description="Indicatie of er een onderloopsheidscherm aanwezig is.")
    gebrek: Gebrek
    # Te vinden in de toestandstabel (figuur 1.11) of als 'algemeen' gebrek in de gebrekentabel (paragraaf 2.3 of 5.3.3).
    is_beschadigd: bool | None = Field(
        default=None,
        description="Indicatie of het onderloopsheidscherm beschadigd is (op meerdere plekken).",
    )
    # Te vinden in de uitleg bij het algemene gebrek in de gebrekentabel (paragraaf 2.3 of 5.3.3).
    is_meerdere_locaties: bool | None = Field(
        default=None,
        description="Indicatie of de schade aan het onderloopsheidscherm op meerdere locaties voorkomt.",
    )
    # Te vinden in de tekst van de constructiebeschrijving of de gebrekentabel.
    opmerkingen: str | None = Field(
        default=None,
        description="Eventuele aanvullende opmerkingen over het onderloopsheidscherm.",
    )
