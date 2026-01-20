"""ParsedPDF dataclass for handling Azure Document Intelligence results."""

import json
import os
import pickle
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@dataclass
class ParsedPDF:
    """Wrapper for Azure Document Intelligence AnalyzeResult with additional methods.

    Attributes:
        result: The Azure Document Intelligence AnalyzeResult object
        source_path: Path to the source PDF file
    """

    result: AnalyzeResult
    source_path: Path

    @classmethod
    def from_pdf(cls, pdf_path: Path, use_cache: bool = True) -> "ParsedPDF":
        """Create a ParsedPDF instance from a PDF file.

        Uses cached pickle file if available and use_cache is True,
        otherwise analyzes the PDF using Azure Document Intelligence.

        Args:
            pdf_path: Path to the PDF file to analyze
            use_cache: Whether to use cached results if available

        Returns:
            ParsedPDF instance containing the analysis results
        """
        # Determine cache file path based on PDF name
        cache_dir = pdf_path.parent / ".cache"
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / f"{pdf_path.stem}_cache.pkl"

        # Try to load from cache
        if use_cache and cache_file.exists():
            print(f"  Loading from cache: {cache_file.name}")
            result = pickle.loads(cache_file.read_bytes())
            return cls(result=result, source_path=pdf_path)

        # Load environment variables
        load_dotenv()
        endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

        if not endpoint or not key:
            raise ValueError("Azure credentials not found in .env file")

        # Initialize Azure Document Intelligence client
        client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

        # Read and analyze the document
        print(f"  Analyzing document with Azure Document Intelligence...")
        with open(pdf_path, "rb") as f:
            document_bytes = f.read()

        poller = client.begin_analyze_document("prebuilt-layout", BytesIO(document_bytes), content_type="application/pdf")
        result = poller.result()

        # Cache the result
        cache_file.write_bytes(pickle.dumps(result))
        print(f"  Results cached to: {cache_file.name}")

        return cls(result=result, source_path=pdf_path)

    def print(self) -> None:
        """Print the document content to the console."""
        print(f"\n{'='*80}")
        print(f"Document Analysis Results: {self.source_path.name}")
        print(f"{'='*80}\n")

        # Print summary
        print(f"Document Summary:")
        print(f"  Pages: {len(self.result.pages) if self.result.pages else 0}")
        print(f"  Content Length: {len(self.result.content) if self.result.content else 0} characters")
        print(f"  Tables Found: {len(self.result.tables) if self.result.tables else 0}")
        print(f"  Paragraphs Found: {len(self.result.paragraphs) if self.result.paragraphs else 0}")

        # Print full content
        if self.result.content:
            print(f"\n{'-'*80}")
            print(f"Extracted Content:")
            print(f"{'-'*80}\n")
            print(self.result.content)

        # Print tables
        if self.result.tables:
            print(f"\n{'-'*80}")
            print(f"Extracted Tables:")
            print(f"{'-'*80}\n")
            for i, table in enumerate(self.result.tables):
                print(f"\nTable {i+1}: {table.row_count} rows × {table.column_count} columns")
                print("-" * 40)

                # Build table data
                table_data = [["" for _ in range(table.column_count)] for _ in range(table.row_count)]

                if table.cells:
                    for cell in table.cells:
                        row = cell.row_index
                        col = cell.column_index
                        if row < len(table_data) and col < len(table_data[0]):
                            table_data[row][col] = cell.content if cell.content else ""

                # Print table rows
                for row in table_data:
                    print(" | ".join(str(cell)[:30] for cell in row))

        # Print paragraphs
        if self.result.paragraphs:
            print(f"\n{'-'*80}")
            print(f"Extracted Paragraphs:")
            print(f"{'-'*80}\n")
            for i, para in enumerate(self.result.paragraphs):
                print(f"\nParagraph {i+1}:")
                print(para.content)

        print(f"\n{'='*80}\n")

    def to_json(self, output_path: Path | None = None) -> Path:
        """Save the analysis results to a JSON file.

        Args:
            output_path: Path where the JSON file should be saved.
                        If None, saves to {source_pdf_stem}.json in the same directory.

        Returns:
            Path to the saved JSON file
        """
        if output_path is None:
            output_path = self.source_path.with_suffix(".json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.result.as_dict(), f, indent=4)

        print(f"  JSON results saved to: {output_path.name}")
        return output_path

    def to_pdf(self, output_path: Path | None = None) -> Path:
        """Save the full analysis results to a PDF file.

        Args:
            output_path: Path where the PDF file should be saved.
                        If None, saves to {source_pdf_stem}_extracted.pdf in the same directory.

        Returns:
            Path to the saved PDF file
        """
        if output_path is None:
            output_path = self.source_path.parent / f"{self.source_path.stem}_extracted.pdf"

        # Create the PDF document
        doc = SimpleDocTemplate(
            str(output_path), pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm
        )

        # Container for PDF elements
        story = []

        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        heading_style = styles["Heading1"]
        heading2_style = styles["Heading2"]
        normal_style = styles["Normal"]

        # Add title
        story.append(Paragraph("Document Intelligence Results", title_style))
        story.append(Paragraph(f"Source: {self.source_path.name}", normal_style))
        story.append(Spacer(1, 0.5 * cm))

        # Add document summary
        story.append(Paragraph("Document Summary", heading_style))
        story.append(Spacer(1, 0.3 * cm))

        summary_data = [
            ["Pages:", str(len(self.result.pages) if self.result.pages else 0)],
            ["Content Length:", f"{len(self.result.content) if self.result.content else 0} characters"],
            ["Tables Found:", str(len(self.result.tables) if self.result.tables else 0)],
            ["Paragraphs Found:", str(len(self.result.paragraphs) if self.result.paragraphs else 0)],
        ]

        summary_table = Table(summary_data, colWidths=[5 * cm, 10 * cm])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 0.5 * cm))

        # Add full extracted content (no truncation)
        if self.result.content:
            story.append(Paragraph("Extracted Content (Full)", heading_style))
            story.append(Spacer(1, 0.3 * cm))

            # Split into paragraphs and add each (no truncation)
            for para_text in self.result.content.split("\n"):
                if para_text.strip():
                    try:
                        # Escape special characters for reportlab
                        escaped_text = (
                            para_text.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        )
                        story.append(Paragraph(escaped_text, normal_style))
                        story.append(Spacer(1, 0.2 * cm))
                    except Exception as e:
                        # Handle any special characters that might cause issues
                        try:
                            story.append(Paragraph(f"[Line with special characters: {str(e)}]", normal_style))
                        except:
                            pass

        # Add all tables (no limit)
        if self.result.tables:
            story.append(PageBreak())
            story.append(Paragraph("Extracted Tables (All)", heading_style))
            story.append(Spacer(1, 0.3 * cm))

            for i, table in enumerate(self.result.tables):
                story.append(
                    Paragraph(f"Table {i+1}: {table.row_count} rows × {table.column_count} columns", heading2_style)
                )
                story.append(Spacer(1, 0.2 * cm))

                # Build table data
                table_data = [["" for _ in range(table.column_count)] for _ in range(table.row_count)]

                if table.cells:
                    for cell in table.cells:
                        row = cell.row_index
                        col = cell.column_index
                        if row < len(table_data) and col < len(table_data[0]):
                            # No truncation - include full content
                            content = cell.content if cell.content else ""
                            # Escape special characters
                            content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                            table_data[row][col] = content

                # Create PDF table
                try:
                    pdf_table = Table(table_data)
                    pdf_table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                ("FONTSIZE", (0, 0), (-1, -1), 8),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ]
                        )
                    )
                    story.append(pdf_table)
                    story.append(Spacer(1, 0.5 * cm))
                except Exception as e:
                    story.append(Paragraph(f"[Table could not be rendered: {str(e)}]", normal_style))
                    story.append(Spacer(1, 0.5 * cm))

        # Add all paragraphs (no limit)
        if self.result.paragraphs:
            story.append(PageBreak())
            story.append(Paragraph("Extracted Paragraphs (All)", heading_style))
            story.append(Spacer(1, 0.3 * cm))

            for i, para in enumerate(self.result.paragraphs):
                story.append(Paragraph(f"Paragraph {i+1}:", heading2_style))
                story.append(Spacer(1, 0.1 * cm))
                try:
                    # Escape special characters
                    escaped_content = para.content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    story.append(Paragraph(escaped_content, normal_style))
                except Exception as e:
                    story.append(Paragraph(f"[Content error: {str(e)}]", normal_style))
                story.append(Spacer(1, 0.3 * cm))

        # Build the PDF
        doc.build(story)
        print(f"  PDF results saved to: {output_path.name}")
        return output_path
