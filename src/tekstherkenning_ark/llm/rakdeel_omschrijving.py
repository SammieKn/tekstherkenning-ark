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
    bovenkant_deksteen_cm : float | None
        Hoogte bovenkant deksteen in cm t.o.v. waterlijn.
    bovenkant_vloer_cm : float | None
        Hoogte waterlijn tot bovenkant vloer in cm.
    """

    _systeem_prompt: ClassVar[
        str
    ] = """Je bent een expert in het analyseren van constructie-omschrijvingen van kademuren.
        Extraheer de relevante informatie uit de omschrijving en vul de velden in.
        Gebruik NietBeschikbaar.LEEG als de informatie niet beschikbaar is,
        NietBeschikbaar.NIET_VAN_TOEPASSING als het veld niet van toepassing is,
        of NietBeschikbaar.NIET_MEETBAAR als de waarde niet meetbaar is.
        """

    bouwjaar: int | None = Field(
        gt=1600, lt=2200, default=None, description="Bouwjaar van het rakdeel, houd leeg als onbekend."
    )

    # Lengte van het rakdeel, wordt gebruikt om de subdelen te toetsen in lengte tov totaal.
    lengte_rakdeel: float | None = Field(
        gt=0.0, default=None, description="Lengte van het rakdeel in meters, houd leeg als onbekend."
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
        description="Geef aan of er een onderloopsheidscherm aanwezig is bij dit rakdeel door middel van boolean.",
    )

    # benodigd voor constructie waterbodem
    bovenkant_deksteen_cm: float | None = Field(
        gt=0.0,
        default=None,
        description=f"""
        Geef de hoogte van de bovenkant van de kademuur in centimeters ten opzichte van NAP.
        Definities:
        - waterlijn_NAP = -{NAP_CM_HOOGTE_WATERLIJN} cm: hoogte van de waterlijn (cm t.o.v. NAP). Positief = boven NAP, negatief = onder NAP.
        - delta: verticale afstand van de waterlijn naar de bovenkant van de kade (cm). Positief als de kade boven de waterlijn ligt, negatief als de kade onder de waterlijn ligt.
        Formule:
        top_kade_NAP = waterlijn_NAP + delta
        Als de bovenkant aangeduid wordt door deksteen/metselwerk/maaiveld, gebruik die waarde voor delta (met correct teken).
        Voorbeeld: waterlijn_NAP = -{NAP_CM_HOOGTE_WATERLIJN} cm, delta = 80 (kade ligt 80 cm boven waterlijn) → top_kade_NAP = -{NAP_CM_HOOGTE_WATERLIJN} + 80 = {80 - NAP_CM_HOOGTE_WATERLIJN} cm.""",
    )
    bovenkant_vloer_cm: float | None = Field(
        lt=0.0,
        default=None,
        description=f"""
        Geef de hoogte ten opzichte van NAP van de bovenkant van de funderingsvloer (cm).
        Definities:
        - De waterlijn bevindt zich op -{NAP_CM_HOOGTE_WATERLIJN} cm ten opzichte van NAP.
        - De hoogte is negatief (onder NAP).
        Berekening:
        - Tel alle onderdelen vanaf de onderzijde van de constructie op (bijvoorbeeld fundering, kespen, balken) tot aan de bovenkant van de vloer.
        - De som van deze diktes, samen met de hoogte van de onderzijde van de constructie ten opzichte van NAP, geeft de hoogte van de bovenkant vloer.
        Voorbeeld:
        Onderzijde constructie op -{NAP_CM_HOOGTE_WATERLIJN + 50} cm, constructiedikte 30 cm → bovenkant vloer = (-{NAP_CM_HOOGTE_WATERLIJN + 50}) + 30 = -{(NAP_CM_HOOGTE_WATERLIJN + 20)} cm.""",
    )
