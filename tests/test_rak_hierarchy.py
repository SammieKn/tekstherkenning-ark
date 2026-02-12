"""Tests for Rak hierarchy methods: children, alle_gebreken, onverwachte_resultaten, alle_onverwachte_resultaten."""

from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.onderbouw import Onderbouw
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
    """Test that Bovenbouw.children returns empty list."""
    rak = mock_rak_with_gebreken
    bovenbouw = rak.rakdelen[0].bovenbouw

    children = bovenbouw.children

    # Bovenbouw has no children anymore since metselwerk was removed
    assert len(children) == 0


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

    # Should have gebreken from: paal1 (1), kesp1 (1), rakdeel (1) = 3 total
    assert len(alle_gebreken) == 3

    # Check that all expected gebreken are present with their paths
    coderingen = [g.codering for path, g in alle_gebreken]
    assert "GP1" in coderingen  # From paal
    assert "GK1" in coderingen  # From kesp
    assert "GR1" in coderingen  # From rakdeel

    # Verify paths are properly formatted
    paths = [path for path, g in alle_gebreken]
    assert any("P1.1" in path for path in paths)
    assert any("K1" in path for path in paths)


def test_rakdeel_alle_gebreken(mock_rak_with_gebreken: Rak):
    """Test that Rakdeel.alle_gebreken includes gebreken from all sub-components."""
    rak = mock_rak_with_gebreken
    rakdeel = rak.rakdelen[0]

    alle_gebreken = rakdeel.alle_gebreken

    # Should have all gebreken from the rakdeel tree
    assert len(alle_gebreken) == 3
    coderingen = [g.codering for path, g in alle_gebreken]
    assert "GP1" in coderingen
    assert "GK1" in coderingen
    assert "GR1" in coderingen

    # Verify all paths start with rakdeel_id
    paths = [path for path, g in alle_gebreken]
    assert all(path.startswith("Constructie A") for path in paths)


def test_onverwachte_resultaten_single_model(mock_rak_with_onverwachte_resultaten: Rak):
    """Test that onverwachte_resultaten returns OnverwachtResultaat instances from a single model."""
    rak = mock_rak_with_onverwachte_resultaten
    paal = rak.rakdelen[0].onderbouw.palen[0]

    onverwachte = paal.onverwachte_resultaten

    # Paal should have 1 OnverwachtResultaat (schoor_graden)
    assert len(onverwachte) == 1
    assert isinstance(onverwachte[0], OnverwachtResultaat)
    assert onverwachte[0].waarde == "onleesbaar"


def test_bovenbouw_alle_onverwachte_resultaten(mock_rak_with_onverwachte_resultaten: Rak):
    """Test that Bovenbouw.alle_onverwachte_resultaten includes OnverwachtResultaat from children."""
    rak = mock_rak_with_onverwachte_resultaten
    bovenbouw = rak.rakdelen[0].bovenbouw

    alle_onverwachte = bovenbouw.alle_onverwachte_resultaten

    # Bovenbouw has: bovenkant_deksteen_cm_tov_nap (1)
    assert len(alle_onverwachte) == 1
    waarden = [o.waarde for path, o in alle_onverwachte]
    assert "niet gemeten" in waarden


def test_onderbouw_alle_onverwachte_resultaten(mock_rak_with_onverwachte_resultaten: Rak):
    """Test that Onderbouw.alle_onverwachte_resultaten includes OnverwachtResultaat from all children."""
    rak = mock_rak_with_onverwachte_resultaten
    onderbouw = rak.rakdelen[0].onderbouw

    alle_onverwachte = onderbouw.alle_onverwachte_resultaten

    # Onderbouw children have: paal.schoor_graden (1) + kesp.hoek_tov_lengte_as_graden (1) + vloer.materiaal (1) = 3
    assert len(alle_onverwachte) == 3
    waarden = [o.waarde for path, o in alle_onverwachte]
    assert "onleesbaar" in waarden
    assert "N/A" in waarden

    # Verify paths contain expected identifiers
    paths = [path for path, o in alle_onverwachte]
    assert any("P1.1" in path for path in paths)
    assert any("K1" in path for path in paths)
    assert any("vloer" in path for path in paths)


def test_rakdeel_alle_onverwachte_resultaten(mock_rak_with_onverwachte_resultaten: Rak):
    """Test that Rakdeel.alle_onverwachte_resultaten includes all OnverwachtResultaat from the tree."""
    rak = mock_rak_with_onverwachte_resultaten
    rakdeel = rak.rakdelen[0]

    alle_onverwachte = rakdeel.alle_onverwachte_resultaten

    # Should have: paal (1) + kesp (1) + vloer (1) + bovenbouw (1) = 4
    assert len(alle_onverwachte) == 4
    waarden = [o.waarde for path, o in alle_onverwachte]
    assert "onleesbaar" in waarden
    assert "N/A" in waarden
    assert "onbekend materiaal" in waarden
    assert "niet gemeten" in waarden

    # Verify all paths start with rakdeel_id
    paths = [path for path, o in alle_onverwachte]
    assert all(path.startswith("Constructie A") for path in paths)


def test_rak_alle_onverwachte_resultaten(mock_rak_with_onverwachte_resultaten: Rak):
    """Test that Rak.alle_onverwachte_resultaten includes all OnverwachtResultaat from the entire hierarchy."""
    rak = mock_rak_with_onverwachte_resultaten

    alle_onverwachte = rak.alle_onverwachte_resultaten

    # Should collect all OnverwachtResultaat instances from the entire tree
    assert len(alle_onverwachte) == 4
    waarden = [o.waarde for path, o in alle_onverwachte]
    assert "onleesbaar" in waarden
    assert "N/A" in waarden
    assert "onbekend materiaal" in waarden
    assert "niet gemeten" in waarden

    # Verify full hierarchical paths
    paths = [path for path, o in alle_onverwachte]
    assert all(path.startswith("Test Rak/Constructie A") for path in paths)
    assert any("onderbouw/P1.1" in path for path in paths)


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


def test_gebreken_path_from_rak(mock_rak_with_gebreken: Rak):
    """Test that gebreken paths follow the correct hierarchical format from Rak level."""
    rak = mock_rak_with_gebreken
    alle_gebreken = rak.alle_gebreken

    # Create a dict mapping codering to path for easier testing
    gebrek_paths = {g.codering: path for path, g in alle_gebreken}

    # Test paal gebrek path: <raknaam>.<rakdeel_id>.onderbouw.<paal_nummer>
    assert "GP1" in gebrek_paths
    assert gebrek_paths["GP1"] == "Test Rak/Constructie A/onderbouw/P1.1"

    # Test kesp gebrek path: <raknaam>.<rakdeel_id>.onderbouw.<kesp_nummer>
    assert "GK1" in gebrek_paths
    assert gebrek_paths["GK1"] == "Test Rak/Constructie A/onderbouw/K1"

    # Test rakdeel gebrek path: <raknaam>.<rakdeel_id>
    assert "GR1" in gebrek_paths
    assert gebrek_paths["GR1"] == "Test Rak/Constructie A"


def test_gebreken_path_from_rakdeel(mock_rak_with_gebreken: Rak):
    """Test that gebreken paths from Rakdeel level start correctly."""
    rakdeel = mock_rak_with_gebreken.rakdelen[0]
    alle_gebreken = rakdeel.alle_gebreken

    gebrek_paths = {g.codering: path for path, g in alle_gebreken}

    # Paths should start with rakdeel_id, not include raknaam
    assert gebrek_paths["GP1"] == "Constructie A/onderbouw/P1.1"
    assert gebrek_paths["GK1"] == "Constructie A/onderbouw/K1"
    assert gebrek_paths["GR1"] == "Constructie A"


def test_gebreken_path_from_onderbouw(mock_rak_with_gebreken: Rak):
    """Test that gebreken paths from Onderbouw level start correctly."""
    onderbouw = mock_rak_with_gebreken.rakdelen[0].onderbouw
    alle_gebreken = onderbouw.alle_gebreken

    gebrek_paths = {g.codering: path for path, g in alle_gebreken}

    # Paths should start with 'onderbouw'
    assert gebrek_paths["GP1"] == "onderbouw/P1.1"
    assert gebrek_paths["GK1"] == "onderbouw/K1"


def test_gebreken_path_from_paal(mock_rak_with_gebreken: Rak):
    """Test that gebreken path from Paal level is just the paal identifier."""
    paal = mock_rak_with_gebreken.rakdelen[0].onderbouw.palen[0]
    alle_gebreken = paal.alle_gebreken

    assert len(alle_gebreken) == 1
    path, gebrek = alle_gebreken[0]
    assert gebrek.codering == "GP1"
    assert path == "P1.1"


def test_onverwachte_resultaten_path_from_rak(mock_rak_with_onverwachte_resultaten: Rak):
    """Test that onverwachte resultaten paths follow the correct hierarchical format."""
    rak = mock_rak_with_onverwachte_resultaten
    alle_onverwachte = rak.alle_onverwachte_resultaten

    # Create a dict mapping waarde to path for easier testing
    onverwacht_paths = {o.waarde: path for path, o in alle_onverwachte}

    # Test paths for different levels in hierarchy
    assert "niet gemeten" in onverwacht_paths  # bovenbouw.bovenkant_deksteen_cm_tov_nap
    assert onverwacht_paths["niet gemeten"] == "Test Rak/Constructie A/bovenbouw"

    assert "onleesbaar" in onverwacht_paths  # paal.schoor_graden
    assert onverwacht_paths["onleesbaar"] == "Test Rak/Constructie A/onderbouw/P1.1"

    assert "N/A" in onverwacht_paths  # kesp.hoek_tov_lengte_as_graden
    assert onverwacht_paths["N/A"] == "Test Rak/Constructie A/onderbouw/K1"


def test_onverwachte_resultaten_path_from_bovenbouw(mock_rak_with_onverwachte_resultaten: Rak):
    """Test that onverwachte resultaten paths from Bovenbouw level start correctly."""
    bovenbouw = mock_rak_with_onverwachte_resultaten.rakdelen[0].bovenbouw
    alle_onverwachte = bovenbouw.alle_onverwachte_resultaten

    onverwacht_paths = {o.waarde: path for path, o in alle_onverwachte}

    # Paths should start with 'bovenbouw'
    assert onverwacht_paths["niet gemeten"] == "bovenbouw"
