"""
Module to test methods related to Paal model.
"""

from tekstherkenning_ark.models.paal import Paal


def test_get_palen_dict_dimensions(paal_tables):
    """check type and dimensions"""
    palen_dict = Paal.from_doc_tables(paal_tables)
    assert isinstance(palen_dict, dict)
    assert len(palen_dict) == 10


def test_get_palen_no_onverwacht_resultaat(paal_tables):
    """check no onverwacht resultaat in parsed palen"""
    palen_dict = Paal.from_doc_tables(paal_tables)

    total_onverwacht = 0
    for palen in palen_dict.values():
        for paal in palen:
            total_onverwacht += len(paal.onverwachte_resultaten)
    assert len(paal.onverwachte_resultaten) == 0, \
        f"Er zijn (onverwacht !) onverwachte resultaten gevonden in de palen: {total_onverwacht}"
