from tekstherkenning_ark.enums import MateriaalBovenbouw, NietBeschikbaar
from tekstherkenning_ark.models.gebrek import (
    BuikInWand,
    Gebrek,
    GrondVoerendGat,
    LokaalVerdwenenMetselwerk,
    Scheefstand,
    Scheur,
    ScheurMetselwerk,
)
from tekstherkenning_ark.models.rak_base_model import RakBaseModel


class Bovenbouw(RakBaseModel):
    """Object met alle eigenschappen van de bovenbouw van het rakdeel.

    Attributes:
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

    # Af te leiden uit de constructiebeschrijving (paragraaf 5.x) of doorsnedetekening.
    materiaal: MateriaalBovenbouw | NietBeschikbaar = NietBeschikbaar.LEEG
    # Te bepalen uit de gebrekentabel (paragraaf 2.3 of 5.3.3) door het aantal scheuren te tellen en te relateren aan de lengte van het rakdeel.
    maximaal_aantal_scheuren_per_10_m: int | None = None
    # Af te leiden uit de doorsnedetekening en de toestandstabel (figuur 1.11) en de gebrekentabel (paragraaf 2.3 of 5.3.3).
    percentage_niet_functionerend_schuifhout: float | None = None
    # Te vinden in de constructiebeschrijving (paragraaf 5.x) of af te leiden uit de doorsnedetekening.
    bovenkant_deksteen_cm_tov_nap: float | None = None

    @property
    def identifier(self) -> str:
        """Return a string that uniquely identifies this Bovenbouw instance."""
        return "bovenbouw"

    @property
    def scheuren(self) -> list[Scheur]:
        """Return a list of all Scheur gebreken in this Bovenbouw."""
        return [gebrek for gebrek in self.gebreken or [] if isinstance(gebrek, Scheur)]

    @property
    def totaal_aantal_scheuren(self) -> int:
        """Totaal aantal scheuren in het metselwerk."""

        return len(self.scheuren)

    @property
    def maximale_scheurwijdte_mm(self) -> float | None:
        """Grootste scheurwijdte uit alle Scheur gebreken."""

        scheurwijdtes = [
            float(gebrek.scheurwijdte_mm)
            for gebrek in self.scheuren
            if isinstance(gebrek.scheurwijdte_mm, (int, float))
        ]

        return max(scheurwijdtes) if scheurwijdtes else None

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

    @property
    def is_scheefstand_met_scheur_aanwezig(self) -> bool:
        """Check of er een Scheefstand gebrek is dat geassocieerd kan worden met een Scheur gebrek."""
        return len(self.scheefstand_met_scheur_in_wand) > 0

    @property
    def scheefstand_met_scheur_in_wand(self) -> list[tuple[Scheefstand, Scheur]]:
        """Returnt een list of tuples met Scheefstand gebreken en hun bijbehorende Scheur gebreken."""
        scheefstand_gebreken = [gebrek for gebrek in self.gebreken if isinstance(gebrek, Scheefstand)]
        scheur_gebreken = [gebrek for gebrek in self.gebreken if isinstance(gebrek, Scheur)]

        scheefstand_met_scheur = []

        for scheefstand in scheefstand_gebreken:
            for scheur in scheur_gebreken:
                if scheefstand.codering == scheur.codering:
                    scheefstand_met_scheur.append((scheefstand, scheur))
                elif all(
                    isinstance(value, float)
                    for value in (
                        scheefstand.start_scheefstand_van_startrak_m,
                        scheefstand.eind_scheefstand_van_startrak_m,
                    )
                ):
                    if (
                        isinstance(scheur.afstand_van_startrak_m, float)
                        and scheefstand.start_scheefstand_van_startrak_m
                        <= scheur.afstand_van_startrak_m
                        <= scheefstand.eind_scheefstand_van_startrak_m  # type: ignore
                    ):
                        scheefstand_met_scheur.append((scheefstand, scheur))

        return scheefstand_met_scheur

    @property
    def is_buik_met_scheur_aanwezig(self) -> bool:
        """Check of er een BuikInWand gebrek is dat geassocieerd kan worden met een Scheur gebrek."""
        return len(self.buik_met_scheur_in_wand) > 0

    @property
    def buik_met_scheur_in_wand(self) -> list[tuple[BuikInWand, Scheur]]:
        """Returnt een list of tuples met BuikInWand gebreken en hun bijbehorende Scheur gebreken."""
        buik_in_wand_gebreken = [gebrek for gebrek in self.gebreken if isinstance(gebrek, BuikInWand)]
        scheur_gebreken = [gebrek for gebrek in self.gebreken if isinstance(gebrek, Scheur)]

        buik_met_scheur = []

        for buik in buik_in_wand_gebreken:
            for scheur in scheur_gebreken:
                if buik.codering == scheur.codering:
                    buik_met_scheur.append((buik, scheur))
                elif all(
                    isinstance(value, float)
                    for value in (buik.start_buik_van_startrak_m, buik.eind_buik_van_startrak_m)
                ):
                    if (
                        isinstance(scheur.afstand_van_startrak_m, float)
                        and buik.start_buik_van_startrak_m
                        <= scheur.afstand_van_startrak_m
                        <= buik.eind_buik_van_startrak_m  # type: ignore
                    ):
                        buik_met_scheur.append((buik, scheur))

        return buik_met_scheur
