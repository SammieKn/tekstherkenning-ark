"""LLM classificatie modellen voor gebreken.

Dit module bevat Pydantic modellen die gebruikt worden om gebrekenomschrijvingen
te classificeren via Azure OpenAI. Elk model extraheert specifieke attributen
uit de omschrijvingstekst.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.llm.llmclassifier import LLMClassifier


class GebrekTypeDetectieLLM(LLMClassifier):
    """LLM model voor detectie van gebrektype(n) in een omschrijving.

    Dit model bepaalt welke type(n) gebrek(en) aanwezig zijn in een
    gebrekomschrijving. Het kan meerdere types detecteren indien deze
    samen voorkomen in één omschrijving.

    Attributes
    ----------
    is_scheur : bool
        Indicatie of er sprake is van een scheur.
    is_grondvoerend_gat_of_verdwenen_metselwerk : bool
        Indicatie of er sprake is van een grondvoerend gat of lokaal
        verdwenen metselwerk (gat, uitgespoeld, ontbrekend metselwerk).
    is_buik_of_scheefstand : bool
        Indicatie of er sprake is van een buik in de wand of scheefstand
        (uitbuiging, afwijking van verticaal).
    is_onderloopsheidscherm : bool
        Indicatie of er sprake is van een beschadigd onderloopsheidscherm.
    """

    _systeem_prompt: ClassVar[
        str
    ] = """Je bent een expert in het analyseren van gebrekenomschrijvingen van kademuren.
Bepaal welke type(n) gebrek(en) aanwezig zijn in de omschrijving.

Een omschrijving kan meerdere types bevatten. Analyseer de tekst zorgvuldig:

1. **Scheur**: Zoek naar termen als "scheur", "scheuren", "barst", "spleet"

2. **Grondvoerend gat of verdwenen metselwerk**: Dit zijn gaten of ontbrekend metselwerk.
   Zoek naar:
   - "grondvoerend" (gat waar grond doorheen stroomt)
   - "ontbreekt", "ontbrekend" (metselwerk)
   - "uitgebroken", "uitgespoeld" (metselwerk)
   - "verdwenen" (metselwerk)
   - "gat in metselwerk"
   - "vermist metselwerk"
   - "lokale beschadiging metselwerk"

3. **Buik in wand of scheefstand**: Dit zijn afwijkingen van de verticale stand.
   Zoek naar:
   - "buik", "uitbuiging"
   - "scheefstand", "scheef"
   - "wijkt af", "afwijking"
   - "buigt uit", "uitgebogen"
   - "naar het water" (in context van afwijking)
   - "niet verticaal", "niet loodrecht"

4. **Onderloopsheidscherm**: Beschadigd onderloopsheidscherm.
   Zoek naar: "scherm", "onderloopsheidscherm"

LET OP: Een omschrijving kan meerdere gebrektypes bevatten. Analyseer de volledige
tekst en markeer alle relevante types als True."""

    is_scheur: bool = Field(
        default=False,
        description="True als de omschrijving een scheur beschrijft",
    )
    is_grondvoerend_gat_of_verdwenen_metselwerk: bool = Field(
        default=False,
        description="True als de omschrijving een grondvoerend gat of verdwenen/ontbrekend metselwerk beschrijft",
    )
    is_buik_of_scheefstand: bool = Field(
        default=False,
        description="True als de omschrijving een buik in de wand of scheefstand beschrijft",
    )
    is_onderloopsheidscherm: bool = Field(
        default=False,
        description="True als de omschrijving een beschadigd onderloopsheidscherm beschrijft",
    )


class ScheurLLM(LLMClassifier):
    """Basis model voor scheur attributen (geen eigen systeem prompt).

    Attributes
    ----------
    afstand_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters.
    lengte_cm : float | NietBeschikbaar
        Lengte van de scheur in centimeters.
    scheurwijdte_mm : float | NietBeschikbaar
        Maximale scheurwijdte in millimeters.
    """

    _systeem_prompt: ClassVar[
        str
    ] = """Je bent een expert in het analyseren van gebrekenomschrijvingen van kademuren.
Extraheer informatie over scheuren uit de omschrijving.
Gebruik NietBeschikbaar.LEEG als de informatie niet beschikbaar is,
NietBeschikbaar.NIET_VAN_TOEPASSING als het veld niet van toepassing is,
of NietBeschikbaar.NIET_MEETBAAR als de waarde niet meetbaar is."""

    afstand_van_startrak_m: float | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="""
        Afstand van het startrak in meters. 
        - Zoek naar 'Op X meter vanaf start rak' of 'vanaf startrak'.
        - Als een object genoemd wordt, zoals een brug, dan is dat het startrak.
        """,
    )
    lengte_cm: float | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="De lengte van de scheur in centimeters. Kan aangegeven worden als 'lengte', 'hoogte', ... Belangrijkste is dat de dimensie toegewezen wordt aan de scheur",
    )
    scheurwijdte_mm: float | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Maximale scheurwijdte in millimeters. Vaak aangegeven als 'SW' of 'scheurwijdte'.",
    )


class ScheurMetselwerkLLM(ScheurLLM):
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


class ScheurHoutLLM(ScheurLLM):
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


class GrondVoerendGatLLM(LLMClassifier):
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


class BuikInWandLLM(LLMClassifier):
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


class ScheefstandLLM(LLMClassifier):
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


class LokaalVerdwenenMetselwerkLLM(LLMClassifier):
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
