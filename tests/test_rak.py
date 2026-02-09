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
    assert len(kzg0202_from_test_cache.rakdelen) == 11, f"Expected 11 rakdelen, got {len(kzg0202_from_test_cache.rakdelen)}"


def test_kzg0202_onverwacht(kzg0202_from_test_cache):
    """Test that the Rak instance from the test cache has the expected gebreken."""
    aantal_overwacht_tot = len(kzg0202_from_test_cache.alle_onverwachte_resultaten)
    assert aantal_overwacht_tot == 1037, f"Expected 1037 onverwachte resultaten, got {aantal_overwacht_tot}"