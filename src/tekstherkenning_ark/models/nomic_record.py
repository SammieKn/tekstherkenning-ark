from __future__ import annotations

import pandas as pd
from pydantic import BaseModel, ConfigDict


class NomicRecord(BaseModel):
    """A row from an auxiliary Nomic CSV.

    Notes
    -----
    The model allows extra fields to preserve the table's source columns.
    """

    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_nomic_df(cls, frame: pd.DataFrame) -> list[NomicRecord]:
        """Create records while preserving every source column.

        Parameters
        ----------
        frame : pandas.DataFrame
            Rows from an auxiliary Nomic CSV.

        Returns
        -------
        list[NomicRecord]
            Records in source row order.
        """
        return [cls(**row) for row in frame.to_dict(orient="records")]
