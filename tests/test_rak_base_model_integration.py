"""Integration test to verify OnverwachtResultaat works with actual models."""

from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat, OnverwachtResultaatType
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.models.vloer import Vloer
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.enums import NietBeschikbaar, MateriaalVloer, AansluitingStatus, SchoorStand


def test_paal_with_onverwacht_resultaat():
    """Test that Paal automatically converts invalid values to OnverwachtResultaat."""

    # Pass a string where a float is expected
    paal = Paal(
        paal_nummer="P1.5",
        diameter_haaks=150,
        diameter_parallel=140,
        diameter_gemiddeld=145,
        hoh_afstand_cm=80,
        hoh_paalnummer="P1.6",
        schoor_graden=5,
        schoor_richting="verkeerde waarde",
        afstand_frontwand_cm=20,
        is_scheefstand=False,
        is_paalbreuk=False,
        is_aantasting=False,
        aansluiting_status=AansluitingStatus.GOED,
        positionering_aansluiting_cm="0",
    )

    assert isinstance(paal.schoor_richting, OnverwachtResultaat)
    assert paal.schoor_richting.waarde == "verkeerde waarde"
    assert paal.paal_nummer == "P1.5"


def test_paal_with_normal_values():
    """Test that Paal accepts normal values."""

    paal = Paal(
        paal_nummer="P1.1",
        diameter_haaks=150,
        diameter_parallel=150,
        diameter_gemiddeld=150,
        hoh_afstand_cm=100,
        hoh_paalnummer="P1.2",
        schoor_graden=5,
        schoor_richting=SchoorStand.POSITIEF,
        afstand_frontwand_cm=25,
        is_scheefstand=False,
        is_paalbreuk=False,
        is_aantasting=False,
        aansluiting_status=AansluitingStatus.GOED,
        positionering_aansluiting_cm="0",
    )

    assert paal.schoor_richting == SchoorStand.POSITIEF
    assert paal.paal_nummer == "P1.1"


def test_kesp_with_onverwacht_resultaat():
    """Test that Kesp automatically converts invalid values to OnverwachtResultaat."""

    # Pass a string where an int is expected
    kesp = Kesp(
        kesp_nummer="K1",
        hoogte_cm=20,
        breedte_cm=15,
        hoek_tov_lengte_as_graden="N/A",
        lengte_uitstekend_deel_cm=10,
        is_opsluitklos_aangetast=False,
    )

    assert isinstance(kesp.hoek_tov_lengte_as_graden, OnverwachtResultaat)
    assert kesp.hoek_tov_lengte_as_graden.waarde == "N/A"
    assert kesp.hoogte_cm == 20


def test_kesp_with_normal_values():
    """Test that Kesp accepts normal values."""

    kesp = Kesp(
        kesp_nummer="K2",
        hoogte_cm=25,
        breedte_cm=20,
        hoek_tov_lengte_as_graden=90,
        lengte_uitstekend_deel_cm=15,
        is_opsluitklos_aangetast=False,
    )

    assert kesp.hoek_tov_lengte_as_graden == 90
    assert kesp.kesp_nummer == "K2"


def test_vloer_with_onverwacht_resultaat():
    """Test that Vloer automatically converts invalid enum values to OnverwachtResultaat."""

    # Pass an invalid string where a MateriaalVloer enum is expected
    vloer = Vloer(materiaal="onbekend materiaal", bovenkant_vloer_cm_tov_nap=-150.0)

    assert isinstance(vloer.materiaal, OnverwachtResultaat)
    assert vloer.materiaal.waarde == "onbekend materiaal"
    assert vloer.bovenkant_vloer_cm_tov_nap == -150.0


def test_vloer_with_normal_values():
    """Test that Vloer accepts normal values."""

    vloer = Vloer(materiaal=MateriaalVloer.HOUT, bovenkant_vloer_cm_tov_nap=-120.5, is_beschadigd=False)

    assert vloer.materiaal == MateriaalVloer.HOUT
    assert vloer.bovenkant_vloer_cm_tov_nap == -120.5
    assert vloer.is_beschadigd is False


def test_bovenbouw_with_onverwacht_resultaat():
    """Test that Bovenbouw automatically converts invalid values to OnverwachtResultaat."""

    # Pass a string where a float is expected
    bovenbouw = Bovenbouw(bovenkant_deksteen_cm_tov_nap="niet gemeten")

    assert isinstance(bovenbouw.bovenkant_deksteen_cm_tov_nap, OnverwachtResultaat)
    assert bovenbouw.bovenkant_deksteen_cm_tov_nap.waarde == "niet gemeten"


def test_bovenbouw_with_normal_values():
    """Test that Bovenbouw accepts normal values."""

    bovenbouw = Bovenbouw(
        bovenkant_deksteen_cm_tov_nap=125.5,
        maximaal_aantal_scheuren_per_10_m=3,
        opmerkingen="Goede staat",
    )

    assert bovenbouw.bovenkant_deksteen_cm_tov_nap == 125.5
    assert bovenbouw.maximaal_aantal_scheuren_per_10_m == 3
    assert bovenbouw.opmerkingen == "Goede staat"


def test_collection_fields_not_affected():
    """Test that collection fields (gebreken) do NOT accept OnverwachtResultaat."""

    # gebreken is a list, so it should remain as list[Gebrek]
    vloer = Vloer(materiaal=MateriaalVloer.HOUT, gebreken=[])

    assert isinstance(vloer.gebreken, list)
    assert len(vloer.gebreken) == 0
