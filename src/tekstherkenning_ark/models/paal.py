from __future__ import annotations
from typing import Any

from tekstherkenning_ark import utils
from tekstherkenning_ark.enums import MateriaalOnderbouw, SchoorStand, NietBeschikbaar, AansluitingStatus
from tekstherkenning_ark.models.gebrek import Gebrek, Scheefstand
from tekstherkenning_ark.models.houtmonster import Houtmonster
from tekstherkenning_ark.models.rak_base_model import RakBaseModel
from azure.ai.documentintelligence.models import DocumentTable
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat

logger = get_logger(__name__)


class Paal(RakBaseModel):
    """Paal (Foundation Pile).

    Attributes:
        paalrij_nummer: Nummer van de paalrij waartoe de paal behoort.
        paal_nummer: Nummer van de paal binnen de paalrij.
        aansluiting_status: Status van de aansluiting paal-kesp of paal-vloer.
        is_negatief_schoor: Indicatie of de paal negatief schoor staat (PNA in de tabel).
        is_onderzocht: Indicatie of de paal is onderzocht.
        schoorstand_graden: Schoorstand van de paal in graden.
        scheefstand: Indicatie of de paal scheefstand heeft.
        materiaal: Materiaal van de paal. (MateriaalOnderbouw)
        diameter_haaks: Diameter haaks op de gevel in mm.
        diameter_parallel: Diameter parallel aan de gevel in mm.
        diameter_gemiddeld: Gemiddelde diameter in mm.
        afstand_hoh: Hart-op-hart afstand tussen palen in mm.
        schoor_graden: Schoorstand van de paal in graden.
        schoor_richting: Richting van de schoorstand (PNV/PNA/LR).
        afstand_frontwand_cm: Afstand tot de frontwand in cm.
        is_scheefstand: Indicatie of er scheefstand is geconstateerd.
        is_paalbreuk: Indicatie of er paalbreuk is geconstateerd.
        is_aantasting: Indicatie of er aantasting is geconstateerd.
        is_juiste_aansluiting: Indicatie of de aansluiting correct is.
        positionering_aansluiting_cm: Positionering van de aansluiting in cm.
        houtmonsters: Lijst van houtmonsters genomen uit deze paal.
        gebreken: Lijst van gebreken (inherited from RakBaseModel).
        opmerkingen: Eventuele opmerkingen (inherited from RakBaseModel).
    """

    # Te vinden in de schades en gebreken tabellen van hoofdstuk 5.
    gebreken: list[Gebrek] = []

    # TODO Waar te vinden? - MT
    paalrij_nummer: str = ""

    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalnummer'.
    paal_nummer: str

    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Onderzocht'.
    is_onderzocht: bool | None = None

    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Schoorstand'.
    schoorstand_graden: float | None = None
    scheefstand: bool | None = None
    materiaal: MateriaalOnderbouw | None = None

    @property
    def identifier(self) -> str:
        """Return a string that uniquely identifies this Paal instance."""
        return str(self.paal_nummer)

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
    is_paalbreuk: bool | NietBeschikbaar
    is_aantasting: bool | NietBeschikbaar

    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Aansluiting'.
    aansluiting_status: AansluitingStatus | OnverwachtResultaat
    positionering_aansluiting_cm: str | NietBeschikbaar

    # Te vinden in bijlage 2 en houtmonsters csv.
    # Te vinden in Bijlage 1, kolom 'Paalnummer' en 'Houtmonster'. @Sammie welke van deze twee is waar?
    houtmonsters: list[Houtmonster] = []

    @property
    def paal_nummer_main(self) -> int:
        """Geef het hoofdnummer van de paal terug als integer. (P1.12 -> 12)"""

        return int(self.paal_nummer.split(".")[1])

    @classmethod
    def from_doc_tables(cls, tables: list[DocumentTable]) -> dict[str, list[Paal]]:
        """Parse and return a list of Paal objects from a Azure Doc
        Intelligence DocumentTable object

        Parameters
        ----------
        tables : list[DocumentTable]
            List of DocumentTable objects as returned by Azure Document Intelligence SDK
            belonging to the `Palen` bijlage

        Returns
        -------
        dict[str, list[Paal]]
            A dictionary mapping constructie ID's to lists of Paal objects containing information from the table
        """

        paal_rows: list[list[str]] = []
        for table in tables:

            # Extract table content as list of rows
            table_rows = utils.get_table_content(table)

            # Skip header rows and add to paal_rows
            content_rows = [r for r in table_rows if utils.contains_paal_id(r[0])]
            paal_rows.extend(content_rows)

        # Parse each row into a Paal object
        paal_dict: dict[str, list[Paal]] = {}
        current_constructie_id = ""

        last_main_paal_nummer = 0

        for row in paal_rows:
            if len(row) != 17:
                logger.warning(f"Onverwacht aantal kolommen in paal rij: verwacht 17, kreeg {len(row)}. Rij: {row}")
                continue
            constructie_id_col_val = utils.clean_string(row[16])

            #

            if constructie_id_col_val != "":
                current_constructie_id = constructie_id_col_val

                if current_constructie_id not in paal_dict:
                    paal_dict[current_constructie_id] = []
                else:
                    logger.warning(f"Duplicate constructie ID found: {current_constructie_id}")

            if current_constructie_id != "":
                paal = cls.from_paal_table_row(row)

                # Validate paal nummers are sequential
                if not paal.paal_nummer_main in [last_main_paal_nummer, last_main_paal_nummer + 1]:
                    logger.warning(
                        f"Paal nummers are not sequential. Expected {last_main_paal_nummer} or {last_main_paal_nummer + 1}, got {paal.paal_nummer_main} for {paal.paal_nummer}. \nLast 5 palen: {[p.paal_nummer for p in paal_dict[current_constructie_id][-5:]]}"
                    )
                last_main_paal_nummer = paal.paal_nummer_main

                # Add paal to the correct constructie ID list
                paal_dict[current_constructie_id].append(paal)

        return paal_dict

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

        row_clean = [utils.clean_string(val) for val in row]
        return cls(
            paal_nummer=utils.clean_paal_id(row_clean[0]),
            diameter_haaks=utils.convert_string_to_int(row_clean[1]),
            diameter_parallel=utils.convert_string_to_int(row_clean[2]),
            diameter_gemiddeld=utils.convert_string_to_int(row_clean[3]),
            hoh_afstand_cm=utils.convert_string_to_int(row_clean[4]),
            hoh_paalnummer=row_clean[5],
            schoor_graden=utils.convert_string_to_int(row_clean[8]),
            schoor_richting=row_clean[9],
            afstand_frontwand_cm=utils.convert_string_to_int(row_clean[10]),
            is_scheefstand=utils.parse_ja_nee(row_clean[11]),
            is_paalbreuk=utils.parse_ja_nee(row_clean[12]),
            is_aantasting=utils.parse_ja_nee(row_clean[13]),
            aansluiting_status=row_clean[14],
            positionering_aansluiting_cm=row_clean[15],
        )


if __name__ == "__main__":

    from tekstherkenning_ark.smart_document import SmartDocument
    from tekstherkenning_ark import constants

    doc = SmartDocument.from_pdf(constants.TEST_PDF_PATH)

    paal_tables = doc.get_meettabel_fundering_paal()
    palen_dict = Paal.from_doc_tables(paal_tables)

    for palen in palen_dict.values():
        for paal in palen:
            print(paal.paal_nummer)
