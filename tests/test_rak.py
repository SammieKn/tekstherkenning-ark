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

import json

from polyfactory.factories.pydantic_factory import ModelFactory
import pytest

from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.rak import Rak
from tests.conftest import TEST_DATA_DIR


def test_kzg0202(kzg0202_rak: Rak):
    """Test that the fixture loads a Rak instance from the test cache correctly."""
    assert isinstance(kzg0202_rak, Rak)
    assert len(kzg0202_rak.rakdelen) == 10, f"Expected 10 rakdelen, got {len(kzg0202_rak.rakdelen)}"


def test_kzg0202_nul_onverwacht(kzg0202_rak: Rak):
    """Test that the Rak instance from the test cache has the expected gebreken."""
    aantal_overwacht_tot = len(kzg0202_rak.rakdelen[0].alle_onverwachte_resultaten)
    assert aantal_overwacht_tot == 0, f"Expected 0 onverwachte resultaten, got {aantal_overwacht_tot}"


def test_kzg0202_gebreken(kzg0202_rak: Rak):
    """Test that the Rak instance from the test cache has the expected gebreken."""
    aantal_gebreken_tot = len(kzg0202_rak.alle_gebreken)
    assert aantal_gebreken_tot == 79, f"Expected 79 gebreken, got {aantal_gebreken_tot}"
    # header gebrekcodering constructie B tabel meegneomen als onbekend gebrek


def test_kzg0202_raknaam(kzg0202_rak: Rak):
    """Test that the Rak instance from the test cache has the expected raknaam."""
    raknaam = kzg0202_rak.raknaam
    assert raknaam == "KZG0202", f"Expected raknaam 'KZG0202', got '{raknaam}'"


def test_kzg0202_aantallen(kzg0202_rak: Rak):
    """Test that the Rak instance from the test cache has the expected aantallen."""
    rak = kzg0202_rak
    assert len(rak.alle_palen) == 139, f"Expected 139 palen, got {len(rak.alle_palen)}"
    assert len(rak.alle_houtmonsters) == 52, f"Expected 52 houtmonstersn, got {len(rak.alle_houtmonsters)}"
    assert (
        len(rak.alle_kespen) == 97
    ), f"Expected 97 kespen, got {len(rak.alle_kespen)}"  # Kesp8,  80 and 84 missing maybe


def test_kzg0202_kesp_breedtes(kzg0202_rak: Rak):
    """
    test kesp breedtes
    """
    all_hoogtes = []
    all_non_numeric = []
    for _, kesp in kzg0202_rak.alle_kespen:
        if isinstance(kesp.hoogte_cm, int):
            all_hoogtes.append(kesp.hoogte_cm)
        else:
            all_non_numeric.append(kesp.hoogte_cm)
    assert (
        len(all_non_numeric) == 1
    ), f"Expected 1 non-numeric kesp hoogte, got {len(all_non_numeric)}: {all_non_numeric}"
    assert sum(all_hoogtes) == 1549, f"Expected total height of 1550 cm, got {sum(all_hoogtes)}"
    # expected = 1549 + 1"NM" (total len 97, numerical len 96)


class TestRakToJson:
    def test_mock_rak_scheuren_to_json(self, mock_rak_with_scheuren: Rak, mock_rak_with_scheuren_json: str):
        """Test that a mock Rak with scheuren can be serialized to JSON."""
        json_str = mock_rak_with_scheuren.model_dump_json(indent=2)

        # Uncomment this line to update the expected JSON file with the current output
        # (useful when intentionally changing the model structure or test data)
        # (TEST_DATA_DIR / "mock_rak_with_scheuren.json").write_text(json_str, encoding="utf-8")

        expected_dict = json.loads(mock_rak_with_scheuren_json)
        actual_dict = json.loads(json_str)

        assert (
            actual_dict["rakdelen"][0]["bovenbouw"]["gebreken"]
            == expected_dict["rakdelen"][0]["bovenbouw"]["gebreken"]
        ), "Gebreken in bovenbouw komen niet overeen"

        assert actual_dict["rakdelen"][0]["alle_gebreken"] == expected_dict["rakdelen"][0]["alle_gebreken"]

    @pytest.mark.parametrize("gebrek_class", [Gebrek] + Gebrek.__subclasses__())
    def test_gebrek_subclasses_to_json(self, gebrek_class: type[Gebrek]):
        """Test that all Gebrek subclasses can be serialized to JSON."""

        # Create a mock instance of the subclass using a ModelFactory,
        # which will fill in all required fields with dummy data
        class SubclassMockFactory(ModelFactory[gebrek_class]):
            __model__ = gebrek_class

        instance = SubclassMockFactory.build()

        # Check if we actually got an instance of the correct class
        assert isinstance(instance, gebrek_class), f"Factory did not create an instance of {gebrek_class.__name__}"

        # Put the gebrek in a Rak
        rak = Rak(
            raknaam="TESTRAK",
            totale_lengte_m=10.0,
            rakdelen=[],
            gebreken=[instance],
        )

        # Create the JSON string from the instance
        json_str = rak.model_dump_json(indent=2)

        assert json_str is not None, f"JSON serialization failed for {gebrek_class.__name__}"

        # Retrieve all expected fields for the subclass
        expected_fields = list(gebrek_class.model_fields.keys()) + list(gebrek_class.model_computed_fields.keys())

        # Subclasses should have more fields than the base Gebrek class
        if gebrek_class != Gebrek:
            assert len(expected_fields) > len(Gebrek.model_fields) + len(Gebrek.model_computed_fields)

        # Check if all expected fields are present in the JSON output
        for field in expected_fields:
            assert (
                f'"{field}":' in json_str
            ), f"Expected field '{field}' not found in JSON output for {gebrek_class.__name__}"
