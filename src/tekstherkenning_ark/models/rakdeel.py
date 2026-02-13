from __future__ import annotations
from typing import TypeVar

from tekstherkenning_ark import constants, utils
from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.models.metselwerk import Metselwerk
from tekstherkenning_ark.models.onderloopsheidscherm import Onderloopsheidscherm
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat
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
        lengte_m: Lengte van het rakdeel in meters.
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
    lengte_m: float | None = None

    # Te vinden in paragraaf 5.1 of af te leiden uit de constructiebeschrijving.
    bouwjaar: int | None = None

    bovenbouw: Bovenbouw
    onderbouw: Onderbouw

    @property
    def identifier(self) -> str:
        """Return a string that uniquely identifies this Rakdeel instance."""
        return str(self.rakdeel_id)

    def model_post_init(self, __context) -> None:
        """Classificeer toestandsbepaling direct na initialisatie."""
        if self.onderdeel_is_aangetast:
            self.classificeer_toestand_op_model()

    # @property
    # # TODO: Checken met geert of we dit wel willen implementeren, nu kan nog niet.
    # def maximaal_aantal_scheuren_per_10_m(self) -> int | None:
    #     """Aantal scheuren genormaliseerd naar 10 meter lengte."""
    #     if self.lengte_m is None or self.lengte_m == 0:
    #         return None
    #     aantal_scheuren = self.bovenbouw.totaal_aantal_scheuren
    #     return round((aantal_scheuren / self.lengte_m) * 10)

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
            lengte_m=rakdeel_omschrijving.lengte_rakdeel,
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
        if key is None:
            return []
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

        if constructieonderdeel_col is None or aangetast_col is None:
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

    def bepaal_doelmodel_pad(self, onderdeel: str) -> str | None:
        """Bepaal doelmodel-pad op basis van `CONSTRUCTIEONDERDEEL_MAPPING`.

        Retourneert een padstring zoals `onderbouw.vloer` of `bovenbouw`.
        """
        tekst = utils.clean_string(onderdeel).lower()

        for model_pad, patronen in constants.CONSTRUCTIEONDERDEEL_MAPPING.items():
            if not any(patroon in tekst for patroon in patronen):
                continue

            if model_pad == "onderbouw.vloer" and isinstance(self.onderbouw.vloer, Vloer):
                return model_pad
            if model_pad == "onderbouw.onderloopsheidscherm" and isinstance(
                self.onderbouw.onderloopsheidscherm, Onderloopsheidscherm
            ):
                return model_pad
            if model_pad == "onderbouw" and isinstance(self.onderbouw, Onderbouw):
                return model_pad
            if model_pad == "bovenbouw" and isinstance(self.bovenbouw, Bovenbouw):
                return model_pad

        return None

    def classificeer_toestand_op_model(self) -> None:
        """Classificeer toestandstabel op modelniveau.

        Alles zonder match blijft op `rakdeel.toestand_onderdelen`.
        """
        self.toestand_onderdelen = {}

        # Reset toestand op doelmodellen voor een schone herberekening
        for model_pad in constants.CONSTRUCTIEONDERDEEL_MAPPING:
            doelmodel = self.get_model_op_pad(model_pad)
            if doelmodel is not None:
                doelmodel.toestand_onderdelen = {}

        for onderdeel, waarde in self.onderdeel_is_aangetast.items():
            doelmodel_pad = self.bepaal_doelmodel_pad(onderdeel)

            if doelmodel_pad is None:
                self.toestand_onderdelen[onderdeel] = waarde
                continue

            doelmodel = self.get_model_op_pad(doelmodel_pad)
            if doelmodel is not None:
                doelmodel.toestand_onderdelen[onderdeel] = waarde
            else:
                self.toestand_onderdelen[onderdeel] = waarde

    def get_model_op_pad(self, model_pad: str) -> RakBaseModel | None:
        """Haal een model op via een punt-notatie pad vanaf `Rakdeel`.

        Voorbeeld: `onderbouw.vloer`.
        """
        current = self
        for deel in model_pad.split("."):
            current = getattr(current, deel, None)
            if current is None:
                return None

        if isinstance(current, RakBaseModel):
            return current

        return None

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
                if self.bovenbouw.metselwerk is None:
                    self.bovenbouw.metselwerk = Metselwerk()
                self.bovenbouw.metselwerk.gebreken.append(gebrek)
                gebrek_assigned = True

            elif isinstance(gebrek, (GrondVoerendGat, BuikInWand)):
                self.bovenbouw.gebreken.append(gebrek)
                gebrek_assigned = True

            if not gebrek_assigned:
                self.gebreken.append(gebrek)
