"""Tests for Rak hierarchy methods: children, alle_gebreken, onverwachte_resultaten, alle_onverwachte_resultaten."""

from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.onderbouw import Onderbouw
from tekstherkenning_ark.models.metselwerk import Metselwerk
from tekstherkenning_ark.models.vloer import Vloer
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat
from tekstherkenning_ark.enums import MateriaalVloer, AansluitingStatus, SchoorStand


def test_rak_children(mock_rak_with_gebreken: Rak):
    """Test that Rak.children returns all direct child RakBaseModel instances."""
    rak = mock_rak_with_gebreken

    # Rak has rakdelen as children
    children = rak.children

    assert len(children) == 1
    assert isinstance(children[0], Rakdeel)
    assert children[0].rakdeel_id == "Constructie A"


def test_rakdeel_children(mock_rak_with_gebreken: Rak):
    """Test that Rakdeel.children returns bovenbouw and onderbouw."""
    rak = mock_rak_with_gebreken
    rakdeel = rak.rakdelen[0]

    children = rakdeel.children

    # Rakdeel has bovenbouw and onderbouw as children
    assert len(children) == 2
    assert any(isinstance(child, Bovenbouw) for child in children)
    assert any(isinstance(child, Onderbouw) for child in children)


def test_bovenbouw_children(mock_rak_with_gebreken: Rak):
    """Test that Bovenbouw.children returns metselwerk."""
    rak = mock_rak_with_gebreken
    bovenbouw = rak.rakdelen[0].bovenbouw

    children = bovenbouw.children

    # Bovenbouw has metselwerk as child
    assert len(children) == 1
    assert isinstance(children[0], Metselwerk)


def test_onderbouw_children(mock_rak_with_gebreken: Rak):
    """Test that Onderbouw.children returns palen, kespen, and vloer."""
    rak = mock_rak_with_gebreken
    onderbouw = rak.rakdelen[0].onderbouw

    children = onderbouw.children

    # Onderbouw has palen (list), kespen (list), and vloer
    # children should include individual paal and kesp instances plus vloer
    assert len(children) >= 3
    assert any(isinstance(child, Paal) for child in children)
    assert any(isinstance(child, Kesp) for child in children)
    assert any(isinstance(child, Vloer) for child in children)


def test_rak_alle_gebreken(mock_rak_with_gebreken: Rak):
    """Test that Rak.alle_gebreken collects all gebreken from the entire hierarchy."""
    rak = mock_rak_with_gebreken

    alle_gebreken = rak.alle_gebreken

    # Should have gebreken from: metselwerk (1), paal1 (1), kesp1 (1), rakdeel (1) = 4 total
    assert len(alle_gebreken) == 4

    # Check that all expected gebreken are present
    coderingen = [g.codering for g in alle_gebreken]
    assert "GM1" in coderingen  # From metselwerk
    assert "GP1" in coderingen  # From paal
    assert "GK1" in coderingen  # From kesp
    assert "GR1" in coderingen  # From rakdeel


def test_metselwerk_alle_gebreken(mock_rak_with_gebreken: Rak):
    """Test that Metselwerk.alle_gebreken returns only its own gebreken (no children)."""
    rak = mock_rak_with_gebreken
    metselwerk = rak.rakdelen[0].bovenbouw.metselwerk

    alle_gebreken = metselwerk.alle_gebreken

    # Metselwerk has 1 gebrek and no children
    assert len(alle_gebreken) == 1
    assert alle_gebreken[0].codering == "GM1"


def test_rakdeel_alle_gebreken(mock_rak_with_gebreken: Rak):
    """Test that Rakdeel.alle_gebreken includes gebreken from all sub-components."""
    rak = mock_rak_with_gebreken
    rakdeel = rak.rakdelen[0]

    alle_gebreken = rakdeel.alle_gebreken

    # Should have all gebreken from the rakdeel tree
    assert len(alle_gebreken) == 4
    coderingen = [g.codering for g in alle_gebreken]
    assert "GM1" in coderingen
    assert "GP1" in coderingen
    assert "GK1" in coderingen
    assert "GR1" in coderingen


def test_onverwachte_resultaten_single_model(mock_rak_with_onverwachte_resultaten: Rak):
    """Test that onverwachte_resultaten returns OnverwachtResultaat instances from a single model."""
    rak = mock_rak_with_onverwachte_resultaten
    paal = rak.rakdelen[0].onderbouw.palen[0]

    onverwachte = paal.onverwachte_resultaten

    # Paal should have 1 OnverwachtResultaat (schoorstand_graden)
    assert len(onverwachte) == 1
    assert isinstance(onverwachte[0], OnverwachtResultaat)
    assert onverwachte[0].waarde == "onleesbaar"


def test_metselwerk_onverwachte_resultaten(mock_rak_with_onverwachte_resultaten: Rak):
    """Test that Metselwerk.onverwachte_resultaten returns its OnverwachtResultaat instances."""
    rak = mock_rak_with_onverwachte_resultaten
    metselwerk = rak.rakdelen[0].bovenbouw.metselwerk

    onverwachte = metselwerk.onverwachte_resultaten

    # Metselwerk should have 1 OnverwachtResultaat (dikte_cm)
    assert len(onverwachte) == 1
    assert isinstance(onverwachte[0], OnverwachtResultaat)
    assert onverwachte[0].waarde == "niet meetbaar"


def test_bovenbouw_alle_onverwachte_resultaten(mock_rak_with_onverwachte_resultaten: Rak):
    """Test that Bovenbouw.alle_onverwachte_resultaten includes OnverwachtResultaat from children."""
    rak = mock_rak_with_onverwachte_resultaten
    bovenbouw = rak.rakdelen[0].bovenbouw

    alle_onverwachte = bovenbouw.alle_onverwachte_resultaten

    # Bovenbouw has: maximale_scheurwijdte_mm (1) + metselwerk.dikte_cm (1) = 2
    assert len(alle_onverwachte) == 2
    waarden = [o.waarde for o in alle_onverwachte]
    assert "niet gemeten" in waarden
    assert "niet meetbaar" in waarden


def test_onderbouw_alle_onverwachte_resultaten(mock_rak_with_onverwachte_resultaten: Rak):
    """Test that Onderbouw.alle_onverwachte_resultaten includes OnverwachtResultaat from all children."""
    rak = mock_rak_with_onverwachte_resultaten
    onderbouw = rak.rakdelen[0].onderbouw

    alle_onverwachte = onderbouw.alle_onverwachte_resultaten

    # Onderbouw children have: paal.schoorstand_graden (1) + kesp.hoek_tov_lengte_as_graden (1) + vloer.materiaal (1) = 3
    assert len(alle_onverwachte) == 3
    waarden = [o.waarde for o in alle_onverwachte]
    assert "onleesbaar" in waarden
    assert "N/A" in waarden
    assert "onbekend materiaal" in waarden


def test_rakdeel_alle_onverwachte_resultaten(mock_rak_with_onverwachte_resultaten: Rak):
    """Test that Rakdeel.alle_onverwachte_resultaten includes all OnverwachtResultaat from the tree."""
    rak = mock_rak_with_onverwachte_resultaten
    rakdeel = rak.rakdelen[0]

    alle_onverwachte = rakdeel.alle_onverwachte_resultaten

    # Should have: paal (1) + kesp (1) + vloer (1) + metselwerk (1) + bovenbouw (1) = 5
    assert len(alle_onverwachte) == 5
    waarden = [o.waarde for o in alle_onverwachte]
    assert "onleesbaar" in waarden
    assert "N/A" in waarden
    assert "onbekend materiaal" in waarden
    assert "niet meetbaar" in waarden
    assert "niet gemeten" in waarden


def test_rak_alle_onverwachte_resultaten(mock_rak_with_onverwachte_resultaten: Rak):
    """Test that Rak.alle_onverwachte_resultaten includes all OnverwachtResultaat from the entire hierarchy."""
    rak = mock_rak_with_onverwachte_resultaten

    alle_onverwachte = rak.alle_onverwachte_resultaten

    # Should collect all OnverwachtResultaat instances from the entire tree
    assert len(alle_onverwachte) == 5
    waarden = [o.waarde for o in alle_onverwachte]
    assert "onleesbaar" in waarden
    assert "N/A" in waarden
    assert "onbekend materiaal" in waarden
    assert "niet meetbaar" in waarden
    assert "niet gemeten" in waarden


def test_empty_rak_alle_gebreken():
    """Test that Rak without gebreken returns empty list."""
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

    vloer = Vloer(materiaal=MateriaalVloer.HOUT)
    onderbouw = Onderbouw(palen=[paal], kespen=[], vloer=vloer)
    bovenbouw = Bovenbouw()
    rakdeel = Rakdeel(rakdeel_id="Test", bovenbouw=bovenbouw, onderbouw=onderbouw)
    rak = Rak(rakdelen=[rakdeel], raknaam="Test", totale_lengte_m=10.0)

    assert len(rak.alle_gebreken) == 0


def test_empty_rak_alle_onverwachte_resultaten():
    """Test that Rak without OnverwachtResultaat returns empty list."""
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

    vloer = Vloer(materiaal=MateriaalVloer.HOUT)
    onderbouw = Onderbouw(palen=[paal], kespen=[], vloer=vloer)
    bovenbouw = Bovenbouw()
    rakdeel = Rakdeel(rakdeel_id="Test", bovenbouw=bovenbouw, onderbouw=onderbouw)
    rak = Rak(rakdelen=[rakdeel], raknaam="Test", totale_lengte_m=10.0)

    assert len(rak.alle_onverwachte_resultaten) == 0
