"""
utils/file_parser.py

File parsing utilities for the Multi-Agent System.
Extracts plain text from uploaded CV files (PDF, DOCX, TXT).
"""

import io
from pathlib import Path


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract plain text from PDF bytes.
    Uses pdfplumber (primary), falls back to PyPDF2.
    """
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages).strip()
    except ImportError:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from DOCX bytes using python-docx."""
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs).strip()


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Route file to the correct extractor based on file extension.

    Supported: .pdf, .docx, .doc, .txt
    Raises ValueError for unsupported types.
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_bytes)
    elif ext == ".txt":
        return file_bytes.decode("utf-8", errors="replace").strip()
    else:
        raise ValueError(
            f"Unsupported file type: '{ext}'. Supported: .pdf, .docx, .doc, .txt"
        )
