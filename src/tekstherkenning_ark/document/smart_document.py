from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from dataclasses import asdict, dataclass, field, replace
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pymupdf
from dotenv import load_dotenv

from tekstherkenning_ark import constants
from tekstherkenning_ark.constants import DATA_DIR
from tekstherkenning_ark.document.rakdeelsectie import RakdeelSectie
from tekstherkenning_ark.document.sectie import Afbeelding, BronLocatie, Paragraaf, Sectie
from tekstherkenning_ark.document.structured_table import DocumentTabel, StructuredTable, TabelCel, TableType
from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.utils import get_constructienaam, get_rak_id

load_dotenv()

logger = get_logger(__name__)

STRUCTUUR_SCHEMA_VERSIE = 1
EXTRACTOR_VERSIE = 3
AFBEELDING_DPI = 150


@dataclass
class SmartDocument:
    """Documentstructuur met secties en brongebonden elementen.

    Attributes
    ----------
    document_name : str
        Naam van het geanalyseerde PDF document.
    sections : list[Sectie]
        Lijst van alle secties in het document.
    analyze_result : None
        Leeg compatibiliteitsveld; lokale extractie gebruikt alleen eigen elementen.
    elementen : dict[str, Paragraaf | DocumentTabel | Afbeelding]
        Canonieke registratie waar secties via element-ID's naar verwijzen.
    bron_hash : str
        Volledige SHA256 van de ingelezen PDF.
    pagina_afmetingen : dict[int, tuple[float, float]]
        Pagina-afmetingen na rotatienormalisatie, met op een gebaseerde sleutels.
    bookmarks : list[tuple[int, str, int]]
        Oorspronkelijke PDF-bookmarks als niveau, titel en bronpagina.
    extractie_metadata : dict
        Versies en instellingen van de daadwerkelijk gebruikte extractor.
    bron_bestandsnaam : str
        Bestandsnaam van de huidige bron, onafhankelijk van gedeelde inhoudscaches.
    """

    document_name: str
    analyze_result: None = None
    sections: list[Sectie] = field(default_factory=list)
    elementen: dict[str, Paragraaf | DocumentTabel | Afbeelding] = field(default_factory=dict)
    bron_hash: str = ""
    pagina_afmetingen: dict[int, tuple[float, float]] = field(default_factory=dict)
    bookmarks: list[tuple[int, str, int]] = field(default_factory=list)
    extractie_metadata: dict = field(default_factory=dict)
    bron_bestandsnaam: str = ""

    @staticmethod
    def _extractie_configuratie() -> dict:
        """Geef de instellingen die de documentstructuur en figuurassets bepalen.

        Returns
        -------
        dict
            Versies en opties voor reproduceerbare extractie en cache-invalidation.
        """
        return {
            "schema_versie": STRUCTUUR_SCHEMA_VERSIE,
            "extractor_versie": EXTRACTOR_VERSIE,
            "pymupdf_versie": pymupdf.VersionBind,
            "use_ocr": False,
            "force_text": True,
            "write_images": True,
            "embed_images": False,
            "image_format": "png",
            "image_dpi": AFBEELDING_DPI,
            "native_tabellen_use_layout": False,
        }

    @property
    def documentvingerafdruk(self) -> str:
        """Identificeer broninhoud en de daadwerkelijk gebruikte parserinstellingen.

        Returns
        -------
        str
            SHA256-cache-identiteit, of leeg voor oude fixtures zonder bronvingerafdruk.
        """
        if not self.bron_hash or not self.extractie_metadata:
            return ""
        gegevens = {"bron_hash": self.bron_hash, "extractie": self.extractie_metadata}
        return sha256(json.dumps(gegevens, sort_keys=True).encode("utf-8")).hexdigest()

    @staticmethod
    def _controleer_png(bestand: Path) -> None:
        """Controleer dat een figuurasset bestaat en werkelijk als PNG decodeert.

        Parameters
        ----------
        bestand : Path
            Te controleren asset.

        Raises
        ------
        ValueError
            Als het bestand ontbreekt, beschadigd is of geen PNG is.
        """
        try:
            with bestand.open("rb") as invoer:
                if invoer.read(8) != b"\x89PNG\r\n\x1a\n":
                    raise ValueError("Geen PNG-bestand")
            afbeelding = pymupdf.Pixmap(str(bestand))
            if afbeelding.width <= 0 or afbeelding.height <= 0:
                raise ValueError("Lege PNG-afbeelding")
        except (OSError, RuntimeError, ValueError) as fout:
            raise ValueError(f"Ontbrekende of ongeldige figuurasset: {bestand}") from fout

    def exporteer_structuur(self, export_map: Path) -> Path:
        """Exporteer een zelfstandige structuur-JSON en PNG's met relatieve paden.

        Parameters
        ----------
        export_map : Path
            Map voor structuur.json en de submap afbeeldingen.

        Returns
        -------
        Path
            Pad naar de pas na volledige assetcontrole gepubliceerde structuur.json.

        Raises
        ------
        ValueError
            Bij ontbrekende assets of oude sectie-inhoud zonder elementregistratie.
        """
        if any(sectie._elementen is None and (sectie.inhoud or sectie.tabellen) for sectie in self.sections):
            raise ValueError("Migreer oude sectie-inhoud eerst naar de elementregistratie.")
        export_map = Path(export_map)
        for element in self.elementen.values():
            if isinstance(element, Afbeelding):
                self._controleer_png(element.bestand)
        export_map.mkdir(parents=True, exist_ok=True)
        elementen = []
        for element in self.elementen.values():
            gegevens = asdict(element)
            if isinstance(element, Afbeelding):
                asset_hash = sha256(element.bestand.read_bytes()).hexdigest()
                # Korte assetnamen voorkomen de Windows-padlimiet; het manifest bewaart de volledige hash.
                relatief_pad = Path("afbeeldingen") / f"{asset_hash[:32]}.png"
                doel = export_map / relatief_pad
                doel.parent.mkdir(parents=True, exist_ok=True)
                if element.bestand.resolve() != doel.resolve():
                    shutil.copyfile(element.bestand, doel)
                gegevens["bestand"] = relatief_pad.as_posix()
                gegevens["asset_hash"] = asset_hash
                gegevens["soort"] = "afbeelding"
            else:
                gegevens["soort"] = "paragraaf" if isinstance(element, Paragraaf) else "tabel"
            elementen.append(gegevens)

        manifest = {
            "schema_versie": STRUCTUUR_SCHEMA_VERSIE,
            "document_naam": self.document_name,
            "bron_bestandsnaam": self.bron_bestandsnaam,
            "bron_hash": self.bron_hash,
            "documentvingerafdruk": self.documentvingerafdruk,
            "extractie": self.extractie_metadata,
            "paginas": [
                {"nummer": nummer, "breedte": maten[0], "hoogte": maten[1]}
                for nummer, maten in self.pagina_afmetingen.items()
            ],
            "bookmarks": self.bookmarks,
            # Niet asdict(sectie): de gedeelde registratie zou de complete inhoud herhalen.
            "secties": [
                {
                    "id": sectie.id,
                    "titel": sectie.titel,
                    "kopniveau": sectie.kopniveau,
                    "ouder_id": sectie.ouder_id,
                    "koplocatie": asdict(sectie.koplocatie) if sectie.koplocatie else None,
                    "element_ids": sectie.element_ids,
                }
                for sectie in self.sections
            ],
            "elementen": elementen,
        }
        tijdelijk_pad = None
        try:
            with NamedTemporaryFile("w", encoding="utf-8", dir=export_map, suffix=".tmp", delete=False) as uitvoer:
                tijdelijk_pad = Path(uitvoer.name)
                json.dump(manifest, uitvoer, ensure_ascii=False, indent=2, allow_nan=False)
            doel = export_map / "structuur.json"
            tijdelijk_pad.replace(doel)
            return doel
        finally:
            if tijdelijk_pad is not None:
                tijdelijk_pad.unlink(missing_ok=True)

    @classmethod
    def _lees_structuur(cls, manifest_pad: Path, verwachte_vingerafdruk: str) -> SmartDocument:
        """Herstel een gevalideerde eigen JSON-cache zonder PDF-extractie.

        Parameters
        ----------
        manifest_pad : Path
            Manifest met uitsluitend bundelrelatieve PNG-paden.
        verwachte_vingerafdruk : str
            Identiteit van de gevraagde bron en huidige parserconfiguratie.

        Returns
        -------
        SmartDocument
            Eigen elementen met herstelde canonieke sectieverwijzingen.

        Raises
        ------
        ValueError
            Bij een verkeerde versie, identiteit, structuur of ongeldige asset.
        """
        gegevens = json.loads(manifest_pad.read_text(encoding="utf-8"))
        if not isinstance(gegevens, dict) or gegevens.get("schema_versie") != STRUCTUUR_SCHEMA_VERSIE:
            raise ValueError("Onbekend structuur-JSON-schema.")
        document = cls(
            document_name=gegevens["document_naam"],
            bron_bestandsnaam=gegevens["bron_bestandsnaam"],
            bron_hash=gegevens["bron_hash"],
            extractie_metadata=gegevens["extractie"],
            pagina_afmetingen={
                pagina["nummer"]: (pagina["breedte"], pagina["hoogte"]) for pagina in gegevens["paginas"]
            },
            bookmarks=[tuple(bookmark) for bookmark in gegevens["bookmarks"]],
        )
        if (
            not verwachte_vingerafdruk
            or document.documentvingerafdruk != verwachte_vingerafdruk
            or gegevens["documentvingerafdruk"] != verwachte_vingerafdruk
        ):
            raise ValueError("Documentvingerafdruk komt niet overeen.")
        if not document.pagina_afmetingen or not gegevens["elementen"] or not gegevens["secties"]:
            raise ValueError("Onvolledige documentcache.")

        elementen = {}
        for opgeslagen in gegevens["elementen"]:
            velden = dict(opgeslagen)
            soort = velden.pop("soort")
            locaties = tuple(
                BronLocatie(locatie["pagina"], tuple(locatie["bbox"])) for locatie in velden["bronlocaties"]
            )
            velden["bronlocaties"] = locaties
            if soort == "paragraaf":
                element = Paragraaf(**velden)
                if not isinstance(element.content, str):
                    raise ValueError("Ongeldige paragraaftekst in documentcache.")
            elif soort == "tabel":
                cellen = []
                for opgeslagen_cel in velden["cells"]:
                    cel = dict(opgeslagen_cel)
                    cel["bronlocaties"] = tuple(
                        BronLocatie(locatie["pagina"], tuple(locatie["bbox"])) for locatie in cel["bronlocaties"]
                    )
                    cellen.append(TabelCel(**cel))
                velden["cells"] = tuple(cellen)
                element = DocumentTabel(**velden)
                if element.row_count < 0 or element.column_count < 0 or any(
                    cel.row_index < 0
                    or cel.column_index < 0
                    or cel.row_span < 1
                    or cel.column_span < 1
                    or cel.row_index + cel.row_span > element.row_count
                    or cel.column_index + cel.column_span > element.column_count
                    for cel in element.cells
                ):
                    raise ValueError("Ongeldig tabelraster in documentcache.")
            elif soort == "afbeelding":
                relatief = Path(velden["bestand"])
                bestand = (manifest_pad.parent / relatief).resolve()
                if (
                    relatief.drive
                    or ".." in relatief.parts
                    or not bestand.is_relative_to(manifest_pad.parent.resolve())
                ):
                    raise ValueError("Figuurasset valt buiten de structuurbundel.")
                cls._controleer_png(bestand)
                if sha256(bestand.read_bytes()).hexdigest() != velden.pop("asset_hash"):
                    raise ValueError("Figuurasset heeft een andere inhoud.")
                velden["bestand"] = bestand
                element = Afbeelding(**velden)
            else:
                raise ValueError(f"Onbekend documentelement: {soort}")
            if not isinstance(element.id, str) or not element.id or element.id in elementen:
                raise ValueError("Ongeldige of dubbele element-ID in documentcache.")
            elementen[element.id] = element

        sectie_ids = set()
        toegewezen = set()
        for opgeslagen in gegevens["secties"]:
            velden = dict(opgeslagen)
            if not velden["id"] or velden["id"] in sectie_ids:
                raise ValueError("Lege of dubbele sectie-ID in documentcache.")
            if velden["ouder_id"] is not None and velden["ouder_id"] not in sectie_ids:
                raise ValueError("Een sectie moet na zijn bestaande ouder komen.")
            locatie = velden["koplocatie"]
            velden["koplocatie"] = BronLocatie(locatie["pagina"], tuple(locatie["bbox"])) if locatie else None
            verwijzingen = velden.pop("element_ids")
            sectie = Sectie(**velden)
            document.sections.append(sectie)
            sectie_ids.add(sectie.id)
            for element_id in verwijzingen:
                if element_id in toegewezen or element_id not in elementen:
                    raise ValueError("Ongeldige of dubbele sectie-elementverwijzing.")
                document.registreer_element(sectie, elementen[element_id])
                toegewezen.add(element_id)
        if toegewezen != set(elementen) or any(
            sectie.ouder_id is not None and sectie.ouder_id not in sectie_ids for sectie in document.sections
        ):
            raise ValueError("Onvolledige document- of sectieverwijzingen.")
        # Sectiegroepering mag de oorspronkelijke documentbrede elementvolgorde niet veranderen.
        document.elementen.clear()
        document.elementen.update(elementen)
        for element in document.elementen.values():
            if isinstance(element, Afbeelding) and element.bijschrift_id is not None:
                bijschrift = document.elementen.get(element.bijschrift_id)
                if not isinstance(bijschrift, Paragraaf):
                    raise ValueError("Ongeldige figuur-bijschriftverwijzing.")
        return document

    def __setstate__(self, toestand: dict[str, object]) -> None:
        """Herstel een document uit een bestaande, vertrouwde lokale fixture.

        Parameters
        ----------
        toestand : dict[str, object]
            Opgeslagen velden, eventueel zonder de nieuwe elementregistratie.
        """
        self.__dict__.update(toestand)
        self.__dict__.setdefault("elementen", {})
        self.__dict__.setdefault("pagina_afmetingen", {})
        self.__dict__.setdefault("bookmarks", [])
        self.__dict__.setdefault("extractie_metadata", {})

    def registreer_element(self, sectie: Sectie, element: Paragraaf | DocumentTabel | Afbeelding) -> None:
        """Registreer een element eenmaal en koppel het in sectieleesvolgorde.

        Parameters
        ----------
        sectie : Sectie
            De sectie binnen dit document waaraan het element toebehoort.
        element : Paragraaf | DocumentTabel | Afbeelding
            Element met een niet-lege, documentgebonden identificatie.

        Raises
        ------
        ValueError
            Als het element geen unieke ID heeft of de sectie niet bij dit document hoort.
        """
        if not element.id or element.id in self.elementen:
            raise ValueError(f"Element-ID is leeg of al geregistreerd: {element.id!r}")
        if not any(bestaande_sectie is sectie for bestaande_sectie in self.sections):
            raise ValueError("De sectie hoort niet bij dit document.")

        self.elementen[element.id] = element
        sectie.element_ids.append(element.id)
        sectie._elementen = self.elementen

    def get_elementen(self, sectie: Sectie) -> tuple[Paragraaf | DocumentTabel | Afbeelding, ...]:
        """Geef sectie-elementen zonder een tweede muteerbare verzameling op te bouwen.

        Parameters
        ----------
        sectie : Sectie
            Sectie waarvan de elementverwijzingen worden gevolgd.

        Returns
        -------
        tuple[Paragraaf | DocumentTabel | Afbeelding, ...]
            De geregistreerde objecten in de oorspronkelijke sectievolgorde.

        Raises
        ------
        ValueError
            Als de sectie niet bij dit document hoort.
        KeyError
            Als een sectieverwijzing geen geregistreerd element aanwijst.
        """
        if not any(bestaande_sectie is sectie for bestaande_sectie in self.sections):
            raise ValueError("De sectie hoort niet bij dit document.")
        return tuple(self.elementen[element_id] for element_id in sectie.element_ids)

    @classmethod
    def from_pdf(cls, pdf_path: Path, use_cache: bool = True) -> SmartDocument:
        """Lees native PDF-tekst en structuur lokaal, zonder OCR of cloudfallback.

        Parameters
        ----------
        pdf_path : Path
            Pad naar een PDF met bestaande selecteerbare tekst.
        use_cache : bool
            Lees een geldige bron- en configuratiegebonden JSON-cache indien beschikbaar.
            False slaat alleen cachelezen over; het nieuwe resultaat wordt wel opgeslagen.
            Oude Azure-caches worden nooit hergebruikt of verwijderd.

        Returns
        -------
        SmartDocument
            Eigen documentelementen zonder levende PDF-objecten.

        Raises
        ------
        ValueError
            Bij een onleesbare, versleutelde PDF of ontbrekende native tekst.
        """
        pdf_path = Path(pdf_path)
        inhoud = pdf_path.read_bytes()
        document = cls(
            document_name=pdf_path.stem,
            bron_bestandsnaam=pdf_path.name,
            bron_hash=sha256(inhoud).hexdigest(),
            extractie_metadata=cls._extractie_configuratie(),
        )
        asset_map = constants.CACHE_DIR / "pymupdf_extractie" / document.documentvingerafdruk
        manifest_pad = asset_map / "structuur.json"
        if use_cache and manifest_pad.is_file():
            try:
                hersteld = cls._lees_structuur(manifest_pad, document.documentvingerafdruk)
            except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError) as fout:
                logger.warning("Documentcache ongeldig; opnieuw lokaal extraheren: %s", fout)
            else:
                # Dezelfde PDF-inhoud onder een andere naam deelt extractie, niet zijn documentnaam.
                hersteld.document_name = pdf_path.stem
                hersteld.bron_bestandsnaam = pdf_path.name
                return hersteld

        # Een manifest mag geen half vernieuwde assetverzameling geldig verklaren.
        manifest_pad.unlink(missing_ok=True)
        try:
            pdf = pymupdf.open(stream=inhoud, filetype="pdf")
        except (pymupdf.FileDataError, pymupdf.EmptyFileError) as fout:
            raise ValueError(f"Onleesbare PDF: {pdf_path.name}") from fout

        with pdf:
            if pdf.needs_pass:
                raise ValueError(f"Versleutelde PDF vereist een wachtwoord: {pdf_path.name}")
            if not any(pagina.get_text().strip() for pagina in pdf):
                raise ValueError(f"PDF bevat geen selecteerbare tekst; OCR is uitgeschakeld: {pdf_path.name}")

            document.bookmarks = [tuple(bookmark) for bookmark in pdf.get_toc()]
            asset_map.mkdir(parents=True, exist_ok=True)
            native_tabellen = {}
            native_regels = {}
            for pagina in pdf:
                # Dezelfde geometrie voor native gegevens en layout, ook bij geroteerde invoer.
                pagina.remove_rotation()
                nummer = pagina.number + 1
                document.pagina_afmetingen[nummer] = (pagina.rect.width, pagina.rect.height)
                native_regels[nummer] = [
                    regel
                    for blok in pagina.get_text("dict", sort=True)["blocks"]
                    for regel in blok.get("lines", [])
                ]
                if not native_regels[nummer]:
                    logger.warning("Pagina %s van %s bevat geen native tekst; OCR blijft uit.", nummer, pdf_path.name)
                native_tabellen[nummer] = [
                    DocumentTabel.from_pymupdf(tabel, nummer, f"{document.bron_hash[:12]}-p{nummer}-t{index}")
                    for index, tabel in enumerate(pagina.find_tables(use_layout=False).tables)
                ]

            # Tijdelijke renders verdwijnen; alleen gevalideerde, gerefereerde PNG's blijven in de cache.
            with TemporaryDirectory(dir=asset_map) as render_map:
                # use_ocr=False voorkomt ook automatische OCR op figuren en beeldpagina's.
                layout = json.loads(
                    pdf.to_json(
                        use_ocr=False,
                        force_text=True,
                        write_images=True,
                        embed_images=False,
                        image_format="png",
                        image_dpi=document.extractie_metadata["image_dpi"],
                        image_path=render_map,
                    )
                )
                elementen = document._lees_layout(layout, native_tabellen, native_regels)
                document._parse_document(elementen)
                document.exporteer_structuur(asset_map)
        return cls._lees_structuur(manifest_pad, document.documentvingerafdruk)

    def _lees_layout(
        self, layout: dict, native_tabellen: dict[int, list[DocumentTabel]], native_regels: dict[int, list[dict]]
    ) -> list[Paragraaf | DocumentTabel | Afbeelding]:
        """Koppel native inhoud aan de leesvolgorde van de layoutboxen.

        Parameters
        ----------
        layout : dict
            Gestructureerde JSON-uitvoer van PyMuPDF.
        native_tabellen, native_regels : dict
            Voor layoutnabewerking gekopieerde brongegevens per pagina.

        Returns
        -------
        list[Paragraaf | DocumentTabel | Afbeelding]
            Gededupliceerde elementen met brongebieden en documentleesvolgorde.
        """
        elementen = []
        kopteksten = Counter(
            " ".join(
                span["text"]
                for regel in (blok.get("textlines") or [])
                for span in regel["spans"]
            ).strip()
            for pagina in layout["pages"]
            for blok in pagina["boxes"]
            if blok["boxclass"] in {"page-header", "page-footer"}
        )
        for pagina in layout["pages"]:
            nummer = pagina["page_number"]
            boxen = pagina["boxes"]
            gebieden = [pymupdf.Rect(*(blok[naam] for naam in ("x0", "y0", "x1", "y1"))) for blok in boxen]
            tabellen_per_blok = {}
            for tabel in native_tabellen[nummer]:
                gebied = pymupdf.Rect(tabel.bronlocaties[0].bbox)
                kandidaten = [
                    index
                    for index, blok in enumerate(boxen)
                    if blok["boxclass"] == "table" and gebieden[index].intersects(gebied)
                ]
                if kandidaten:
                    anker = max(kandidaten, key=lambda index: (gebieden[index] & gebied).get_area())
                else:
                    anker = next((index for index, box in enumerate(gebieden) if box.y0 >= gebied.y0), len(boxen))
                    logger.warning(
                        "Native tabel op pagina %s zonder layouttabel; bronsegment blijft behouden.", nummer
                    )
                tabellen_per_blok.setdefault(anker, []).append(tabel)

            gebruikte_regels = set()
            for index in range(len(boxen) + 1):
                for tabel in tabellen_per_blok.get(index, ()):
                    elementen.append(replace(tabel, leesvolgorde=len(elementen)))
                if index == len(boxen):
                    continue
                blok = boxen[index]
                gebied = gebieden[index]
                rol = blok["boxclass"]
                identiteit = f"{self.bron_hash[:12]}-p{nummer}-b{index}"
                locatie = BronLocatie(nummer, tuple(gebied))
                if rol == "picture":
                    afbeelding_pad = Path(blok["image"])
                    if not afbeelding_pad.is_file():
                        raise ValueError(f"Figuurasset ontbreekt: {afbeelding_pad}")
                    elementen.append(Afbeelding(identiteit, afbeelding_pad, (locatie,), len(elementen)))

                regels = []
                for regel_index, regel in enumerate(native_regels[nummer]):
                    regelgebied = pymupdf.Rect(regel["bbox"])
                    middelpunt = (regelgebied.tl + regelgebied.br) / 2
                    in_tabel = any(
                        pymupdf.Rect(tabel.bronlocaties[0].bbox).contains(middelpunt)
                        for tabel in native_tabellen[nummer]
                    )
                    if regel_index not in gebruikte_regels and gebied.contains(middelpunt) and not in_tabel:
                        regels.append("".join(span["text"] for span in regel["spans"]))
                        gebruikte_regels.add(regel_index)
                if regels:
                    tekst = "\n".join(regels)
                    tekstrol = "text" if rol == "picture" else rol
                    if re.match(r"(?i)^figuur\s+\d+(?:\.\d+)*\s*:", tekst.strip()):
                        tekstrol = "caption"
                    if rol in {"page-header", "page-footer"}:
                        koptekst = " ".join(
                            span["text"] for regel in (blok.get("textlines") or []) for span in regel["spans"]
                        ).strip()
                        # Een eenmalige vervolgalinea bovenaan een pagina is niet noodzakelijk een paginakop.
                        if kopteksten[koptekst] < 2 and not re.fullmatch(r"\d+(?:\s*(?:/|van)\s*\d+)?", tekst.strip()):
                            tekstrol = "text"
                    elementen.append(Paragraaf(tekst, identiteit + "-tekst", len(elementen), (locatie,), tekstrol))

            # Niet-geclassificeerde native tekst mag niet stil verdwijnen bij een layoutmisser.
            aantal_restregels = 0
            for regel_index, regel in enumerate(native_regels[nummer]):
                middelpunt = (pymupdf.Rect(regel["bbox"]).tl + pymupdf.Rect(regel["bbox"]).br) / 2
                if regel_index in gebruikte_regels or any(
                    pymupdf.Rect(tabel.bronlocaties[0].bbox).contains(middelpunt)
                    for tabel in native_tabellen[nummer]
                ):
                    continue
                restgebied = pymupdf.Rect(regel["bbox"])
                anker = next(
                    (
                        index
                        for index, bestaand in enumerate(elementen)
                        if bestaand.bronlocaties[0].pagina == nummer
                        and bestaand.bronlocaties[0].bbox[1] >= restgebied.y0
                        and bestaand.bronlocaties[0].bbox[0] < restgebied.x1
                        and bestaand.bronlocaties[0].bbox[2] > restgebied.x0
                    ),
                    len(elementen),
                )
                elementen.insert(
                    anker,
                    Paragraaf(
                        "".join(span["text"] for span in regel["spans"]),
                        f"{self.bron_hash[:12]}-p{nummer}-rest{regel_index}",
                        bronlocaties=(BronLocatie(nummer, tuple(restgebied)),),
                    ),
                )
                aantal_restregels += 1
            if aantal_restregels:
                logger.warning(
                    "%s native regels op pagina %s zonder layoutbox; in hun bronkolom bewaard.",
                    aantal_restregels,
                    nummer,
                )
        return [replace(element, leesvolgorde=index) for index, element in enumerate(elementen)]

    def get_rakdeel_secties(self) -> list[RakdeelSectie]:
        """Haal de secties op die rakdelen beschrijven.

        Returns
        -------
        list[RakdeelSectie]
            Lijst van rakdeel secties met constructie informatie.
        """
        rakdeel_secties = []
        for i, sectie in enumerate(self.sections):
            if get_constructienaam(sectie.titel):
                einde = next(
                    (
                        index
                        for index in range(i + 1, len(self.sections))
                        if get_constructienaam(self.sections[index].titel)
                        or self.sections[index].kopniveau < sectie.kopniveau
                    ),
                    len(self.sections),
                )
                rakdeel_secties.append(RakdeelSectie.from_smart_document(self.sections[i:einde]))
        return rakdeel_secties

    def get_meettabel_houtmonsters(self) -> StructuredTable | None:
        """Haal de meettabel voor houtmonsters op.

        Returns
        -------
        StructuredTable | None
            Gestructureerde tabelinhoud met houtmonster metingen.
        """
        for sectie in self.sections:
            if "meettabel houtmonsters" in sectie.titel.lower() and sectie.tabellen:
                table = StructuredTable.from_doc_table(sectie.tabellen, table_type=TableType.HOUTMONSTERS)
                if table:
                    return table

        return None

    def get_meettabel_fundering_paal(self) -> StructuredTable | None:
        """Haal de meettabel voor palen op.

        Returns
        -------
        StructuredTable | None
            Gestructureerde tabelinhoud waar >50% van eerste kolom een geldig paal ID bevat.
        """
        for sectie in self.sections:
            if "meettabel fundering" in sectie.titel.lower() and sectie.tabellen:

                table = StructuredTable.from_doc_table(sectie.tabellen, table_type=TableType.PALEN)
                if table:
                    return table
        return None

    def get_meettabel_fundering_kesp(self) -> StructuredTable | None:
        """Haal de meettabel voor kespen op.

        Returns
        -------
        StructuredTable | None
            Tabelinhoud waar >50% van eerste kolom een geldig kesp ID bevat.
        """
        for sectie in self.sections:
            if "meettabel fundering" in sectie.titel.lower() and sectie.tabellen:
                table = StructuredTable.from_doc_table(sectie.tabellen, table_type=TableType.KESPEN)
                if table:
                    return table

        return None

    def get_raknaam(self) -> str:
        for tabel in self.sections[0].tabellen if self.sections else ():
            if tabel.column_count == 2:
                for cell in tabel.cells:
                    if get_rak_id(cell.content):
                        return get_rak_id(cell.content) or cell.content.strip()

        # Fallback: try to extract from PDF name
        logger.warning(f"Could not find Rak ID in tables, trying to extract from PDF name...")
        raknaam_from_pdf = self._get_raknaam_from_pdf_name()
        if raknaam_from_pdf:
            return raknaam_from_pdf

        logger.warning(f"Could not extract Rak ID from PDF name, returning {constants.ONBEKEND_RAK_NAAM} as fallback")

        return constants.ONBEKEND_RAK_NAAM

    def _get_raknaam_from_pdf_name(self) -> str | None:
        """Try to extract the Rak ID from the PDF name"""

        doc_name = self.document_name.replace(".pdf", "")
        rak_id = get_rak_id(doc_name)
        if rak_id:
            return rak_id

        return None

    def _parse_document(self, elementen: list[Paragraaf | DocumentTabel | Afbeelding]) -> None:
        """Wijs de elementstroom aan de meest specifieke actieve sectie toe.

        Parameters
        ----------
        elementen : list[Paragraaf | DocumentTabel | Afbeelding]
            Native inhoud in layoutleesvolgorde, niet in ruwe PDF-streamvolgorde.
        """
        huidige_sectie = None
        ouders = []
        for element in elementen:
            if isinstance(element, Paragraaf) and self._is_section_start(element, huidige_sectie):
                huidige_sectie = self._start_new_section(element, huidige_sectie)
                while ouders and ouders[-1].kopniveau >= huidige_sectie.kopniveau:
                    ouders.pop()
                huidige_sectie.ouder_id = ouders[-1].id if ouders else None
                ouders.append(huidige_sectie)
                continue
            if huidige_sectie is None:
                huidige_sectie = Sectie("Introductie", id=f"{self.bron_hash[:12]}-intro", kopniveau=0)
                self.sections.append(huidige_sectie)
            self.registreer_element(huidige_sectie, element)
            if (
                isinstance(element, Paragraaf)
                and element.rol == "caption"
                and not re.match(r"(?i)^tabel\s", element.content.strip())
            ):
                bijschriftgebied = pymupdf.Rect(element.bronlocaties[0].bbox)
                kandidaten = [
                    afbeelding
                    for afbeelding in huidige_sectie.afbeeldingen
                    if afbeelding.bijschrift_id is None
                    and afbeelding.bronlocaties[0].pagina == element.bronlocaties[0].pagina
                    and 0 <= bijschriftgebied.y0 - afbeelding.bronlocaties[0].bbox[3] < 40
                    and afbeelding.bronlocaties[0].bbox[0] < bijschriftgebied.x1
                    and afbeelding.bronlocaties[0].bbox[2] > bijschriftgebied.x0
                ]
                if len(kandidaten) == 1:
                    afbeelding = kandidaten[0]
                    self.elementen[afbeelding.id] = replace(afbeelding, bijschrift_id=element.id)

    def _is_section_start(self, paragraph: Paragraaf, current_section: Sectie | None) -> bool:
        """Herken daadwerkelijke koppen zonder een gedrukte inhoudsopgave te verwarren.

        Parameters
        ----------
        paragraph : Paragraaf
            Native tekst met layoutrol en bronlocatie.
        current_section : Sectie | None
            Huidige sectie; behouden als lokale parseraanroepvorm.

        Returns
        -------
        bool
            Of deze tekst een nieuwe sectie opent.
        """
        titel = " ".join(paragraph.content.split())
        if not titel or len(titel) > 180 or re.search(r"\.{3,}", titel):
            return False
        if paragraph.rol in {"page-header", "page-footer", "caption", "footnote"}:
            return False
        if re.match(r"(?i)^(?:tabel|figuur)\s+\d+(?:\.\d+)*\s*[:.]", titel):
            return False
        if current_section is not None and current_section.titel.casefold() == "inhoudsopgave":
            if not re.match(r"^\d+(?:\.\d+)*\.?\s+", titel):
                return False
        if re.match(r"(?i)^bijlage\s+\d+\b", titel):
            return True
        if paragraph.rol == "section-header":
            return True
        return any(
            pagina == paragraph.bronlocaties[0].pagina and titel.casefold() == bookmark.casefold()
            for niveau, bookmark, pagina in self.bookmarks
        )

    def _start_new_section(self, paragraph: Paragraaf, current_section: Sectie | None) -> Sectie:
        """Maak een sectie met native koplocatie en reproduceerbaar kopniveau.

        Parameters
        ----------
        paragraph : Paragraaf
            De koptekst en zijn brongebied.
        current_section : Sectie | None
            De voorgaande sectie, zonder mutatie van zijn inhoud.

        Returns
        -------
        Sectie
            Nieuwe sectie in de platte documentleesvolgorde.
        """
        titel = " ".join(paragraph.content.split())
        nummering = re.match(r"^(\d+(?:\.\d+)*)\.?\s+", titel)
        niveau = len(nummering[1].split(".")) if nummering else 1
        for bookmark_niveau, bookmark, pagina in self.bookmarks:
            if pagina == paragraph.bronlocaties[0].pagina and titel.casefold() == bookmark.casefold():
                niveau = bookmark_niveau
                break
        sectie = Sectie(
            titel,
            id=f"{self.bron_hash[:12]}-s{len(self.sections)}",
            kopniveau=niveau,
            koplocatie=paragraph.bronlocaties[0],
        )
        self.sections.append(sectie)
        return sectie


if __name__ == "__main__":
    TEST_PDF_PATH = DATA_DIR / "HEG0801_Houtmonstername&VisueleInspectie_V1.1_20220311.pdf"

    doc = SmartDocument.from_pdf(TEST_PDF_PATH)
    print(doc)
    print("\n" + "=" * 80 + "\n")

    for i, sectie in enumerate(doc.sections[:5]):
        print(f"\n[{i+1}] {sectie.titel}")
        print("-" * 60)
        for j, paragraph in enumerate(sectie.inhoud[:3]):
            print(f"  Paragraaf {j+1}: {paragraph.content[:100]}...")
        if len(sectie.inhoud) > 3:
            print(f"  ... en nog {len(sectie.inhoud) - 3} paragrafen")
