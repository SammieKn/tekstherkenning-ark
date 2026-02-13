"""Genereer een Excel met toestandsbepaling (onderdeel_is_aangetast).

Voor elk PDF-rapport in `data/duikrapporten` wordt een `Rak` aangemaakt
en alle `Rakdeel.onderdeel_is_aangetast` sleutel/waarde-paren verzameld.

Output: Excel-bestand in `data/toestandsbepaling` met kolommen:
`rak_id`, `rakdeel_id`, `onderdeel`, `aangetast`.
"""

from __future__ import annotations

from datetime import datetime
import pandas as pd

from tekstherkenning_ark import constants
from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.models.rak import Rak


def waarde_naar_serieel(waarde):
    """Converteer verschillende waardetypen naar iets dat in Excel kan staan.

    Houd booleans als booleans, conversie voor enums/objects naar hun waarde/repr.
    """
    # bool eerst (isinstance(True, int) is True, dus check bool expliciet)
    if isinstance(waarde, bool):
        return waarde

    # Pydantic modellen: model_dump geeft een dict met details
    if hasattr(waarde, "model_dump"):
        try:
            return waarde.model_dump()
        except Exception:
            return str(waarde)

    # Enums / flexibele enums hebben vaak attribute `value`
    if hasattr(waarde, "value"):
        return waarde.value

    return str(waarde)


def haal_rakdeel_id_uit_pad(pad: str) -> str:
    """Haal `rakdeel_id` uit een hiërarchisch pad zoals `rak/rakdeel/onderbouw/vloer`."""
    delen = [deel for deel in pad.split("/") if deel]
    if len(delen) >= 2:
        return delen[1]
    return ""


def main():
    pdf_rapporten = [file for file in (constants.DATA_DIR / "duikrapporten").glob("*.pdf")]

    resultaten: list[dict] = []

    for file in pdf_rapporten:
        # Volg bestaande filter uit `rak_to_excel.py`
        if "boor" in file.stem.lower():
            continue

        print(f"Verwerken: {file.name}")
        doc = SmartDocument.from_pdf(file)
        rak = Rak.from_smart_document(doc, use_caching=True)

        rak_id = rak.raknaam

        for pad, onderdeel, aangetast in rak.alle_toestandsbepalingen:
            resultaten.append(
                {
                    "rak_id": rak_id,
                    "rakdeel_id": haal_rakdeel_id_uit_pad(pad),
                    "onderdeel": onderdeel,
                    "aangetast": waarde_naar_serieel(aangetast),
                }
            )

    output_dir = constants.DATA_DIR / "toestandsbepaling"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / f"toestandsbepaling_{timestamp}.xlsx"

    if resultaten:
        df = pd.DataFrame(resultaten)
    else:
        df = pd.DataFrame(columns=["rak_id", "rakdeel_id", "onderdeel", "aangetast"])

    df.to_excel(out_path, index=False)
    print(f"Gereed. Excel opgeslagen naar: {out_path}")


if __name__ == "__main__":
    main()
