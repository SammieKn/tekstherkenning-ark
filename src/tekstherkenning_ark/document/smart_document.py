from __future__ import annotations
from dataclasses import dataclass, field
import os
from pathlib import Path
import pickle
from typing import Callable


from tekstherkenning_ark import constants
from tekstherkenning_ark.constants import DATA_DIR
from tekstherkenning_ark.utils import (
    get_constructienaam,
    get_paal_id,
    get_kesp_id,
    get_rak_id,
    get_table_content,
    remove_titel_rows,
    remove_invalid_rows,
)
from tekstherkenning_ark.document.sectie import Sectie
from tekstherkenning_ark.document.rakdeelsectie import RakdeelSectie
from azure.ai.documentintelligence.models import AnalyzeResult, DocumentTable, DocumentParagraph
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from io import BytesIO

from dotenv import load_dotenv
from tekstherkenning_ark.logger import get_logger
import re

load_dotenv()

logger = get_logger(__name__)


@dataclass
class SmartDocument:
    """Smart document parser voor Azure Document Intelligence results.

    Attributes
    ----------
    pdf_path : Path
        Pad naar het geanalyseerde PDF document.
    sections : list[Sectie]
        Lijst van alle secties in het document.
    analyze_result : AnalyzeResult
        Het originele Azure Document Intelligence analyze result.
    """

    pdf_path: Path
    analyze_result: AnalyzeResult
    sections: list[Sectie] = field(default_factory=list)

    @classmethod
    def from_pdf(cls, pdf_path: Path, use_cache: bool = True) -> SmartDocument:
        """Create a SmartDocument instance from a PDF file.

        Uses cached pickle file if available and use_cache is True,
        otherwise analyzes the PDF using Azure Document Intelligence.

        Args:
            pdf_path: Path to the PDF file to analyze
            use_cache: Whether to use cached results if available

        Returns:
            SmartDocument instance containing the analysis results
        """

        # Determine cache file path based on PDF name
        cache_file = constants.CACHE_DIR / f"{pdf_path.stem}_docai_result.pkl"

        # Try to load from cache
        if use_cache and cache_file.exists():
            logger.info(f"Loading from cache: {cache_file.name}")
            result = pickle.loads(cache_file.read_bytes())
        else:
            # Load environment variables
            doc_ai_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
            doc_ai_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

            if not doc_ai_endpoint or not doc_ai_key:
                raise ValueError("Azure credentials not found in .env file")

            # Initialize Azure Document Intelligence client
            client = DocumentIntelligenceClient(endpoint=doc_ai_endpoint, credential=AzureKeyCredential(doc_ai_key))

            # Read and analyze the document
            logger.info(f"Analyzing document with Azure Document Intelligence...")
            document_bytes = BytesIO(pdf_path.read_bytes())

            poller = client.begin_analyze_document("prebuilt-layout", document_bytes, content_type="application/pdf")
            result = poller.result()

            # Cache the result
            cache_file.write_bytes(pickle.dumps(result))
            logger.info(f"Results cached to: {cache_file.name}")

        doc = cls(analyze_result=result, pdf_path=pdf_path)
        doc._parse_document()
        return doc

    def _get_table_min_offset(self, table: DocumentTable) -> int:
        """Bepaal de minimale offset van een tabel."""
        if not table.cells:
            return 0

        min_offset = min(cell.spans[0].offset for cell in table.cells if cell.spans)
        return min_offset

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
                rakdeel_secties.append(RakdeelSectie.from_smart_document(self.sections[i:]))
        return rakdeel_secties

    def get_meettabel_houtmonsters(self) -> list[list[str]]:
        """Haal de meettabel voor houtmonsters op.

        Returns
        -------
        list[list[str]]
            Tabelinhoud met houtmonster metingen.
        """
        for sectie in self.sections:
            if "meettabel houtmonsters" in sectie.titel.lower() and sectie.tabellen:
                rows: list[list[str]] = []
                for tabel in sectie.tabellen:
                    rows.extend(get_table_content(tabel))
                rows_wo_header = remove_titel_rows(rows)
                rows_valid = remove_invalid_rows(rows_wo_header)
                rows_cleaned = [
                    row for row in rows_valid if all(x not in row[0].lower() for x in ["meettabel", "[rak]"])
                ]
                return rows_cleaned
        return []

    def get_meettabel_fundering_paal(self) -> list[list[str]]:
        """Haal de meettabel voor palen op.

        Returns
        -------
        list[list[str]]
            Tabelinhoud waar >50% van eerste kolom een geldig paal ID bevat.
        """
        for sectie in self.sections:
            if "meettabel fundering" in sectie.titel.lower() and sectie.tabellen:
                rows: list[list[str]] = []
                for tabel in sectie.tabellen:
                    if self._is_table_type_by_id_func(tabel, get_paal_id):
                        rows.extend(get_table_content(tabel))
                rows_wo_header = remove_titel_rows(rows)
                rows_valid = remove_invalid_rows(rows_wo_header)
                rows_cleaned = [
                    row for row in rows_valid if all(x not in row[0].lower() for x in ["meettabel", "[rak]"])
                ]
                return rows_cleaned
        return []

    def get_meettabel_fundering_kesp(self) -> list[list[str]]:
        """Haal de meettabel voor kespen op.

        Returns
        -------
        list[list[str]]
            Tabelinhoud waar >50% van eerste kolom een geldig kesp ID bevat.
        """
        for sectie in self.sections:
            if "meettabel fundering" in sectie.titel.lower() and sectie.tabellen:
                rows: list[list[str]] = []
                for tabel in sectie.tabellen:
                    if self._is_table_type_by_id_func(tabel, get_kesp_id):
                        rows.extend(get_table_content(tabel))
                rows_wo_header = remove_titel_rows(rows)
                rows_cleaned = remove_invalid_rows(rows_wo_header)
                return rows_cleaned
        return []

    def get_raknaam(self) -> str:
        for tabel in self.sections[0].tabellen:
            if tabel.column_count == 2:
                for cell in tabel.cells:
                    if get_rak_id(cell.content):
                        return get_rak_id(cell.content) or cell.content.strip()
        return "Onbekend Rak"

    def _parse_document(self) -> None:
        """Parse het AnalyzeResult en splits het op in secties."""

        if self.analyze_result.paragraphs is None:
            return

        current_section = None
        intro_paragraphs = []

        paragraphs = [
            p
            for p in self.analyze_result.paragraphs
            if p.role not in ["pageHeader", "pageFooter", "pageNumber", "title", "footnote", "formulaBlock"]
        ]

        for paragraph in paragraphs:
            if self._is_section_start(paragraph, current_section):
                current_section = self._start_new_section(paragraph, current_section)
            elif current_section is not None:
                current_section.inhoud.append(paragraph)
            else:
                intro_paragraphs.append(paragraph)

        if current_section:
            self.sections.append(current_section)

        if intro_paragraphs:
            intro_section = Sectie(titel="Introductie", inhoud=intro_paragraphs)
            self.sections.insert(0, intro_section)

        self._assign_tables_to_sections()

    def _is_section_start(self, paragraph: DocumentParagraph, current_section: Sectie | None) -> bool:
        """Bepaal of een paragraaf een nieuwe sectie start."""
        if paragraph.role == "sectionHeading" and paragraph.content.strip() and paragraph.content.strip()[0].isdigit():
            return True
        if paragraph.content.startswith("Bijlage "):
            return current_section is not None and not current_section.titel.startswith("Introductie")
        return False

    def _start_new_section(self, paragraph: DocumentParagraph, current_section: Sectie | None) -> Sectie:
        """Start een nieuwe sectie en voeg de vorige toe aan de lijst."""
        if current_section:
            self.sections.append(current_section)

        offset = paragraph.spans[0].offset if paragraph.spans else 0
        return Sectie(titel=paragraph.content, heading_offset=offset)

    def _assign_tables_to_sections(self) -> None:
        """Wijs tabellen toe aan secties op basis van hun offset."""
        tables = self.analyze_result.tables or []

        for table in tables:
            min_offset = self._get_table_min_offset(table)

            assigned = False
            for i, sectie in enumerate(self.sections):
                next_offset = self.sections[i + 1].heading_offset if i + 1 < len(self.sections) else float("inf")

                if sectie.heading_offset <= min_offset < next_offset:
                    sectie.tabellen.append(table)
                    assigned = True
                    break

            if not assigned and self.sections:
                self.sections[-1].tabellen.append(table)

    def _is_table_type_by_id_func(
        self, tabel: DocumentTable, id_func: Callable[[str], str | None], threshold: float = 0.5
    ) -> bool:
        """Check of een tabel bij een type hoort op basis van een ID-extractie functie.

        Parameters
        ----------
        tabel : DocumentTable
            De tabel om te controleren.
        id_func : callable
            Functie die een string neemt en een ID of None teruggeeft (bijv. get_paal_id).
        threshold : float
            Minimale fractie van cellen die moeten matchen.

        Returns
        -------
        bool
            True als de tabel voldoet aan het type.
        """
        if not tabel.cells:
            return False

        first_col_cells = [cell.content for cell in tabel.cells if cell.column_index == 0]
        if not first_col_cells:
            return False

        matching_cells = sum(1 for cell in first_col_cells if id_func(cell) is not None)
        return (matching_cells / len(first_col_cells)) > threshold

    def __repr__(self) -> str:
        section_summary = "\n".join(
            [f"  - {s.titel} ({len(s.inhoud)} paragrafen, {len(s.tabellen)} tabellen)" for s in self.sections]
        )
        return f"SmartDocument met {len(self.sections)} secties:\n{section_summary}"


if __name__ == "__main__":
    TEST_PDF_PATH = DATA_DIR / "HEG0801_Houtmonstername&VisueleInspectie_V1.1_20220311.pdf"

    doc = SmartDocument.from_pdf(TEST_PDF_PATH)
    print(doc)
    print("\n" + "=" * 80 + "\n")

    for i, sectie in enumerate(doc.sections[:5]):
        print(f"\n[{i+1}] {sectie.titel}")
        print("-" * 60)
        for j, paragraph in enumerate(sectie.inhoud[:3]):
            offset = paragraph.spans[0].offset if paragraph.spans else 0
            print(f"  Paragraaf {j+1} (offset {offset}): {paragraph.content[:100]}...")
        if len(sectie.inhoud) > 3:
            print(f"  ... en nog {len(sectie.inhoud) - 3} paragrafen")
