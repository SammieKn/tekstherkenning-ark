from __future__ import annotations
from typing import TypeVar

from tekstherkenning_ark import utils
from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.models.onderloopsheidscherm import Onderloopsheidscherm
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat, OnverwachtResultaatType
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.rak_base_model import RakBaseModel
from tekstherkenning_ark.models.vloer import Vloer
from tekstherkenning_ark.document.smart_document import RakdeelSectie
from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.gebrek import (
    BuikInWand,
    Gebrek,
    GrondVoerendGat,
    LokaalVerdwenenMetselwerk,
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
    onderdeel_is_aangetast: dict[str, bool | NietBeschikbaar | OnverwachtResultaat] = {}

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

    # @property
    # # TODO: Checken met geert of we dit wel willen implementeren, nu kan nog niet.
    # def maximaal_aantal_scheuren_per_10_m(self) -> int | None:
    #     """Aantal scheuren genormaliseerd naar 10 meter lengte."""
    #     if self.lengte_m is None or self.lengte_m == 0:
    #         return None
    #     aantal_scheuren = self.bovenbouw.totaal_aantal_scheuren
    #     return round((aantal_scheuren / self.lengte_m) * 10)

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

        # Leid lengte af uit hoh-aftanden tussen onderliggende palen
        eerste_rij_palen = self.onderbouw.eerste_rij_palen

        if not eerste_rij_palen:
            return None

        processed_paal_nummers: set[str] = set()
        current_paal = eerste_rij_palen[0]
        total_length_cm = 0.0

        while current_paal:

            # Check for cyclical references to prevent infinite loops
            if current_paal.paal_nummer in processed_paal_nummers:
                return OnverwachtResultaat(
                    waarde=None,
                    onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
                    details=f"Cyclische paalreferenties gedetecteerd bij Rakdeel {self.rakdeel_id}",
                )

            # Check if hoh_afstand_cm is available for the current paal
            if isinstance(current_paal.hoh_afstand_cm, NietBeschikbaar) or current_paal.hoh_afstand_cm is None:
                return OnverwachtResultaat(
                    waarde=None,
                    onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
                    details=f"Ontbrekende hoh_afstand_cm voor paal {current_paal.paal_nummer} in Rakdeel {self.rakdeel_id}",
                )

            # Actually add the length of the current paal to the total length
            total_length_cm += current_paal.hoh_afstand_cm
            processed_paal_nummers.add(current_paal.paal_nummer)

            # Determine the next paal in the sequence based on hoh_paalnummer.
            palen_that_refer_to_current_paal = [
                p for p in eerste_rij_palen if p.hoh_paalnummer == current_paal.paal_nummer
            ]

            # Check if there are multiple palen that refer to the same hoh_paalnummer, which would indicate a data issue
            if len(palen_that_refer_to_current_paal) > 1:
                return OnverwachtResultaat(
                    waarde=None,
                    onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
                    details=f"Meerdere palen verwijzen naar hetzelfde hoh_paalnummer {current_paal.paal_nummer} in Rakdeel {self.rakdeel_id}",
                )

            if len(palen_that_refer_to_current_paal) == 1:
                current_paal = palen_that_refer_to_current_paal[0]
            else:
                # No next paal
                current_paal = None

        # Validate that we have processed the expected number of palen based on the first row palen in onderbouw
        if not len(processed_paal_nummers) == len(eerste_rij_palen):
            return OnverwachtResultaat(
                waarde=None,
                onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
                details=f"Onvolledige verwerking van palen bij Rakdeel {self.rakdeel_id}: {len(processed_paal_nummers)} van {len(eerste_rij_palen)} palen verwerkt. Dit kan duiden op onvolledige data of een gebroken reeks.",
            )

        total_length_m = total_length_cm / 100.0
        return total_length_m

    @property
    def aantal_scheuren_per_meter(self) -> float | None:
        """Scheur-dichtheid per meter."""
        if not self.lengte_m:
            return None

        aantal_scheuren = self.bovenbouw.totaal_aantal_scheuren
        return round(aantal_scheuren / self.lengte_m, 2)

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

        onderdeel_is_aangetast = cls.from_toestandbepaling_table(section.toestand_tabel)

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
            onderdeel_is_aangetast=onderdeel_is_aangetast,
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

    @staticmethod
    def from_toestandbepaling_table(
        structured_table: StructuredTable | None,
    ) -> dict[str, bool | NietBeschikbaar | OnverwachtResultaat]:
        """Parse toestandsbepaling table from structured table.

        Parameters
        ----------
        structured_table : StructuredTable | None
            Structured table containing toestandsbepaling data.

        Returns
        -------
        dict[str, bool | NietBeschikbaar | OnverwachtResultaat]
            Dictionary mapping construction components to their condition status.
        """
        dict_toestandsbepaling: dict[str, bool | NietBeschikbaar | OnverwachtResultaat] = {}

        if structured_table is None:
            logger.warning("Geen toestandsbepaling tabel gevonden")
            return dict_toestandsbepaling

        # Get columns
        constructieonderdeel_col = structured_table.get_column(header_in="Constructieonderdeel")
        aangetast_col = structured_table.get_column(header_in="Aangetast")

        if not constructieonderdeel_col and not aangetast_col:
            logger.error("Could not find required columns in toestandsbepaling table")
            return dict_toestandsbepaling

        num_rows = len(constructieonderdeel_col.values)

        for row_idx in range(num_rows):
            constructieonderdeel = utils.clean_string(constructieonderdeel_col.values[row_idx])
            aangetast = utils.clean_string(aangetast_col.values[row_idx])

            if constructieonderdeel:  # Skip empty rows
                aangetast_clean = utils.parse_ja_nee(aangetast)
                if isinstance(aangetast_clean, (bool, NietBeschikbaar, OnverwachtResultaat)):
                    dict_toestandsbepaling[constructieonderdeel] = aangetast_clean
                else:
                    logger.warning(
                        f"Onverwacht resultaat '{aangetast_clean}' voor '{constructieonderdeel}', wordt overgeslagen."
                    )

        return dict_toestandsbepaling

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
            if isinstance(gebrek, (ScheurMetselwerk, LokaalVerdwenenMetselwerk)):
                self.bovenbouw.gebreken.append(gebrek)
                gebrek_assigned = True

            elif isinstance(gebrek, (GrondVoerendGat, BuikInWand)):
                self.bovenbouw.gebreken.append(gebrek)
                gebrek_assigned = True

            if not gebrek_assigned:
                self.gebreken.append(gebrek)
