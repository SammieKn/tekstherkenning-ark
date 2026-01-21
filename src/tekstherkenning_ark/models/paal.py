from __future__ import annotations
from typing import Any

from pydantic import BaseModel

from tekstherkenning_ark.enums import Materiaal, SchoorStand, NietBeschikbaar, AansluitingStatus
from tekstherkenning_ark.models.gebrek import Gebrek, Scheefstand
from tekstherkenning_ark.models.houtmonster import Houtmonster
from azure.ai.documentintelligence.models import DocumentTable


class Paal(BaseModel):
    """Paal (Foundation Pile).

    Attributes:
        gebreken: Lijst van gebreken gevonden in de paal.
        paalrij_nummer: Nummer van de paalrij waartoe de paal behoort.
        paalnummer: Nummer van de paal binnen de paalrij.
        aansluiting_status: Status van de aansluiting paal-kesp of paal-vloer.
        is_negatief_schoor: Indicatie of de paal negatief schoor staat (PNA in de tabel).
        is_onderzocht: Indicatie of de paal is onderzocht.
        opmerkingen: Eventuele opmerkingen over de paal.
        schoorstand_graden: Schoorstand van de paal in graden.
        scheefstand: Indicatie of de paal scheefstand heeft.
        materiaal: Materiaal van de paal.
        diameter_haaks: Diameter haaks op de gevel in mm.
        diameter_parallel: Diameter parallel aan de gevel in mm.
        diameter_gemiddeld: Gemiddelde diameter in mm.
        afstand_hoh: Hart-op-hart afstand tussen palen in mm.
        schoor_graden: Schoorstand van de paal in graden.
        schoor_richting: Richting van de schoorstand (PNV/PNA/LR).
        afstand_frontwand_cm: Afstand tot de frontwand in cm.
        is_scheefstand: Indicatie of er scheefstand is geconstateerd.
        is_paalbreak: Indicatie of er paalbreuk is geconstateerd.
        is_aantasting: Indicatie of er aantasting is geconstateerd.
        is_juiste_aansluiting: Indicatie of de aansluiting correct is.
        positionering_aansluiting_cm: Positionering van de aansluiting in cm.
        houtmonsters: Lijst van houtmonsters genomen uit deze paal.
    """

    # Te vinden in de schades en gebreken tabellen van hoofdstuk 5.
    gebreken: list[Gebrek] = []
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalnummer'.
    paalrij_nummer: str
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalnummer'.
    paalrij_nummer: str
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalnummer'.
    paalnummer: str
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalrij'.
    paalrij_nummer: str
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Aansluiting'.
    aansluiting_status: AansluitingStatus
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Onderzocht'.
    is_onderzocht: bool | None = None
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Opmerkingen'.
    opmerkingen: str = ""
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Schoorstand'.
    schoorstand_graden: float | None = None
    scheefstand: bool | None = None
    materiaal: Materiaal | None = None

    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolommen 'diameter'.
    diameter_haaks: int | NietBeschikbaar
    diameter_parallel: int | NietBeschikbaar
    diameter_gemiddeld: int | NietBeschikbaar

    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Hart-op-hart-afstanden' -> 'afstand' en 'Paal'.
    hoh_afstand_cm: int | NietBeschikbaar
    hoh_paalnummer: str

    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolommen 'Schoorstand'.
    schoor_graden: int | NietBeschikbaar
    schoor_richting: SchoorStand | NietBeschikbaar

    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Afstand frontwand'.
    afstand_frontwand_cm: int | NietBeschikbaar
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolommen 'Schades'.
    is_scheefstand: bool | NietBeschikbaar
    is_paalbreak: bool | NietBeschikbaar
    is_aantasting: bool | NietBeschikbaar
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolommen 'aansluiting'.
    is_juiste_aansluiting: bool | NietBeschikbaar
    positionering_aansluiting_cm: int | NietBeschikbaar
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Opmerkingen'.
    opmerkingen: str = ""

    # Te vinden in bijlage 2 en houtmonsters csv.
    # Te vinden in Bijlage 1, kolom 'Paalnummer' en 'Houtmonster'. @Sammie welke van deze twee is waar?
    houtmonsters: list[Houtmonster] = []

    @classmethod
    def from_doc_table(cls, table: DocumentTable) -> list[Paal]:
        """Parse and return a list of Paal objects from a Azure Doc
        Intelligence DocumentTable object

        Parameters
        ----------
        table : DocumentTable
            DocumentTable object as returned by Azure Document Intelligence SDK
            belonging to the `Palen` bijlage

        Returns
        -------
        list[Paal]
            A list of Paal objects containing information from the table
        """
        from tekstherkenning_ark.parsed_pdf import ParsedPDF

        rows = ParsedPDF.extract_table_content(table)

        for line in rows:
            print(line)

        data_rows = rows[7:]  # Skip header rows

        a = 1

    @classmethod
    def from_paal_table_row(cls, row: list[str]) -> Paal:
        """Parse and return a Paal object from a single row of the
        funderingspalen table.

        Parameters
        ----------
        row : list[str]
            A single row from the funderingspalen table as a list of strings.

        Returns
        -------
        Paal
            A Paal object containing information from the row.
        """

        return cls(
            paalnummer=row[0],
            diameter_haaks=row[1],
            diameter_parallel=row[2],
            diameter_gemiddeld=row[3],
            hoh_afstand_cm=row[4],
            hoh_paalnummer=row[5],
            schoor_graden=row[8],
            schoor_richting=row[9],
        )
