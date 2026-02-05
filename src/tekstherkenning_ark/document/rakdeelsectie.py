from __future__ import annotations
from dataclasses import dataclass

from azure.ai.documentintelligence.models import DocumentTable, DocumentParagraph

from tekstherkenning_ark.document.sectie import Sectie
from tekstherkenning_ark.utils import get_constructienaam


@dataclass
class RakdeelSectie:
    """Representeert een rakdeel sectie met constructie informatie.

    Attributes
    ----------
    constructie_naam : str
        Naam van de constructie.
    beschrijving : list[DocumentParagraph]
        Beschrijvende paragrafen.
    toestand_tabel : list[DocumentTable]
        Tabellen met toestandsinformatie.
    gebreken_tabel : list[DocumentTable]
        Tabellen met gebrekeninformatie.
    """

    constructie_naam: str
    beschrijving: list[DocumentParagraph]
    toestand_tabel: list[DocumentTable]
    gebreken_tabel: list[DocumentTable]

    @classmethod
    def from_smart_document(cls, secties: list[Sectie], index: int) -> RakdeelSectie:
        """Maak een rakdeel sectie uit SmartDocument-secties.

        Parameters
        ----------
        secties : list[Sectie]
            Lijst met alle secties uit het SmartDocument.
        index : int
            Index van de sectie die de constructie beschrijft.

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
            if get_constructienaam(sectie.titel):
                constructie_naam = get_constructienaam(sectie.titel) or ""
                beschrijving = sectie.inhoud
            elif "toestand" in sectie.titel.lower():
                toestand_tabel = RakdeelSectie._get_toestand_tabel(sectie.tabellen)
            elif "gebrek" in sectie.titel.lower():
                gebreken_tabel = RakdeelSectie._get_gebreken_tabel(sectie.tabellen)

        return cls(
            constructie_naam=constructie_naam,
            beschrijving=beschrijving,
            toestand_tabel=toestand_tabel,
            gebreken_tabel=gebreken_tabel,
        )

    @staticmethod
    def _get_toestand_tabel(list_of_tables: list[DocumentTable]) -> list[DocumentTable]:
        """Helper om de juiste toestand tabel te vinden uit een lijst van tabellen."""
        expected_headers = {"constructieonderdeel", "aangetast"}
        tabels = []
        for tabel in list_of_tables:
            if tabel.cells:
                first_row_cells = [cell.content.lower() for cell in tabel.cells if cell.row_index == 0]
                if set(first_row_cells) == expected_headers:
                    tabels.append(tabel)
        return tabels

    @staticmethod
    def _get_gebreken_tabel(list_of_tables: list[DocumentTable]) -> list[DocumentTable]:
        """Helper om de juiste gebreken tabel te vinden uit een lijst van tabellen."""
        tabels = []
        for tabel in list_of_tables:
            if tabel.column_count == 3 and tabel.cells:
                tabels.append(tabel)
        return tabels
