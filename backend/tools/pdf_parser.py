"""PDF text extraction helpers."""

from __future__ import annotations

import fitz


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF byte payload.

    Returns empty string for invalid, empty, or image-only/scanned PDFs.
    """

    if not file_bytes:
        return ""

    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as document:
            page_texts: list[str] = []
            for page in document:
                text = (page.get_text("text") or "").strip()
                if text:
                    page_texts.append(text)

            if not page_texts:
                return ""

            return "\n".join(page_texts).strip()
    except Exception:
        return ""
