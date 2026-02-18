"""Mock Rak object met OnverwachtResultaat op verschillende niveaus."""

from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.onderbouw import Onderbouw
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.models.vloer import Vloer


def create_mock_rak_with_onverwachte_resultaten() -> Rak:
    """Maak een mock Rak object met OnverwachtResultaat op verschillende niveaus.

    Returns
    -------
    Rak
        Mock Rak object met onverwachte resultaten in verschillende velden.
    """
    return Rak(
        raknaam="Test Rak",
        totale_lengte_m=50.0,
        rakdelen=[
            Rakdeel(
                rakdeel_id="Constructie A",
                omschrijving="Houten paalfundering",
                lengte_m_omschrijving=50.0,
                bovenbouw=Bovenbouw(
                    bovenkant_deksteen_cm_tov_nap="niet gemeten",
                ),
                onderbouw=Onderbouw(
                    palen=[
                        Paal(
                            paal_nummer="P1.1",
                            schoor_graden="onleesbaar",
                            diameter_haaks=150,
                            diameter_parallel=150,
                            diameter_gemiddeld=150,
                            hoh_afstand_cm=100,
                            hoh_paalnummer="P1.2",
                            schoor_richting="PNV",
                            afstand_frontwand_cm=25,
                            is_scheefstand=False,
                            is_paalbreuk=False,
                            is_aantasting=False,
                            aansluiting_status="G",
                            positionering_aansluiting_cm="0",
                        ),
                    ],
                    kespen=[
                        Kesp(
                            kesp_nummer="K1",
                            hoogte_cm=20,
                            breedte_cm=15,
                            hoek_tov_lengte_as_graden="N/A",
                            lengte_uitstekend_deel_cm=10,
                            is_opsluitklos_aangetast=False,
                        ),
                    ],
                    vloer=Vloer(
                        materiaal="onbekend materiaal",
                        bovenkant_vloer_cm_tov_nap=-120.5,
                    ),
                ),
            ),
        ],
    )
