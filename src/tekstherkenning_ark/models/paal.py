from __future__ import annotations

from tekstherkenning_ark import utils
from tekstherkenning_ark.enums import MateriaalOnderbouw, SchoorStand, NietBeschikbaar, AansluitingStatus
from tekstherkenning_ark.models.gebrek import Gebrek, Scheefstand
from tekstherkenning_ark.models.houtmonster import Houtmonster
from tekstherkenning_ark.models.rak_base_model import RakBaseModel
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat
from tekstherkenning_ark.document.structured_table import StructuredTable

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

    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalnummer'.
    paal_nummer: str

    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Onderzocht'.
    is_onderzocht: bool | None = None

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
    def identifier(self) -> str:
        """Return a string that uniquely identifies this Paal instance."""
        return str(self.paal_nummer)

    @property
    def paal_nummer_main(self) -> int | None:
        """Geef het hoofdnummer van de paal terug als integer. (P1.12 -> 12)"""

        try:
            return int(self.paal_nummer.split(".")[1])
        except:
            logger.warning(f"Failed to extract main nummer from paal nummer {self.paal_nummer}")
            return None

    @classmethod
    def from_doc_tables(cls, structured_table: StructuredTable | None) -> dict[str, list[Paal]]:
        """Parse and return a list of Paal objects from a structured table.

        Parameters
        ----------
        structured_table : StructuredTable
            Structured table containing paal data with expected headers and sub-headers.

        Returns
        -------
        dict[str, list[Paal]]
            A dictionary mapping constructie ID's to lists of Paal objects containing information from the table
        """
        if structured_table is None:
            logger.warning(f"Geen {cls.__name__.lower()} tabel gevonden")
            return {}
        # Get the paalnummer column to identify valid paal rows
        paal_nummer_col = structured_table.get_column(header_in="Paalnummer", unit_in="[Px.y]")
        opmerkingen_col = structured_table.get_column(header_in="Opmerkingen", unit_in="[aanvullende tekst]")

        if opmerkingen_col is None or not any("constructie" in str(val).lower() for val in opmerkingen_col.values):
            if opmerkingen_col is None:
                logger.warning("Could not find constructie ID column in table based on header 'Opmerkingen'. ")
            else:
                logger.warning("Could not find any constructie ID values in column with header 'Opmerkingen'.")
            opmerkingen_col = paal_nummer_col

        if not paal_nummer_col:
            logger.error("Could not find paalnummer column in table")
            return {}

        # Parse each row into a Paal object
        paal_dict: dict[str, list[Paal]] = {}
        current_constructie_id = ""

        num_rows = len(paal_nummer_col.values)

        for row_idx in range(num_rows):

            constructie_id_col_val = utils.clean_string(opmerkingen_col.values[row_idx])

            if constructie_id_col_val.lower().startswith("constructie"):
                current_constructie_id = constructie_id_col_val

                if current_constructie_id in paal_dict:
                    logger.warning(f"Duplicate constructie ID found: {current_constructie_id}")

            paal_nummer_val = paal_nummer_col.values[row_idx]

            if utils.contains_paal_id(paal_nummer_val):
                paal = cls.from_paal_table_row(structured_table, row_idx)

                # Add paal to the correct constructie ID list
                if current_constructie_id not in paal_dict:
                    paal_dict[current_constructie_id] = []
                paal_dict[current_constructie_id].append(paal)

        # If one or more palen were found without a constructie ID, remove all construction ids
        if "" in paal_dict:
            logger.warning("One or more palen found without constructie ID. Removing all constructie IDs for palen.")
            paal_dict = utils.remove_constructie_id(paal_dict)

        # Validate paal nummers are sequential within each constructie ID
        prev_main_paal_nummer = 0

        for paal in utils.dict_items_flat(paal_dict):
            if not paal.paal_nummer_main in [prev_main_paal_nummer, prev_main_paal_nummer + 1]:
                logger.warning(
                    f"Non-sequential paal nummers found. Expected Px.{prev_main_paal_nummer + 1} after Px.{prev_main_paal_nummer} but instead got {paal.paal_nummer}"
                )
            prev_main_paal_nummer = paal.paal_nummer_main

        return paal_dict

    @classmethod
    def from_paal_table_row(cls, table: StructuredTable, row_idx: int) -> Paal:
        """Parse and return a Paal object from a single row of the
        funderingspalen structured table.

        Parameters
        ----------
        table : StructuredTable
            Structured table containing paal data.
        row_idx : int
            Index of the row to parse.

        Returns
        -------
        Paal
            A Paal object containing information from the row.
        """

        return cls(
            paal_nummer=utils.clean_paal_id(table.get_value(header_in="Paalnummer", unit_in="[Px.y]", index=row_idx)),
            diameter_haaks=table.get_value("Diameter", "Haaks", "[mm]", row_idx),
            diameter_parallel=table.get_value("Diameter", "Parrallel", "[mm]", row_idx),
            diameter_gemiddeld=table.get_value("Diameter", "Gemiddelde", "[mm]", row_idx),
            hoh_afstand_cm=table.get_value("Hart-op-hart-afstanden", "Afstand", "[cm]", row_idx),
            hoh_paalnummer=table.get_value("Hart-op-hart-afstanden", ["Paal", "aa"], "[Px.y]", row_idx),
            schoor_graden=table.get_value("Schoorstand", "Graden", "[]", row_idx),
            schoor_richting=table.get_value("Schoorstand", "Richting", "[+ ]", row_idx),
            afstand_frontwand_cm=table.get_value("Afstand", "Frontwand", "[cm]", row_idx),
            is_scheefstand=utils.parse_ja_nee(table.get_value("Schades", "Scheefstand", "[Ja/Nee]", row_idx)),
            is_paalbreuk=utils.parse_ja_nee(table.get_value("Schades", "Paalbreuk", "[Ja/Nee]", row_idx)),
            is_aantasting=utils.parse_ja_nee(table.get_value("Schades", "Aantasting", "[Ja/Nee]", row_idx)),
            aansluiting_status=table.get_value("Aansluiting", "Aansluiting", "[G/S]", row_idx),
            positionering_aansluiting_cm=table.get_value("Aansluiting", "Positionering", "[+]+[cm]", row_idx),
        )


if __name__ == "__main__":

    from tekstherkenning_ark.document.smart_document import SmartDocument
    from tekstherkenning_ark.document.structured_table import StructuredTable, TableColumn
    from tekstherkenning_ark import constants

    doc = SmartDocument.from_pdf(constants.TEST_PDF_PATH)

    palen_table = doc.get_meettabel_fundering_paal()

    palen_dict = Paal.from_doc_tables(palen_table)

    for palen in palen_dict.values():
        for paal in palen:
            print(paal.paal_nummer)
