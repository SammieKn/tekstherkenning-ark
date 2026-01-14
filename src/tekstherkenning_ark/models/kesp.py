from pydantic import BaseModel

from .gebrek import Gebrek


class Kesp(BaseModel):
    """Kesp.

    Attributes:
        breedte_cm: Breedte van de kesp in centimeters.
        gebreken: Lijst van gebreken in de kesp.
        hoogte_cm: Hoogte van de kesp in centimeters.
        kespnummer: Uniek nummer van de kesp, zoals vermeld in de meettabel kespen.
        is_aantasting: Indicatie of er aantasting van de kesp is vastgesteld.
        is_beschadigd: Indicatie of de kesp beschadigd is.
        is_gebroken: Indicatie of de kesp gebroken is.
        hoek_tov_lengte_as_graden: Hoek die de kesp maakt met de lengte-as van de frontwand, in graden.
        indrukking_paal_in_kesp_cm: Indrukking van de funderingspaal in de kesp, in centimeters.
        lengte_uitstekend_deel_cm: Lengte van het uitstekende deel van de kesp ten opzichte van de voorzijde van de frontwand, in centimeters.
        mate_inknijping_cm: Mate van inknijping ten opzichte van de oorspronkelijke staat, in centimeters.
        opmerkingen: Eventuele aanvullende opmerkingen over de kesp.
        is_opsluitklos_aanwezig: Indicatie of een opsluitklos aanwezig is.
        is_vervorming: Indicatie of er vervorming van de kesp is vastgesteld.
        paalrij_nr: Nummer van de paalrij waartoe de kesp behoort.
    """

    # Te vinden in Bijlage 3, kolom 'Breedte'.
    breedte_cm: int
    gebreken: list[Gebrek]
    # Te vinden in Bijlage 3, kolom 'Hoogte'.
    hoogte_cm: int
    # Te vinden in Bijlage 3, kolom 'Kespnummer'.
    kespnummer: str
    # Te vinden in Bijlage 3, kolom 'Aantasting'.
    is_aantasting: bool | None = None
    # Te vinden in de gebrekentabel, kolom 'Schades' of uit de tekst in paragraaf 2.3.
    is_beschadigd: bool | None = None
    # Te vinden in de gebrekentabel, kolom 'Schades' of uit de tekst in paragraaf 2.3.
    is_gebroken: bool | None = None
    # Te vinden in Bijlage 3, kolom 'Hoek t.o.v. lengte-as frontwand'.
    hoek_tov_lengte_as_graden: int | None = None
    # Te vinden in Bijlage 3, kolom 'Indrukking van de funderingspaal in de kesp'.
    indrukking_paal_in_kesp_cm: int | None = None
    # Te vinden in Bijlage 3, kolom 'Lengte uitstekende deel t.o.v. voorzijde frontwand'.
    lengte_uitstekend_deel_cm: int | None = None
    # Te vinden in Bijlage 3, kolom 'Mate van inknijping t.o.v. oorspronkelijke staat'.
    mate_inknijping_cm: int | None = None
    # Te vinden in Bijlage 3, kolom 'Opmerkingen'.
    opmerkingen: str | None = None
    # Te vinden in Bijlage 3, kolom 'Opsluitklos aanwezig?'.
    is_opsluitklos_aanwezig: bool | None = None
    # Te vinden in Bijlage 3, kolom 'Vervormingen'.
    is_vervorming: bool | None = None

    # TBD waar te vinden
    paalrij_nr: str | None = None
