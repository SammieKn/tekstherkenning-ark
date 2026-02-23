from tekstherkenning_ark.enums import (
    AansluitingStatus,
    MateriaalOnderbouw,
    MateriaalFundering,
    NietBeschikbaar,
)
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.models.onderloopsheidscherm import Onderloopsheidscherm
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat, OnverwachtResultaatType
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.rak_base_model import RakBaseModel
from tekstherkenning_ark.models.vloer import Vloer
from tekstherkenning_ark.models.gebrek import Gebrek


class Onderbouw(RakBaseModel):
    """Object met alle eigenschappen van de onderbouw van het rakdeel.

    Attributes:
        kespen: Lijst van onderzochte kespen onder het rakdeel.
        onderloopsheidscherm: Onderloopsheidscherm van de onderbouw.
        palen: Lijst van palen onder het rakdeel.
        vloer: Vloer van de onderbouw.
        materiaal: Materiaal van de onderbouw (bijvoorbeeld hout, beton, staal).
    """

    # Te vinden in de meettabel kespen (Bijlage 3).
    kespen: list[Kesp]
    # Elke paalrij bevat de bijbehorende palen. Te vinden in de meettabel funderingspalen (Bijlage 3).
    palen: list[Paal]

    vloer: Vloer | None = None
    onderloopsheidscherm: Onderloopsheidscherm | None = None

    # Af te leiden uit de constructiebeschrijving (paragraaf 5.x) of doorsnedetekening.
    materiaal: MateriaalOnderbouw | NietBeschikbaar = NietBeschikbaar.LEEG
    materiaal_fundering: MateriaalFundering | NietBeschikbaar = NietBeschikbaar.LEEG

    @property
    def identifier(self) -> str:
        """Return a string that uniquely identifies this Onderbouw instance."""
        return "onderbouw"

    @property
    def totaal_aantal_palen(self) -> int:
        """Totaal aantal palen in de onderbouw."""
        return len(self.palen)

    @property
    def eerste_rij_palen(self) -> list[Paal]:
        """Geef de palen van de eerste rij terug (bijvoorbeeld P1.1, P1.2, P1.3, etc.),
        gesorteerd op paal_nummer_main."""

        palen = [paal for paal in self.palen if paal.paalrij_nummer == 1]
        palen = sorted(palen, key=lambda p: p.paal_nummer_main)

        return palen

    @property
    def aantal_onderzochte_palen(self) -> int:
        """Aantal palen dat daadwerkelijk onderzocht is."""
        return sum(1 for paal in self.palen if paal.is_onderzocht)

    @property
    def percentage_slechte_palen(self) -> float | None:
        """Percentage palen met bacteriële aantasting."""
        if not self.palen:
            return None

        aantal_slecht = sum(1 for paal in self.palen if paal.is_aantasting)
        return round((aantal_slecht / len(self.palen)) * 100, 2)

    @property
    def percentage_ongewenste_schoorstand(self) -> float | None:
        """Percentage palen met ongewenste/afwijkende schoorstand."""
        if not self.palen:
            return None

        aantal_ongewenst = sum(1 for paal in self.palen if paal.is_ongewenste_schoorstand and paal.paalrij_nummer == 1)
        return round((aantal_ongewenst / len(self.palen)) * 100, 2)

    @property
    def aantal_palen_met_scheefstand(self) -> int:
        """Aantal palen met geconstateerde scheefstand."""
        return sum(1 for paal in self.palen if paal.is_scheefstand)

    @property
    def aantal_palen_met_paalbreuk(self) -> int:
        """Aantal palen met geconstateerde paalbreuk."""
        return sum(1 for paal in self.palen if paal.is_paalbreuk)

    @property
    def totaal_aantal_kespen(self) -> int:
        """Totaal aantal kespen in de onderbouw."""
        return len(self.kespen)

    @property
    def percentage_beschadigde_kespen(self) -> float | None:
        """Percentage kespen met vervorming of aantasting."""
        if not self.kespen:
            return None

        aantal_beschadigd = sum(1 for kesp in self.kespen if kesp.is_vervormd or kesp.is_aangetast)
        return round((aantal_beschadigd / len(self.kespen)) * 100, 2)

    @property
    def percentage_vervormde_kespen(self) -> float | None:
        """Percentage kespen met vervorming."""
        if not self.kespen:
            return None

        aantal_vervormd = sum(1 for kesp in self.kespen if kesp.is_vervormd)
        return round((aantal_vervormd / len(self.kespen)) * 100, 2)

    @property
    def percentage_beschadigde_verbinding(self) -> float | None:
        """Percentage palen met slechte paal-kesp/paal-vloer aansluiting."""
        if not self.palen:
            return None

        aantal_slecht = sum(1 for paal in self.palen if paal.aansluiting_status is AansluitingStatus.SLECHT)
        return round((aantal_slecht / len(self.palen)) * 100, 2)

    def get_consecutive_palen(self) -> list[Paal] | OnverwachtResultaat:
        """Geef de palen in volgorde van hoh_paalnummer verwijzingen, beginnend bij de eerste rij palen (P1.1, P1.2, etc.).

        Returns
        -------
        list[Paal] | None | OnverwachtResultaat
        - list[Paal]: de palen in de eerste rij van de onderbouw, in volgorde van hoh_paalnummer
        - OnverwachtResultaat: als de paal data fouten bevat, bijvoorbeeld:
            - Ontbrekende hoh_afstand_cm voor een paal
            - Cyclische paalreferenties via hoh_paalnummer
            - Ontbrekende paalreferenties (bijvoorbeeld een ontbrekende P1.13 in een reeks van P1.1 t/m P1.20)
        """

        if not self.eerste_rij_palen:
            return []

        current_paal = self.eerste_rij_palen[0]
        consecutive_palen = []

        while current_paal:

            # Check for cyclical references to prevent infinite loops
            if current_paal in consecutive_palen:
                return OnverwachtResultaat(
                    waarde=None,
                    onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
                    details=f"Cyclische paalreferenties gedetecteerd bij Rakdeel: paal {current_paal.paal_nummer} verwijst terug naar een eerder verwerkte paal.",
                )

            # Check if hoh_afstand_cm is available for the current paal
            if not current_paal.hoh_afstand_cm:
                return OnverwachtResultaat(
                    waarde=None,
                    onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
                    details=f"Ontbrekende hoh_afstand_cm voor paal {current_paal.paal_nummer} in Rakdeel",
                )

            consecutive_palen.append(current_paal)

            current_paal = self.get_next_paal(current_paal)
            if isinstance(current_paal, OnverwachtResultaat):
                return current_paal

        # Validate that we have processed the expected number of palen based on the first row palen in onderbouw
        if not len(consecutive_palen) == len(self.eerste_rij_palen):
            return OnverwachtResultaat(
                waarde=None,
                onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
                details=f"Onvolledige verwerking van palen: {len(consecutive_palen)} van {len(self.eerste_rij_palen)} palen verwerkt. Dit kan duiden op onvolledige data of een gebroken reeks.",
            )

        return consecutive_palen

    def get_next_paal(self, current_paal: Paal) -> Paal | OnverwachtResultaat | None:
        """Geef de volgende paal in dezelfde rij terug obv hoh_paalnummer, of None als er geen volgende paal is.

        Returns
        -------
        Paal | None | OnverwachtResultaat
        - Paal: de volgende paal in dezelfde rij van de onderbouw
        - None: als er geen volgende paal is
        - OnverwachtResultaat: als er meerdere palen verwijzen naar hetzelfde hoh_paalnummer, wat duidt op een datafout
        """

        # Determine the next paal in the sequence based on hoh_paalnummer.
        palen_that_refer_to_current_paal = [
            p for p in self.eerste_rij_palen if p.hoh_paalnummer == current_paal.paal_nummer
        ]

        # Check if there are multiple palen that refer to the same hoh_paalnummer, which would indicate a data issue
        if len(palen_that_refer_to_current_paal) > 1:
            return OnverwachtResultaat(
                waarde=None,
                onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
                details=f"Meerdere palen verwijzen naar hetzelfde hoh_paalnummer {current_paal.paal_nummer}",
            )

        if len(palen_that_refer_to_current_paal) == 1:
            return palen_that_refer_to_current_paal[0]

        # No next paal
        return None
