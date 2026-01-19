from typing import Any, Union

from pydantic import BaseModel

from .gebrek import Gebrek, Scheefstand
from .enums import SchoorStand, NietBeschikbaar

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
    # Te vinden in de schades en gebreken tabellen van hoofdstuk 5.
    gebreken: list[Union[Gebrek, Scheefstand]] = []
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalnummer'.
    paalrij_nummer: str
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
