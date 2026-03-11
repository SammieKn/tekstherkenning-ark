"""Mock Rak object met gebreken op verschillende niveaus."""

from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.onderbouw import Onderbouw
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.models.vloer import Vloer
from tekstherkenning_ark.models.gebrek import Gebrek


def create_mock_rak_with_gebreken() -> Rak:
    """Maak een mock Rak object met gebreken op verschillende niveaus.

    Returns
    -------
    Rak
        Mock Rak object met gebreken in bovenbouw, paal, kesp en rakdeel.
    """
    return Rak(
        raknaam="Test Rak",
        totale_lengte_m=50.0,
        rakdelen=[
            Rakdeel(
                rakdeel_id="Constructie A",
                omschrijving="Houten paalfundering",
                lengte_m_omschrijving=4.0,
                bovenbouw=Bovenbouw(
                    gebreken=[
                        Gebrek(
                            codering="GM1",
                            omschrijving="Scheur in metselwerk",
                            figuurnummer="F1",
                        ),
                    ],
                ),
                onderbouw=Onderbouw(
                    palen=[
                        Paal(
                            paal_nummer="P1.1",
                            diameter_haaks=150,
                            diameter_parallel=150,
                            diameter_gemiddeld=150,
                            hoh_afstand_cm=100,
                            hoh_paalnummer="",
                            schoor_graden=5,
                            schoor_richting="PNV",
                            afstand_frontwand_cm=25,
                            is_scheefstand=False,
                            is_paalbreuk=False,
                            is_aantasting=False,
                            aansluiting_status="G",
                            positionering_aansluiting_cm="0",
                            is_onderzocht=True,
                            gebreken=[
                                Gebrek(
                                    codering="GP1",
                                    omschrijving="Aantasting paal",
                                    figuurnummer="F2",
                                ),
                            ],
                        ),
                        Paal(
                            paal_nummer="P1.2",
                            diameter_haaks=150,
                            diameter_parallel=150,
                            diameter_gemiddeld=150,
                            hoh_afstand_cm=120,
                            hoh_paalnummer="P1.1",
                            schoor_graden=5,
                            schoor_richting="PNV",
                            afstand_frontwand_cm=25,
                            is_scheefstand=False,
                            is_paalbreuk=False,
                            is_aantasting=False,
                            aansluiting_status="G",
                            positionering_aansluiting_cm="0",
                            is_onderzocht=False,
                        ),
                        Paal(
                            paal_nummer="P2.2",
                            diameter_haaks=150,
                            diameter_parallel=150,
                            diameter_gemiddeld=150,
                            hoh_afstand_cm=200,
                            hoh_paalnummer="P1.2",
                            schoor_graden=5,
                            schoor_richting="PNV",
                            afstand_frontwand_cm=25,
                            is_scheefstand=False,
                            is_paalbreuk=False,
                            is_aantasting=False,
                            aansluiting_status="G",
                            positionering_aansluiting_cm="0",
                            is_onderzocht=True,
                        ),
                        Paal(
                            paal_nummer="P1.3",
                            diameter_haaks=150,
                            diameter_parallel=150,
                            diameter_gemiddeld=150,
                            hoh_afstand_cm=200,
                            hoh_paalnummer="P1.2",
                            schoor_graden=5,
                            schoor_richting="PNV",
                            afstand_frontwand_cm=25,
                            is_scheefstand=False,
                            is_paalbreuk=False,
                            is_aantasting=False,
                            aansluiting_status="G",
                            positionering_aansluiting_cm="0",
                            is_onderzocht=True,
                        ),
                    ],
                    kespen=[
                        Kesp(
                            kesp_nummer="K1",
                            hoogte_cm=20,
                            breedte_cm=15,
                            lengte_uitstekend_deel_cm=10,
                            is_opsluitklos_aangetast=False,
                            is_aangetast=False,
                        ),
                        Kesp(
                            kesp_nummer="K2",
                            hoogte_cm=20,
                            breedte_cm=15,
                            lengte_uitstekend_deel_cm=10,
                            is_opsluitklos_aangetast=False,
                            is_aangetast=True,
                        ),
                        Kesp(
                            kesp_nummer="K3",
                            hoogte_cm=20,
                            breedte_cm=15,
                            lengte_uitstekend_deel_cm=10,
                            is_opsluitklos_aangetast=False,
                            is_aangetast=True,
                        ),
                        Kesp(
                            kesp_nummer="K4",
                            hoogte_cm=20,
                            breedte_cm=15,
                            lengte_uitstekend_deel_cm=10,
                            is_opsluitklos_aangetast=False,
                            is_aangetast=True,
                        ),
                        Kesp(
                            kesp_nummer="K5",
                            hoogte_cm=20,
                            breedte_cm=15,
                            lengte_uitstekend_deel_cm=10,
                            is_opsluitklos_aangetast=False,
                            is_aangetast=True,
                        ),
                        Kesp(
                            kesp_nummer="K6",
                            hoogte_cm=20,
                            breedte_cm=15,
                            lengte_uitstekend_deel_cm=10,
                            is_opsluitklos_aangetast=False,
                            is_aangetast=True,
                            gebreken=[
                                Gebrek(
                                    codering="GK1",
                                    omschrijving="Vervorming kesp",
                                    figuurnummer="F3",
                                ),
                            ],
                        ),
                        Kesp(
                            kesp_nummer="K7",
                            hoogte_cm=20,
                            breedte_cm=15,
                            lengte_uitstekend_deel_cm=10,
                            is_opsluitklos_aangetast=False,
                            is_aangetast=False,
                        ),
                    ],
                    vloer=Vloer(
                        materiaal="Hout",
                        bovenkant_vloer_cm_tov_nap=-120.5,
                    ),
                ),
                gebreken=[
                    Gebrek(
                        codering="GR1",
                        omschrijving="Algemeen gebrek rakdeel",
                        figuurnummer="NVT",
                    ),
                ],
            ),
        ],
    )
