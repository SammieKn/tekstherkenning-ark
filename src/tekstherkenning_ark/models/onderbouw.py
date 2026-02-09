from tekstherkenning_ark.enums import (
    AansluitingStatus,
    MateriaalOnderbouw,
    MateriaalVloer,
    NietBeschikbaar,
)
from tekstherkenning_ark.models.kesp import Kesp
from tekstherkenning_ark.models.onderloopsheidscherm import Onderloopsheidscherm
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

    @property
    def identifier(self) -> str:
        """Return a string that uniquely identifies this Onderbouw instance."""
        return "onderbouw"

    @property
    def totaal_aantal_palen(self) -> int:
        """Totaal aantal palen in de onderbouw."""
        return len(self.palen)

    @property
    def aantal_onderzochte_palen(self) -> int:
        """Aantal palen dat daadwerkelijk onderzocht is."""
        return sum(1 for paal in self.palen if paal.is_onderzocht is True)

    @property
    def percentage_slechte_palen(self) -> float | None:
        """Percentage palen met bacteriële aantasting."""
        if not self.palen:
            return None

        aantal_slecht = sum(1 for paal in self.palen if paal.is_aantasting is True)
        return round((aantal_slecht / len(self.palen)) * 100, 2)

    # TODO: Checken met Geert hoe een ongewenste schoorstand gedefinieerd is en of dit veld in de meettabel palen staat.
    # @property
    # def percentage_ongewenste_schoorstand(self) -> float | None:
    #     """Percentage palen met ongewenste/afwijkende schoorstand."""
    #     if not self.palen:
    #         return None

    #     # Tel palen met significante schoorstand (> 15 graden als voorbeeld)
    #     aantal_ongewenst = sum(
    #         1 for paal in self.palen if paal.schoorstand_graden is not None and abs(paal.schoorstand_graden) > 15
    #     )
    #     return round((aantal_ongewenst / len(self.palen)) * 100, 2)

    @property
    def aantal_palen_met_scheefstand(self) -> int:
        """Aantal palen met geconstateerde scheefstand."""
        return sum(1 for paal in self.palen if paal.is_scheefstand is True)

    @property
    def aantal_palen_met_paalbreuk(self) -> int:
        """Aantal palen met geconstateerde paalbreuk."""
        return sum(1 for paal in self.palen if paal.is_paalbreuk is True)

    @property
    def totaal_aantal_kespen(self) -> int:
        """Totaal aantal kespen in de onderbouw."""
        return len(self.kespen)

    @property
    def percentage_beschadigde_kespen(self) -> float | None:
        # TODO: Checken met Geert hoe een beschadigde kesp gedefinieerd is en of dit veld in de meettabel kespen staat.
        """Percentage kespen met vervorming of aantasting."""
        if not self.kespen:
            return None

        aantal_beschadigd = sum(1 for kesp in self.kespen if kesp.is_vervormd is True or kesp.is_aangetast is True)
        return round((aantal_beschadigd / len(self.kespen)) * 100, 2)

    @property
    def percentage_beschadigde_verbinding(self) -> float | None:
        """Percentage palen met slechte paal-kesp/paal-vloer aansluiting."""
        if not self.palen:
            return None

        aantal_slecht = sum(
            1
            for paal in self.palen
            if isinstance(paal.aansluiting_status, AansluitingStatus)
            and paal.aansluiting_status == AansluitingStatus.SLECHT
        )
        return round((aantal_slecht / len(self.palen)) * 100, 2)
