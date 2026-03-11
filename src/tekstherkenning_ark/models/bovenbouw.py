from pydantic import computed_field

from tekstherkenning_ark.enums import MateriaalBovenbouw, NietBeschikbaar
from tekstherkenning_ark.logger import get_logger

logger = get_logger(__name__)
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
        bovenkant_deksteen_cm_tov_nap: Hoogte van de bovenkant van de deksteen ten opzichte van NAP, in centimeters.
        gebreken: Lijst van gebreken (inherited from RakBaseModel).
        opmerkingen: Eventuele opmerkingen (inherited from RakBaseModel).

    Properties (berekend):
        scheuren: Lijst van alle Scheur gebreken in de bovenbouw.
        maximaal_aantal_scheuren_per_10_m: Maximaal aantal scheuren per 10 meter (sliding window).
        totaal_aantal_scheuren: Totaal aantal scheuren in het metselwerk.
        maximale_scheurwijdte_mm: Grootste scheurwijdte uit alle Scheur gebreken.
        is_buik_in_wand_aanwezig: Check of BuikInWand gebrek aanwezig is.
        is_grondvoerend_gat_aanwezig: Check of GrondVoerendGat gebrek aanwezig is.
        is_lokaal_verdwenen_metselwerk: Check of LokaalVerdwenenMetselwerk gebrek aanwezig is.
        is_scheefstand_aanwezig: Check of Scheefstand gebrek aanwezig is.
        is_scheefstand_met_scheur_aanwezig: Check of Scheefstand geassocieerd met Scheur aanwezig is.
        scheefstand_met_scheur_in_wand: Lijst van Scheefstand-Scheur paren.
        is_buik_met_scheur_aanwezig: Check of BuikInWand geassocieerd met Scheur aanwezig is.
        buik_met_scheur_in_wand: Lijst van BuikInWand-Scheur paren.
    """

    # Af te leiden uit de constructiebeschrijving (paragraaf 5.x) of doorsnedetekening.
    materiaal: MateriaalBovenbouw | NietBeschikbaar = NietBeschikbaar.LEEG

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

    @computed_field
    @property
    def maximaal_aantal_scheuren_per_10_m(self) -> int:
        """Maximaal aantal scheuren per 10 meter, berekend via een sliding window over de scheurafstanden."""

        scheur_afstanden = sorted(
            [s.afstand_van_startrak_m for s in self.scheuren if isinstance(s.afstand_van_startrak_m, (int, float))]
        )

        if len(scheur_afstanden) != len(self.scheuren):
            logger.warning(
                f"{len(self.scheuren) - len(scheur_afstanden)} / {len(self.scheuren)} scheuren"
                f" in bovenbouw hebben geen geldige afstand_van_startrak_m waarde en worden genegeerd"
                f" in de maximaal_aantal_scheuren_per_10_m berekening."
            )

        max_scheuren_per_10_m = 0

        for scheur_locatie in scheur_afstanden:
            n_scheuren = len([s for s in scheur_afstanden if scheur_locatie <= s < scheur_locatie + 10])
            max_scheuren_per_10_m = max(max_scheuren_per_10_m, n_scheuren)

        return max_scheuren_per_10_m

    @computed_field
    @property
    def totaal_aantal_scheuren(self) -> int:
        """Totaal aantal scheuren in het metselwerk."""

        return len(self.scheuren)

    @computed_field
    @property
    def maximale_scheurwijdte_mm(self) -> float | None:
        """Grootste scheurwijdte uit alle Scheur gebreken."""

        scheurwijdtes = [
            float(gebrek.scheurwijdte_mm)
            for gebrek in self.scheuren
            if isinstance(gebrek.scheurwijdte_mm, (int, float))
        ]

        return max(scheurwijdtes) if scheurwijdtes else None

    @computed_field
    @property
    def is_buik_in_wand_aanwezig(self) -> bool:
        """Check of BuikInWand gebrek aanwezig is."""
        return any(isinstance(gebrek, BuikInWand) for gebrek in self.gebreken)

    @computed_field
    @property
    def is_grondvoerend_gat_aanwezig(self) -> bool:
        """Check of GrondVoerendGat gebrek aanwezig is."""
        return any(isinstance(gebrek, GrondVoerendGat) for gebrek in self.gebreken)

    @computed_field
    @property
    def is_lokaal_verdwenen_metselwerk(self) -> bool:
        """Check of LokaalVerdwenenMetselwerk gebrek aanwezig is."""
        return any(isinstance(gebrek, LokaalVerdwenenMetselwerk) for gebrek in self.gebreken)

    @property
    def is_scheefstand_aanwezig(self) -> bool:
        """Check of Scheefstand gebrek aanwezig is."""
        return any(isinstance(gebrek, Scheefstand) for gebrek in self.gebreken)

    @computed_field
    @property
    def is_scheefstand_met_scheur_aanwezig(self) -> bool:
        """Check of er een Scheefstand gebrek is dat geassocieerd kan worden met een Scheur gebrek."""
        return len(self.scheefstand_met_scheur_in_wand) > 0

    @computed_field
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

    @computed_field
    @property
    def is_buik_met_scheur_aanwezig(self) -> bool:
        """Check of er een BuikInWand gebrek is dat geassocieerd kan worden met een Scheur gebrek."""
        return len(self.buik_met_scheur_in_wand) > 0

    @computed_field
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
