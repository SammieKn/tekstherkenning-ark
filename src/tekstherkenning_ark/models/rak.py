from __future__ import annotations
from pydantic import BaseModel

from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.smart_document import SmartDocument


class Rak(BaseModel):
    """Rak.

    Attributes:
        rakdelen: Lijst van rakdelen waaruit het rak is opgebouwd.
        raknaam: Naam of code van het rak.
        totale_lengte_m: Totale lengte van het rak in meters.
        opmerkingen: Eventuele aanvullende opmerkingen over het gehele rak.
    """

    # Elk rakdeel heeft een eigen constructietype.
    rakdelen: list[Rakdeel]
    # Te vinden in de rapporttitel, projectgegevens of paragraaf 2.2.1 (paspoortgegevens).
    raknaam: str
    # Te vinden in paragraaf 2.2.1 (paspoortgegevens) en/of de constructiebeschrijving (eerste zin van paragraaf 5.x).
    totale_lengte_m: float
    # Te vinden in de samenvatting, inleiding of slotbeschouwing van het rapport.
    opmerkingen: str = ""

    @classmethod
    def from_smart_document(cls, doc: SmartDocument) -> Rak:
        """Maak een Rak-object en alle bijbehorende subobjecten aan vanuit een SmartDocument."""

        paal_tables = doc.get_meettabel_fundering_paal()
        palen_dict = Paal.from_doc_tables(paal_tables)

        kesp_tables = doc.get_meettabel_fundering_kesp()
        kespen_dict = Kesp.from_doc_tables(kesp_tables)

        houtmonster_tables = doc.get_meettabel_houtmonsters()
        # houtmonsters = Houtmonster.from_doc_tables(houtmonster_tables) # implemented in #24

        rakdeel_sections = doc.get_rakdeel_secties()
        rakdelen = [
            Rakdeel.from_doc_section(
                section,
                palen_dict,
                kespen_dict,
                # houtmonsters, # implemented in #24
            )
            for section in rakdeel_sections
        ]

        raknaam = doc.get_raknaam()
        totale_lengte_m = doc.get_rak_totale_lengte_m()
        opmerkingen = doc.get_rak_opmerkingen()

        return cls(
            rakdelen=rakdelen,
            raknaam=raknaam,
            totale_lengte_m=totale_lengte_m,
            opmerkingen=opmerkingen,
        )
