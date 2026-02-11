from __future__ import annotations

from tekstherkenning_ark import utils
from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.rak_base_model import RakBaseModel
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.document.structured_table import StructuredTable

logger = get_logger(__name__)


class Kesp(RakBaseModel):
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
        paalrij_nr: Nummer van de paalrij waartoe de kesp behoort.
        gebreken: Lijst van gebreken (inherited from RakBaseModel).
        opmerkingen: Eventuele opmerkingen (inherited from RakBaseModel).
    """

    # Te vinden in Bijlage 3, kolom 'Kespnummer'.
    kesp_nummer: str
    # Te vinden in Bijlage 3, kolom 'Hoogte'.
    hoogte_cm: int | NietBeschikbaar
    # Te vinden in Bijlage 3, kolom 'Breedte'.
    breedte_cm: int | NietBeschikbaar
    # Te vinden in Bijlage 3, kolom 'Hoek t.o.v. lengte-as frontwand'.
    hoek_tov_lengte_as_graden: int | NietBeschikbaar | None = None
    # Te vinden in Bijlage 3, kolom 'Lengte uitstekende deel t.o.v. voorzijde frontwand'.
    lengte_uitstekend_deel_cm: int | NietBeschikbaar
    # Te vinden in Bijlage 3, kolom 'Mate van inknijping t.o.v. oorspronkelijke staat'.
    mate_inknijping_cm: int | NietBeschikbaar | None = None
    # Te vinden in Bijlage 3, kolom 'Indrukking van de funderingspaal in de kesp'.
    indrukking_paal_in_kesp: bool | NietBeschikbaar | None = None
    # Te vinden in Bijlage 3, kolom 'Opsluitklos aanwezig?'.
    is_opsluitklos_aanwezig: bool | NietBeschikbaar | None = None
    # Te vinden in Bijlage 3, kolom 'Opsluitklos aantasting'.
    is_opsluitklos_aangetast: bool | NietBeschikbaar
    # Te vinden in Bijlage 3, kolom 'Schades Vervormingen'.
    is_vervormd: bool | NietBeschikbaar | None = None
    # Te vinden in Bijlage 3, kolom 'Schades Aantasting'.
    is_aangetast: bool | NietBeschikbaar | None = None

    @property
    def identifier(self) -> str:
        """Return a string that uniquely identifies this Kesp instance."""
        return self.kesp_nummer

    @classmethod
    def from_doc_tables(cls, structured_table: StructuredTable | None) -> dict[str, list[Kesp]]:
        """Parse and return a list of Kesp objects from a structured table.

        Parameters
        ----------
        structured_table : StructuredTable
            Structured table containing kesp data with expected headers and sub-headers.

        Returns
        -------
        dict[str, list[Kesp]]
            A dictionary mapping constructie ID's to lists of Kesp objects containing information from the table
        """
        if structured_table is None:
            logger.warning(f"Geen {cls.__name__.lower()} tabel gevonden")
            return {}
        # Get the kespnummer column to identify valid kesp rows
        kesp_nummer_col = structured_table.get_column(header_in="Kespnummer", unit_in="[Ky]")
        opmerkingen_col = structured_table.get_column(header_in="Opmerkingen", unit_in="[aanvullende tekst]")

        # Special case: constructie id staat niet in de opmerkingen maar in de kesp id kolom
        if opmerkingen_col is None or not any("constructie" in str(val).lower() for val in opmerkingen_col.values):
            if opmerkingen_col is None:
                logger.warning("Could not find constructie ID column in table based on header 'Opmerkingen'. ")
            else:
                logger.warning("Could not find any constructie ID values in column with header 'Opmerkingen'.")
            opmerkingen_col = kesp_nummer_col

        if not kesp_nummer_col:
            logger.error("Could not find kespnummer column in table")
            return {}

        # Parse each row into a Kesp object
        kesp_dict: dict[str, list[Kesp]] = {}
        current_constructie_id = ""

        num_rows = len(kesp_nummer_col.values)

        for row_idx in range(num_rows):

            constructie_id_col_val = utils.clean_string(opmerkingen_col.values[row_idx])

            if constructie_id_col_val.lower().startswith("constructie"):
                current_constructie_id = constructie_id_col_val

                if current_constructie_id in kesp_dict:
                    logger.warning(f"Duplicate constructie ID found: {current_constructie_id}")

            kesp_nummer_val = kesp_nummer_col.values[row_idx]

            if utils.contains_kesp_id(kesp_nummer_val):
                kesp = cls.from_kesp_table_row(structured_table, row_idx)

                # Add kesp to the correct constructie ID list
                if current_constructie_id not in kesp_dict:
                    kesp_dict[current_constructie_id] = []
                kesp_dict[current_constructie_id].append(kesp)

        if "" in kesp_dict:
            logger.warning(f"{len(kesp_dict[''])} kespen found with constructie ID missing.")

        return kesp_dict

    @classmethod
    def from_kesp_table_row(cls, table: StructuredTable, row_idx: int) -> Kesp:
        """Parse and return a Kesp object from a single row of the
        kespen structured table.

        Parameters
        ----------
        table : StructuredTable
            Structured table containing kesp data.
        row_idx : int
            Index of the row to parse.

        Returns
        -------
        Kesp
            A Kesp object containing information from the row.
        """

        opsluitklos_aanwezig_val = table.get_value(
            header_in="Opsluitklos", sub_header_in="Aanwezig? Aanwezig?", unit_in="[Ja/Nee]", index=row_idx
        )

        return cls(
            kesp_nummer=table.get_value(header_in="Kespnummer", unit_in="[Ky]", index=row_idx),
            hoogte_cm=table.get_value(header_in="Afmetingen", sub_header_in="Hoogte", unit_in="[cm]", index=row_idx),
            breedte_cm=table.get_value(header_in="Afmetingen", sub_header_in="Breedte", unit_in="[cm]", index=row_idx),
            hoek_tov_lengte_as_graden=table.get_value(
                header_in="Hoek t.o.v. lengte-as frontwand", unit_in="[]", index=row_idx
            ),
            lengte_uitstekend_deel_cm=table.get_value(
                header_in="Lengte uitstekende deel t.o.v. voorzijde frontwand", unit_in="[cm]", index=row_idx
            ),
            mate_inknijping_cm=table.get_value(
                header_in=[
                    "Mate van inknijping to.v. oorspronkelijke staat",
                    "Mate van inknijping Lo.v. oorspronkelijke staat",
                ],
                unit_in="0",
                index=row_idx,
            ),
            indrukking_paal_in_kesp_cm=table.get_value(
                header_in="Indrukking van de funderingspaal in de kesp", unit_in="[Ja/Nee]", index=row_idx
            ),
            is_opsluitklos_aanwezig=(
                utils.parse_ja_nee(opsluitklos_aanwezig_val) if opsluitklos_aanwezig_val != "" else None
            ),
            is_opsluitklos_aangetast=utils.parse_ja_nee(
                table.get_value(header_in="Opsluitklos", sub_header_in="Aantasting", unit_in="[Ja/Nee]", index=row_idx)
            ),
            is_vervormd=utils.parse_ja_nee(
                table.get_value(header_in="Schades", sub_header_in="Vervormingen", unit_in="[Ja/Nee]", index=row_idx)
            ),
            is_aangetast=utils.parse_ja_nee(
                table.get_value(header_in="Schades", sub_header_in="Aantasting", unit_in="[Ja/Nee]", index=row_idx)
            ),
        )
