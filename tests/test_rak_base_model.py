"""Tests for RakBaseModel automatic type hint modification."""

from typing import get_args, get_origin, Union
from tekstherkenning_ark.models.rak_base_model import RakBaseModel
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat


class TestSubclass(RakBaseModel):
    """Test subclass to verify type hint modification."""

    simple_str: str
    optional_int: int | None
    collection_list: list[str]
    simple_bool: bool


def test_instance_can_accept_onverwacht_resultaat():
    """Test that an instance can actually accept OnverwachtResultaat values."""

    # Create instance with OnverwachtResultaat
    instance = TestSubclass(
        simple_str="simple", optional_int=42, collection_list=["a", "b"], simple_bool="Onverwachte waarde"
    )

    assert isinstance(instance.simple_bool, OnverwachtResultaat)
    assert instance.simple_bool.waarde == "Onverwachte waarde"


def test_instance_can_accept_normal_values():
    """Test that an instance can still accept normal values."""

    instance = TestSubclass(simple_str="hello", optional_int=42, collection_list=["a", "b"], simple_bool=True)

    assert instance.simple_str == "hello"
    assert instance.optional_int == 42
    assert instance.collection_list == ["a", "b"]
    assert instance.simple_bool is True
