from __future__ import annotations

from pydantic import BaseModel

from tekstherkenning_ark import utils
from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.models.gebrek import Gebrek
from azure.ai.documentintelligence.models import DocumentTable
from tekstherkenning_ark.logger import get_logger

logger = get_logger(__name__)


class Kesp(BaseModel):
    """Kesp.

    Attributes:
        kespnummer: Uniek nummer van de kesp, zoals vermeld in de meettabel kespen.
        hoogte_cm: Hoogte van de kesp in centimeters.
        breedte_cm: Breedte van de kesp in centimeters.
        hoek_tov_lengte_as_graden: Hoek die de kesp maakt met de lengte-as van de frontwand, in graden.
        lengte_uitstekend_deel_cm: Lengte van het uitstekende deel van de kesp ten opzichte van de voorzijde van de frontwand, in centimeters.
        mate_inknijping_cm: Mate van inknijping ten opzichte van de oorspronkelijke staat, in centimeters.
        indrukking_paal_in_kesp_cm: Indrukking van de funderingspaal in de kesp, in centimeters.
        is_opsluitklos_aanwezig: Indicatie of een opsluitklos aanwezig is.
        is_opsluitklos_aangetast: Indicatie of de opsluitklos aangetast is.
        is_vervormd: Indicatie of er vervorming van de kesp is vastgesteld.
        is_aangetast: Indicatie of er aantasting van de kesp is vastgesteld.
        opmerkingen: Eventuele aanvullende opmerkingen over de kesp.
        paalrij_nr: Nummer van de paalrij waartoe de kesp behoort.
        gebreken: Lijst van gebreken in de kesp.
    """

    # Te vinden in Bijlage 3, kolom 'Kespnummer'.
    kesp_nummer: str
    # Te vinden in Bijlage 3, kolom 'Hoogte'.
    hoogte_cm: int
    # Te vinden in Bijlage 3, kolom 'Breedte'.
    breedte_cm: int
    # Te vinden in Bijlage 3, kolom 'Hoek t.o.v. lengte-as frontwand'.
    hoek_tov_lengte_as_graden: int | None = None
    # Te vinden in Bijlage 3, kolom 'Lengte uitstekende deel t.o.v. voorzijde frontwand'.
    lengte_uitstekend_deel_cm: int | NietBeschikbaar
    # Te vinden in Bijlage 3, kolom 'Mate van inknijping t.o.v. oorspronkelijke staat'.
    mate_inknijping_cm: int | None = None
    # Te vinden in Bijlage 3, kolom 'Indrukking van de funderingspaal in de kesp'.
    indrukking_paal_in_kesp: bool | None = None
    # Te vinden in Bijlage 3, kolom 'Opsluitklos aanwezig?'.
    is_opsluitklos_aanwezig: bool | None = None
    # Te vinden in Bijlage 3, kolom 'Opsluitklos aantasting'.
    is_opsluitklos_aangetast: bool | NietBeschikbaar
    # Te vinden in Bijlage 3, kolom 'Schades Vervormingen'.
    is_vervormd: bool | None = None
    # Te vinden in Bijlage 3, kolom 'Schades Aantasting'.
    is_aangetast: bool | None = None
    # Te vinden in Bijlage 3, kolom 'Opmerkingen'.
    opmerkingen: str = ""

    # TBD waar te vinden
    paalrij_nr: str | None = None

    gebreken: list[Gebrek] = []

    @classmethod
    def from_doc_tables(cls, tables: list[DocumentTable]) -> dict[str, list[Kesp]]:
        """Parse and return a list of Kesp objects from a Azure Doc
        Intelligence DocumentTable object

        Parameters
        ----------
        tables : list[DocumentTable]
            List of DocumentTable objects as returned by Azure Document Intelligence SDK
            belonging to the `Kespen` bijlage

        Returns
        -------
        dict[str, list[Kesp]]
            A dictionary mapping constructie ID's to lists of Kesp objects containing information from the table
        """

        kesp_rows: list[list[str]] = []
        for table in tables:

            # Extract table content as list of rows
            table_rows = utils.get_table_content(table)

            # Skip header rows and add to paal_rows
            content_rows = [r for r in table_rows if utils.contains_kesp_id(r[0])]
            kesp_rows.extend(content_rows)

        # Parse each row into a Paal object
        kesp_dict: dict[str, list[Kesp]] = {}
        current_constructie_id = ""

        for row in kesp_rows:

            constructie_id_col_val = row[11].strip()

            if constructie_id_col_val != "":
                current_constructie_id = constructie_id_col_val

                if current_constructie_id not in kesp_dict:
                    kesp_dict[current_constructie_id] = []
                else:
                    raise ValueError(f"Duplicate constructie ID found: {current_constructie_id}")

            if current_constructie_id != "":
                paal = cls.from_kesp_table_row(row)
                kesp_dict[current_constructie_id].append(paal)

        return kesp_dict

    @classmethod
    def from_kesp_table_row(cls, row: list[str]) -> Kesp:
        """Parse and return a Kesp object from a single row of the
        kespen table.

        Parameters
        ----------
        row : list[str]
            A single row from the kespen table as a list of strings.

        Returns
        -------
        Kesp
            A Kesp object containing information from the row.
        """

        row_clean = [utils.clean_string(val) for val in row]

        return cls(
            kesp_nummer=row_clean[0],
            hoogte_cm=row_clean[1],
            breedte_cm=row_clean[2],
            hoek_tov_lengte_as_graden=row_clean[3],
            lengte_uitstekend_deel_cm=row_clean[4],
            mate_inknijping_cm=row_clean[5],
            indrukking_paal_in_kesp_cm=row_clean[6],
            is_opsluitklos_aanwezig=utils.parse_ja_nee(row_clean[7]) if row_clean[7] != "" else None,
            is_opsluitklos_aangetast=utils.parse_ja_nee(row_clean[8]),
            is_vervormd=utils.parse_ja_nee(row_clean[9]),
            is_aangetast=utils.parse_ja_nee(row_clean[10]),
        )
