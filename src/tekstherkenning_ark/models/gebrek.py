from __future__ import annotations

import asyncio
from typing import Literal
from pydantic import BaseModel, computed_field

from tekstherkenning_ark.utils import (
    clean_string,
    contains_kesp_id,
    contains_paal_id,
    is_algemeen_gebrek,
)
from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.document.structured_table import StructuredTable
from tekstherkenning_ark.llm.gebrek_classificatie import (
    GebrekTypeDetectieLLM,
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
        resultaten = await asyncio.gather(*classificatie_taken)
        list_gebreken = [g for sublijst in resultaten for g in sublijst]

        return list_gebreken

    @staticmethod
    async def classify_gebrek(gebrek: Gebrek) -> list[Gebrek]:
        """Classificeer een Gebrek instantie naar een of meer specifieke subtypes.

        Delegeert naar `classify_paal_kesp_gebrek` voor paal- en kespcoderingen,
        en naar `classify_algemeen_gebrek` voor algemene gebreken.

        Parameters
        ----------
        gebrek : Gebrek
            Een Gebrek instantie.

        Returns
        -------
        list[Gebrek]
            Een lijst van specifieke subtypes van Gebrek met geëxtraheerde
            attributen. Bevat het originele gebrek als geen type herkend is.
        """
        if contains_paal_id(gebrek.codering) or contains_kesp_id(gebrek.codering):
            return await Gebrek.classify_paal_kesp_gebrek(gebrek)
        return await Gebrek.classify_algemeen_gebrek(gebrek)

    @staticmethod
    async def classify_paal_kesp_gebrek(gebrek: Gebrek) -> list[Gebrek]:
        """Classificeer een gebrek met een paal- of kespcodering.

        Wanneer de omschrijving een scheur bevat, wordt het gebrek geclassificeerd
        als ScheurHout via een LLM. Anders wordt het originele gebrek teruggegeven.

        Parameters
        ----------
        gebrek : Gebrek
            Een Gebrek instantie met een paal- of kespcodering.

        Returns
        -------
        list[Gebrek]
            Een lijst met één ScheurHout instantie, of het originele gebrek
            als er geen scheur in de omschrijving staat.
        """
        if "scheur" not in gebrek.omschrijving.lower():
            return [gebrek]

        llm_result = await ScheurHoutLLM.classificeer_omschrijving(gebrek.omschrijving)
        return [ScheurHout(**gebrek.model_dump(), **llm_result.model_dump())]

    @staticmethod
    async def classify_algemeen_gebrek(gebrek: Gebrek) -> list[Gebrek]:
        """Classificeer een algemeen gebrek naar een of meer specifieke subtypes.

        Gebruikt een LLM om te bepalen welk(e) type(n) gebrek(en) aanwezig zijn
        in de omschrijving. Wanneer meerdere types gedetecteerd worden, wordt voor
        elk type een apart subtype-object aangemaakt. LLM classificaties worden
        parallel uitgevoerd.

        Parameters
        ----------
        gebrek : Gebrek
            Een Gebrek instantie.

        Returns
        -------
        list[Gebrek]
            Een lijst van specifieke subtypes van Gebrek met geëxtraheerde
            attributen. Bevat het originele gebrek als geen type herkend is.
        """
        omschrijving = gebrek.omschrijving.lower()

        type_detectie = await GebrekTypeDetectieLLM.classificeer_omschrijving(gebrek.omschrijving)

        llm_taken = []

        if type_detectie.is_scheur:
            if "metselwerk" in omschrijving:
                llm_taken.append(ScheurMetselwerkLLM.classificeer_omschrijving(gebrek.omschrijving))
            else:
                llm_taken.append(ScheurLLM.classificeer_omschrijving(gebrek.omschrijving))

        if type_detectie.is_grondvoerend_gat and is_algemeen_gebrek(gebrek.codering):
            llm_taken.append(GrondVoerendGatLLM.classificeer_omschrijving(gebrek.omschrijving))

        if type_detectie.is_verdwenen_metselwerk and is_algemeen_gebrek(gebrek.codering):
            llm_taken.append(LokaalVerdwenenMetselwerkLLM.classificeer_omschrijving(gebrek.omschrijving))

        if type_detectie.is_buik_in_wand and is_algemeen_gebrek(gebrek.codering):
            llm_taken.append(BuikInWandLLM.classificeer_omschrijving(gebrek.omschrijving))

        if type_detectie.is_scheefstand and is_algemeen_gebrek(gebrek.codering):
            llm_taken.append(ScheefstandLLM.classificeer_omschrijving(gebrek.omschrijving))

        heeft_onderloopsheidscherm = type_detectie.is_onderloopsheidscherm and is_algemeen_gebrek(gebrek.codering)

        if not llm_taken and not heeft_onderloopsheidscherm:
            return [gebrek]

        llm_resultaten = list(await asyncio.gather(*llm_taken))

        geclassificeerde_gebreken = Gebrek._llm_resultaten_naar_gebreken(gebrek, llm_resultaten)

        if heeft_onderloopsheidscherm:
            geclassificeerde_gebreken.append(OnderloopsheidschermBeschadigd(**gebrek.model_dump()))

        return geclassificeerde_gebreken

    @staticmethod
    def _llm_resultaten_naar_gebreken(
        gebrek: Gebrek,
        llm_resultaten: list,
    ) -> list[Gebrek]:
        """Zet LLM classificatieresultaten om naar de correcte Gebrek subtype instanties.

        Parameters
        ----------
        gebrek : Gebrek
            Het originele gebrek waaruit de basisattributen worden overgenomen.
        llm_resultaten : list
            Lijst van LLM classificatieresultaten.

        Returns
        -------
        list[Gebrek]
            Een lijst van Gebrek subtype instanties.
        """
        geclassificeerde_gebreken: list[Gebrek] = []

        for llm_result in llm_resultaten:
            if isinstance(llm_result, ScheurHoutLLM):
                geclassificeerde_gebreken.append(ScheurHout(**gebrek.model_dump(), **llm_result.model_dump()))
            elif isinstance(llm_result, ScheurMetselwerkLLM):
                geclassificeerde_gebreken.append(ScheurMetselwerk(**gebrek.model_dump(), **llm_result.model_dump()))
            elif isinstance(llm_result, ScheurLLM):
                geclassificeerde_gebreken.append(Scheur(**gebrek.model_dump(), **llm_result.model_dump()))
            elif isinstance(llm_result, GrondVoerendGatLLM):
                geclassificeerde_gebreken.append(GrondVoerendGat(**gebrek.model_dump(), **llm_result.model_dump()))
            elif isinstance(llm_result, LokaalVerdwenenMetselwerkLLM):
                geclassificeerde_gebreken.append(
                    LokaalVerdwenenMetselwerk(**gebrek.model_dump(), **llm_result.model_dump())
                )
            elif isinstance(llm_result, BuikInWandLLM):
                geclassificeerde_gebreken.append(BuikInWand(**gebrek.model_dump(), **llm_result.model_dump()))
            elif isinstance(llm_result, ScheefstandLLM):
                geclassificeerde_gebreken.append(Scheefstand(**gebrek.model_dump(), **llm_result.model_dump()))

        return geclassificeerde_gebreken


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
    start_buik_van_startrak_m_ingevuld : float | NietBeschikbaar
        Direct uitgelezen startafstand van het startrak in meters.
    eind_buik_van_startrak_m_ingevuld : float | NietBeschikbaar
        Direct uitgelezen eindafstand van het startrak in meters.
    lengte_buik_m_ingevuld : float | NietBeschikbaar
        Direct uitgelezen lengte van de buik in meters.
    uitbuiking_cm : int | NietBeschikbaar
        Mate van uitbuiging in centimeters. Te vinden in de omschrijving
        van de gebrekentabel.
    start_buik_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters bij het begin van de buik.
        Wordt afgeleid als niet direct beschikbaar.
    eind_buik_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters bij het einde van de buik.
        Wordt afgeleid als niet direct beschikbaar.
    lengte_buik_m : float | NietBeschikbaar
        Lengte van de buik in meters. Wordt afgeleid als niet direct beschikbaar.
    """

    start_buik_van_startrak_m_ingevuld: float | NietBeschikbaar = NietBeschikbaar.LEEG
    eind_buik_van_startrak_m_ingevuld: float | NietBeschikbaar = NietBeschikbaar.LEEG
    lengte_buik_m_ingevuld: float | NietBeschikbaar = NietBeschikbaar.LEEG
    uitbuiking_cm: int | NietBeschikbaar

    @computed_field
    @property
    def start_buik_van_startrak_m(self) -> float | NietBeschikbaar:
        """Afstand van het startrak in meters. Wordt afgeleid van de start van de buik."""
        if isinstance(self.start_buik_van_startrak_m_ingevuld, float):
            return self.start_buik_van_startrak_m_ingevuld
        elif all(
            (
                isinstance(value, float)
                for value in (self.eind_buik_van_startrak_m_ingevuld, self.lengte_buik_m_ingevuld)
            )
        ):
            return self.eind_buik_van_startrak_m_ingevuld - self.lengte_buik_m_ingevuld
        else:
            return NietBeschikbaar.LEEG

    @computed_field
    @property
    def eind_buik_van_startrak_m(self) -> float | NietBeschikbaar:
        """Afstand van het startrak in meters. Wordt afgeleid van het eind van de buik."""
        if isinstance(self.eind_buik_van_startrak_m_ingevuld, float):
            return self.eind_buik_van_startrak_m_ingevuld
        elif all(
            (
                isinstance(value, float)
                for value in (self.start_buik_van_startrak_m_ingevuld, self.lengte_buik_m_ingevuld)
            )
        ):
            return self.start_buik_van_startrak_m_ingevuld + self.lengte_buik_m_ingevuld
        else:
            return NietBeschikbaar.LEEG

    @computed_field
    @property
    def lengte_buik_m(self) -> float | NietBeschikbaar:
        """Lengte van de buik in meters. Wordt afgeleid van de start en eind van de buik."""
        if isinstance(self.lengte_buik_m_ingevuld, float):
            return self.lengte_buik_m_ingevuld
        elif all(
            (
                isinstance(value, float)
                for value in (self.start_buik_van_startrak_m_ingevuld, self.eind_buik_van_startrak_m_ingevuld)
            )
        ):
            return self.eind_buik_van_startrak_m_ingevuld - self.start_buik_van_startrak_m_ingevuld
        else:
            return NietBeschikbaar.LEEG


class Scheefstand(Gebrek):
    """Model voor scheefstand.

    Attributes
    ----------
    start_scheefstand_van_startrak_m_ingevuld : float | NietBeschikbaar
        Direct uitgelezen startafstand van het startrak in meters.
    eind_scheefstand_van_startrak_m_ingevuld : float | NietBeschikbaar
        Direct uitgelezen eindafstand van het startrak in meters.
    lengte_scheefstand_m_ingevuld : float | NietBeschikbaar
        Direct uitgelezen lengte van de scheefstand in meters.
    hoek_graden : int | NietBeschikbaar
        Hoek van de scheefstand in graden. Te vinden in de omschrijving
        van de gebrekentabel indien vermeld.
    start_scheefstand_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters bij het begin van de scheefstand.
        Wordt afgeleid als niet direct beschikbaar.
    eind_scheefstand_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters bij het einde van de scheefstand.
        Wordt afgeleid als niet direct beschikbaar.
    lengte_scheefstand_m : float | NietBeschikbaar
        Lengte van de scheefstand in meters. Wordt afgeleid als niet direct beschikbaar.
    """

    start_scheefstand_van_startrak_m_ingevuld: float | NietBeschikbaar = NietBeschikbaar.LEEG
    eind_scheefstand_van_startrak_m_ingevuld: float | NietBeschikbaar = NietBeschikbaar.LEEG
    lengte_scheefstand_m_ingevuld: float | NietBeschikbaar = NietBeschikbaar.LEEG
    hoek_graden: int | NietBeschikbaar = NietBeschikbaar.LEEG

    @computed_field
    @property
    def start_scheefstand_van_startrak_m(self) -> float | NietBeschikbaar:
        """Afstand van het startrak in meters. Wordt afgeleid van de start van de scheefstand."""
        if isinstance(self.start_scheefstand_van_startrak_m_ingevuld, float):
            return self.start_scheefstand_van_startrak_m_ingevuld
        elif all(
            (
                isinstance(value, float)
                for value in (self.eind_scheefstand_van_startrak_m_ingevuld, self.lengte_scheefstand_m_ingevuld)
            )
        ):
            return self.eind_scheefstand_van_startrak_m_ingevuld - self.lengte_scheefstand_m_ingevuld
        else:
            return NietBeschikbaar.LEEG

    @computed_field
    @property
    def eind_scheefstand_van_startrak_m(self) -> float | NietBeschikbaar:
        """Afstand van het startrak in meters. Wordt afgeleid van het eind van de scheefstand."""
        if isinstance(self.eind_scheefstand_van_startrak_m_ingevuld, float):
            return self.eind_scheefstand_van_startrak_m_ingevuld
        elif all(
            (
                isinstance(value, float)
                for value in (self.start_scheefstand_van_startrak_m_ingevuld, self.lengte_scheefstand_m_ingevuld)
            )
        ):
            return self.start_scheefstand_van_startrak_m_ingevuld + self.lengte_scheefstand_m_ingevuld
        else:
            return NietBeschikbaar.LEEG

    @computed_field
    @property
    def lengte_scheefstand_m(self) -> float | NietBeschikbaar:
        """Lengte van de scheefstand in meters. Wordt afgeleid van de start en eind van de scheefstand."""
        if isinstance(self.lengte_scheefstand_m_ingevuld, float):
            return self.lengte_scheefstand_m_ingevuld
        elif all(
            (
                isinstance(value, float)
                for value in (
                    self.start_scheefstand_van_startrak_m_ingevuld,
                    self.eind_scheefstand_van_startrak_m_ingevuld,
                )
            )
        ):
            return self.eind_scheefstand_van_startrak_m_ingevuld - self.start_scheefstand_van_startrak_m_ingevuld
        else:
            return NietBeschikbaar.LEEG


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
