from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from tekstherkenning_ark.llm.base import LLMClassificeerbaar
from tekstherkenning_ark.enums import (
    MateriaalBovenbouw,
    MateriaalOnderbouw,
    MateriaalFundering,
    MateriaalVloer,
    NietBeschikbaar,
)


class RakdeelOmschrijving(LLMClassificeerbaar):
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
        description="Het materiaal van de onderbouw van het rakdeel. Dit is alles boven de fundering onder de kade.",
    )
    materiaal_bovenbouw: MateriaalBovenbouw | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Het materiaal van de bovenbouw van het rakdeel. Dit is het verticale, dragende deel van de bovenbouw.",
    )
    # benodigd voor onderbouw/fundering
    materiaal_vloer: MateriaalVloer | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG, description="Het materiaal van de vloer van het rakdeel."
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
        description="De hoogte van de bovenkant van de kademuur in centimeters ten opzichte van de waterlijn. Ook wel kerende hoogte genoemd. De bovenkant wordt vaak aangegeven door deksteen, metselwerk of maaiveld.",
    )
    bovenkant_vloer_cm: float | None = Field(
        gt=0.0,
        default=None,
        description="De hoogte van de waterlijn tot de bovenkant van de funderingsvloer. Als meerdere elementen onder de waterlijn worden vermeldt, dan tel je die op tot de vloer.",
    )
