from typing import Any

from pydantic import BaseModel

from .aansluiting_status import AansluitingStatus
from .gebrek import Gebrek


class Paal(BaseModel):
    """Paal.

    Attributes:
        gebreken: Lijst van gebreken in de paal.
        paalnummer: Nummer van de paal binnen de paalrij.
        aansluiting_status: Status van de aansluiting paal-kesp of paal-vloer.
        houtmonsters: Lijst van houtmonsters genomen uit deze paal.
        is_negatief_schoor: Indicatie of de paal negatief schoor staat (PNA in de tabel).
        is_onderzocht: Indicatie of de paal is onderzocht.
        opmerkingen: Eventuele opmerkingen over de paal.
        schoorstand_graden: Schoorstand van de paal in graden.
    """

    gebreken: list[Gebrek]
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalnummer'.
    paalnummer: str
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Aansluiting'.
    aansluiting_status: AansluitingStatus | None = None
    # Te vinden in Bijlage 1, kolom 'Paalnummer' en 'Houtmonster'.
    houtmonsters: list[dict[str, Any]] | None = None
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Schoorstand'.
    is_negatief_schoor: bool | None = None
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Onderzocht'.
    is_onderzocht: bool | None = None
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Opmerkingen'.
    opmerkingen: str | None = None
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Schoorstand'.
    schoorstand_graden: float | None = None
