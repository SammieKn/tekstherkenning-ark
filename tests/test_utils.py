"""
Test Utils Module
"""

import pytest

# Import directly to avoid circular import issues
from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat, OnverwachtResultaatType

# Import utils functions - this must come after models import
from tekstherkenning_ark.utils import (
    clean_kesp_id,
    get_table_content,
    parse_ja_nee,
    clean_paal_id,
    contains_paal_id,
    contains_kesp_id,
    get_paal_id,
    get_kesp_id,
    is_algemeen_gebrek,
    is_houtmonster_id,
    clean_string,
    dict_items_flat,
    remove_constructie_id,
)


def test_parse_ja():
    """Test parsing 'Ja' values"""
    assert parse_ja_nee("Ja") is True
    assert parse_ja_nee("ja") is True
    assert parse_ja_nee("JA") is True
    assert parse_ja_nee("  Ja  ") is True
    assert parse_ja_nee("Jazeker") is True


def test_parse_nee():
    """Test parsing 'Nee' values"""
    assert parse_ja_nee("Nee") is False
    assert parse_ja_nee("nee") is False
    assert parse_ja_nee("NEE") is False
    assert parse_ja_nee("  Nee  ") is False
    assert parse_ja_nee("Neen") is False


def test_parse_a_as_ja():
    """Test parsing 'a' as Ja (special case)"""
    assert parse_ja_nee("a") is True
    assert parse_ja_nee("A") is True


def test_parse_niet_beschikbaar():
    """Test parsing NietBeschikbaar enum values"""
    assert parse_ja_nee("NVT") == NietBeschikbaar.NIET_VAN_TOEPASSING
    assert parse_ja_nee("NM") == NietBeschikbaar.NIET_MEETBAAR
    assert parse_ja_nee("") == NietBeschikbaar.LEEG


def test_parse_onverwacht():
    """Test parsing unexpected values"""
    result = parse_ja_nee("misschien")
    assert isinstance(result, OnverwachtResultaat)
    assert result.waarde == "misschien"
    assert result.onverwacht_resultaat_type == OnverwachtResultaatType.PARSING_FOUT

    result = parse_ja_nee("123")
    assert isinstance(result, OnverwachtResultaat)


def test_clean_known_exceptions():
    """Test cleaning known exception cases"""
    assert clean_paal_id("P.2.163") == "P2.163"
    assert clean_paal_id("21.169") == "P2.169"


def test_clean_normal_paal_id():
    """Test cleaning normal paal IDs"""
    assert clean_paal_id("P1.1") == "P1.1"
    assert clean_paal_id("P2.10") == "P2.10"


def test_clean_with_whitespace():
    """Test cleaning paal IDs with whitespace"""
    assert clean_paal_id("  P1.1  ") == "P1.1"


def test_contains_valid_paal_id():
    """Test strings containing valid paal IDs"""
    assert contains_paal_id("P1.1") is True
    assert contains_paal_id("P2.10") is True
    assert contains_paal_id("P2.163") is True
    assert contains_paal_id("Some text P1.1 more text") is True
    assert contains_paal_id("P.2.163") is True  # Exception case


def test_not_contains_paal_id():
    """Test strings not containing valid paal IDs"""
    assert contains_paal_id("P1") is False
    assert contains_paal_id("P.1") is False
    assert contains_paal_id("1.1") is False
    assert contains_paal_id("random text") is False


def test_contains_valid_kesp_id():
    """Test strings containing valid kesp IDs"""
    assert contains_kesp_id("K1") is True
    assert contains_kesp_id("K24") is True
    assert contains_kesp_id("K100") is True
    assert contains_kesp_id("Some text K1 more text") is True


def test_not_contains_kesp_id():
    """Test strings not containing valid kesp IDs"""
    assert contains_kesp_id("K") is False
    assert contains_kesp_id("1") is False
    assert contains_kesp_id("random text") is False


def test_extract_valid_paal_id():
    """Test extracting valid paal IDs"""
    assert get_paal_id("P1.1") == "P1.1"
    assert get_paal_id("P2.10") == "P2.10"
    assert get_paal_id("P2.163") == "P2.163"
    assert get_paal_id("Some text P1.1 more text") == "P1.1"
    assert get_paal_id("P.2.163") == "P2.163"  # Exception case


def test_extract_no_paal_id():
    """Test extracting from strings without paal IDs"""
    assert get_paal_id("random text") is None
    assert get_paal_id("P1") is None
    assert get_paal_id("K1") is None


def test_extract_valid_kesp_id():
    """Test extracting valid kesp IDs"""
    assert get_kesp_id("K1") == "K1"
    assert get_kesp_id("K24") == "K24"
    assert get_kesp_id("K100") == "K100"
    assert get_kesp_id("Some text K1 more text") == "K1"


def test_extract_no_kesp_id():
    """Test extracting from strings without kesp IDs"""
    assert get_kesp_id("random text") is None
    assert get_kesp_id("K") is None
    assert get_kesp_id("P1.1") is None


def test_valid_algemeen_gebrek_patterns():
    """Test valid algemeen gebrek patterns"""
    assert is_algemeen_gebrek("GB1") is True
    assert is_algemeen_gebrek("GB12") is True
    assert is_algemeen_gebrek("GB123") is True
    assert is_algemeen_gebrek("gb1") is True  # Case insensitive
    assert is_algemeen_gebrek("Algemeen") is True


def test_invalid_algemeen_gebrek_patterns():
    """Test invalid algemeen gebrek patterns"""
    assert is_algemeen_gebrek("GB1234") is False  # Too many digits
    assert is_algemeen_gebrek("GB") is False  # No digits
    assert is_algemeen_gebrek("G1") is False
    assert is_algemeen_gebrek("random") is False


def test_valid_houtmonster_id():
    """Test valid houtmonster IDs"""
    assert is_houtmonster_id("HEG0801/CONSTRUCTIE A/P1.16/HM") is True
    assert is_houtmonster_id("DOC123/CONSTRUCTIE B/P2.10/HM") is True
    assert is_houtmonster_id("ABC/CONSTRUCTIE C/P1.1/hm") is True  # Case insensitive


def test_invalid_houtmonster_id():
    """Test invalid houtmonster IDs"""
    assert is_houtmonster_id("HEG0801/CONSTRUCTIE A/P1.16") is False  # Missing HM
    assert is_houtmonster_id("HEG0801/P1.16/HM") is False  # Missing constructie
    assert is_houtmonster_id("HEG0801/CONSTRUCTIE A/K1/HM") is False  # Not a paal ID
    assert is_houtmonster_id("random text") is False


def test_clean_quotes():
    """Test removing quotes"""
    assert clean_string('"test"') == "test"
    assert clean_string("'test'") == "test"
    assert clean_string("`test`") == "test"


def test_clean_whitespace():
    """Test removing whitespace"""
    assert clean_string("  test  ") == "test"
    assert clean_string("\ntest\n") == "test"
    assert clean_string("\ttest\t") == "test"


def test_clean_between_colons():
    """Test removing content between colons"""
    assert clean_string("test:remove:value") == "testvalue"
    assert clean_string("test:abc:def") == "testdef"


def test_clean_unicode():
    """Test normalizing unicode characters"""
    assert clean_string("café") == "cafe"
    assert clean_string("naïve") == "naive"
    assert clean_string("Zürich") == "Zurich"


def test_clean_combined():
    """Test cleaning with multiple transformations"""
    assert clean_string('  "café:test:"  ') == "cafe"
    assert clean_string("'  test  '") == "test"


def test_dict_items_flat_normal():
    """Test flattening a normal dictionary with multiple keys"""
    item_dict = {
        "Constructie A": ["item1", "item2"],
        "Constructie B": ["item3", "item4", "item5"],
        "Constructie C": ["item6"],
    }
    result = dict_items_flat(item_dict)
    assert result == ["item1", "item2", "item3", "item4", "item5", "item6"]


def test_dict_items_flat_empty():
    """Test flattening an empty dictionary"""
    result = dict_items_flat({})
    assert result == []


def test_dict_items_flat_with_empty_lists():
    """Test flattening a dictionary containing empty lists"""
    item_dict = {
        "Constructie A": ["item1", "item2"],
        "Constructie B": [],
        "Constructie C": ["item3"],
    }
    result = dict_items_flat(item_dict)
    assert result == ["item1", "item2", "item3"]


def test_remove_constructie_id_normal():
    """Test that remove_constructie_id returns all items under empty key"""
    item_dict = {
        "Constructie A": ["item1", "item2"],
        "Constructie B": ["item3", "item4"],
    }
    result = remove_constructie_id(item_dict)
    assert result == {"": ["item1", "item2", "item3", "item4"]}


def test_remove_constructie_id_with_unassigned():
    """Test remove_constructie_id when there are already unassigned items"""
    item_dict = {
        "": ["item1"],
        "Constructie A": ["item2", "item3"],
    }
    result = remove_constructie_id(item_dict)
    assert result == {"": ["item1", "item2", "item3"]}


def test_remove_constructie_id_empty():
    """Test remove_constructie_id with an empty dictionary"""
    result = remove_constructie_id({})
    assert result == {"": []}


def test_clean_kesp_id_valid_id():
    """Test cleaning kesp IDs"""
    assert clean_kesp_id("K1") == "K1"


def test_clean_kesp_id_ocr_errors():
    """Test cleaning kesp IDs with common OCR errors"""
    assert clean_kesp_id("K5O") == "K50"
    assert clean_kesp_id("KB") == "K8"
    assert clean_kesp_id("  Kgg  ") == "K99"


def test_clean_kesp_id_no_k():
    """Test cleaning kesp IDs that don't start with K - should return original value"""
    assert clean_kesp_id("  aangetast  ") == "aangetast"
