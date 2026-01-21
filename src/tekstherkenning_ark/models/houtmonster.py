from pydantic import BaseModel

from tekstherkenning_ark.models.gebrek import Gebrek


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
    # Te vinden in bijlage 1, kolom "Houtmonster", of bijlage 2, kolom "Houtmonstercode"
    houtmonster_code: str
    # Te vinden in bijlage 1, kolom "Diameter paal" of bijlage 2, kolom "Diameter paal ter hoogte van houtmonster:"
    diameter_paal_ter_hoogte_houtmonster_mm: int | None = None
    # Te vinden in bijlage 1, kolom "Hoogte t.o.v. NAP" of bijlage 2, kolom "Hoogte monstername onder NAP:"
    hoogte_onder_nap_cm: int | None = None
    # Te vinden in bijlage 1, kolom "Hoogte t.o.v. kesp/vloer", of bijlage 2, kolom "Hoogte monstername t.o.v. onderzijde fundering:"
    hoogte_tov_onderzijde_fundering_cm: int | None = None
    # Te vinden in bijlage 1, kolom "Wankant aanwezig?" of bijlage 2, kolom "Wankant aanwezig:"
    is_wankant_aanwezig: bool | None = None
    # Te vinden in bijlage 1, kolom "Datum monstername"
    datum_monstername: str | None = None
    # Te vinden in bijlage 2, kolom "Monster aangetast"
    is_aangetast: bool | None = None
    # Te vinden in bijlage 2, kolom "Stichtingjaar houtmonster:"
    stichtingjaar: int | None = None
