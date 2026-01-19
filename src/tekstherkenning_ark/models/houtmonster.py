from pydantic import BaseModel

from tekstherkenning_ark.models.gebrek import Gebrek


class Houtmonster(BaseModel):
    """Houtmonster.

    Attributes:
        houtmonster_code: Code van het houtmonster.
        diameter_paal_ter_hoogte_houtmonster_mm: Diameter van de paal ter hoogte van het houtmonster in millimeters.
        hoogte_onder_nap_cm: Hoogte onder NAP in centimeters.
        hoogte_tov_onderzijde_fundering_cm: Hoogte ten opzichte van onderzijde fundering in centimeters.
        stichtingjaar: Stichtingjaar van het hout.
        is_aangetast: Indicatie of het hout is aangetast.
        is_wankant_aanwezig: Indicatie of er wankant aanwezig is.
    """

    houtmonster_code: str
    diameter_paal_ter_hoogte_houtmonster_mm: int | None = None
    hoogte_onder_nap_cm: int | None = None
    hoogte_tov_onderzijde_fundering_cm: int | None = None
    stichtingjaar: int | None = None
    is_aangetast: bool | None = None
    is_wankant_aanwezig: bool | None = None
