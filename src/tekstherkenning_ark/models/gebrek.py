from __future__ import annotations

from typing import Literal
from pydantic import BaseModel
from azure.ai.documentintelligence.models import DocumentTable

from tekstherkenning_ark.utils import get_table_content, contains_kesp_id, contains_paal_id, is_algemeen_gebrek
from tekstherkenning_ark.enums import NietBeschikbaar


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
    def from_doc_tables(cls, tables: list[DocumentTable]) -> list[Gebrek]:
        """Maak een lijst van Gebrek instanties uit meerdere document tabellen.

        Parameters
        ----------
        tables : list[DocumentTable]
            Lijst van DocumentTable objecten zoals teruggegeven door Azure Document Intelligence SDK
            behorend bij de gebreken bijlage

        Returns
        -------
        list[Gebrek]
            Een lijst van Gebrek instanties.
        """
        expected_header = ["Gebrekcodering", "Omschrijving", "Figuurnummer"]

        gebrek_rows: list[list[str]] = []
        for table in tables:
            # Extraheer tabel inhoud als lijst van rijen
            table_rows = get_table_content(table)

            # Controleer header van eerste tabel
            if len(gebrek_rows) == 0 and table_rows[0] != expected_header:
                raise ValueError(f"Onverwachte tabel header. " f"Verwacht {expected_header}, kreeg {table_rows[0]}")

            # Sla header rijen over en voeg toe aan gebrek_rows
            content_rows = [r for r in table_rows if r[0] != expected_header[0]]
            gebrek_rows.extend(content_rows)

        # Parsing logica om Gebrek instanties te maken
        list_gebreken = []
        for row in gebrek_rows:
            if row[0].strip() == "-" or row[0].strip() == "":
                break
            try:
                gebrek_instance = cls(codering=row[0], omschrijving=row[1], figuurnummer=row[2])
            except Exception as e:
                raise ValueError(f"Fout bij parsen van rij {row}: {e}")

            list_gebreken.append(gebrek_instance)

        return list_gebreken

    @staticmethod
    def classify_gebrek(gebrek: Gebrek) -> Gebrek:
        """Classificeer een Gebrek instantie naar een specifiek subtype.

        Parameters
        ----------
        gebrek : Gebrek
            Een Gebrek instantie.

        Returns
        -------
        Gebrek
            Een specifiek subtype van Gebrek.
        """
        omschrijving = gebrek.omschrijving.lower()

        # logica voor scheur
        if "scheur" in omschrijving:
            if contains_paal_id(omschrijving) or contains_kesp_id(gebrek.codering):
                pass
                # code to classify as ScheurHout based on llm
            elif "metselwerk" in omschrijving:
                pass
                # code to classify as ScheurMetselwerk based on llm

        # logica voor grondvoerend gat
        if "grondvoerend" in omschrijving and is_algemeen_gebrek(gebrek.codering):
            pass
            # code to classify as GrondVoerendGat based on llm

        # logica voor buikinwand
        if "buik" in omschrijving and is_algemeen_gebrek(gebrek.codering):
            pass
            # code to classify as BuikInWand based on llm

        if "scheefstand" in omschrijving and is_algemeen_gebrek(gebrek.codering):
            pass
            # code to classify as Scheefstand based on llm

        # logica voor lokaal verdwenen metselwerk
        # TODO: uitbreiden met echte synoniemen
        synonyms = [
            "ontbreekt metselwerk",
            "vermist metselwerk",
            "uitgespoeld metselwerk",
            "gat in metselwerk",
            "lokale beschadiging metselwerk",
        ]
        if any(synonym in omschrijving for synonym in synonyms) and is_algemeen_gebrek(gebrek.codering):
            pass
            # code to classify as LokaalVerdwenenMetselwerk based on llm\

        return gebrek  # Retourneer het originele gebrek als geen subtype herkend is


class Scheur(Gebrek):
    """Model voor een scheur.

    Attributes
    ----------
    lengte_cm : float | NietBeschikbaar
        Lengte van de scheur in centimeters. Te vinden in de omschrijving
        van de gebrekentabel.
    scheurwijdte_mm : float | NietBeschikbaar
        Maximale scheurwijdte in millimeters. Te vinden in de omschrijving
        van de gebrekentabel, vaak als 'SW'.
    """

    lengte_cm: float | NietBeschikbaar
    scheurwijdte_mm: float | NietBeschikbaar


class ScheurMetselwerk(Scheur):
    """Model voor een scheur in metselwerk.

    Attributes
    ----------
    afstand_van_startrak_m : float | NietBeschikbaar
        Afstand van het startrak in meters. Te vinden in de omschrijving
        van de gebrekentabel, bijv. "Op X meter vanaf start rak...".
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
    afmetingen_cm : list[int | NietBeschikbaar]
        Afmetingen van het gat in centimeters (b x h x d). Te vinden in
        de omschrijving van de gebrekentabel.
    """

    afstand_van_startrak_m: float | NietBeschikbaar = NietBeschikbaar.LEEG
    afmetingen_cm: list[int | NietBeschikbaar]


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
    afmetingen_cm : list[int | NietBeschikbaar]
        Afmetingen van het verdwenen metselwerk in centimeters (b x h x d).
        Te vinden in de omschrijving van de gebrekentabel.
    """

    afstand_van_startrak_m: float | NietBeschikbaar = NietBeschikbaar.LEEG
    afmetingen_cm: list[int | NietBeschikbaar]
