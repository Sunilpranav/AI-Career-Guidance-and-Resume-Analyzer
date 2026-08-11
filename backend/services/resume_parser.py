"""
resume_parser.py — Extracts plain text from PDF and DOCX files.
Uses pypdf for PDFs and python-docx for Word documents.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text(file_path: str) -> str:
    """
    Extract text content from a PDF or DOCX file.
    Returns the raw text string (may be empty if file has no text layers).
    Raises ValueError for unsupported formats.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(file_path)
    elif suffix == ".docx":
        return _extract_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Only PDF and DOCX are supported.")


def _extract_pdf(file_path: str) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages)
    except Exception as e:
        logger.error(f"PDF extraction failed for {file_path}: {e}")
        raise RuntimeError(f"Could not read PDF: {e}") from e


def _extract_docx(file_path: str) -> str:
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        logger.error(f"DOCX extraction failed for {file_path}: {e}")
        raise RuntimeError(f"Could not read DOCX: {e}") from e
