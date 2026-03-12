from __future__ import annotations
import hashlib
import pickle

from typing import ClassVar

from pydantic import Field

from tekstherkenning_ark.llm.llmclassifier import LLMClassifier
from tekstherkenning_ark.constants import NAP_CM_HOOGTE_WATERLIJN
from tekstherkenning_ark.llm.azureopenaillm import AzureOpenAILLM
from tekstherkenning_ark.enums import (
    MateriaalBovenbouw,
    MateriaalOnderbouw,
    MateriaalFundering,
    MateriaalVloer,
    NietBeschikbaar,
)


class RakdeelOmschrijving(LLMClassifier):
    """Model voor het classificeren van rakdeel omschrijvingen via LLM.

    Attributes
    ----------
    bouwjaar : int | None
        Bouwjaar van het rakdeel.
    lengte_rakdeel : float | None
        Lengte van het rakdeel in meters.
    materiaal_fundering : MateriaalFundering | NietBeschikbaar
        Het materiaal van de fundering.
    materiaal_onderbouw : MateriaalOnderbouw | NietBeschikbaar
        Het materiaal van de onderbouw.
    materiaal_bovenbouw : MateriaalBovenbouw | NietBeschikbaar
        Het materiaal van de bovenbouw.
    materiaal_vloer : MateriaalVloer | NietBeschikbaar
        Het materiaal van de vloer.
    onderloopsheidscherm : bool | NietBeschikbaar
        Indicatie of onderloopsheidscherm aanwezig is.
    bovenkant_deksteen_tot_waterlijn_cm : float | None
        Direct benoemde afstand van waterlijn tot bovenkant deksteen in cm.
    bovenkant_deksteen_tot_nap_cm : float | None
        Direct benoemde hoogte van bovenkant deksteen ten opzichte van NAP in cm.
    waterlijn_tot_bovenkant_vloer_cm : float | None
        Direct benoemde afstand van waterlijn tot bovenkant vloer in cm.
    nap_tot_bovenkant_vloer_cm : float | None
        Direct benoemde hoogte van bovenkant vloer ten opzichte van NAP in cm.
    onderzijde_constructie_nap_cm : float | None
        Direct benoemde hoogte van onderzijde constructie ten opzichte van NAP in cm.
    afstand_onderzijde_constructie_tot_bovenkant_vloer_cm : float | None
        Direct benoemde afstand van onderzijde constructie tot bovenkant vloer in cm.
    """

    _systeem_prompt: ClassVar[
        str
    ] = """Je bent een expert in het analyseren van constructie-omschrijvingen van kademuren.
        Extraheer de relevante informatie uit de omschrijving en vul de velden in.
        Gebruik NietBeschikbaar.LEEG als de informatie niet beschikbaar is,
        NietBeschikbaar.NIET_VAN_TOEPASSING als het veld niet van toepassing is,
        of NietBeschikbaar.NIET_MEETBAAR als de waarde niet meetbaar is.

        Als de waterlijn benoemt wordt in afstanden, gebruik dan de variable van de waterlijn als referentiepunt, bijvoorbeeld:
        - bovenkant_deksteen_cm_tov_waterlijn
        - waterlijn_tot_bovenkant_vloer_cm

        Als de hoogte ten opzichte van NAP benoemt wordt, gebruik dan de variable van NAP als referentiepunt, bijvoorbeeld:
        - bovenkant_deksteen_cm_tov_nap
        - nap_tot_bovenkant_vloer_cm
        \n
        - Gebruik ALLEEN verticale afstanden voor hoogte berekeningen.
        - Afstanden worden in de tekst omschreven van boven naar beneden, dus als er meerdere afstanden worden benoemd, is de bovenste afstand de referentie voor de volgende afstand.
        """

    bouwjaar: int | NietBeschikbaar = Field(
        gt=1600, lt=2200, default=NietBeschikbaar.LEEG, description="Bouwjaar van het rakdeel, houd leeg als onbekend."
    )

    # Lengte van het rakdeel, wordt gebruikt om de subdelen te toetsen in lengte tov totaal.
    lengte_rakdeel: float | NietBeschikbaar = Field(
        gt=0.0, default=NietBeschikbaar.LEEG, description="Lengte van het rakdeel in meters, houd leeg als onbekend."
    )

    # Benodigd om type constructie te bepalen
    materiaal_fundering: MateriaalFundering | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Het materiaal van de fundering van het rakdeel. Dit is alles onder de vloer, bijvoorbeeld de palen of damwanden.",
    )
    materiaal_onderbouw: MateriaalOnderbouw | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Het materiaal van de onderbouw van het rakdeel. Dit is alles boven de fundering en onder de kade.",
    )
    materiaal_bovenbouw: MateriaalBovenbouw | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Het materiaal van de bovenbouw van het rakdeel. Dit is het verticale, dragende deel van de bovenbouw.",
    )
    # benodigd voor onderbouw/fundering
    materiaal_vloer: MateriaalVloer | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Het materiaal van de vloer van het rakdeel. Als is aangegeven dat palen erin zijn gestort, dan is het een betonnen vloer.",
    )

    # onderloopsheidscherm aanwezig ja/nee
    onderloopsheidscherm: bool | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Geef aan of er een onderloopsheidscherm aanwezig is bij dit rakdeel door middel van boolean. Herkenbaar aan woorden zoals 'grondkerend scherm', 'onderloopsheidscherm', 'scherm' in de omschrijving.",
    )
    bovenkant_deksteen_tot_waterlijn_cm: float | NietBeschikbaar = Field(
        gt=0.0,
        default=NietBeschikbaar.LEEG,
        description="Geef de hoogte van de bovenkant van de deksteen ten opzichte van de waterlijn (cm).",
    )
    bovenkant_deksteen_tot_nap_cm: float | NietBeschikbaar = Field(
        gt=0.0,
        default=NietBeschikbaar.LEEG,
        description="Geef de hoogte van de bovenkant van de deksteen ten opzichte van NAP (cm).",
    )
    waterlijn_tot_bovenkant_vloer_cm: float | NietBeschikbaar = Field(
        gt=0.0,
        default=NietBeschikbaar.LEEG,
        description="Geef de afstand onder de waterlijn tot de bovenkant van de vloer in cm.",
    )
    nap_tot_bovenkant_vloer_cm: float | NietBeschikbaar = Field(
        gt=0.0,
        default=NietBeschikbaar.LEEG,
        description="Geef de afstand onder NAP tot de bovenkant van de vloer in cm.",
    )
    onderzijde_constructie_nap_cm: float | NietBeschikbaar = Field(
        gt=0.0,
        default=NietBeschikbaar.LEEG,
        description="Geef de afstand onder NAP tot de onderzijde van de constructie in cm. Te herkennen aan 'onderzijde constructie bevindt zich op x cm onder NAP.'",
    )
    afstand_onderzijde_constructie_tot_bovenkant_vloer_cm: float | NietBeschikbaar = Field(
        gt=0.0,
        default=NietBeschikbaar.LEEG,
        description="Geef de afstand van de bovenkant vloer tot de onderzijde van de constructie in cm. Tel de hoogtes van de constructieonderdelen tussen vloer en onderzijde constructie bij elkaar op.",
    )

    @property
    def bovenkant_vloer_cm(self) -> float | None:
        """Bepaal de hoogte van de bovenkant van de vloer ten opzichte van NAP in cm, op basis van de beschikbare informatie."""
        if isinstance(self.nap_tot_bovenkant_vloer_cm, float):
            return self.nap_tot_bovenkant_vloer_cm
        elif all(
            (
                isinstance(value, float)
                for value in [
                    self.onderzijde_constructie_nap_cm,
                    self.afstand_onderzijde_constructie_tot_bovenkant_vloer_cm,
                ]
            )
        ):
            return self.onderzijde_constructie_nap_cm - self.afstand_onderzijde_constructie_tot_bovenkant_vloer_cm
        elif isinstance(self.waterlijn_tot_bovenkant_vloer_cm, float):
            return self.waterlijn_tot_bovenkant_vloer_cm + NAP_CM_HOOGTE_WATERLIJN
        else:
            return None

    @property
    def bovenkant_deksteen_cm(self) -> float | None:
        """Bepaal de hoogte van de bovenkant van de deksteen ten opzichte van NAP in cm, op basis van de beschikbare informatie."""
        if isinstance(self.bovenkant_deksteen_tot_nap_cm, float):
            return self.bovenkant_deksteen_tot_nap_cm
        elif isinstance(self.bovenkant_deksteen_tot_waterlijn_cm, float):
            return self.bovenkant_deksteen_tot_waterlijn_cm - NAP_CM_HOOGTE_WATERLIJN
        else:
            return None
