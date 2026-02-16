from __future__ import annotations

import asyncio
from typing import Literal
from pydantic import BaseModel

from tekstherkenning_ark.utils import (
    clean_string,
    get_paal_id,
    contains_kesp_id,
    contains_paal_id,
    is_algemeen_gebrek,
)
from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.document.structured_table import StructuredTable
from tekstherkenning_ark.llm.gebrek_classificatie import (
    ScheurLLM,
    ScheurMetselwerkLLM,
    ScheurHoutLLM,
    GrondVoerendGatLLM,
    BuikInWandLLM,
    ScheefstandLLM,
    LokaalVerdwenenMetselwerkLLM,
)
from tekstherkenning_ark.logger import get_logger

logger = get_logger(__name__)


class Gebrek(BaseModel):
    """Model voor een gebrek.

    Attributes
    ----------
    codering : str
        Codering van het gebrek.
    omschrijving : str
        Omschrijving van het gebrek.
    figuurnummer : str | NietBeschikbaar
        Figuurnummer behorend bij het gebrek.
    """

    codering: str
    omschrijving: str
    figuurnummer: str | NietBeschikbaar

    @classmethod
    async def from_doc_tables(cls, structured_table: StructuredTable | None) -> list[Gebrek]:
        """Maak een lijst van Gebrek instanties uit een structured table.

        Parameters
        ----------
        structured_table : StructuredTable | None
            Structured table met gebrek informatie.

        Returns
        -------
        list[Gebrek]
            Een lijst van Gebrek instanties.
        """
        if structured_table is None:
            logger.warning(f"Geen {cls.__name__.lower()} tabel gevonden")
            return []

        # Get columns
        codering_col = structured_table.get_column(header_in="Gebrekcodering")
        omschrijving_col = structured_table.get_column(header_in="Omschrijving")
        figuurnummer_col = structured_table.get_column(header_in="Figuurnummer")

        if not codering_col and not omschrijving_col and not figuurnummer_col:
            logger.error("Could not find any required columns in gebreken table")
            return []

        # Parsing logica om Gebrek instanties te maken
        list_gebreken = []

        for row_idx in range(structured_table.num_rows):
            codering_val = clean_string(codering_col.values[row_idx]) if codering_col else ""

            # Stop at empty or dash rows
            if codering_val == "-" or codering_val == "":
                break

            gebrek_instance = cls(
                codering=codering_val,
                omschrijving=omschrijving_col.values[row_idx] if omschrijving_col else "",
                figuurnummer=figuurnummer_col.values[row_idx] if figuurnummer_col else "",
            )
            list_gebreken.append(gebrek_instance)

        # Classificeer elk gebrek naar een specifiek subtype indien mogelijk (parallel)
        classificatie_taken = [cls.classify_gebrek(gebrek) for gebrek in list_gebreken]
        geclassificeerde_gebreken = await asyncio.gather(*classificatie_taken)
        list_gebreken = list(geclassificeerde_gebreken)

        return list_gebreken

    @staticmethod
    async def classify_gebrek(gebrek: Gebrek) -> Gebrek:
        """Classificeer een Gebrek instantie naar een specifiek subtype.

        Parameters
        ----------
        gebrek : Gebrek
            Een Gebrek instantie.

        Returns
        -------
        Gebrek
            Een specifiek subtype van Gebrek met geëxtraheerde attributen.
        """
        omschrijving = gebrek.omschrijving.lower()

        # logica voor scheur
        if "scheur" in omschrijving:
            # Gebruik LLM voor classificatie van scheuren
            if contains_paal_id(omschrijving) or contains_kesp_id(gebrek.codering):
                llm_result = await ScheurHoutLLM.classificeer_omschrijving(gebrek.omschrijving)
                return ScheurHout(
                    **gebrek.model_dump(),
                    **llm_result.model_dump(),
                )
            elif "metselwerk" in omschrijving:
                llm_result = await ScheurMetselwerkLLM.classificeer_omschrijving(gebrek.omschrijving)
                return ScheurMetselwerk(
                    **gebrek.model_dump(),
                    **llm_result.model_dump(),
                )
            else:
                llm_result = await ScheurLLM.classificeer_omschrijving(gebrek.omschrijving)
                return Scheur(
                    **gebrek.model_dump(),
                    **llm_result.model_dump(),
                )

        # logica voor grondvoerend gat
        if "grondvoerend" in omschrijving and is_algemeen_gebrek(gebrek.codering):
            llm_result = await GrondVoerendGatLLM.classificeer_omschrijving(gebrek.omschrijving)
            return GrondVoerendGat(
                **gebrek.model_dump(),
                **llm_result.model_dump(),
            )

        # logica voor buikinwand
        if "buik" in omschrijving and is_algemeen_gebrek(gebrek.codering):
            llm_result = await BuikInWandLLM.classificeer_omschrijving(gebrek.omschrijving)
            return BuikInWand(
                **gebrek.model_dump(),
                **llm_result.model_dump(),
            )
        # logica voor scheefstand
        if "scheefstand" in omschrijving and is_algemeen_gebrek(gebrek.codering):
            llm_result = await ScheefstandLLM.classificeer_omschrijving(gebrek.omschrijving)
            return Scheefstand(
                **gebrek.model_dump(),
                **llm_result.model_dump(),
            )

        if "scherm" in omschrijving and is_algemeen_gebrek(gebrek.codering):
            return OnderloopsheidschermBeschadigd(**gebrek.model_dump())

        # logica voor lokaal verdwenen metselwerk
        synonyms = [
            "ontbreekt metselwerk",
            "vermist metselwerk",
            "uitgespoeld metselwerk",
            "gat in metselwerk",
            "lokale beschadiging metselwerk",
        ]
        if any(synonym in omschrijving for synonym in synonyms) and is_algemeen_gebrek(gebrek.codering):
            llm_result = await LokaalVerdwenenMetselwerkLLM.classificeer_omschrijving(gebrek.omschrijving)
            return LokaalVerdwenenMetselwerk(
                **gebrek.model_dump(),
                **llm_result.model_dump(),
            )

        return gebrek  # Retourneer het originele gebrek als geen subtype herkend is


class Scheur(Gebrek):
    """Model voor een scheur.

    Attributes
    ----------
    afstand_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters. Te vinden in de omschrijving
        van de gebrekentabel, bijv. "Op X meter vanaf start rak...".
    lengte_cm : float | NietBeschikbaar
        Lengte van de scheur in centimeters. Te vinden in de omschrijving
        van de gebrekentabel.
    scheurwijdte_mm : float | NietBeschikbaar
        Maximale scheurwijdte in millimeters. Te vinden in de omschrijving
        van de gebrekentabel, vaak als 'SW'.
    """

    afstand_van_startrak_m: float | NietBeschikbaar = NietBeschikbaar.LEEG
    lengte_cm: float | NietBeschikbaar = NietBeschikbaar.LEEG
    scheurwijdte_mm: float | NietBeschikbaar = NietBeschikbaar.LEEG


class ScheurMetselwerk(Scheur):
    """Model voor een scheur in metselwerk.

    Attributes
    ----------
    afstand_van_waterlijn_cm : float | NietBeschikbaar
        Afstand van de waterlijn in centimeters.
    afstand_van_deksloof_cm : float | NietBeschikbaar
        Afstand van de deksloof in centimeters.
    is_inprikbaar : bool | NietBeschikbaar
        Indicatie of de scheur inprikbaar is.
    orientatie : Literal["verticaal", "horizontaal", "diagonaal"] | NietBeschikbaar
        Oriëntatie van de scheur.
    """

    afstand_van_startrak_m: float | NietBeschikbaar = NietBeschikbaar.LEEG
    afstand_van_waterlijn_cm: float | NietBeschikbaar = NietBeschikbaar.LEEG
    afstand_van_deksloof_cm: float | NietBeschikbaar = NietBeschikbaar.LEEG
    is_inprikbaar: bool | NietBeschikbaar = NietBeschikbaar.LEEG
    orientatie: Literal["verticaal", "horizontaal", "diagonaal"] | NietBeschikbaar = NietBeschikbaar.LEEG


class ScheurHout(Scheur):
    """Model voor een scheur in hout.

    Attributes
    ----------
    diepte_cm : float | NietBeschikbaar
        Diepte van de scheur in centimeters.
    orientatie : Literal["verticaal", "horizontaal"] | NietBeschikbaar
        Oriëntatie van de scheur.
    """

    diepte_cm: float | NietBeschikbaar = NietBeschikbaar.LEEG
    orientatie: Literal["verticaal", "horizontaal"] | NietBeschikbaar = NietBeschikbaar.LEEG


class GrondVoerendGat(Gebrek):
    """Model voor een grondvoerend gat achter het metselwerk.

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

    afstand_van_startrak_m: float | NietBeschikbaar = NietBeschikbaar.LEEG
    breedte_cm: int | NietBeschikbaar = NietBeschikbaar.LEEG
    hoogte_cm: int | NietBeschikbaar = NietBeschikbaar.LEEG
    diepte_cm: int | NietBeschikbaar = NietBeschikbaar.LEEG


class BuikInWand(Gebrek):
    """Model voor een buik in wand.

    Attributes
    ----------
    afstand_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters.
    uitbuiking_cm : int | NietBeschikbaar
        Mate van uitbuiging in centimeters. Te vinden in de omschrijving
        van de gebrekentabel.
    """

    afstand_van_startrak_m: float | NietBeschikbaar = NietBeschikbaar.LEEG
    uitbuiking_cm: int | NietBeschikbaar


class Scheefstand(Gebrek):
    """Model voor scheefstand.

    Attributes
    ----------
    afstand_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters.
    hoek_graden : int | NietBeschikbaar
        Hoek van de scheefstand in graden. Te vinden in de omschrijving
        van de gebrekentabel indien vermeld.
    """

    afstand_van_startrak_m: float | NietBeschikbaar = NietBeschikbaar.LEEG
    hoek_graden: int | NietBeschikbaar = NietBeschikbaar.LEEG


class LokaalVerdwenenMetselwerk(Gebrek):
    """Model voor lokaal verdwenen metselwerk.

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

    afstand_van_startrak_m: float | NietBeschikbaar = NietBeschikbaar.LEEG
    breedte_cm: int | NietBeschikbaar = NietBeschikbaar.LEEG
    hoogte_cm: int | NietBeschikbaar = NietBeschikbaar.LEEG
    diepte_cm: int | NietBeschikbaar = NietBeschikbaar.LEEG


class OnderloopsheidschermBeschadigd(Gebrek):
    """Model voor een onderloopsheidscherm."""

    is_beschadigd: bool = True
