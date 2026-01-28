"""LLM classificatie modellen voor gebreken.

Dit module bevat Pydantic modellen die gebruikt worden om gebrekenomschrijvingen
te classificeren via Azure OpenAI. Elk model extraheert specifieke attributen
uit de omschrijvingstekst.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.llm.base import LLMClassificeerbaar


class ScheurLLM(BaseModel):
    """Basis model voor scheur attributen (geen eigen systeem prompt).

    Attributes
    ----------
    lengte_cm : float | NietBeschikbaar
        Lengte van de scheur in centimeters.
    scheurwijdte_mm : float | NietBeschikbaar
        Maximale scheurwijdte in millimeters.
    """

    lengte_cm: float | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Lengte van de scheur in centimeters. Zoek naar termen zoals 'lengte' of 'L'.",
    )
    scheurwijdte_mm: float | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Maximale scheurwijdte in millimeters. Vaak aangegeven als 'SW' of 'scheurwijdte'.",
    )


class ScheurMetselwerkLLM(ScheurLLM, LLMClassificeerbaar):
    """LLM model voor scheur in metselwerk classificatie.

    Attributes
    ----------
    lengte_cm : float | NietBeschikbaar
        Lengte van de scheur in centimeters.
    scheurwijdte_mm : float | NietBeschikbaar
        Maximale scheurwijdte in millimeters.
    afstand_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters.
    afstand_van_waterlijn_cm : float | NietBeschikbaar
        Afstand van de waterlijn in centimeters.
    afstand_van_deksloof_cm : float | NietBeschikbaar
        Afstand van de deksloof in centimeters.
    is_inprikbaar : bool | NietBeschikbaar
        Indicatie of de scheur inprikbaar is.
    orientatie : Literal["verticaal", "horizontaal", "diagonaal"] | NietBeschikbaar
        Oriëntatie van de scheur.
    """

    _systeem_prompt: ClassVar[
        str
    ] = """Je bent een expert in het analyseren van gebrekenomschrijvingen van kademuren.
Extraheer informatie over scheuren in metselwerk uit de omschrijving.
Gebruik NietBeschikbaar.LEEG als de informatie niet beschikbaar is,
NietBeschikbaar.NIET_VAN_TOEPASSING als het veld niet van toepassing is,
of NietBeschikbaar.NIET_MEETBAAR als de waarde niet meetbaar is."""

    afstand_van_startrak_m: float | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Afstand van het startrak in meters. Zoek naar 'Op X meter vanaf start rak' of 'vanaf startrak'.",
    )
    afstand_van_waterlijn_cm: float | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Afstand van de waterlijn in centimeters. Zoek naar 'waterlijn' of 'WL'.",
    )
    afstand_van_deksloof_cm: float | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Afstand van de deksloof in centimeters. Zoek naar 'deksloof'.",
    )
    is_inprikbaar: bool | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Indicatie of de scheur inprikbaar is. Zoek naar 'inprikbaar'.",
    )
    orientatie: Literal["verticaal", "horizontaal", "diagonaal"] | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Oriëntatie van de scheur: verticaal, horizontaal of diagonaal.",
    )


class ScheurHoutLLM(ScheurLLM, LLMClassificeerbaar):
    """LLM model voor scheur in hout classificatie.

    Attributes
    ----------
    lengte_cm : float | NietBeschikbaar
        Lengte van de scheur in centimeters.
    scheurwijdte_mm : float | NietBeschikbaar
        Maximale scheurwijdte in millimeters.
    diepte_cm : float | NietBeschikbaar
        Diepte van de scheur in centimeters.
    orientatie : Literal["verticaal", "horizontaal"] | NietBeschikbaar
        Oriëntatie van de scheur.
    """

    _systeem_prompt: ClassVar[
        str
    ] = """Je bent een expert in het analyseren van gebrekenomschrijvingen van kademuren.
Extraheer informatie over scheuren in hout (palen, kespen) uit de omschrijving.
Gebruik NietBeschikbaar.LEEG als de informatie niet beschikbaar is,
NietBeschikbaar.NIET_VAN_TOEPASSING als het veld niet van toepassing is,
of NietBeschikbaar.NIET_MEETBAAR als de waarde niet meetbaar is."""

    diepte_cm: float | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Diepte van de scheur in centimeters. Zoek naar 'diepte'.",
    )
    orientatie: Literal["verticaal", "horizontaal"] | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Oriëntatie van de scheur: verticaal of horizontaal.",
    )


class GrondVoerendGatLLM(LLMClassificeerbaar):
    """LLM model voor grondvoerend gat classificatie.

    Attributes
    ----------
    afstand_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters.
    breedte_cm : int | NietBeschikbaar
        Breedte van het gat in centimeters.
    hoogte_cm : int | NietBeschikbaar
        Hoogte van het gat in centimeters.
    diepte_cm : int | NietBeschikbaar
        Diepte van het gat in centimeters.
    """

    _systeem_prompt: ClassVar[
        str
    ] = """Je bent een expert in het analyseren van gebrekenomschrijvingen van kademuren.
Extraheer informatie over grondvoerende gaten uit de omschrijving.
Dit zijn gaten achter het metselwerk waar grond doorheen kan stromen.
Gebruik NietBeschikbaar.LEEG als de informatie niet beschikbaar is,
NietBeschikbaar.NIET_VAN_TOEPASSING als het veld niet van toepassing is,
of NietBeschikbaar.NIET_MEETBAAR als de waarde niet meetbaar is."""

    afstand_van_startrak_m: float | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Afstand van het startrak in meters. Zoek naar 'vanaf start rak' of 'meter'.",
    )
    breedte_cm: int | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Breedte van het gat in centimeters. Zoek naar 'breedte', 'b' of 'b x h x d'.",
    )
    hoogte_cm: int | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Hoogte van het gat in centimeters. Zoek naar 'hoogte', 'h' of 'b x h x d'.",
    )
    diepte_cm: int | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Diepte van het gat in centimeters. Zoek naar 'diepte', 'd' of 'b x h x d'.",
    )


class BuikInWandLLM(LLMClassificeerbaar):
    """LLM model voor buik in wand classificatie.

    Attributes
    ----------
    afstand_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters.
    uitbuiking_cm : int | NietBeschikbaar
        Mate van uitbuiging in centimeters.
    """

    _systeem_prompt: ClassVar[
        str
    ] = """Je bent een expert in het analyseren van gebrekenomschrijvingen van kademuren.
Extraheer informatie over buik in wand (uitbuiging van de kademuur) uit de omschrijving.
Gebruik NietBeschikbaar.LEEG als de informatie niet beschikbaar is,
NietBeschikbaar.NIET_VAN_TOEPASSING als het veld niet van toepassing is,
of NietBeschikbaar.NIET_MEETBAAR als de waarde niet meetbaar is."""

    afstand_van_startrak_m: float | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Afstand van het startrak in meters. Zoek naar 'vanaf start rak' of 'meter'.",
    )
    uitbuiking_cm: int | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Mate van uitbuiging in centimeters. Zoek naar 'uitbuiging' of 'buik'.",
    )


class ScheefstandLLM(LLMClassificeerbaar):
    """LLM model voor scheefstand classificatie.

    Attributes
    ----------
    afstand_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters.
    hoek_graden : int | NietBeschikbaar
        Hoek van de scheefstand in graden.
    """

    _systeem_prompt: ClassVar[
        str
    ] = """Je bent een expert in het analyseren van gebrekenomschrijvingen van kademuren.
Extraheer informatie over scheefstand uit de omschrijving.
Gebruik NietBeschikbaar.LEEG als de informatie niet beschikbaar is,
NietBeschikbaar.NIET_VAN_TOEPASSING als het veld niet van toepassing is,
of NietBeschikbaar.NIET_MEETBAAR als de waarde niet meetbaar is."""

    afstand_van_startrak_m: float | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Afstand van het startrak in meters. Zoek naar 'vanaf start rak' of 'meter'.",
    )
    hoek_graden: int | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Hoek van de scheefstand in graden. Zoek naar 'hoek', 'graden' of '°'.",
    )


class LokaalVerdwenenMetselwerkLLM(LLMClassificeerbaar):
    """LLM model voor lokaal verdwenen metselwerk classificatie.

    Attributes
    ----------
    afstand_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters.
    breedte_cm : int | NietBeschikbaar
        Breedte van het verdwenen metselwerk in centimeters.
    hoogte_cm : int | NietBeschikbaar
        Hoogte van het verdwenen metselwerk in centimeters.
    diepte_cm : int | NietBeschikbaar
        Diepte van het verdwenen metselwerk in centimeters.
    """

    _systeem_prompt: ClassVar[
        str
    ] = """Je bent een expert in het analyseren van gebrekenomschrijvingen van kademuren.
Extraheer informatie over lokaal verdwenen metselwerk uit de omschrijving.
Dit betreft metselwerk dat ontbreekt, is uitgespoeld, of beschadigd is.
Gebruik NietBeschikbaar.LEEG als de informatie niet beschikbaar is,
NietBeschikbaar.NIET_VAN_TOEPASSING als het veld niet van toepassing is,
of NietBeschikbaar.NIET_MEETBAAR als de waarde niet meetbaar is."""

    afstand_van_startrak_m: float | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Afstand van het startrak in meters. Zoek naar 'vanaf start rak' of 'meter'.",
    )
    breedte_cm: int | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Breedte van het verdwenen metselwerk in centimeters. Zoek naar 'breedte', 'b' of 'b x h x d'.",
    )
    hoogte_cm: int | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Hoogte van het verdwenen metselwerk in centimeters. Zoek naar 'hoogte', 'h' of 'b x h x d'.",
    )
    diepte_cm: int | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Diepte van het verdwenen metselwerk in centimeters. Zoek naar 'diepte', 'd' of 'b x h x d'.",
    )
