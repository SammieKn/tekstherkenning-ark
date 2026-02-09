from tekstherkenning_ark.enums import MateriaalBovenbouw, NietBeschikbaar
from tekstherkenning_ark.models.gebrek import (
    BuikInWand,
    Gebrek,
    GrondVoerendGat,
    LokaalVerdwenenMetselwerk,
    Scheefstand,
    ScheurMetselwerk,
)
from tekstherkenning_ark.models.metselwerk import Metselwerk
from tekstherkenning_ark.models.rak_base_model import RakBaseModel


class Bovenbouw(RakBaseModel):
    """Object met alle eigenschappen van de bovenbouw van het rakdeel.

    Attributes:
        metselwerk: Object met alle eigenschappen van het metselwerk.
        materiaal: Materiaal van de bovenbouw (bijvoorbeeld metselwerk, beton, natuursteen).
        maximaal_aantal_scheuren_per_10_m: Maximaal aantal scheuren per 10 meter in het metselwerk.
        percentage_niet_functionerend_schuifhout: Percentage van het schuifhout dat niet functioneert.
        bovenkant_deksteen_cm_tov_nap: Hoogte van de bovenkant van de deksteen ten opzichte van NAP, in centimeters.
        gebreken: Lijst van gebreken (inherited from RakBaseModel).
        opmerkingen: Eventuele opmerkingen (inherited from RakBaseModel).

    Properties (berekend):
        totaal_aantal_scheuren: Totaal aantal scheuren in het metselwerk.
        maximale_scheurwijdte_mm: Grootste scheurwijdte uit alle ScheurMetselwerk gebreken.
        lijst_scheurwijdtes: Alle geconstateerde scheurwijdtes.
        is_buik_in_wand_aanwezig: Check of BuikInWand gebrek aanwezig is.
        is_grondvoerend_gat_aanwezig: Check of GrondVoerendGat gebrek aanwezig is.
        is_lokaal_verdwenen_metselwerk: Check of LokaalVerdwenenMetselwerk gebrek aanwezig is.
        is_scheefstand_aanwezig: Check of Scheefstand gebrek aanwezig is.
    """

    @property
    def identifier(self) -> str:
        """Return a string that uniquely identifies this Bovenbouw instance."""
        return "bovenbouw"

    @property
    def totaal_aantal_scheuren(self) -> int:
        """Totaal aantal scheuren in het metselwerk."""
        if self.metselwerk is None:
            return 0
        return sum(1 for gebrek in self.metselwerk.gebreken if isinstance(gebrek, ScheurMetselwerk))

    @property
    def maximale_scheurwijdte_mm(self) -> float | None:
        """Grootste scheurwijdte uit alle ScheurMetselwerk gebreken."""
        if self.metselwerk is None:
            return None

        scheurwijdtes = [
            gebrek.scheurwijdte_mm
            for gebrek in self.metselwerk.gebreken
            if isinstance(gebrek, ScheurMetselwerk) and isinstance(gebrek.scheurwijdte_mm, (int, float))
        ]
        return max(scheurwijdtes) if scheurwijdtes else None

    @property
    def lijst_scheurwijdtes(self) -> list[float]:
        """Alle geconstateerde scheurwijdtes voor analyse."""
        if self.metselwerk is None:
            return []

        return [
            float(gebrek.scheurwijdte_mm)
            for gebrek in self.metselwerk.gebreken
            if isinstance(gebrek, ScheurMetselwerk) and isinstance(gebrek.scheurwijdte_mm, (int, float))
        ]

    @property
    def is_buik_in_wand_aanwezig(self) -> bool:
        """Check of BuikInWand gebrek aanwezig is."""
        return any(isinstance(gebrek, BuikInWand) for gebrek in self.gebreken)

    @property
    def is_grondvoerend_gat_aanwezig(self) -> bool:
        """Check of GrondVoerendGat gebrek aanwezig is."""
        return any(isinstance(gebrek, GrondVoerendGat) for gebrek in self.gebreken)

    @property
    def is_lokaal_verdwenen_metselwerk(self) -> bool:
        """Check of LokaalVerdwenenMetselwerk gebrek aanwezig is."""
        return any(isinstance(gebrek, LokaalVerdwenenMetselwerk) for gebrek in self.gebreken)

    @property
    def is_scheefstand_aanwezig(self) -> bool:
        """Check of Scheefstand gebrek aanwezig is."""
        return any(isinstance(gebrek, Scheefstand) for gebrek in self.gebreken)

    metselwerk: Metselwerk | None = None
    # Af te leiden uit de constructiebeschrijving (paragraaf 5.x) of doorsnedetekening.
    materiaal: MateriaalBovenbouw | NietBeschikbaar = NietBeschikbaar.LEEG
    # Te bepalen uit de gebrekentabel (paragraaf 2.3 of 5.3.3) door het aantal scheuren te tellen en te relateren aan de lengte van het rakdeel.
    maximaal_aantal_scheuren_per_10_m: int | None = None
    # Af te leiden uit de doorsnedetekening en de toestandstabel (figuur 1.11) en de gebrekentabel (paragraaf 2.3 of 5.3.3).
    percentage_niet_functionerend_schuifhout: float | None = None
    # Te vinden in de constructiebeschrijving (paragraaf 5.x) of af te leiden uit de doorsnedetekening.
    bovenkant_deksteen_cm_tov_nap: float | None = None
