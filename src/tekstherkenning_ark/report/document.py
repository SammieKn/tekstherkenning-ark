"""
Een algemeen document parser die de inhoud van Azure Doc Intelligence verwerkt naar chronologische secties.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union

@dataclass
class Sectie:
    titel: str
    inhoud: List[str] = field(default_factory=list)
    tabellen: List[str] = field(default_factory=list)

    def full_text(self) -> str:
        """Combineert alle tekstuele inhoud van de sectie."""
        return "\n".join(self.inhoud)
    
@dataclass
class GeparsteTabel:
    titel: str
    data: List[List[str]] = field(default_factory=list)  # 2D lijst voor rijen en kolommen

class SmartDocument:
    def __init__(self, analyze_result) -> None:
        self.sections: List[Sectie] = []
        