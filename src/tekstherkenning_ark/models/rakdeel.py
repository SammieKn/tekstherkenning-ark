from __future__ import annotations
from typing import Type, TypeVar

from pydantic import BaseModel
from azure.ai.documentintelligence.models import DocumentParagraph, DocumentTable

from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.smart_document import RakdeelSectie
from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.gebrek import Gebrek, Scheefstand, Scheur, GrondVoerendGat, BuikInWand
from tekstherkenning_ark.models.onderbouw import Onderbouw
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.smart_document import RakdeelSectie

T = TypeVar("T", Paal, Kesp)


class Rakdeel(BaseModel):
    """Rakdeel.

    Attributes:
        bovenbouw: Object met alle eigenschappen van de bovenbouw van het rakdeel.
        constructietype: Type constructie van het rakdeel (bijvoorbeeld houten paalfundering, betonnen L-wand, etc.).
        gebreken: Lijst van gebreken in het rakdeel.
        lengte_m: Lengte van het rakdeel in meters.
        onderbouw: Object met alle eigenschappen van de onderbouw van het rakdeel.
        rakdeel_id: Unieke identificatie van het rakdeel, bijvoorbeeld 'Constructie A' of 'Constructie B'.
        bouwjaar: Bouwjaar van het rakdeel.
        opmerkingen: Eventuele aanvullende opmerkingen over het rakdeel.
    """

    # Te vinden in paragraaf 5.x, kopregel of inhoudsopgave.
    rakdeel_id: str

    # De constructie omschrijving
    omschrijving: str = ""

    # Te vinden in paragraaf 5.x, eerste zin.
    lengte_m: float | None = None

    # Te vinden in paragraaf 5.1 of af te leiden uit de constructiebeschrijving.
    bouwjaar: int | None = None

    bovenbouw: Bovenbouw
    onderbouw: Onderbouw
    gebreken: list[Gebrek] = []

    @classmethod
    def from_smart_doc_section(
        cls, section: RakdeelSectie, kespen_dict: dict[str, Kesp], palen_dict: dict[str, Paal]
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
        rakdeel_omschrijving = RakdeelOmschrijving.classificeer_omschrijving(omschrijving)

        # Parse gebrekentabel
        gebreken = Rakdeel._parse_gebreken_tabel(tabellen=section.gebreken_tabel)

        # Verkrijg palen en kespen voor dit rakdeel
        palen = cls.get_for_constructie_naam(section.constructie_naam, palen_dict)
        kespen = cls.get_for_constructie_naam(section.constructie_naam, kespen_dict)

        # stap 3 is de eigenschappen van onderbouw en bovenbouw te koppelen
        onderbouw = Onderbouw(
            palen=palen,
            kespen=kespen,
            # onderloopsheidscherm=rakdeel_omschrijving.onderloopsheidscherm, # TODO
            # vloer=rakdeel_omschrijving.materiaal_vloer,
            materiaal=rakdeel_omschrijving.materiaal_onderbouw,
        )
        bovenbouw = Bovenbouw(
            materiaal=rakdeel_omschrijving.materiaal_bovenbouw,
            bovenkant_deksteen_cm_tov_nap=rakdeel_omschrijving.bovenkant_deksteen_cm,
        )

        rakdeel = Rakdeel(
            bovenbouw=bovenbouw,
            gebreken=gebreken,
            lengte_m=rakdeel_omschrijving.lengte_rakdeel,
            onderbouw=onderbouw,
            rakdeel_id=section.constructie_naam,
            bouwjaar=rakdeel_omschrijving.bouwjaar,
            omschrijving=omschrijving,
        )

        return rakdeel

    @staticmethod
    def get_for_constructie_naam(rakdeel_id: str, obj_dict: dict[str, T]) -> list[T]:
        """Haalt een lijst van objecten (Paal of Kesp) op voor dit rakdeel op basis van de constructie naam."""

        rakdeel_id_lower = rakdeel_id.lower()
        key = next((key for key in obj_dict.keys() if key.lower().startswith(rakdeel_id_lower)), "")

        if not key:
            print(f"Waarschuwing: Geen constructienaam gevonden in {T.__name__} voor rakdeel_id {rakdeel_id}")

        return obj_dict.get(key, [])

    @classmethod
    def _parse_gebreken_tabel(cls, tabellen: list[DocumentTable]) -> list[Gebrek]:
        # @TAVMWB: Dit is een helper functie voor een specifieke instantie om diens gebrekentabel te parsen.
        # TODO: implementeer de parsing logica hier
        """Parse de gebrekentabel naar een lijst van Gebrek modellen.

        Args:
            tabel (DocumentTable): De DocumentTable die de gebrekentabel bevat.

        Returns:
            list[Gebrek]: Lijst van gegenereerde Gebrek modellen.
        """
        gebreken: list[Gebrek] = []
        return gebreken
