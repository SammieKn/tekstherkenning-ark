from pydantic import BaseModel

from tekstherkenning_ark.models.gebrek import Gebrek


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
    kespnummer: str
    # Te vinden in Bijlage 3, kolom 'Hoogte'.
    hoogte_cm: int
    # Te vinden in Bijlage 3, kolom 'Breedte'.
    breedte_cm: int
    # Te vinden in Bijlage 3, kolom 'Hoek t.o.v. lengte-as frontwand'.
    hoek_tov_lengte_as_graden: int | None = None
    # Te vinden in Bijlage 3, kolom 'Lengte uitstekende deel t.o.v. voorzijde frontwand'.
    lengte_uitstekend_deel_cm: int | None = None
    # Te vinden in Bijlage 3, kolom 'Mate van inknijping t.o.v. oorspronkelijke staat'.
    mate_inknijping_cm: int | None = None
    # Te vinden in Bijlage 3, kolom 'Indrukking van de funderingspaal in de kesp'.
    indrukking_paal_in_kesp_cm: int | None = None
    # Te vinden in Bijlage 3, kolom 'Opsluitklos aanwezig?'.
    is_opsluitklos_aanwezig: bool | None = None
    # Te vinden in Bijlage 3, kolom 'Opsluitklos aantasting'.
    is_opsluitklos_aangetast: bool | None = None
    # Te vinden in Bijlage 3, kolom 'Schades Vervormingen'.
    is_vervormd: bool | None = None
    # Te vinden in Bijlage 3, kolom 'Schades Aantasting'.
    is_aangetast: bool | None = None
    # Te vinden in Bijlage 3, kolom 'Opmerkingen'.
    opmerkingen: str | None = None

    # TBD waar te vinden
    paalrij_nr: str | None = None

    gebreken: list[Gebrek]
