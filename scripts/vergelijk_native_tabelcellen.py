"""Toon exacte verschillen tussen PyMuPDF-broncellen en SmartDocument-tabellen.

De uitvoer bevat ruwe rapporttekst. Controleer die op gevoelige gegevens voordat je
uitvoer deelt of opslaat.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf

from tekstherkenning_ark import constants
from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.document.structured_table import DocumentTabel


TabelMatrix = tuple[tuple[str | None, ...], ...]


def lees_broncellen(pdf_pad: Path, *, via_byte_stream: bool = False) -> dict[str, TabelMatrix]:
    """Lees de ruwe tabelcellen op dezelfde manier als de corpusreferentie.

    Parameters
    ----------
    pdf_pad : Path
        Pad naar een PDF met native, selecteerbare tekst.
    via_byte_stream : bool
        Open de PDF als bytesstream in plaats van via het bestandspad.

    Returns
    -------
    dict[str, TabelMatrix]
        Native celmatrices, gesleuteld op pagina- en tabelnummer.
    """
    tabellen = {}
    pdf = (
        pymupdf.open(stream=pdf_pad.read_bytes(), filetype="pdf")
        if via_byte_stream
        else pymupdf.open(pdf_pad)
    )
    with pdf:
        for pagina in pdf:
            pagina.remove_rotation()
            pagina.get_text("dict", sort=True)
            for index, tabel in enumerate(pagina.find_tables(use_layout=False).tables):
                matrix = tabel.extract()
                tabellen[f"p{pagina.number + 1}-t{index}"] = tuple(
                    tuple(
                        (matrix[rij_index][kolom_index] or "") if celgebied is not None else None
                        for kolom_index, celgebied in enumerate(rij.cells)
                    )
                    for rij_index, rij in enumerate(tabel.rows)
                )
    return tabellen


def lees_smartdocument(pdf_pad: Path) -> dict[str, TabelMatrix]:
    """Extraheer de native tabelmatrices via de productie-PDF-route.

    Parameters
    ----------
    pdf_pad : Path
        Pad naar dezelfde PDF als gebruikt voor de bronmatrix.

    Returns
    -------
    dict[str, TabelMatrix]
        SmartDocument-tabellen met documentgebonden voorvoegsel verwijderd.
    """
    document = SmartDocument.from_pdf(pdf_pad, use_cache=False)
    voorvoegsel = f"{document.bron_hash[:12]}-"
    return {
        element.id.removeprefix(voorvoegsel): element.matrix
        for element in document.elementen.values()
        if isinstance(element, DocumentTabel)
    }


def normaliseer_regelindeling(waarde: str) -> str:
    """Normaliseer uitsluitend witruimte voor de diagnostische vergelijking.

    Parameters
    ----------
    waarde : str
        Een ruwe celwaarde.

    Returns
    -------
    str
        Tekst met regeleinden en opeenvolgende witruimte samengevoegd.
    """
    return " ".join(waarde.split())


def vergelijk_matrices(bron: dict[str, TabelMatrix], extractie: dict[str, TabelMatrix]) -> int:
    """Toon verschillen in tabelstructuur en celinhoud.

    Parameters
    ----------
    bron : dict[str, TabelMatrix]
        Rechtstreeks uit PyMuPDF gelezen referentietabellen.
    extractie : dict[str, TabelMatrix]
        Tabellen uit SmartDocument.

    Returns
    -------
    int
        Aantal cellen met afwijkende aanwezigheid of inhoud.
    """
    verschillen = 0
    for tabel_id in sorted(bron.keys() | extractie.keys()):
        bron_matrix = bron.get(tabel_id)
        extractie_matrix = extractie.get(tabel_id)
        if bron_matrix is None or extractie_matrix is None:
            verschillen += 1
            print(
                f"  {tabel_id}: tabel ontbreekt; "
                f"bron={'aanwezig' if bron_matrix is not None else 'ontbreekt'}, "
                f"extractie={'aanwezig' if extractie_matrix is not None else 'ontbreekt'}"
            )
            continue

        bron_afmeting = (len(bron_matrix), max((len(rij) for rij in bron_matrix), default=0))
        extractie_afmeting = (len(extractie_matrix), max((len(rij) for rij in extractie_matrix), default=0))
        if bron_afmeting != extractie_afmeting:
            print(f"  {tabel_id}: rasterafmeting bron={bron_afmeting}, extractie={extractie_afmeting}")

        for rij_index in range(max(bron_afmeting[0], extractie_afmeting[0])):
            bron_rij = bron_matrix[rij_index] if rij_index < len(bron_matrix) else ()
            extractie_rij = extractie_matrix[rij_index] if rij_index < len(extractie_matrix) else ()
            for kolom_index in range(max(len(bron_rij), len(extractie_rij))):
                bron_waarde = bron_rij[kolom_index] if kolom_index < len(bron_rij) else None
                extractie_waarde = extractie_rij[kolom_index] if kolom_index < len(extractie_rij) else None
                if bron_waarde == extractie_waarde:
                    continue

                verschillen += 1
                witruimte_gelijk = (
                    normaliseer_regelindeling(bron_waarde) == normaliseer_regelindeling(extractie_waarde)
                    if isinstance(bron_waarde, str) and isinstance(extractie_waarde, str)
                    else False
                )
                print(
                    f"  {tabel_id}[rij={rij_index}, kolom={kolom_index}]:\n"
                    f"    bron      = {bron_waarde!r}\n"
                    f"    extractie = {extractie_waarde!r}\n"
                    f"    alleen witruimte? {witruimte_gelijk}"
                )
    return verschillen


def main() -> int:
    """Vergelijk opgegeven PDF's in de opgegeven volgorde.

    Returns
    -------
    int
        Processtatus: nul zonder verschillen, een als verschillen zijn gevonden.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pdf",
        nargs="+",
        type=Path,
        help="PDF-bestanden in verwerkingsvolgorde; geef bijvoorbeeld eerst HEG0201 en dan KZG1002 op.",
    )
    parser.add_argument(
        "--bron-via-byte-stream",
        action="store_true",
        help="Open de referentie-PDF als bytesstream, zoals SmartDocument.from_pdf().",
    )
    opties = parser.parse_args()
    ontbrekend = [pad for pad in opties.pdf if not pad.is_file()]
    if ontbrekend:
        parser.error("PDF-bestand niet gevonden: " + ", ".join(str(pad) for pad in ontbrekend))

    oorspronkelijke_cachemap = constants.CACHE_DIR
    aantal_afwijkingen = 0
    try:
        with TemporaryDirectory(prefix="ark-celvergelijking-") as tijdelijke_map:
            constants.CACHE_DIR = Path(tijdelijke_map)
            for index, pdf_pad in enumerate(opties.pdf, start=1):
                print(f"\n[{index}/{len(opties.pdf)}] {pdf_pad.name} (PyMuPDF {pymupdf.VersionBind})")
                bron = lees_broncellen(pdf_pad, via_byte_stream=opties.bron_via_byte_stream)
                extractie = lees_smartdocument(pdf_pad)
                print(f"  tabellen: bron={len(bron)}, extractie={len(extractie)}")
                afwijkingen = vergelijk_matrices(bron, extractie)
                aantal_afwijkingen += afwijkingen
                print(f"  afwijkende cellen/tabellen: {afwijkingen}")
    finally:
        constants.CACHE_DIR = oorspronkelijke_cachemap

    print(f"\nTotaal: {aantal_afwijkingen} afwijkingen in {len(opties.pdf)} PDF('s).")
    return int(aantal_afwijkingen > 0)


if __name__ == "__main__":
    raise SystemExit(main())
