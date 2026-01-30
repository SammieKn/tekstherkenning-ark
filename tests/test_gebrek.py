"""
tests for the gebrek module
"""
import pytest

from tekstherkenning_ark.models.gebrek import Gebrek


def test_from_table(gebreken_tabel_fixture):
    """test from table method"""

    gebreken = Gebrek.from_doc_table(gebreken_tabel_fixture)
    assert isinstance(gebreken, list), "Expected a list of Gebrek instances"
    assert all(isinstance(g, Gebrek) for g in gebreken), "All items in the list should be Gebrek instances"
    assert len(gebreken) == 4, f"Expected 4 gebreken, got {len(gebreken)}"


def test_from_faulty_table(palen_tabel_fixture):
    """test from table method with faulty table"""
    with pytest.raises(ValueError, match="Unexpected table header"):
        Gebrek.from_doc_table(palen_tabel_fixture)
