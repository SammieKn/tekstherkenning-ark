from typing import Literal
from pydantic import BaseModel
from azure.ai.documentintelligence.models import DocumentTable

from tekstherkenning_ark.utils import get_table_content


class Gebrek(BaseModel):
    """Model representing a 'gebrek' (deficiency or issue).

    Attributes:
        locatie_meter: Locatie van het gebrek in meters.
        codering: Codering van het gebrek.
        omschrijving: Omschrijving van het gebrek.
    """

    codering: str
    omschrijving: str
    figuurnummer: str

    @classmethod
    def from_doc_table(cls, doc_table:  DocumentTable) -> list["Gebrek"]:
        """Create a list of Gebrek instances from a document table.

        Parameters
        ------------
        doc_table : DocumentTable
            The document table containing gebreken data

        Returns
        ---------
        list[Gebrek]: A list of Gebrek instances.
        """
        table_as_list_str = get_table_content(doc_table)

        # assuming first row is header and contains these expected columns
        expected_header = ['Gebrekcodering', 'Omschrijving', 'Figuurnummer']
        if not table_as_list_str[0] == expected_header:
            raise ValueError(f"Unexpected table header. "
                             f"Expected {expected_header}, got {table_as_list_str[0]}")

        # Parsing logic to create Gebrek instances
        list_gebreken = []
        for row in table_as_list_str[1:]:
            try:
                gebrek_instance = cls(
                    codering=row[0],
                    omschrijving=row[1],
                    figuurnummer=row[2]
                )
            except Exception as e:
                # what to do with errors?
                raise ValueError(f"Error parsing row {row}: {e}")

            list_gebreken.append(gebrek_instance)

        return list_gebreken


class Scheur(Gebrek):
    """Scheur (crack).

    Attributes:
        lengte_cm: Lengte van de scheur in centimeters.
        scheurwijdte_mm: Maximale scheurwijdte in millimeters.
        afstand_van_startrak: Afstand van het startrak.
        orientatie: Orientatie van de scheur (vertikaal of horizontaal).
    """

    # Te vinden in de omschrijving van de gebrekentabel.
    lengte_cm: int
    # Te vinden in de omschrijving van de gebrekentabel, vaak als 'SW'.
    scheurwijdte_mm: int

    # Te vinden in de omschrijving van de gebrekentabel, "Op X meter vanaf start rak is een verticale scheur .."
    afstand_van_startrak: int | None = None

    # Te vinden in de omschrijving van de gebrekentabel, "Op X meter vanaf start rak is een verticale scheur .."
    orientatie: Literal["vertikaal", "horizontaal"] | None = None


class GrondVoerendGat(Gebrek):
    """Grondvoerend gat.

    Attributes:
        afmetingen_cm: Afmetingen van het gat in centimeters (b x h x d).
    """

    # Te vinden in de omschrijving van de gebrekentabel.
    afmetingen_cm: list[int | None]


class BuikInWand(Gebrek):
    """Buik in wand.

    Attributes:
        uitbuiging_cm: Mate van uitbuiging in centimeters.
    """

    # Te vinden in de omschrijving van de gebrekentabel.
    uitbuiking_cm: int


class Scheefstand(Gebrek):
    """Scheefstand.

    Attributes:
        hoek_graden: Hoek van de scheefstand in graden.
    """

    # Te vinden in de omschrijving van de gebrekentabel indien vermeld.
    hoek_graden: int


class LokaalVerdwenenMetselwerk(Gebrek):
    """Lokaal verdwenen metselwerk.

    Attributes:
        afmetingen_cm: Afmetingen van het verdwenen metselwerk in centimeters (b x h x d).
    """

    # Te vinden in de omschrijving van de gebrekentabel.
    afmetingen_cm: list[int | None]
