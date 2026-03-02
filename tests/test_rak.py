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

from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.onderbouw import Onderbouw
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.models.vloer import Vloer


def test_kzg0202(kzg0202_rak: Rak):
    """Test that the fixture loads a Rak instance from the test cache correctly."""
    assert isinstance(kzg0202_rak, Rak)
    assert len(kzg0202_rak.rakdelen) == 10, f"Expected 10 rakdelen, got {len(kzg0202_rak.rakdelen)}"


def test_kzg0202_nul_onverwacht(kzg0202_rak: Rak):
    """Test that the Rak instance from the test cache has the expected gebreken."""
    aantal_overwacht_tot = len(kzg0202_rak.alle_onverwachte_resultaten)
    assert aantal_overwacht_tot == 0, f"Expected 0 onverwachte resultaten, got {aantal_overwacht_tot}"


def test_kzg0202_gebreken(kzg0202_rak: Rak):
    """Test that the Rak instance from the test cache has the expected gebreken."""
    aantal_gebreken_tot = len(kzg0202_rak.alle_gebreken)
    assert aantal_gebreken_tot == 78, f"Expected 78 gebreken, got {aantal_gebreken_tot}"
    # header gebrekcodering constructie B tabel meegneomen als onbekend gebrek


# TODO fix these tests when working on issues #89 adnd #90 - MT
# def test_kzg0202_raknaam(kzg0202_rak: Rak):
#     """Test that the Rak instance from the test cache has the expected raknaam."""
#     raknaam = kzg0202_rak.raknaam
#     assert raknaam == "KZG0202", f"Expected raknaam 'KZG0202', got '{raknaam}'"


# def test_kzg0202_aantallen(kzg0202_rak: Rak):
#     """Test that the Rak instance from the test cache has the expected aantallen."""
#     rak = kzg0202_rak
#     assert len(rak.alle_palen) == 139, f"Expected 139 palen, got {len(rak.alle_palen)}"
#     assert len(rak.alle_houtmonsters) == 52, f"Expected 52 houtmonstersn, got {len(rak.alle_houtmonsters)}"
#     assert (
#         len(rak.alle_kespen) == 97
#     ), f"Expected 97 kespen, got {len(rak.alle_kespen)}"  # Kesp8,  80 and 84 missing maybe


# def test_kzg0202_kesp_breedtes(kzg0202_rak: Rak):
#     """
#     test kesp breedtes
#     """
#     all_hoogtes = []
#     all_non_numeric = []
#     for _, kesp in kzg0202_rak.alle_kespen:
#         if isinstance(kesp.hoogte_cm, int):
#             all_hoogtes.append(kesp.hoogte_cm)
#         else:
#             all_non_numeric.append(kesp.hoogte_cm)
#     assert (
#         len(all_non_numeric) == 1
#     ), f"Expected 1 non-numeric kesp hoogte, got {len(all_non_numeric)}: {all_non_numeric}"
#     assert sum(all_hoogtes) == 1549, f"Expected total height of 1550 cm, got {sum(all_hoogtes)}"
#     # expected = 1549 + 1"NM" (total len 97, numerical len 96)


def test_vijf_slechte_kespen_naast_elkaar_met_mock(mock_rak_with_gebreken: Rak):
    """Test vijf_slechte_kespen_naast_elkaar met mock data (K2-K6 zijn aangetast)."""

    assert mock_rak_with_gebreken.vijf_slechte_kespen_naast_elkaar


def test_vijf_slechte_kespen_naast_elkaar_minder_dan_vijf_kespen(mock_rak_with_gebreken: Rak):
    """Test vijf_slechte_kespen_naast_elkaar met minder dan 5 kespen totaal."""

    # Keep only K1-K3
    mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen = mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen[:3]
    assert not mock_rak_with_gebreken.vijf_slechte_kespen_naast_elkaar


def test_vijf_slechte_kespen_naast_elkaar_onderbroken(mock_rak_with_gebreken: Rak):
    """Test vijf_slechte_kespen_naast_elkaar met exact 4 consecutive aangetaste kespen."""

    # K3 niet aangetast
    mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen[2].is_aangetast = False

    assert not mock_rak_with_gebreken.vijf_slechte_kespen_naast_elkaar


def test_vijf_slechte_kespen_naast_elkaar_gebrek(mock_rak_with_gebreken: Rak):
    """Test vijf_slechte_kespen_naast_elkaar met een gebrek op K1 maar K1 zelf niet aangetast."""

    # Maak K3 niet aangetast maar voeg een gebrek toe
    mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen[2].is_aangetast = False
    mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen[2].gebreken.append(
        Gebrek(codering="GK1", omschrijving="Beschadigd kesp", figuurnummer="F2")
    )

    assert mock_rak_with_gebreken.vijf_slechte_kespen_naast_elkaar


def test_vijf_slechte_kespen_naast_elkaar_meer_dan_vijf(mock_rak_with_gebreken: Rak):
    """Test vijf_slechte_kespen_naast_elkaar met 6 consecutive aangetaste kespen."""

    # K7 ook aangetast maken
    mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen[6].is_aangetast = True

    assert mock_rak_with_gebreken.vijf_slechte_kespen_naast_elkaar


def test_vijf_slechte_kespen_naast_elkaar_geen_kespen(mock_rak_with_gebreken: Rak):
    """Test vijf_slechte_kespen_naast_elkaar met geen kespen."""
    # Verwijder alle kespen
    mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen = []

    assert not mock_rak_with_gebreken.vijf_slechte_kespen_naast_elkaar


def test_vijf_slechte_kespen_naast_elkaar_next_rak(mock_rak_with_gebreken: Rak):
    """Test vijf_slechte_kespen_naast_elkaar wanneer een volgende kesp in een nieuw rakdeel zit."""

    # K1-K2 niet aangetast, K3-K7 aangetast
    for i, kesp in enumerate(mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen):
        kesp.is_aangetast = i >= 1  # alleen de laatste 5 kespen worden aangetast
        kesp.gebreken = []

    # Check dat er nu 5 slechte kespen naast elkaar zijn
    assert mock_rak_with_gebreken.vijf_slechte_kespen_naast_elkaar

    # K3 ook niet aangetast maken
    mock_rak_with_gebreken.rakdelen[0].onderbouw.kespen[2].is_aangetast = False

    # Check dat er nu geen 5 slechte kespen naast elkaar zijn
    assert not mock_rak_with_gebreken.vijf_slechte_kespen_naast_elkaar

    # Voeg kesp toe, maar in volgende rakdeel
    nieuw_rakdeel = mock_rak_with_gebreken.rakdelen[0].model_copy()
    nieuw_rakdeel.rakdeel_id = "Constructie B"
    nieuw_rakdeel.onderbouw.kespen = [
        Kesp(
            kesp_nummer="K8",
            hoogte_cm=100,
            breedte_cm=50,
            lengte_uitstekend_deel_cm=30,
            is_opsluitklos_aangetast=False,
            is_aangetast=True,
        )
    ]
    mock_rak_with_gebreken.rakdelen.append(nieuw_rakdeel)

    # Check dat er nu nog steeds geen 5 slechte kespen naast elkaar zijn, omdat K8 in een nieuw rakdeel zit
    assert not mock_rak_with_gebreken.vijf_slechte_kespen_naast_elkaar
