from __future__ import annotations
from typing import TypeVar
from pydantic import computed_field

from pydantic import computed_field

from tekstherkenning_ark import constants, utils
from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.models.onderloopsheidscherm import Onderloopsheidscherm
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat, OnverwachtResultaatType
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.rak_base_model import RakBaseModel
from tekstherkenning_ark.models.toestand_onderdeel import ToestandOnderdeel
from tekstherkenning_ark.models.vloer import Vloer
from tekstherkenning_ark.document.smart_document import RakdeelSectie
from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.gebrek import (
    BuikInWand,
    Gebrek,
    GrondVoerendGat,
    LokaalVerdwenenMetselwerk,
    OnderloopsheidschermBeschadigd,
    Scheur,
    ScheurHout,
    ScheurMetselwerk,
)
from tekstherkenning_ark.models.onderbouw import Onderbouw
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.utils import get_kesp_id, get_paal_id
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.document.structured_table import StructuredTable

logger = get_logger(__name__)

T = TypeVar("T", Paal, Kesp)


class Rakdeel(RakBaseModel):
    """Rakdeel.

    Attributes:
        rakdeel_id: Unieke identificatie van het rakdeel.
        bovenbouw: Object met alle eigenschappen van de bovenbouw van het rakdeel.
        constructietype: Type constructie van het rakdeel (bijvoorbeeld houten paalfundering, betonnen L-wand, etc.).
        lengte_m_omschrijving: Lengte van het rakdeel in meters uitgelezen uit de omschrijving.
        onderbouw: Object met alle eigenschappen van de onderbouw van het rakdeel.
        rakdeel_id: Unieke identificatie van het rakdeel, bijvoorbeeld 'Constructie A' of 'Constructie B'.
        bouwjaar: Bouwjaar van het rakdeel.
        gebreken: Lijst van gebreken (inherited from RakBaseModel).
        opmerkingen: Eventuele opmerkingen (inherited from RakBaseModel).
    """

    # Te vinden in paragraaf 5.x, kopregel of inhoudsopgave.
    rakdeel_id: str

    # De constructie omschrijving
    omschrijving: str = ""

    # Te vinden in paragraaf 5.x, eerste zin.
    lengte_m_omschrijving: float | None = None

    # Te vinden in paragraaf 5.1 of af te leiden uit de constructiebeschrijving.
    bouwjaar: int | None = None

    bovenbouw: Bovenbouw
    onderbouw: Onderbouw

    @property
    def identifier(self) -> str:
        """Return a string that uniquely identifies this Rakdeel instance."""
        return str(self.rakdeel_id)

    @computed_field
    @property
    def percentage_niet_functionerend_schuifhout(self) -> float | OnverwachtResultaat | None:
        """Percentage van het schuifhout dat niet functioneert,
        afgeleid van de opsluitklossen bij de kespen in de onderbouw."""

        if not self.onderbouw.kespen:
            return None

        if any(
            isinstance(k.is_opsluitklos_aangetast, OnverwachtResultaat)
            or isinstance(k.is_opsluitklos_aanwezig, OnverwachtResultaat)
            for k in self.onderbouw.kespen
        ):
            return OnverwachtResultaat(
                waarde="Onduidelijke staat van opsluitklossen in kesp data, kan percentage niet functionerend schuifhout niet betrouwbaar berekenen",
                onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
            )

        inconsistente_kespen = [
            k for k in self.onderbouw.kespen if k.is_opsluitklos_aangetast and not k.is_opsluitklos_aanwezig
        ]

        if any(inconsistente_kespen):
            kespen_ids = ", ".join(k.kesp_nummer for k in inconsistente_kespen)
            return OnverwachtResultaat(
                waarde=f"Tegenstrijdige data in kespen {kespen_ids}: opsluitklos is aangetast maar ook niet aanwezig. Kan percentage niet functionerend schuifhout niet betrouwbaar berekenen",
                onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
            )

        n_opsluitklos = len([k for k in self.onderbouw.kespen if k.is_opsluitklos_aanwezig])
        n_opsluitklos_aangetast = len([k for k in self.onderbouw.kespen if k.is_opsluitklos_aangetast])

        return (n_opsluitklos - n_opsluitklos_aangetast) / (n_opsluitklos) * 100

    @property
    def maximaal_aantal_scheuren_per_10_m(self) -> int:
        """Aantal scheuren genormaliseerd naar 10 meter lengte."""

        # Verkrijg de scheur-afstanden in de bovenbouw
        scheur_afstanden = sorted(
            [
                s.afstand_van_startrak_m
                for s in self.bovenbouw.scheuren
                if isinstance(s.afstand_van_startrak_m, (int, float))
            ]
        )

        if len(scheur_afstanden) != len(self.bovenbouw.scheuren):
            logger.warning(
                f"{len(self.bovenbouw.scheuren) - len(scheur_afstanden)} / {len(self.bovenbouw.scheuren)} scheuren"
                f" in rakdeel {self.rakdeel_id} hebben geen geldige afstand_van_startrak_m waarde en worden genegeerd "
                f"in de maximaal_aantal_scheuren_per_10_m berekening."
            )

        # Loop over de scheuren, en bepaal het aantal scheuren in elke 10 meter window
        max_scheuren_per_10_m = 0

        for i, scheur_locatie in enumerate(scheur_afstanden):
            n_scheuren = len([s for s in scheur_afstanden if scheur_locatie <= s < scheur_locatie + 10])
            max_scheuren_per_10_m = max(max_scheuren_per_10_m, n_scheuren)

        return max_scheuren_per_10_m

    @computed_field
    @property
    def lengte_m(self) -> float | None | OnverwachtResultaat:
        """Lengte van het rakdeel in meters.

        Als lengte_m_omschrijving beschikbaar is, wordt deze gebruikt, anders wordt de lengte afgeleid a.d.h.v. de paalafstanden in de onderbouw.
        """

        return self.lengte_m_omschrijving or self.lengte_m_afgeleid

    @property
    def lengte_m_afgeleid(self) -> float | None | OnverwachtResultaat:
        """Lengte van het rakdeel in meters afgeleid a.d.h.v. de paalafstanden in de onderbouw.

        Returns
        -------
        float | None | OnverwachtResultaat
        - float: de opgetelde hoh_afstanden van de palen in de eerste rij van de onderbouw, omgerekend naar meters
        - None: als er geen palen in de onderbouw zijn
        - OnverwachtResultaat: als de paal data fouten bevat, bijvoorbeeld:
            - Ontbrekende hoh_afstand_cm voor een paal
            - Cyclische paalreferenties via hoh_paalnummer
            - Ontbrekende paalreferenties (bijvoorbeeld een ontbrekende P1.13 in een reeks van P1.1 t/m P1.20)
        """

        # Get consecutive palen in the first row
        consecutive_palen = self.onderbouw.get_consecutive_palen()

        if consecutive_palen == []:
            return None
        if not consecutive_palen:
            return consecutive_palen

        # Calculate total distance between palen
        total_length_cm = sum(paal.hoh_afstand_cm for paal in consecutive_palen)

        # Convert to meters
        total_length_m = total_length_cm / 100.0

        return total_length_m

    @computed_field
    @property
    def aantal_scheuren_per_meter(self) -> float | None:
        """Scheur-dichtheid per meter."""
        if not self.lengte_m:
            return None

        aantal_scheuren = self.bovenbouw.totaal_aantal_scheuren
        return round(aantal_scheuren / self.lengte_m, 2)

    def model_post_init(self, __context) -> None:
        """Classificeer toestandsbepaling direct na initialisatie."""
        if self.toestand_onderdelen:
            self.assign_toestandsbepalingen_to_children()

    @classmethod
    async def from_smart_doc_section(
        cls, section: RakdeelSectie, kespen_dict: dict[str, list[Kesp]], palen_dict: dict[str, list[Paal]]
    ) -> Rakdeel:
        """Genereer een lijst van Rakdeel modellen vanuit een lijst van RakdeelSectie modellen.

        Args:
            sections (list[RakdeelSectie]): Lijst van RakdeelSectie modellen.

        Returns:
            list[Rakdeel]: Lijst van gegenereerde Rakdeel modellen.
        """

        # Parse constructieomschrijving met LLM
        # dit is van belang voor paragrafen die aangemaakt worden vanuit de tekeningen (symbolen).
        omschrijving = ""
        for paragraaf in section.beschrijving:
            if len(paragraaf.content.strip()) > 20:
                omschrijving += paragraaf.content + "\n"
        rakdeel_omschrijving = await RakdeelOmschrijving.classificeer_omschrijving(omschrijving)

        toestand_onderdelen = ToestandOnderdeel.from_toestandbepaling_table(section.toestand_tabel)

        # Parse gebrekentabel
        gebreken = await Gebrek.from_doc_tables(section.gebreken_tabel)
        overige_gebreken = cls.assign_gebreken_to_palen_kespen(gebreken, palen_dict, kespen_dict)

        # Verkrijg palen en kespen voor dit rakdeel
        palen = cls.get_for_constructie_naam(section.constructie_naam, palen_dict)
        kespen = cls.get_for_constructie_naam(section.constructie_naam, kespen_dict)

        # stap 3 is de eigenschappen van onderbouw en bovenbouw te koppelen
        onderbouw = Onderbouw(
            palen=palen,
            kespen=kespen,
            onderloopsheidscherm=Onderloopsheidscherm.from_rakdeel_omschrijving(rakdeel_omschrijving),
            vloer=Vloer.from_rakdeel_omschrijving(rakdeel_omschrijving),
            materiaal=rakdeel_omschrijving.materiaal_onderbouw,
            materiaal_fundering=rakdeel_omschrijving.materiaal_fundering,
        )
        bovenbouw = Bovenbouw(
            materiaal=rakdeel_omschrijving.materiaal_bovenbouw,
            bovenkant_deksteen_cm_tov_nap=rakdeel_omschrijving.bovenkant_deksteen_cm,
        )

        rakdeel = Rakdeel(
            bovenbouw=bovenbouw,
            lengte_m_omschrijving=rakdeel_omschrijving.lengte_rakdeel,
            onderbouw=onderbouw,
            rakdeel_id=section.constructie_naam,
            bouwjaar=rakdeel_omschrijving.bouwjaar,
            omschrijving=omschrijving,
            toestand_onderdelen=toestand_onderdelen,
        )

        # Add gebreken to rakdeel and subcomponents
        rakdeel.assign_overige_gebreken_to_children(overige_gebreken)

        return rakdeel

    @staticmethod
    def assign_gebreken_to_palen_kespen(
        gebreken: list[Gebrek], palen_dict: dict[str, list[Paal]], kespen_dict: dict[str, list[Kesp]]
    ) -> list[Gebrek]:
        """Probeer gebreken toe te wijzen aan palen of kespen op basis van codering. Als dit niet lukt, worden ze teruggegeven als 'overige gebreken'."""
        overige_gebreken = []

        for gebrek in gebreken:

            kesp = None
            paal = None

            # Probeer eerst aan kespen toe te wijzen
            kesp_id = get_kesp_id(gebrek.codering)
            if kesp_id:
                for kesp_list in kespen_dict.values():
                    kesp = next((k for k in kesp_list if k.kesp_nummer == kesp_id), None)
                    if kesp:
                        kesp.gebreken.append(gebrek)
                        break
                if not kesp:
                    logger.warning(
                        f"Gevonden kesp ID '{kesp_id}' in gebrek codering zonder overeenkomende kesp in rakdeel."
                    )

            # Probeer dan aan palen toe te wijzen
            if not kesp:
                paal_id = get_paal_id(gebrek.codering)
                if paal_id:
                    for paal_list in palen_dict.values():
                        paal = next((p for p in paal_list if p.paal_nummer == paal_id), None)
                        if paal:
                            paal.gebreken.append(gebrek)
                            break
                    if not paal:
                        logger.warning(
                            f"Gevonden paal ID '{paal_id}' in gebrek codering zonder overeenkomende paal in rakdeel."
                        )

            # Als het gebrek niet is toegewezen, voeg het toe aan de overige gebreken
            if paal is None and kesp is None:
                overige_gebreken.append(gebrek)

        return overige_gebreken

    @staticmethod
    def get_for_constructie_naam(rakdeel_id: str, obj_dict: dict[str, list[T]]) -> list[T]:
        """Haalt een lijst van objecten (Paal of Kesp) op voor dit rakdeel op basis van de constructie naam."""

        rakdeel_id_lower = rakdeel_id.lower()
        key = next((key for key in obj_dict.keys() if key.lower().startswith(rakdeel_id_lower)), None)

        return obj_dict.get(key, [])

    def assign_toestandsbepalingen_to_children(self):
        """Classificeer toestandstabel en verdeel onder de onderdelen van het rakdeel
        (vloer, onderbouw, bovenbouw, onderloopsheidscherm). Toestandbepalingen die niet
        geclassificeerd kunnen worden worden aan het rakdeel zelf toegevoegd."""

        rakdeel_toestand_onderdelen = []

        # TODO @Sammie wat doen we hier als een toestandonderdeel wel matcht op bijv. vloer,
        # maar er geen vloer object is binnen dit rakdeel? Vloer aanmaken of negeren? - Matthias

        # Assign toestandsbepalingen to children based on CONSTRUCTIEONDERDEEL_MAPPING
        for toestand_onderdeel in self.toestand_onderdelen:
            if toestand_onderdeel.is_vloer():
                if not self.onderbouw.vloer:
                    self.onderbouw.vloer = Vloer(materiaal=NietBeschikbaar.LEEG)
                    self.onderbouw.vloer.toestand_onderdelen.append(toestand_onderdeel)
                else:
                    self.onderbouw.vloer.toestand_onderdelen.append(toestand_onderdeel)
            elif self.onderbouw and toestand_onderdeel.is_onderbouw():
                self.onderbouw.toestand_onderdelen.append(toestand_onderdeel)

            elif self.bovenbouw and toestand_onderdeel.is_bovenbouw():
                self.bovenbouw.toestand_onderdelen.append(toestand_onderdeel)

            elif self.onderbouw.onderloopsheidscherm and toestand_onderdeel.is_onderloopsheidscherm():
                self.onderbouw.onderloopsheidscherm.toestand_onderdelen.append(toestand_onderdeel)

            else:
                rakdeel_toestand_onderdelen.append(toestand_onderdeel)

        # Assign toestandsbepalingen that could not be classified to the rakdeel itself
        self.toestand_onderdelen = rakdeel_toestand_onderdelen

    def assign_overige_gebreken_to_children(self, gebreken: list[Gebrek]) -> None:
        """Voeg gebreken toe aan het model. Indien mogelijk worden gebreken
        verdeeld over onderliggende componenten (kespen, palen, etc). Algemene
        gebreken worden opgeslagen in het Rakdeel model zelf.

        Parameters
        ----------
        gebreken : list[Gebrek]
            Lijst van gebreken onttrokken uit de gebreken tabel in het duikrapport.
        """

        for gebrek in gebreken:
            gebrek_assigned = False

            # Match gebreken to onderdeel
            if isinstance(gebrek, (Scheur, ScheurMetselwerk, LokaalVerdwenenMetselwerk)):
                self.bovenbouw.gebreken.append(gebrek)
                gebrek_assigned = True

            elif isinstance(gebrek, (GrondVoerendGat, BuikInWand)):
                self.bovenbouw.gebreken.append(gebrek)
                gebrek_assigned = True

            elif isinstance(gebrek, OnderloopsheidschermBeschadigd):
                if self.onderbouw.onderloopsheidscherm:
                    self.onderbouw.onderloopsheidscherm.gebreken.append(gebrek)
                    gebrek_assigned = True

            if not gebrek_assigned:
                self.gebreken.append(gebrek)
