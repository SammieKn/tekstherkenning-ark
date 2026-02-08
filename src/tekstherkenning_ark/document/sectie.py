from __future__ import annotations
from dataclasses import dataclass, field

from azure.ai.documentintelligence.models import DocumentTable, DocumentParagraph


@dataclass
class Sectie:
    """Een sectie in het document met titel, paragrafen en tabellen.

    Attributes
    ----------
    titel : str
        De titel van de sectie (section heading).
    inhoud : list[DocumentParagraph]
        Lijst van paragrafen in de sectie.
    tabellen : list[DocumentTable]
        Lijst van tabellen die bij deze sectie horen.
    heading_offset : int
        Offset van de section heading in het originele document.
    """

    titel: str
    inhoud: list[DocumentParagraph] = field(default_factory=list)
    tabellen: list[DocumentTable] = field(default_factory=list)
    heading_offset: int = 0

    def full_text(self) -> str:
        """Combineert alle tekstuele inhoud van de sectie."""
        return "\n".join(p.content for p in self.inhoud)
