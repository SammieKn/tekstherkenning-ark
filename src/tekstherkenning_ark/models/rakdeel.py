from __future__ import annotations
from typing import Type, TypeVar

from pydantic import BaseModel
from azure.ai.documentintelligence.models import DocumentParagraph, DocumentTable

from tekstherkenning_ark.models.metselwerk import Metselwerk
from tekstherkenning_ark.models.onderloopsheidscherm import Onderloopsheidscherm
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.vloer import Vloer
from tekstherkenning_ark.smart_document import RakdeelSectie
from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.gebrek import Gebrek, ScheurHout, ScheurMetselwerk
from tekstherkenning_ark.models.onderbouw import Onderbouw
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.smart_document import RakdeelSectie
from tekstherkenning_ark.utils import contains_kesp_id, get_kesp_id, get_paal_id

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

        # Parse gebrekentabel
        gebreken = await Gebrek.from_doc_tables(tables=section.gebreken_tabel)

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
        )

        # Add gebreken to rakdeel and subcomponents
        rakdeel.add_gebreken(gebreken)

        return rakdeel

    @staticmethod
    def get_for_constructie_naam(rakdeel_id: str, obj_dict: dict[str, list[T]]) -> list[T]:
        """Haalt een lijst van objecten (Paal of Kesp) op voor dit rakdeel op basis van de constructie naam."""

        rakdeel_id_lower = rakdeel_id.lower()
        key = next((key for key in obj_dict.keys() if key.lower().startswith(rakdeel_id_lower)), "")

        return obj_dict.get(key, [])

    def add_gebreken(self, gebreken: list[Gebrek]) -> None:
        """Voeg gebreken toe aan het model. Indien mogelijk worden gebreken
        verdeeld over onderliggende componenten (kespen, palen, etc). Algemene
        gebreken worden opgeslagen in het Rakdeel model zelf.

        Parameters
        ----------
        gebreken : list[Gebrek]
            Lijst van gebreken onttrokken uit de gebreken tabel in het duikrapport.
        """

        # Kesp, Paal, Onderloopsheidscherm, Vloer, Metselwerk

        for gebrek in gebreken:

            # Try to extract kesp or paal id
            kesp_id = get_kesp_id(gebrek.codering)
            paal_id = get_paal_id(gebrek.codering)

            # Match gebreken to o
            if isinstance(gebrek, ScheurMetselwerk):
                if self.bovenbouw.metselwerk is None:
                    self.bovenbouw.metselwerk = Metselwerk()
                self.bovenbouw.metselwerk.gebreken.append(gebrek)

            # Match kesp
            elif not kesp_id is None:
                kesp = next((k for k in self.onderbouw.kespen if k.kesp_nummer == kesp_id), None)
                if kesp:
                    kesp.gebreken.append(gebrek)
                else:
                    print(
                        f"Waarschuwing: Kesp ID {kesp_id} gevonden in gebrek codering, maar geen overeenkomende Kesp in rakdeel {self.rakdeel_id}"
                    )

            # Match paal
            elif not paal_id is None:
                paal = next((p for p in self.onderbouw.palen if p.paal_nummer == paal_id), None)
                if paal:
                    paal.gebreken.append(gebrek)
                else:
                    print(
                        f"Waarschuwing: Paal ID {paal_id} gevonden in gebrek codering, maar geen overeenkomende Paal in rakdeel {self.rakdeel_id}"
                    )

            else:
                # If it doesnt belong to metselwerk, paal or kesp add to rakdeel itself
                self.gebreken.append(gebrek)
