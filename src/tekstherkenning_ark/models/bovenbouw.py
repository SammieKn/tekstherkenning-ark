from pydantic import BaseModel

from tekstherkenning_ark.enums import MateriaalBovenbouw, NietBeschikbaar
from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.metselwerk import Metselwerk


class Bovenbouw(BaseModel):
    """Object met alle eigenschappen van de bovenbouw van het rakdeel.

    Attributes:
        metselwerk: Object met alle eigenschappen van het metselwerk.
        is_buik_in_wand_aanwezig: Indicatie of er een buik in de wand aanwezig is.
        is_grondvoerend_gat_aanwezig: Indicatie of er een grondvoerend gat aanwezig is.
        is_lokaal_verdwenen_metselwerk: Indicatie of er lokaal metselwerk verdwenen is.
        materiaal: Materiaal van de bovenbouw (bijvoorbeeld metselwerk, beton, natuursteen).
        maximaal_aantal_scheuren_per_10_m: Maximaal aantal scheuren per 10 meter in het metselwerk.
        maximale_scheurwijdte_mm: Maximale scheurwijdte in het metselwerk, in millimeters.
        opmerkingen: Eventuele aanvullende opmerkingen over de bovenbouw.
        percentage_niet_functionerend_schuifhout: Percentage van het schuifhout dat niet functioneert.
        is_scheefstand_aanwezig: Indicatie of er scheefstand van de wand aanwezig is.
        bovenkant_deksteen_cm_tov_nap: Hoogte van de bovenkant van de deksteen ten opzichte van NAP, in centimeters.
    """

    metselwerk: Metselwerk | None = None
    # Te vinden in de gebrekentabel (paragraaf 2.3 of 5.3.3) als 'algemeen' gebrek.
    is_buik_in_wand_aanwezig: bool | None = None
    # Te vinden in de gebrekentabel (paragraaf 2.3 of 5.3.3) als 'algemeen' gebrek.
    is_grondvoerend_gat_aanwezig: bool | None = None
    # Te vinden in de gebrekentabel (paragraaf 2.3 of 5.3.3) als 'GBx' met omschrijving 'lokaal verdwenen metselwerk'.
    is_lokaal_verdwenen_metselwerk: bool | None = None
    # Af te leiden uit de constructiebeschrijving (paragraaf 5.x) of doorsnedetekening.
    materiaal: MateriaalBovenbouw | NietBeschikbaar = NietBeschikbaar.LEEG
    # Te bepalen uit de gebrekentabel (paragraaf 2.3 of 5.3.3) door het aantal scheuren te tellen en te relateren aan de lengte van het rakdeel.
    maximaal_aantal_scheuren_per_10_m: int | None = None
    # Te vinden in de gebrekentabel (paragraaf 2.3 of 5.3.3), kolom 'Omschrijving', vaak als 'SW'.
    maximale_scheurwijdte_mm: float | None = None
    # Te vinden in de tekst van de constructiebeschrijving of de gebrekentabel.
    opmerkingen: str = ""
    # Af te leiden uit de doorsnedetekening en de toestandstabel (figuur 1.11) en de gebrekentabel (paragraaf 2.3 of 5.3.3).
    percentage_niet_functionerend_schuifhout: float | None = None
    # Te vinden in de gebrekentabel (paragraaf 2.3 of 5.3.3) als 'algemeen' gebrek.
    is_scheefstand_aanwezig: bool | None = None
    # Te vinden in de constructiebeschrijving (paragraaf 5.x) of af te leiden uit de doorsnedetekening.
    bovenkant_deksteen_cm_tov_nap: float | None = None

    gebreken: list[Gebrek] = []

    @property
    def alle_gebreken(self) -> list[Gebrek]:
        """Geef een lijst van alle gebreken in de bovenbouw, inclusief die in het metselwerk.

        Returns:
            list[Gebrek]: Lijst van alle gebreken in de bovenbouw.
        """
        alle_gebreken = self.gebreken.copy()
        if self.metselwerk:
            alle_gebreken.extend(self.metselwerk.gebreken)
        return alle_gebreken
