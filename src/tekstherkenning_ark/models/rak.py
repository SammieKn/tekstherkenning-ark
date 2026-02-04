from __future__ import annotations
import asyncio
import pickle

from tekstherkenning_ark import constants
from tekstherkenning_ark.constants import DATA_DIR
from tekstherkenning_ark.models.houtmonster import Houtmonster
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.rak_base_model import RakBaseModel
from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.smart_document import SmartDocument
from tekstherkenning_ark.logger import get_logger

logger = get_logger(__name__)


class Rak(RakBaseModel):
    """Rak.

    Attributes:
        rakdelen: Lijst van rakdelen waaruit het rak is opgebouwd.
        raknaam: Naam of code van het rak.
        totale_lengte_m: Totale lengte van het rak in meters.
        opmerkingen: Eventuele opmerkingen (inherited from RakBaseModel).
    """

    # Elk rakdeel heeft een eigen constructietype.
    rakdelen: list[Rakdeel]
    # Te vinden in de rapporttitel, projectgegevens of paragraaf 2.2.1 (paspoortgegevens).
    raknaam: str
    # Te vinden in paragraaf 2.2.1 (paspoortgegevens) en/of de constructiebeschrijving (eerste zin van paragraaf 5.x).
    totale_lengte_m: float

    @classmethod
    def from_smart_document(cls, doc: SmartDocument, use_caching: bool = True) -> Rak:
        """Maak een Rak-object en alle bijbehorende subobjecten aan vanuit een SmartDocument."""

        cache_file = constants.CACHE_DIR / f"rak_{doc.pdf_path.stem}.pkl"
        if cache_file.exists() and use_caching:
            logger.info(f"Loading cached Rak from {cache_file}")
            rak_instance = pickle.loads(cache_file.read_bytes())
            return rak_instance

        # Laad palen, kespen en houtmonsters uit tabellen
        paal_tables = doc.get_meettabel_fundering_paal()
        palen_dict = Paal.from_doc_tables(paal_tables)

        kesp_tables = doc.get_meettabel_fundering_kesp()
        kespen_dict = Kesp.from_doc_tables(kesp_tables)

        houtmonster_tables = doc.get_meettabel_houtmonsters()
        houtmonsters = Houtmonster.from_doc_tables(houtmonster_tables)

        # Plaats houtmonsters onder juiste palen
        processed_houtmonsters: set[Houtmonster] = set()
        for _, palen in palen_dict.items():
            for paal in palen:
                paal.houtmonsters = [
                    hm
                    for hm in houtmonsters
                    if paal.paal_nummer == hm.paal_nummer or paal.paal_nummer == hm.codering.split("/")[2]
                ]
                if paal.houtmonsters:
                    processed_houtmonsters.update(set(paal.houtmonsters))

        # Validate that all houtmonsters have been assigned to a paal
        unprocessed_houtmonsters = set(houtmonsters) - processed_houtmonsters
        if unprocessed_houtmonsters:
            raise ValueError(
                f"The following houtmonsters could not be assigned to a paal: {[hm.codering for hm in unprocessed_houtmonsters]}\n for paal_nummers {[[paal.paal_nummer for paal in palen] for palen in palen_dict.values()]}"
            )

        # Maak rakdelen aan (parallel via async)
        rakdeel_sections = doc.get_rakdeel_secties()

        async def maak_rakdelen_async():
            rakdeel_taken = [
                Rakdeel.from_smart_doc_section(
                    section=section,
                    palen_dict=palen_dict,
                    kespen_dict=kespen_dict,
                )
                for section in rakdeel_sections
            ]
            return await asyncio.gather(*rakdeel_taken)

        rakdelen = asyncio.run(maak_rakdelen_async())

        # raknaam = doc.get_raknaam()
        # totale_lengte_m = doc.get_rak_totale_lengte_m()
        # opmerkingen = doc.get_rak_opmerkingen()

        rak_instance = cls(
            rakdelen=list(rakdelen),
            raknaam="",  # TODO
            totale_lengte_m=0.0,  # TODO
            opmerkingen="",
        )

        cache_file.write_bytes(pickle.dumps(rak_instance))

        return rak_instance


if __name__ == "__main__":

    doc = SmartDocument.from_pdf(constants.TEST_PDF_PATH)

    rak = Rak.from_smart_document(doc)

    for rd in rak.rakdelen:
        print(rd.rakdeel_id)
        for p in [p for p in rd.onderbouw.palen if p.gebreken]:
            print(f"  Paal: {p.paal_nummer}")
            for gebrek in p.gebreken:
                print(f"    Gebrek: {gebrek.codering}")

        for kesp in [k for k in rd.onderbouw.kespen if k.gebreken]:
            print(f"  Kesp: {kesp.kesp_nummer}")
            for gebrek in kesp.gebreken:
                print(f"    Gebrek: {gebrek.codering}")

        if rd.bovenbouw.metselwerk and rd.bovenbouw.metselwerk.gebreken:
            print(f"  Metselwerk gebreken:")
            for gebrek in rd.bovenbouw.metselwerk.gebreken:
                print(f"    Gebrek: {gebrek.codering}")

        for gebrek in rd.gebreken:
            print(f"  Rakdeel gebrek: {gebrek.codering}")
