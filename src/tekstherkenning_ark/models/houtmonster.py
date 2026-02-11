from __future__ import annotations

from tekstherkenning_ark import utils
from tekstherkenning_ark.models.rak_base_model import RakBaseModel
from tekstherkenning_ark.document.structured_table import StructuredTable
from tekstherkenning_ark.logger import get_logger

logger = get_logger(__name__)


class Houtmonster(RakBaseModel):
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
        gebreken: Inherited from RakBaseModel.
        opmerkingen: Inherited from RakBaseModel.
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

    @property
    def identifier(self) -> str:
        """Return the codering as unique identifier for this houtmonster."""
        return str(self.codering)

    @classmethod
    def from_doc_tables(cls, structured_table: StructuredTable) -> list[Houtmonster]:
        """Parse and return a list of Houtmonster objects from a structured table.

        Parameters
        ----------
        structured_table : StructuredTable
            Structured table containing houtmonster data with expected headers.

        Returns
        -------
        list[Houtmonster]
            A list of Houtmonster objects containing information from the table.
        """

        # Get the codering column to identify valid houtmonster rows
        codering_col = structured_table.get_column(header_in="Codering", unit_in="[RAKxxxx/Px.y/HM]")

        if not codering_col:
            logger.error("Could not find codering column in table")
            return []

        # Parse each row into a Houtmonster object
        houtmonster_list = []
        num_rows = len(codering_col.values)

        for row_idx in range(num_rows):
            codering_val = codering_col.values[row_idx]

            if utils.is_houtmonster_id(codering_val):
                houtmonster = cls.from_houtmonster_table_row(structured_table, row_idx)
                houtmonster_list.append(houtmonster)

        return houtmonster_list

    @classmethod
    def from_houtmonster_table_row(cls, table: StructuredTable, row_idx: int) -> Houtmonster:
        """Parse and return a Houtmonster object from a single row of the
        houtmonsteren structured table.

        Parameters
        ----------
        table : StructuredTable
            Structured table containing houtmonster data.
        row_idx : int
            Index of the row to parse.

        Returns
        -------
        Houtmonster
            A Houtmonster object containing information from the row.
        """

        wankant_val = table.get_value(header_in="Wankant aanwezig?", unit_in="[Ja/Nee]", index=row_idx)

        return cls(
            codering=table.get_value(header_in="Codering", unit_in="[RAKxxxx/Px.y/HM]", index=row_idx),
            rak_code=table.get_value(header_in="Rakcode", unit_in="[RAKxxxx]", index=row_idx),
            paal_nummer=table.get_value(header_in="Paalnummer", unit_in="[Px.y]", index=row_idx),
            houtmonster_code=table.get_value(header_in="Houtmonster", unit_in="[HMxxxxx]", index=row_idx),
            diameter_paal_ter_hoogte_houtmonster_mm=table.get_value(
                header_in="Diameter paal", unit_in="[mm]", index=row_idx
            ),
            hoogte_onder_nap_cm=table.get_value(header_in="Hoogte t.o.v. NAP", unit_in="[cm]", index=row_idx),
            hoogte_tov_onderzijde_fundering_cm=table.get_value(
                header_in="Hoogte t.o.v. kesp/vloer", unit_in="[cm]", index=row_idx
            ),
            is_wankant_aanwezig=utils.parse_ja_nee(wankant_val) if wankant_val else None,
            datum_monstername=table.get_value(header_in="Datum monstername", unit_in="[dd-mm-j\\]", index=row_idx),
        )

    def __hash__(self):
        return hash(self.codering)


if __name__ == "__main__":

    from tekstherkenning_ark.document.smart_document import SmartDocument
    from tekstherkenning_ark import constants

    doc = SmartDocument.from_pdf(constants.TEST_PDF_PATH)

    houtmonsters_tables = doc.get_meettabel_houtmonsters()
    houtmonsters = Houtmonster.from_doc_tables(houtmonsters_tables)

    for x in houtmonsters:
        print(x.codering)
