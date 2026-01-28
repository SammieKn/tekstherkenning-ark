"""
Test Houtmonster Module
"""

from tekstherkenning_ark.models.houtmonster import Houtmonster
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat


def test_invalid_houtmonster():
    my_houtmonster = Houtmonster(
        codering=123,  # Invalid type, should be str or OnverwachtResultaat
        rak_code="RK01",
        paal_nummer="P001",
        houtmonster_code="HM01",
        diameter_paal_ter_hoogte_houtmonster_mm="not_an_int",  # Invalid type
        hoogte_onder_nap_cm=150,
        hoogte_tov_onderzijde_fundering_cm=200,
        is_wankant_aanwezig=True,
        datum_monstername="2023-01-01",
        is_aangetast=False,
        stichtingjaar=1990
    )
    assert isinstance(my_houtmonster.codering, OnverwachtResultaat)


def test_invalid_nee_houtmonster():
    my_houtmonster = Houtmonster(
        codering="C01",
        rak_code="RK01",
        paal_nummer="P001",
        houtmonster_code="HM01",
        diameter_paal_ter_hoogte_houtmonster_mm=300,
        hoogte_onder_nap_cm=150,
        hoogte_tov_onderzijde_fundering_cm=200,
        is_wankant_aanwezig="nee",  # Invalid type, should be bool or OnverwachtResultaat
        datum_monstername="2023-01-01",
        is_aangetast="ee",
        stichtingjaar=1990
    )
    assert isinstance(my_houtmonster.is_wankant_aanwezig, OnverwachtResultaat)
    assert my_houtmonster.is_wankant_aanwezig.waarde == "nee"
    assert isinstance(my_houtmonster.is_aangetast, OnverwachtResultaat)
    assert my_houtmonster.is_aangetast.waarde == "ee"
