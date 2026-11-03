import os
import re
from pathlib import Path
from typing import List, Dict, Any
import pypdf
import docx


class ExtractionError(Exception):
    """Custom exception raised when document extraction fails."""
    pass


class TextExtractor:
    """Extracts text and structural metadata from PDF, DOCX, and TXT files."""

    @staticmethod
    def extract(file_path: str, file_type: str) -> List[Dict[str, Any]]:
        """
        Extract text from file.
        Returns a list of dictionaries with structure:
        [
            {
                "page_number": int or None,
                "section_title": str or None,
                "text": str
            }, ...
        ]
        """
        path = Path(file_path)
        if not path.exists():
            raise ExtractionError(f"File not found: {file_path}")

        file_type = file_type.lower().strip().replace(".", "")

        if file_type == "pdf":
            return TextExtractor._extract_pdf(path)
        elif file_type == "docx":
            return TextExtractor._extract_docx(path)
        elif file_type == "txt":
            return TextExtractor._extract_txt(path)
        else:
            raise ExtractionError(f"Unsupported file format: {file_type}")

    @staticmethod
    def _extract_pdf(path: Path) -> List[Dict[str, Any]]:
        """Extract text from PDF page by page."""
        pages_content = []
        try:
            reader = pypdf.PdfReader(str(path))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    raise ExtractionError("PDF file is password-protected and cannot be decrypted.")

            total_pages = len(reader.pages)
            if total_pages == 0:
                raise ExtractionError("PDF contains no pages.")

            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                page_text = page_text.strip()
                if page_text:
                    pages_content.append({
                        "page_number": i + 1,
                        "section_title": f"Page {i + 1}",
                        "text": page_text
                    })

            if not pages_content:
                raise ExtractionError("No readable text could be extracted from PDF (document may be scanned or empty).")

            return pages_content
        except Exception as e:
            if isinstance(e, ExtractionError):
                raise
            raise ExtractionError(f"Error parsing PDF: {str(e)}")

    @staticmethod
    def _extract_docx(path: Path) -> List[Dict[str, Any]]:
        """Extract text from DOCX, grouping by headings/sections."""
        try:
            doc = docx.Document(str(path))
            sections_content = []
            current_section = "Introduction"
            current_paragraphs = []
            page_estimate = 1
            word_count = 0

            for p in doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue

                # Check if paragraph is a heading
                if p.style and p.style.name.startswith("Heading"):
                    if current_paragraphs:
                        sections_content.append({
                            "page_number": page_estimate,
                            "section_title": current_section,
                            "text": "\n".join(current_paragraphs)
                        })
                        current_paragraphs = []
                    current_section = text
                else:
                    current_paragraphs.append(text)
                    words = len(text.split())
                    word_count += words
                    if word_count > 450:  # Approximate page break
                        page_estimate += 1
                        word_count = 0

            if current_paragraphs:
                sections_content.append({
                    "page_number": page_estimate,
                    "section_title": current_section,
                    "text": "\n".join(current_paragraphs)
                })

            # Also inspect tables if any
            for table in doc.tables:
                table_lines = []
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        table_lines.append(row_text)
                if table_lines:
                    sections_content.append({
                        "page_number": page_estimate,
                        "section_title": "Document Table",
                        "text": "\n".join(table_lines)
                    })

            if not sections_content:
                raise ExtractionError("No textual content found in DOCX file.")

            return sections_content
        except Exception as e:
            if isinstance(e, ExtractionError):
                raise
            raise ExtractionError(f"Error parsing DOCX: {str(e)}")

    @staticmethod
    def _extract_txt(path: Path) -> List[Dict[str, Any]]:
        """Extract text from plain text file, handling encodings."""
        content = ""
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                with open(path, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        content = content.strip()
        if not content:
            raise ExtractionError("Text file is empty or cannot be decoded.")

        # Split into logical sections or pages (~400 words per section)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        sections = []
        current_chunk = []
        current_words = 0
        section_idx = 1

        for p in paragraphs:
            words = len(p.split())
            current_chunk.append(p)
            current_words += words
            if current_words >= 350:
                sections.append({
                    "page_number": section_idx,
                    "section_title": f"Section {section_idx}",
                    "text": "\n\n".join(current_chunk)
                })
                current_chunk = []
                current_words = 0
                section_idx += 1

        if current_chunk:
            sections.append({
                "page_number": section_idx,
                "section_title": f"Section {section_idx}",
                "text": "\n\n".join(current_chunk)
            })

        return sections
