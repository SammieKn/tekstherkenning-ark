from __future__ import annotations

import pandas as pd

from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.models.rak_base_model import RakBaseModel


class Boorweerstandsmeting(RakBaseModel):
    """Measurement from a bore-resistance test.

    Attributes
    ----------
    rakdeel_id : str
        Rakdeel that contains the measured pile.
    codering : str
        Unique measurement code from the source report.
    rak_code : str
        Code of the Rak.
    paal_nummer : str
        Pile number associated with the measurement.
    bma_nummer : str
        Measurement apparatus number, which may contain multiple numbers.
    diameter_paal_mm : int | NietBeschikbaar
        Pile diameter in millimeters.
    hoogte_onder_nap_cm : int | NietBeschikbaar
        Measurement height below NAP in centimeters.
    hoogte_tov_onderzijde_fundering_cm : int | NietBeschikbaar
        Measurement height relative to the bottom of the foundation in centimeters.
    datum_meting : str
        Date of the measurement.
    resultaat_tekst : str
        Textual measurement result.
    pagina : int | NietBeschikbaar
        Page number in the source report.
    bron : str
        Source reference.
    bron_rij : str
        Original source row text.
    """

    rakdeel_id: str
    codering: str
    rak_code: str
    paal_nummer: str
    bma_nummer: str
    diameter_paal_mm: int | NietBeschikbaar
    hoogte_onder_nap_cm: int | NietBeschikbaar
    hoogte_tov_onderzijde_fundering_cm: int | NietBeschikbaar
    datum_meting: str
    resultaat_tekst: str
    pagina: int | NietBeschikbaar
    bron: str
    bron_rij: str

    @classmethod
    def from_nomic_df(cls, frame: pd.DataFrame) -> list[Boorweerstandsmeting]:
        """Parse boorweerstandsmetingen from their Nomic dataframe.

        Parameters
        ----------
        frame : pandas.DataFrame
            Rows from ``boorweerstandsmetingen.csv``.

        Returns
        -------
        list[Boorweerstandsmeting]
            Measurements in source row order.
        """
        if frame.empty and len(frame.columns) == 0:
            return []

        fields = (
            "rakdeel_id",
            "codering",
            "rak_code",
            "paal_nummer",
            "bma_nummer",
            "diameter_paal_mm",
            "hoogte_onder_nap_cm",
            "hoogte_tov_onderzijde_fundering_cm",
            "datum_meting",
            "resultaat_tekst",
            "pagina",
            "bron",
            "bron_rij",
        )
        cls._require_nomic_columns(frame, fields)
        measurements = cls._models_from_nomic_df(frame, fields)
        for measurement in measurements:
            if not measurement.rakdeel_id.strip():
                raise ValueError("A Nomic boorweerstandsmeting row has no rakdeel_id")
        return measurements

    @property
    def identifier(self) -> str:
        """Return the Nomic measurement code as identifier."""
        return self.codering
