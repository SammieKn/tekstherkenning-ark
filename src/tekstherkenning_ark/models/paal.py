from typing import Any, Union

from pydantic import BaseModel

from .gebrek import Gebrek, Scheefstand
from .enums import SchoorStand, NietBeschikbaar

class Paal(BaseModel):
    """Paal (Foundation Pile).
`
    Attributes:
        gebreken: Lijst van gebreken gevonden in de paal.
        paalrij_nummer: Nummer van de paalrij waartoe de paal behoort.
        paalnummer: Nummer van de paal binnen de paalrij.
        diameter_haaks: Diameter haaks op de gevel in mm.
        diameter_parallel: Diameter parallel aan de gevel in mm.
        diameter_gemiddeld: Gemiddelde diameter in mm.
        afstand_hoh: Hart-op-hart afstand tussen palen in mm.
        schoor_graden: Schoorstand van de paal in graden.
        schoor_richting: Richting van de schoorstand (PNV/PNA/LR).
        afstand_frontwand_cm: Afstand tot de frontwand in cm.
        is_scheefstand: Indicatie of er scheefstand is geconstateerd.
        is_paalbreak: Indicatie of er paalbreuk is geconstateerd.
        is_aantasting: Indicatie of er aantasting is geconstateerd.
        is_juiste_aansluiting: Indicatie of de aansluiting correct is.
        positionering_aansluiting_cm: Positionering van de aansluiting in cm.
        opmerkingen: Eventuele opmerkingen over de paal.
        houtmonsters: Lijst van houtmonsters genomen uit deze paal.
    """
    # Te vinden in de schades en gebreken tabellen van hoofdstuk 5.
    gebreken: list[Union[Gebrek, Scheefstand]] = []
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalnummer'.
    paalrij_nummer: str
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalnummer'.
    paalrij_nummer: str
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Paalnummer'.
    paalnummer: str
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolommen 'diameter'.
    diameter_haaks: int | NietBeschikbaar | None = None
    diameter_parallel: int | NietBeschikbaar | None = None
    diameter_gemiddeld: int | NietBeschikbaar | None = None
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'afstand'.
    afstand_hoh: int | NietBeschikbaar | None = None
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolommen 'Schoorstand'.
    schoor_graden : int | NietBeschikbaar | None = None
    schoor_richting : SchoorStand | NietBeschikbaar | None = None
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Afstand frontwand'.
    afstand_frontwand_cm: int | NietBeschikbaar | None = None
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolommen 'Schades'.
    is_scheefstand: bool | NietBeschikbaar | None = None
    is_paalbreak: bool | NietBeschikbaar | None = None
    is_aantasting: bool | NietBeschikbaar | None = None
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolommen 'aansluiting'.
    is_juiste_aansluiting: bool | NietBeschikbaar | None = None
    positionering_aansluiting_cm: int | NietBeschikbaar | None = None
    # Te vinden in de meettabel funderingspalen, Bijlage 3, kolom 'Opmerkingen'.
    opmerkingen: str | None = None
    # Te vinden in bijlage 2 en houtmonsters csv.
    houtmonsters: list[dict[str, Any]] | None = None
   