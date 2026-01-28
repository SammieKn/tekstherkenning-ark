from pydantic import BaseModel
from azure.ai.documentintelligence.models import DocumentParagraph, DocumentTable

from tekstherkenning_ark.smart_document import RakdeelSectie
from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.gebrek import Gebrek, Scheefstand, Scheur, GrondVoerendGat, BuikInWand
from tekstherkenning_ark.models.onderbouw import Onderbouw
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.smart_document import RakdeelSectie


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

    bovenbouw: Bovenbouw
    # Te vinden in paragraaf 5.x, eerste alinea.
    constructietype: str
    gebreken: list[Gebrek] = []
    # Te vinden in paragraaf 5.x, eerste zin.
    lengte_m: float | None = None
    onderbouw: Onderbouw
    # Te vinden in paragraaf 5.x, kopregel of inhoudsopgave.
    rakdeel_id: str
    # Te vinden in paragraaf 5.1 of af te leiden uit de constructiebeschrijving.
    bouwjaar: int | None = None
    # Te vinden in de tekst van de constructiebeschrijving of samenvatting.
    opmerkingen: str = ""

    @classmethod
    def from_smartdocument(cls, section: RakdeelSectie) -> Rakdeel:
        """Genereer een lijst van Rakdeel modellen vanuit een lijst van RakdeelSectie modellen.

        Args:
            sections (list[RakdeelSectie]): Lijst van RakdeelSectie modellen.

        Returns:
            list[Rakdeel]: Lijst van gegenereerde Rakdeel modellen.
        """
        # TODO: Implementeer de parsing logica hier
        # stap 1 is de constructie omschrijving parsen
        omschrijving = ""
        # dit is van belang voor paragrafen die aangemaakt worden vanuit de tekeningen (symbolen).
        for paragraaf in section.beschrijving:
            if len(paragraaf.content.strip()) > 20:
                omschrijving += paragraaf.content + "\n"
        rakdeel_omschrijving = RakdeelOmschrijving.classificeer_omschrijving(omschrijving)

        # stap 2 is de gebrekentabel parsen naar gebreken
        gebreken = Rakdeel._parse_gebreken_tabel(tabellen=section.gebreken_tabel)
        # stap 3 is de eigenschappen van onderbouw en bovenbouw te koppelen
        onderbouw = Onderbouw(
            # kespen=Kesp.from_doctables?
            onderloopsheidscherm=rakdeel_omschrijving.onderloopsheidscherm,
            # palen=palen.from_doctables?
            vloer=rakdeel_omschrijving.materiaal_vloer,
            materiaal=rakdeel_omschrijving.materiaal_onderbouw,
        )
        bovenbouw = Bovenbouw(
            materiaal=rakdeel_omschrijving.materiaal_bovenbouw,
            bovenkant_deksteen_cm_tov_nap=rakdeel_omschrijving.bovenkant_deksteen_cm,
        )

        rakdeel = Rakdeel(
            bovenbouw=bovenbouw,
            constructietype=omschrijving,  # TODO: Bepaal constructietype op basis van omschrijving en/of tabellen
            gebreken=gebreken,
            lengte_m=rakdeel_omschrijving.lengte_rakdeel,
            onderbouw=onderbouw,
            rakdeel_id=section.constructie_naam,
            bouwjaar=rakdeel_omschrijving.bouwjaar,
            opmerkingen="",
        )

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
