from __future__ import annotations
from pydantic import BaseModel

from azure.ai.documentintelligence.models import DocumentTable

from tekstherkenning_ark import utils


class Houtmonster(BaseModel):
    """Houtmonster.

    Attributes:
        codering: Codering van het houtmonster.
        rak_code: Code van het rak waar het houtmonster bij hoort.
        paal_nummer: Nummer van de paal waaruit het houtmonster is genomen.
        houtmonster_code: Code van het houtmonster.
        diameter_paal_ter_hoogte_houtmonster_mm: Diameter van de paal ter hoogte van het houtmonster in millimeters.
        hoogte_onder_nap_cm: Hoogte onder NAP in centimeters.
        hoogte_tov_onderzijde_fundering_cm: Hoogte ten opzichte van onderzijde fundering in centimeters.
        is_wankant_aanwezig: Indicatie of er wankant aanwezig is.
        datum_monstername: Datum waarop het monster is genomen.
        is_aangetast: Indicatie of het hout is aangetast.
        stichtingjaar: Stichtingjaar van het hout.
    """

    # Te vinden in bijlage 1, kolom 'Codering'
    codering: str
    # Te vinden in bijlage 1, kolom "Rak code"
    rak_code: str
    # Te vinden in bijlage 1, kolom "Paal nummer"
    paal_nummer: str
    # Te vinden in bijlage 1, kolom "Houtmonster", of bijlage 2, kolom "Houtmonstercode"
    houtmonster_code: str
    # Te vinden in bijlage 1, kolom "Diameter paal" of bijlage 2, kolom "Diameter paal ter hoogte van houtmonster:"
    diameter_paal_ter_hoogte_houtmonster_mm: int | None = None
    # Te vinden in bijlage 1, kolom "Hoogte t.o.v. NAP" of bijlage 2, kolom "Hoogte monstername onder NAP:"
    hoogte_onder_nap_cm: int | None = None
    # Te vinden in bijlage 1, kolom "Hoogte t.o.v. houtmonster/vloer", of bijlage 2, kolom "Hoogte monstername t.o.v. onderzijde fundering:"
    hoogte_tov_onderzijde_fundering_cm: int | None = None
    # Te vinden in bijlage 1, kolom "Wankant aanwezig?" of bijlage 2, kolom "Wankant aanwezig:"
    is_wankant_aanwezig: bool | None = None
    # Te vinden in bijlage 1, kolom "Datum monstername"
    datum_monstername: str | None = None
    # Te vinden in bijlage 2, kolom "Monster aangetast"
    is_aangetast: bool | None = None
    # Te vinden in bijlage 2, kolom "Stichtingjaar houtmonster:"
    stichtingjaar: int | None = None

    @classmethod
    def from_doc_tables(cls, tables: list[DocumentTable]) -> list[Houtmonster]:
        """Parse and return a list of Houtmonster objects from a Azure Document
        Intelligence DocumentTable object

        Parameters
        ----------
        tables : list[DocumentTable]
            List of DocumentTable objects as returned by Azure Document Intelligence SDK
            belonging to the `Houtmonster` bijlage

        Returns
        -------
        dict[str, list[Houtmonster]]
            A dictionary mapping constructie ID's to lists of Houtmonster objects containing information from the table
        """

        houtmonster_rows: list[list[str]] = []
        for table in tables:

            # Extract table content as list of rows
            table_rows = utils.get_table_content(table)

            # Skip header rows and add to paal_rows
            content_rows = [r for r in table_rows if utils.is_houtmonster_id(r[0])]
            houtmonster_rows.extend(content_rows)

        # Parse each row into a Houtmonster object
        houtmonster_list = [cls.from_houtmonster_table_row(row) for row in houtmonster_rows]

        return houtmonster_list

    @classmethod
    def from_houtmonster_table_row(cls, row: list[str]) -> Houtmonster:
        """Parse and return a Houtmonster object from a single row of the
        houtmonsteren table.

        Parameters
        ----------
        row : list[str]
            A single row from the houtmonsteren table as a list of strings.

        Returns
        -------
        Houtmonster
            A Houtmonster object containing information from the row.
        """

        row_clean = [utils.clean_string(val) for val in row]

        return cls(
            codering=row_clean[0],
            rak_code=row_clean[1],
            paal_nummer=row_clean[2],
            houtmonster_code=row_clean[3],
            diameter_paal_ter_hoogte_houtmonster_mm=row_clean[4],
            hoogte_onder_nap_cm=row_clean[5],
            hoogte_tov_onderzijde_fundering_cm=row_clean[6],
            is_wankant_aanwezig=utils.parse_ja_nee(row_clean[7]),
            datum_monstername=row_clean[8],
        )
