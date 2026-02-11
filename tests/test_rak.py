"""
We willen de volgende "integratietesten" uitvoeren voor de Rak klasse:

- gegeven goed geparste SmartDocument een rak object zonder OnverwachtResultaat
- gegeven geparste SmartDocument met enkele gebreken een rak object met OnverwachtResultaat in veld X
- gegeven een onvolledig SmartDocument (ontbreken van tabellen en of teksten) een rak object met OnverwachtResultaat in veld Y

TODO:
 - gegeven kzg0202 hoeveel OnverwachtResultaat in totaal willen/verwachten we echt?

Uitgangspunten:
We testen NIET het LLM classificatieproces zelf.
We halen de smart doc en LLM resultaten uit de fixtures,
zodat we de testdata kunnen controleren en aanpassen indien nodig.

"""

from tekstherkenning_ark.models.rak import Rak


def test_kzg0202(kzg0202_from_test_cache):
    """Test that the fixture loads a Rak instance from the test cache correctly."""
    assert isinstance(kzg0202_from_test_cache, Rak)
    assert len(kzg0202_from_test_cache.rakdelen) == 10, f"Expected 10 rakdelen, got {len(kzg0202_from_test_cache.rakdelen)}"


def test_kzg0202_nul_onverwacht(kzg0202_from_test_cache):
    """Test that the Rak instance from the test cache has the expected gebreken."""
    aantal_overwacht_tot = len(kzg0202_from_test_cache.alle_onverwachte_resultaten)
    assert aantal_overwacht_tot == 0, f"Expected 0 onverwachte resultaten, got {aantal_overwacht_tot}"


def test_kzg0202_gebreken(kzg0202_from_test_cache):
    """Test that the Rak instance from the test cache has the expected gebreken."""
    aantal_gebreken_tot = len(kzg0202_from_test_cache.alle_gebreken)
    assert aantal_gebreken_tot == 69, f"Expected 69 gebreken, got {aantal_gebreken_tot}"
    # header gebrekcodering constructie B tabel meegneomen als onbekend gebrek


def test_kzg0202_raknaam(kzg0202_from_test_cache):
    """Test that the Rak instance from the test cache has the expected raknaam."""
    raknaam = kzg0202_from_test_cache.raknaam
    assert raknaam == "KZG0202", f"Expected raknaam 'KZG0202', got '{raknaam}'"


def test_kzg0202_aantallen(kzg0202_from_test_cache):
    """Test that the Rak instance from the test cache has the expected aantallen."""
    rak = kzg0202_from_test_cache
    assert len(rak.alle_palen) == 139, f"Expected 139 palen, got {len(rak.alle_palen)}"
    assert len(rak.alle_houtmonsters) == 52, f"Expected 52 houtmonstersn, got {len(rak.alle_houtmonsters)}"
    assert len(rak.alle_kespen) == 97, f"Expected 97 kespen, got {len(rak.alle_kespen)}"  # Kesp8,  80 and 84 missing maybe


def test_kzg0202_kesp_breedtes(kzg0202_from_test_cache):
    """
    test kesp breedtes
    """
    all_hoogtes = []
    all_non_numeric = []
    for _, kesp in kzg0202_from_test_cache.alle_kespen:
        if isinstance(kesp.hoogte_cm, int):
           all_hoogtes.append(kesp.hoogte_cm)
        else:
            all_non_numeric.append(kesp.hoogte_cm)
    assert len(all_non_numeric) == 1, f"Expected 1 non-numeric kesp hoogte, got {len(all_non_numeric)}: {all_non_numeric}"
    assert sum(all_hoogtes) == 1549, f"Expected total height of 1550 cm, got {sum(all_hoogtes)}"
    # expected = 1549 + 1"NM" (total len 97, numerical len 96)
    