from __future__ import annotations
from dataclasses import dataclass

from azure.ai.documentintelligence.models import DocumentTable, DocumentParagraph

from tekstherkenning_ark.document.sectie import Sectie
from tekstherkenning_ark.utils import get_constructienaam, get_table_content, remove_titel_rows, remove_invalid_rows


@dataclass
class RakdeelSectie:
    """Representeert een rakdeel sectie met constructie informatie.

    Attributes
    ----------
    constructie_naam : str
        Naam van de constructie.
    beschrijving : list[DocumentParagraph]
        Beschrijvende paragrafen.
    toestand_tabel : list[list[str]]
        Tabelinhoud met toestandsinformatie.
    gebreken_tabel : list[list[str]]
        Tabelinhoud met gebrekeninformatie.
    """

    constructie_naam: str
    beschrijving: list[DocumentParagraph]
    toestand_tabel: list[list[str]]
    gebreken_tabel: list[list[str]]

    @classmethod
    def from_smart_document(cls, secties: list[Sectie]) -> RakdeelSectie:
        """Maak een rakdeel sectie uit SmartDocument-secties.

        Parameters
        ----------
        secties : list[Sectie]
            Lijst met alle secties uit het SmartDocument.

        Returns
        -------
        RakdeelSectie
            Geconstrueerde rakdeel sectie met beschrijving en tabellen.

        Raises
        ------
        ValueError
            Als de index buiten bereik valt.
        """
        constructie_naam = ""
        beschrijving = []
        toestand_tabel = []
        gebreken_tabel = []

        for sectie in secties:
            # if sectie titel contains "constructie [a-z]" then it is the base rakdeelsectie
            if get_constructienaam(sectie.titel) and not constructie_naam:
                constructie_naam = get_constructienaam(sectie.titel) or ""
                beschrijving = sectie.inhoud
            elif "toestand" in sectie.titel.lower() and not toestand_tabel:
                toestand_tabel = RakdeelSectie._get_toestand_tabel(sectie.tabellen)
            elif "gebrek" in sectie.titel.lower() and not gebreken_tabel:
                gebreken_tabel = RakdeelSectie._get_gebreken_tabel(sectie.tabellen)
                break

        return cls(
            constructie_naam=constructie_naam or "Onbekende constructie",
            beschrijving=beschrijving,
            toestand_tabel=toestand_tabel,
            gebreken_tabel=gebreken_tabel,
        )

    @staticmethod
    def _get_toestand_tabel(list_of_tables: list[DocumentTable]) -> list[list[str]]:
        """Helper om de juiste toestand tabel te vinden uit een lijst van tabellen."""
        rows: list[list[str]] = []

        for tabel in list_of_tables:
            if tabel.cells:
                rows.extend(get_table_content(tabel))
        rows_wo_header = remove_titel_rows(rows)
        rows_cleaned = remove_invalid_rows(rows_wo_header)
        return rows_cleaned

    @staticmethod
    def _get_gebreken_tabel(list_of_tables: list[DocumentTable]) -> list[list[str]]:
        """Helper om de juiste gebreken tabel te vinden uit een lijst van tabellen."""
        rows: list[list[str]] = []
        for tabel in list_of_tables:
            if tabel.column_count == 3 and tabel.cells:
                rows.extend(get_table_content(tabel))
        rows_wo_header = remove_titel_rows(rows)
        rows_cleaned = remove_invalid_rows(rows_wo_header)
        return rows_cleaned
