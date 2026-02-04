"""Integration test to verify OnverwachtResultaat works with actual models."""

from tekstherkenning_ark.models.rak_base_model import RakBaseModel
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat, OnverwachtResultaatType
from tekstherkenning_ark.enums import NietBeschikbaar


class SimpleTestModel(RakBaseModel):
    """Simple test model with various field types."""

    naam: str
    leeftijd: int | None = None
    actief: bool = True


def test_simple_model_with_onverwacht_resultaat():
    """Test that OnverwachtResultaat can be used in place of regular values."""

    onverwacht_naam = OnverwachtResultaat(
        waarde="Parsing fout",
        onverwacht_resultaat_type=OnverwachtResultaatType.PARSING_FOUT,
        details="Kon naam niet parsen",
    )

    model = SimpleTestModel(naam=onverwacht_naam, leeftijd=25, actief=True)

    assert isinstance(model.naam, OnverwachtResultaat)
    assert model.naam.waarde == "Parsing fout"
    assert model.leeftijd == 25
    assert model.actief is True


def test_simple_model_with_normal_values():
    """Test that normal values still work."""

    model = SimpleTestModel(naam="Test Naam", leeftijd=30, actief=False)

    assert model.naam == "Test Naam"
    assert model.leeftijd == 30
    assert model.actief is False


def test_optional_field_with_onverwacht_resultaat():
    """Test that optional fields can accept OnverwachtResultaat."""

    onverwacht_leeftijd = OnverwachtResultaat(
        waarde="niet gevonden", onverwacht_resultaat_type=OnverwachtResultaatType.PARSING_FOUT
    )

    model = SimpleTestModel(naam="Test", leeftijd=onverwacht_leeftijd)

    assert isinstance(model.leeftijd, OnverwachtResultaat)


def test_enum_field_with_onverwacht_resultaat():
    """Test that enum fields can accept OnverwachtResultaat."""

    class ModelMetEnum(RakBaseModel):
        status: NietBeschikbaar | str

    onverwacht = OnverwachtResultaat(
        waarde="unexpected status", onverwacht_resultaat_type=OnverwachtResultaatType.INCORRECT_TYPE
    )

    model = ModelMetEnum(status=onverwacht)

    assert isinstance(model.status, OnverwachtResultaat)
