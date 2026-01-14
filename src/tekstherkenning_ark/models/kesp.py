from pydantic import BaseModel, Field

from .gebrek import Gebrek


class Kesp(BaseModel):

    # Te vinden in Bijlage 3, kolom 'Breedte'.
    breedte_cm: int = Field(description="Breedte van de kesp in centimeters.")
    gebreken: list[Gebrek]
    # Te vinden in Bijlage 3, kolom 'Hoogte'.
    hoogte_cm: int = Field(description="Hoogte van de kesp in centimeters.")
    # Te vinden in Bijlage 3, kolom 'Kespnummer'.
    kespnummer: str = Field(description="Uniek nummer van de kesp, zoals vermeld in de meettabel kespen.")
    # Te vinden in Bijlage 3, kolom 'Aantasting'.
    is_aantasting: bool | None = Field(
        default=None,
        description="Indicatie of er aantasting van de kesp is vastgesteld.",
    )
    # Te vinden in de gebrekentabel, kolom 'Schades' of uit de tekst in paragraaf 2.3.
    is_beschadigd: bool | None = Field(default=None, description="Indicatie of de kesp beschadigd is.")
    # Te vinden in de gebrekentabel, kolom 'Schades' of uit de tekst in paragraaf 2.3.
    is_gebroken: bool | None = Field(default=None, description="Indicatie of de kesp gebroken is.")
    # Te vinden in Bijlage 3, kolom 'Hoek t.o.v. lengte-as frontwand'.
    hoek_tov_lengte_as_graden: int | None = Field(
        default=None,
        description="Hoek die de kesp maakt met de lengte-as van de frontwand, in graden.",
    )
    # Te vinden in Bijlage 3, kolom 'Indrukking van de funderingspaal in de kesp'.
    indrukking_paal_in_kesp_cm: int | None = Field(
        default=None,
        description="Indrukking van de funderingspaal in de kesp, in centimeters.",
    )
    # Te vinden in Bijlage 3, kolom 'Lengte uitstekende deel t.o.v. voorzijde frontwand'.
    lengte_uitstekend_deel_cm: int | None = Field(
        default=None,
        description="Lengte van het uitstekende deel van de kesp ten opzichte van de voorzijde van de frontwand, in centimeters.",
    )
    # Te vinden in Bijlage 3, kolom 'Mate van inknijping t.o.v. oorspronkelijke staat'.
    mate_inknijping_cm: int | None = Field(
        default=None,
        description="Mate van inknijping ten opzichte van de oorspronkelijke staat, in centimeters.",
    )
    # Te vinden in Bijlage 3, kolom 'Opmerkingen'.
    opmerkingen: str | None = Field(default=None, description="Eventuele aanvullende opmerkingen over de kesp.")
    # Te vinden in Bijlage 3, kolom 'Opsluitklos aanwezig?'.
    is_opsluitklos_aanwezig: bool | None = Field(default=None, description="Indicatie of een opsluitklos aanwezig is.")
    # Te vinden in Bijlage 3, kolom 'Vervormingen'.
    is_vervorming: bool | None = Field(
        default=None,
        description="Indicatie of er vervorming van de kesp is vastgesteld.",
    )
