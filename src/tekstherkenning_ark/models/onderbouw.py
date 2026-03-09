from pydantic import computed_field

from tekstherkenning_ark.enums import (
    AansluitingStatus,
    MateriaalOnderbouw,
    MateriaalFundering,
    NietBeschikbaar,
    SchoorStand,
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

    @computed_field
    @property
    def aantal_paalrijen(self) -> int:
        """Aantal paalrijen in de onderbouw (unieke paalrij_nummer waarden)."""
        return len(set(paal.paalrij_nummer for paal in self.palen))

    @computed_field
    @property
    def aantal_palen_per_rij(self) -> dict[int, int]:
        """Aantal palen per paalrij in de onderbouw.

        Returns
        -------
        dict[int, int]
            Dictionary waarbij de keys de paalrij_nummer zijn en de values het aantal palen in die rij.
        """
        return {rij_nummer: len(palen) for rij_nummer, palen in self.paal_rijen.items()}

    @computed_field
    @property
    def aantal_rijen_onderzocht(self) -> int:
        """Aantal onderzochte paalrijen in de onderbouw."""
        return {rij_nummer: any(paal.is_onderzocht for paal in palen) for rij_nummer, palen in self.paal_rijen.items()}

    @computed_field
    @property
    def aantal_palen_dwars(self) -> int:
        """Aantal paalrijen in dwarsdoorsneden (maximale paalrij_nummer waarde)."""
        if not self.palen:
            return 0
        return max(paal.paalrij_nummer if isinstance(paal.paalrij_nummer, (int, float)) else 0 for paal in self.palen)

    @computed_field
    @property
    def aantal_aansluitingen(self) -> int:
        """Totaal aantal aansluitingen tussen palen en kespen in de onderbouw."""
        return sum(
            paal.aansluiting_status in [AansluitingStatus.GOED, AansluitingStatus.SLECHT] for paal in self.palen
        )

    @computed_field
    @property
    def aantal_slechte_aansluitingen(self) -> int:
        """Totaal aantal slechte aansluitingen tussen palen en kespen in de onderbouw."""
        return sum(paal.aansluiting_status is AansluitingStatus.SLECHT for paal in self.palen)

    @computed_field
    @property
    def totaal_aantal_palen(self) -> int:
        """Totaal aantal palen in de onderbouw."""
        return len(self.palen)

    @property
    def paal_rijen(self) -> dict[int, list[Paal]]:
        """Geef een dictionary terug waarbij de keys de paalrij_nummer zijn en de values lijsten van palen in die rij."""
        paal_rijen_dict = {}
        for paal in self.palen:
            if paal.paalrij_nummer not in paal_rijen_dict:
                paal_rijen_dict[paal.paalrij_nummer] = []
            paal_rijen_dict[paal.paalrij_nummer].append(paal)

        for rij_nummer in paal_rijen_dict:
            paal_rijen_dict[rij_nummer] = sorted(paal_rijen_dict[rij_nummer], key=lambda p: p.paal_nummer_main)
        return paal_rijen_dict

    @property
    def eerste_rij_palen(self) -> list[Paal]:
        """Geef de palen van de eerste rij terug (bijvoorbeeld P1.1, P1.2, P1.3, etc.),
        gesorteerd op paal_nummer_main."""

        return self.paal_rijen[1] if 1 in self.paal_rijen else []

    def get_eerste_paal_met_aansluitende_statussen(
        self,
        aansluiting_statussen: list[AansluitingStatus],
        include_onverwacht_resultaat: bool = False,
    ) -> Paal | None:
        """Geef de eerste paal terug waar een reeks van minimaal vijf aansluitende statussen is bereikt."""
        for palen in self.paal_rijen.values():
            aansluitende_status_count = 0

            for paal in palen:
                is_match = paal.aansluiting_status in aansluiting_statussen
                if include_onverwacht_resultaat and isinstance(paal.aansluiting_status, OnverwachtResultaat):
                    is_match = True

                if is_match:
                    aansluitende_status_count += 1
                    if aansluitende_status_count >= 5:
                        return paal
                else:
                    aansluitende_status_count = 0

        return None

    @computed_field
    @property
    def is_vijf_aansluitende_slechte_paal_kesp_verbinding_in_rij(self) -> bool | OnverwachtResultaat:
        """Controleer of er in een paalrij minimaal vijf aaneengesloten slechte aansluitingen voorkomen."""
        slechte_status_reeks = self.get_eerste_paal_met_aansluitende_statussen([AansluitingStatus.SLECHT])
        if slechte_status_reeks:
            return True

        onverwachte_status_reeks = self.get_eerste_paal_met_aansluitende_statussen(
            [AansluitingStatus.SLECHT, AansluitingStatus.NIET_MEETBAAR],
            include_onverwacht_resultaat=True,
        )
        if onverwachte_status_reeks:
            return OnverwachtResultaat(
                waarde=True,
                onverwacht_resultaat_type=OnverwachtResultaatType.ONDERLIGGENDE_DATA_INCORRECT,
                details=f"Onverwacht resultaat bij aansluiting van paal {onverwachte_status_reeks.paal_nummer} in rij {onverwachte_status_reeks.paalrij_nummer}. Dit kan duiden op onvolledige data of een fout in de data-extractie.",
            )

        return False

    @computed_field
    @property
    def aantal_onderzochte_palen(self) -> int:
        """Aantal palen dat daadwerkelijk onderzocht is."""
        return sum(1 for paal in self.palen if paal.is_onderzocht)

    @computed_field
    @property
    def percentage_slechte_palen(self) -> float | None:
        """Percentage palen met bacteriële aantasting."""
        if not self.palen:
            return None

        aantal_slecht = sum(1 for paal in self.palen if paal.is_aantasting)
        return round((aantal_slecht / len(self.palen)) * 100, 2)

    @computed_field
    @property
    def aantal_ongewenst_schoor(self) -> int:
        """Aantal palen met geconstateerde negatieve schoorstand."""

        return sum((paal.is_ongewenste_schoorstand or 0) and paal.paalrij_nummer == 1 for paal in self.palen)

    @computed_field
    @property
    def percentage_ongewenste_schoorstand(self) -> float | None:
        """Percentage palen met ongewenste/afwijkende schoorstand."""
        if not self.palen:
            return None

        return round((self.aantal_ongewenst_schoor / len(self.palen)) * 100, 2)

    @computed_field
    @property
    def aantal_palen_met_scheefstand(self) -> int:
        """Aantal palen met geconstateerde scheefstand."""
        return sum(1 for paal in self.palen if paal.is_scheefstand)

    @computed_field
    @property
    def is_schoorpalen_in_een_richting(self) -> bool | NietBeschikbaar:
        """Controleer of alle palen met geconstateerde schoorstand in dezelfde richting staan (allemaal positief of allemaal negatief)."""
        schoorstanden = {paal.schoor_richting for paal in self.palen if paal.is_schoorpaal}
        return len(schoorstanden) <= 1 if schoorstanden else NietBeschikbaar.NIET_VAN_TOEPASSING

    @computed_field
    @property
    def aantal_schoorpalen(self) -> int:
        """Aantal palen met geconstateerde schoorstand."""
        return sum(1 for paal in self.palen if paal.is_schoorpaal)

    @computed_field
    @property
    def aantal_palen_met_paalbreuk(self) -> int:
        """Aantal palen met geconstateerde paalbreuk."""
        return sum(1 for paal in self.palen if paal.is_paalbreuk)

    @computed_field
    @property
    def totaal_aantal_kespen(self) -> int:
        """Totaal aantal kespen in de onderbouw."""
        return len(self.kespen)

    @computed_field
    @property
    def aantal_beschadigde_kespen(self) -> int:
        """Aantal kespen met vervorming of aantasting."""
        return sum((kesp.is_vervormd or 0) or (kesp.is_aangetast or 0) for kesp in self.kespen)

    @computed_field
    @property
    def percentage_beschadigde_kespen(self) -> float | None:
        """Percentage kespen met vervorming of aantasting."""
        if not self.kespen:
            return None

        return round((self.aantal_beschadigde_kespen / len(self.kespen)) * 100, 2)

    @computed_field
    @property
    def percentage_vervormde_kespen(self) -> float | None:
        """Percentage kespen met vervorming."""
        if not self.kespen:
            return None

        aantal_vervormd = sum(1 for kesp in self.kespen if kesp.is_vervormd)
        return round((aantal_vervormd / len(self.kespen)) * 100, 2)

    @computed_field
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
