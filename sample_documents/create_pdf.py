import os
from pathlib import Path
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, ArrayObject, DecodedStreamObject, NumberObject, create_string_object

def create_simple_pdf(output_path: str, title: str, text_lines: list):
    """Generate a valid PDF containing text streams without external heavy dependencies."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)  # Standard Letter

    # Build basic PDF content stream with font and text operators
    stream_content = "BT\n/F1 18 Tf\n50 720 Td\n(" + title + ") Tj\nET\n"
    stream_content += "BT\n/F2 11 Tf\n50 680 Td\n16 TL\n"
    for line in text_lines:
        safe_line = line.replace("(", "\\(").replace(")", "\\)")
        stream_content += f"({safe_line}) '\n"
    stream_content += "ET\n"

    # Add fonts to page resources
    font_f1 = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica-Bold")
    })
    font_f2 = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica")
    })

    fonts = DictionaryObject({
        NameObject("/F1"): font_f1,
        NameObject("/F2"): font_f2
    })

    if "/Resources" not in page:
        page[NameObject("/Resources")] = DictionaryObject()
    page["/Resources"][NameObject("/Font")] = fonts

    # Set content stream
    content_stream = DecodedStreamObject()
    content_stream.set_data(stream_content.encode("latin-1"))
    page[NameObject("/Contents")] = content_stream

    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"Created PDF: {output_path}")

if __name__ == "__main__":
    lines = [
        "1. Purpose and Scope:",
        "This policy governs all corporate travel, accommodation, and expense reimbursements.",
        "All business travel must be pre-approved by the department manager.",
        "",
        "2. Per Diem and Meal Allowances:",
        "Employees traveling on corporate business are entitled to a standard per diem of $75 per day.",
        "Itemized receipts are required for all individual expenses exceeding $25.",
        "",
        "3. Flight and Ground Transportation:",
        "Economy class travel is standard for domestic and short-haul flights under 6 hours.",
        "Business class travel is permitted for international flights exceeding 6 hours in duration.",
        "",
        "4. Submission Deadlines:",
        "Expense reports must be submitted via the finance portal within 30 days of trip conclusion."
    ]
    out = Path(__file__).resolve().parent / "Corporate_Travel_Policy.pdf"
    create_simple_pdf(str(out), "Corporate Travel & Expense Policy", lines)
