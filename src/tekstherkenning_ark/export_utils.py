from pathlib import Path
from typing import Any

import pandas as pd

from tekstherkenning_ark.document.smart_document import SmartDocument

RAK_TABLE_NAME = "rakken"
RAKDEEL_TABLE_NAME = "rakdelen"
HOUTMONSTER_TABLE_NAME = "houtmonsters"
PALEN_TABLE_NAME = "palen"
KESPEN_TABLE_NAME = "kespen"
GEBREKEN_TABLE_NAME = "gebreken"
TOESTANDBEPALINGEN_TABLE_NAME = "toestandsbepalingen"
ONVERWACHT_RESULTATEN_TABLE_NAME = "onverwachte_resultaten"


def remove_collection_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Verwijder alle velden uit een dictionary waarvan de waarde een list is of een dict instance.

    Dit is nodig voor Excel export omdat geneste lijsten en geneste objecten niet goed
    geserialiseerd kunnen worden naar Excel.

    Parameters
    ----------
    data : dict[str, Any]
        Dictionary met mogelijk list-waarden of dict instances

    Returns
    -------
    dict[str, Any]
        Dictionary zonder list-waarden en dict instances
    """

    cleaned_data = {key: value for key, value in data.items() if not isinstance(value, (list, dict))}
    return cleaned_data


def get_dfs_from_pdfs(pdf_rapporten: list[Path]) -> dict[str, pd.DataFrame]:
    """Get a list of dataframe tables for a set of duikrapport pdfs"""
    from tekstherkenning_ark.models.rak import Rak

    smartdocs = [SmartDocument.from_pdf(file) for file in pdf_rapporten if not "boor" in file.stem.lower()]
    rakken = [Rak.from_smart_document(doc, use_caching=True) for doc in smartdocs]

    rak_df = pd.concat([rak._get_rak_df() for rak in rakken])
    rakdeel_df = pd.concat([rak._get_rakdeel_df() for rak in rakken])
    houtmonster_df = pd.concat([rak._get_houtmonsters_df() for rak in rakken])
    kespen_df = pd.concat([rak._get_kespen_df() for rak in rakken])
    palen_df = pd.concat([rak._get_palen_df() for rak in rakken])
    gebreken_df = pd.concat([rak._get_gebreken_df() for rak in rakken])

    gebreken_dfs_per_type: dict[str, list[pd.DataFrame]] = {}
    for rak in rakken:
        df_dict = rak._get_gebreken_per_type_dfs()
        for k, v in df_dict.items():
            if not k in gebreken_dfs_per_type:
                gebreken_dfs_per_type[k] = []
            gebreken_dfs_per_type[k].append(v)

    gebreken_df_per_type: dict[str, pd.DataFrame] = {}
    for k, v in gebreken_dfs_per_type.items():
        gebreken_df_per_type[k] = pd.concat(v)

    toestandsbepalingen_df = pd.concat([rak._get_toestandsbepalingen_df() for rak in rakken])
    onverwacht_resultaten_df = pd.concat([rak._get_onverwacht_resultaten_df() for rak in rakken])

    return {
        RAK_TABLE_NAME: rak_df,
        RAKDEEL_TABLE_NAME: rakdeel_df,
        HOUTMONSTER_TABLE_NAME: houtmonster_df,
        PALEN_TABLE_NAME: palen_df,
        KESPEN_TABLE_NAME: kespen_df,
        GEBREKEN_TABLE_NAME: gebreken_df,
        **{f"{GEBREKEN_TABLE_NAME}_{k}": v for k, v in gebreken_df_per_type.items()},
        TOESTANDBEPALINGEN_TABLE_NAME: toestandsbepalingen_df,
        ONVERWACHT_RESULTATEN_TABLE_NAME: onverwacht_resultaten_df,
    }
