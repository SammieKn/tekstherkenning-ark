from typing import Any

from pydantic import BaseModel, Field

from .aansluiting_status import AansluitingStatus
from .gebrek import Gebrek


class Paal(BaseModel):
    """Paal"""

    gebreken: list[Gebrek]
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalnummer'.
    paalnummer: str = Field(description="Nummer van de paal binnen de paalrij.")
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Aansluiting'.
    aansluiting_status: AansluitingStatus | None = Field(
        default=None, description="Status van de aansluiting paal-kesp of paal-vloer."
    )
    # Te vinden in Bijlage 1, kolom 'Paalnummer' en 'Houtmonster'.
    houtmonsters: list[dict[str, Any]] | None = Field(
        default=None, description="Lijst van houtmonsters genomen uit deze paal."
    )
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Schoorstand'.
    is_negatief_schoor: bool | None = Field(
        default=None,
        description="Indicatie of de paal negatief schoor staat (PNA in de tabel).",
    )
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Onderzocht'.
    is_onderzocht: bool | None = Field(default=None, description="Indicatie of de paal is onderzocht.")
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Opmerkingen'.
    opmerkingen: str | None = Field(default=None, description="Eventuele opmerkingen over de paal.")
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Schoorstand'.
    schoorstand_graden: float | None = Field(default=None, description="Schoorstand van de paal in graden.")
