from dataclasses import dataclass, field
import pickle

from tekstherkenning_ark.constants import DATA_DIR
from azure.ai.documentintelligence.models import AnalyzeResult, DocumentTable, DocumentParagraph

result = pickle.load(open(DATA_DIR / ".cache" / "HEG0801_Houtmonstername&VisueleInspectie_V1.1_20220311_cache.pkl", "rb"))


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
    
@dataclass
class RakdeelSectie:
    """Representeert een rakdeel sectie met constructie informatie.
    
    Attributes
    ----------
    constructie_naam : str
        Naam van de constructie.
    beschrijving : list[DocumentParagraph]
        Beschrijvende paragrafen.
    toestand_tabel : list[DocumentTable]
        Tabellen met toestandsinformatie.
    gebreken_tabel : list[DocumentTable]
        Tabellen met gebrekeninformatie.
    """
    constructie_naam: str
    beschrijving: list[DocumentParagraph]
    toestand_tabel: list[DocumentTable]
    gebreken_tabel: list[DocumentTable]
    

class SmartDocument:
    """Smart document parser voor Azure Document Intelligence results.
    
    Attributes
    ----------
    sections : list[Sectie]
        Lijst van alle secties in het document.
    analyze_result : AnalyzeResult
        Het originele Azure Document Intelligence analyze result.
    """
    
    def __init__(self, analyze_result: AnalyzeResult) -> None:
        self.sections: list[Sectie] = []
        self.analyze_result: AnalyzeResult = analyze_result
        self._parse_document()
    
    def _parse_document(self) -> None:
        """Parse het AnalyzeResult en splits het op in secties."""
        if self.analyze_result.paragraphs is None:
            return
        
        current_section = None
        intro_paragraphs = []
        
        paragraphs = [
            p for p in self.analyze_result.paragraphs 
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
                next_offset = self.sections[i + 1].heading_offset if i + 1 < len(self.sections) else float('inf')
                
                if sectie.heading_offset <= min_offset < next_offset:
                    sectie.tabellen.append(table)
                    assigned = True
                    break
            
            if not assigned and self.sections:
                self.sections[-1].tabellen.append(table)
    
    def _get_table_min_offset(self, table: DocumentTable) -> int:
        """Bepaal de minimale offset van een tabel."""
        if not table.cells:
            return 0
        
        min_offset = min(
            cell.spans[0].offset 
            for cell in table.cells 
            if cell.spans
        )
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
            if "Constructie" in sectie.titel:
                titel = sectie.titel.split(" ")[1:]
                omschrijving = self.sections[i].inhoud
                toestand_tabellen = self.sections[i+2].tabellen
                gebreken_tabellen = self.sections[i+3].tabellen
                rakdeel_secties.append(
                    RakdeelSectie(
                        constructie_naam=" ".join(titel),
                        beschrijving=omschrijving,
                        toestand_tabel=toestand_tabellen,
                        gebreken_tabel=gebreken_tabellen
                    )
                )
        return rakdeel_secties
    
    def get_meettabel_houtmonsters(self) -> list[DocumentTable]:
        """Haal de meettabel voor houtmonsters op.
        
        Returns
        -------
        list[DocumentTable]
            Lijst van tabellen met houtmonster metingen.
        """
        for sectie in self.sections:
            if "meettabel houtmonsters" in sectie.titel.lower() and sectie.tabellen:
                return sectie.tabellen
        return []
    
    def _is_table_type_by_first_column(self, tabel: DocumentTable, prefix: str, threshold: float = 0.5) -> bool:
        """Check of een tabel bij een type hoort op basis van eerste kolom prefix."""
        if tabel.column_count <= 10:
            return False
        
        first_col_cells = [cell.content for cell in tabel.cells if cell.column_index == 0]
        if not first_col_cells:
            return False
        
        matching_cells = sum(1 for cell in first_col_cells if cell.startswith(prefix))
        return (matching_cells / len(first_col_cells)) > threshold
    
    def get_meettabel_fundering_paal(self) -> list[DocumentTable]:
        """Haal de meettabel voor palen op.
        
        Returns
        -------
        list[DocumentTable]
            Tabellen waar >50% van eerste kolom met 'P' begint.
        """
        for sectie in self.sections:
            if "meettabel fundering" in sectie.titel.lower() and sectie.tabellen:
                return [tabel for tabel in sectie.tabellen if self._is_table_type_by_first_column(tabel, "P")]
        return []
    
    def get_meettabel_fundering_kesp(self) -> list[DocumentTable]:
        """Haal de meettabel voor kespen op.
        
        Returns
        -------
        list[DocumentTable]
            Tabellen waar >50% van eerste kolom met 'K' begint.
        """
        for sectie in self.sections:
            if "meettabel fundering" in sectie.titel.lower() and sectie.tabellen:
                return [tabel for tabel in sectie.tabellen if self._is_table_type_by_first_column(tabel, "K")]
        return []
    
    def __repr__(self) -> str:
        section_summary = "\n".join([
            f"  - {s.titel} ({len(s.inhoud)} paragrafen, {len(s.tabellen)} tabellen)" 
            for s in self.sections
        ])
        return f"SmartDocument met {len(self.sections)} secties:\n{section_summary}"


if __name__ == "__main__":
    doc = SmartDocument(result)
    print(doc)
    print("\n" + "="*80 + "\n")
    
    for i, sectie in enumerate(doc.sections[:5]):
        print(f"\n[{i+1}] {sectie.titel}")
        print("-" * 60)
        for j, paragraph in enumerate(sectie.inhoud[:3]):
            offset = paragraph.spans[0].offset if paragraph.spans else 0
            print(f"  Paragraaf {j+1} (offset {offset}): {paragraph.content[:100]}...")
        if len(sectie.inhoud) > 3:
            print(f"  ... en nog {len(sectie.inhoud) - 3} paragrafen")
