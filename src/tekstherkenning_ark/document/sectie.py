from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from tekstherkenning_ark.document.structured_table import DocumentTabel


@dataclass(frozen=True)
class BronLocatie:
    """Een gebied op een PDF-pagina, in punten gemeten vanaf linksboven.

    Attributes
    ----------
    pagina : int
        Een op een gebaseerde paginanummering.
    bbox : tuple[float, float, float, float]
        Linker-, boven-, rechter- en ondergrens van het brongebied.
    """

    pagina: int
    bbox: tuple[float, float, float, float]


@dataclass(frozen=True)
class Paragraaf:
    """Native PDF-tekst met documentgebonden identiteit en bronverwijzingen.

    Attributes
    ----------
    content : str
        Ongewijzigde native tekst; behoudt het bestaande tekstcontract.
    id : str
        Identificatie binnen hetzelfde document en dezelfde parserconfiguratie.
    leesvolgorde : int
        Positie tussen tekst, tabellen en figuren in het document.
    bronlocaties : tuple[BronLocatie, ...]
        Brongebieden, eventueel op meerdere pagina's.
    rol : str
        Layoutrol, bijvoorbeeld tekst, bijschrift of paginakop.
    """

    content: str
    id: str = ""
    leesvolgorde: int = 0
    bronlocaties: tuple[BronLocatie, ...] = ()
    rol: str = "text"


@dataclass(frozen=True)
class Afbeelding:
    """Een volledige raster- of vectorfiguur met verwijzing naar een PNG-asset.

    Attributes
    ----------
    id : str
        Identificatie van deze plaatsing, niet alleen van het afbeeldingsbestand.
    bestand : Path
        Pad naar de gerenderde PNG, zonder ingebedde afbeeldingsdata.
    bronlocaties : tuple[BronLocatie, ...]
        Brongebieden van de figuur.
    leesvolgorde : int
        Positie tussen de overige documentelementen.
    bijschrift_id : str | None
        Verwijzing naar een afzonderlijke native paragraaf, indien eenduidig gekoppeld.
    """

    id: str
    bestand: Path
    bronlocaties: tuple[BronLocatie, ...]
    leesvolgorde: int = 0
    bijschrift_id: str | None = None


@dataclass(init=False)
class Sectie:
    """Een sectie in het document met titel, paragrafen en tabellen.

    Attributes
    ----------
    titel : str
        De titel van de sectie (section heading).
    inhoud : Sequence[Paragraaf]
        Paragrafen afgeleid van de registratie, of de bestaande fixture-inhoud.
    tabellen : Sequence[DocumentTabel]
        Tabellen afgeleid van de registratie, of de bestaande fixture-inhoud.
    heading_offset : int
        Offset van de section heading in het originele document.
    id : str
        Identificatie binnen het document.
    kopniveau : int
        Niveau in de hoofdstuk- en sectiehierarchie, beginnend bij een.
    ouder_id : str | None
        Identificatie van de bovenliggende sectie.
    koplocatie : BronLocatie | None
        Brongebied van de sectiekop.
    element_ids : list[str]
        Verwijzingen naar documentelementen in leesvolgorde.
    """

    titel: str
    heading_offset: int = 0
    id: str = ""
    kopniveau: int = 1
    ouder_id: str | None = None
    koplocatie: BronLocatie | None = None
    element_ids: list[str] = field(default_factory=list)
    _inhoud: list[Paragraaf] = field(default_factory=list, repr=False)
    _tabellen: list[DocumentTabel] = field(default_factory=list, repr=False)
    _elementen: dict[str, Paragraaf | DocumentTabel | Afbeelding] | None = field(default=None, repr=False)

    def __init__(
        self,
        titel: str,
        inhoud: Sequence[Paragraaf] | None = None,
        tabellen: Sequence[DocumentTabel] | None = None,
        heading_offset: int = 0,
        id: str = "",
        kopniveau: int = 1,
        ouder_id: str | None = None,
        koplocatie: BronLocatie | None = None,
        element_ids: list[str] | None = None,
    ) -> None:
        """Behoud de bestaande constructor naast registratiegebonden secties.

        Parameters
        ----------
        titel : str
            Titel van de sectie.
        inhoud, tabellen : Sequence, optional
            Bestaande inhoud voor nog niet gemigreerde lokale fixtures.
        heading_offset : int
            Alleen voor de bestaande offset-gebaseerde fixtures.
        id, kopniveau, ouder_id, koplocatie, element_ids
            Identiteit, hierarchie en bronverwijzingen van de sectie.
        """
        self.titel = titel
        self.heading_offset = heading_offset
        self.id = id
        self.kopniveau = kopniveau
        self.ouder_id = ouder_id
        self.koplocatie = koplocatie
        self.element_ids = list(element_ids or ())
        self._inhoud = list(inhoud or ())
        self._tabellen = list(tabellen or ())
        self._elementen = None

    @property
    def inhoud(self) -> Sequence[Paragraaf]:
        """Selecteer sectieparagrafen zonder een tweede muteerbare inhoudslijst.

        Returns
        -------
        Sequence[Paragraaf]
            Native paragrafen of de bestaande fixture-inhoud.
        """
        if self._elementen is None:
            return self._inhoud
        return tuple(
            self._elementen[element_id]
            for element_id in self.element_ids
            if isinstance(self._elementen[element_id], Paragraaf)
            and self._elementen[element_id].rol not in {"page-header", "page-footer", "footnote"}
        )

    @property
    def tabellen(self) -> Sequence[DocumentTabel]:
        """Selecteer de geregistreerde tabellen van deze sectie.

        Returns
        -------
        Sequence[DocumentTabel]
            Native tabellen of de bestaande fixture-inhoud.
        """
        if self._elementen is None:
            return self._tabellen
        return tuple(
            self._elementen[element_id]
            for element_id in self.element_ids
            if isinstance(self._elementen[element_id], DocumentTabel)
        )

    @property
    def afbeeldingen(self) -> tuple[Afbeelding, ...]:
        """Selecteer de figuurplaatsingen van deze sectie.

        Returns
        -------
        tuple[Afbeelding, ...]
            Afbeeldingen in de gemengde sectieleesvolgorde.
        """
        if self._elementen is None:
            return ()
        return tuple(
            self._elementen[element_id]
            for element_id in self.element_ids
            if isinstance(self._elementen[element_id], Afbeelding)
        )

    def __setstate__(self, toestand: dict[str, object]) -> None:
        """Herstel een sectie uit een bestaande, vertrouwde lokale fixture.

        Parameters
        ----------
        toestand : dict[str, object]
            Opgeslagen velden, eventueel zonder nieuwe elementverwijzingen.
        """
        toestand = dict(toestand)
        self._inhoud = toestand.pop("inhoud", toestand.get("_inhoud", []))
        self._tabellen = toestand.pop("tabellen", toestand.get("_tabellen", []))
        self.__dict__.update(toestand)
        # Pickle roept __init__ niet aan; oude fixtures missen de nieuwe default_factory-velden.
        self.__dict__.setdefault("element_ids", [])
        self.__dict__.setdefault("_elementen", None)

    def full_text(self) -> str:
        """Combineer de native tekst van de sectie.

        Returns
        -------
        str
            Paragrafen gescheiden door regeleinden, zonder tekstnormalisatie.
        """
        return "\n".join(p.content for p in self.inhoud)
