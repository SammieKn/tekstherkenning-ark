from pathlib import Path

import pandas as pd

from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.models.rak import Rak

RAKDEEL_TABLE_NAME = "rakdelen"
HOUTMONSTER_TABLE_NAME = "houtmonsters"
PALEN_TABLE_NAME = "palen"
KESPEN_TABLE_NAME = "kespen"
GEBREKEN_TABLE_NAME = "gebreken"
TOESTANDBEPALINGEN_TABLE_NAME = "toestandsbepalingen"
ONVERWACHT_RESULTATEN_TABLE_NAME = "onverwachte_resultaten"


def get_dfs_from_pdfs(pdf_rapporten: list[Path]) -> dict[str, pd.DataFrame]:
    """Get a list of dataframe tables for a set of duikrapport pdfs"""

    smartdocs = [SmartDocument.from_pdf(file) for file in pdf_rapporten if not "boor" in file.stem.lower()]
    rakken = [Rak.from_smart_document(doc, use_caching=True) for doc in smartdocs]

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
            gebreken_dfs_per_type[k].extend(v)

    gebreken_df_per_type: dict[str, pd.DataFrame] = {}
    for k, v in gebreken_dfs_per_type.items():
        gebreken_df_per_type[k] = pd.concat(gebreken_dfs_per_type[k])

    toestandsbepalingen_df = pd.concat([rak._get_toestandsbepalingen_df() for rak in rakken])
    onverwacht_resultaten_df = pd.concat([rak._get_onverwacht_resultaten_df() for rak in rakken])

    return {
        RAKDEEL_TABLE_NAME: rakdeel_df,
        HOUTMONSTER_TABLE_NAME: houtmonster_df,
        PALEN_TABLE_NAME: palen_df,
        KESPEN_TABLE_NAME: kespen_df,
        GEBREKEN_TABLE_NAME: gebreken_df,
        **{f"{GEBREKEN_TABLE_NAME}_{k}": v for k, v in gebreken_df_per_type.items()},
        TOESTANDBEPALINGEN_TABLE_NAME: toestandsbepalingen_df,
        ONVERWACHT_RESULTATEN_TABLE_NAME: onverwacht_resultaten_df,
    }
