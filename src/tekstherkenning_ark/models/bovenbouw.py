from pydantic import BaseModel, Field

from .metselwerk import Metselwerk


class Bovenbouw(BaseModel):
    """Object met alle eigenschappen van de bovenbouw van het rakdeel.

    Bovenbouw
    """

    metselwerk: Metselwerk
    # Te vinden in de gebrekentabel (paragraaf 2.3 of 5.3.3) als 'algemeen' gebrek.
    is_buik_in_wand_aanwezig: bool | None = Field(
        default=None, description="Indicatie of er een buik in de wand aanwezig is."
    )
    # Te vinden in de gebrekentabel (paragraaf 2.3 of 5.3.3) als 'algemeen' gebrek.
    is_grondvoerend_gat_aanwezig: bool | None = Field(
        default=None, description="Indicatie of er een grondvoerend gat aanwezig is."
    )
    # Te vinden in de gebrekentabel (paragraaf 2.3 of 5.3.3) als 'GBx' met omschrijving 'lokaal verdwenen metselwerk'.
    is_lokaal_verdwenen_metselwerk: bool | None = Field(
        default=None, description="Indicatie of er lokaal metselwerk verdwenen is."
    )
    # Af te leiden uit de constructiebeschrijving (paragraaf 5.x) of doorsnedetekening.
    materiaal: str | None = Field(
        default=None,
        description="Materiaal van de bovenbouw (bijvoorbeeld metselwerk, beton, natuursteen).",
    )
    # Te bepalen uit de gebrekentabel (paragraaf 2.3 of 5.3.3) door het aantal scheuren te tellen en te relateren aan de lengte van het rakdeel.
    maximaal_aantal_scheuren_per_10_m: int | None = Field(
        default=None,
        description="Maximaal aantal scheuren per 10 meter in het metselwerk.",
    )
    # Te vinden in de gebrekentabel (paragraaf 2.3 of 5.3.3), kolom 'Omschrijving', vaak als 'SW'.
    maximale_scheurwijdte_mm: float | None = Field(
        default=None,
        description="Maximale scheurwijdte in het metselwerk, in millimeters.",
    )
    # Te vinden in de tekst van de constructiebeschrijving of de gebrekentabel.
    opmerkingen: str | None = Field(default=None, description="Eventuele aanvullende opmerkingen over de bovenbouw.")
    # Af te leiden uit de doorsnedetekening en de toestandstabel (figuur 1.11) en de gebrekentabel (paragraaf 2.3 of 5.3.3).
    percentage_niet_functionerend_schuifhout: float | None = Field(
        default=None,
        description="Percentage van het schuifhout dat niet functioneert.",
    )
    # Te vinden in de gebrekentabel (paragraaf 2.3 of 5.3.3) als 'algemeen' gebrek.
    is_scheefstand_aanwezig: bool | None = Field(
        default=None, description="Indicatie of er scheefstand van de wand aanwezig is."
    )
