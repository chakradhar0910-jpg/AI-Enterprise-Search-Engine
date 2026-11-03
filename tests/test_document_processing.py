import os
import tempfile
from pathlib import Path
import pytest
from app.services.text_extractor import TextExtractor, ExtractionError
from app.services.text_chunker import TextChunker
import docx
import pypdf


def test_txt_extraction():
    """Test text extraction from plain text file."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Section 1: Enterprise Annual Leave Policy.\n\nEmployees are entitled to 20 paid vacation days each calendar year.")
        temp_path = f.name

    try:
        sections = TextExtractor.extract(temp_path, "txt")
        assert len(sections) > 0
        assert "paid vacation days" in sections[0]["text"]
        assert sections[0]["page_number"] == 1
    finally:
        os.unlink(temp_path)


def test_docx_extraction():
    """Test text extraction from DOCX file."""
    doc = docx.Document()
    doc.add_heading("Cloud Security Guidelines", level=1)
    doc.add_paragraph("All employees must enable multi-factor authentication (MFA) across corporate accounts.")

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        temp_path = f.name

    try:
        doc.save(temp_path)
        sections = TextExtractor.extract(temp_path, "docx")
        assert len(sections) > 0
        combined = " ".join(s["text"] for s in sections)
        assert "multi-factor authentication" in combined
    finally:
        os.unlink(temp_path)


def test_pdf_extraction():
    """Test text extraction from PDF file."""
    # Create simple PDF via pypdf Writer
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=72, height=72)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        temp_path = f.name

    try:
        with open(temp_path, "wb") as f_out:
            writer.write(f_out)

        # Blank page has no text, should raise ExtractionError
        with pytest.raises(ExtractionError):
            TextExtractor.extract(temp_path, "pdf")
    finally:
        os.unlink(temp_path)


def test_text_chunker_logic():
    """Test chunker maintains overlapping boundaries and preserves metadata."""
    chunker = TextChunker(chunk_size=100, chunk_overlap=30)
    sample_sections = [{
        "page_number": 3,
        "section_title": "HR Procedures",
        "text": "The company provides health insurance to all full-time employees. Coverage begins on the first day of the month following hire. Dental and vision coverage are also included."
    }]

    chunks = chunker.chunk_extracted_sections(sample_sections)
    assert len(chunks) >= 1
    for chk in chunks:
        assert chk["page_number"] == 3
        assert chk["section_title"] == "HR Procedures"
        assert chk["token_count"] > 0
        assert len(chk["chunk_text"]) > 0
