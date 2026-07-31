"""Flat per-page text extraction for narrative documents (the DHCS Policy
Guide) that don't follow a rigid template like the P&P PDFs. Strips the
leading page-number stamp and flags cover/TOC-style pages so they can be
excluded from LLM extraction."""
import re

import fitz  # PyMuPDF


def extract_narrative_pages(path):
    """Returns list of {"page": int, "text": str, "skip": bool}."""
    doc = fitz.open(path)
    pages = []

    for page_index in range(doc.page_count):
        page_num = page_index + 1
        page = doc[page_index]
        text = re.sub(r"\s+", " ", page.get_text()).strip()

        # Strip a leading page-number stamp, e.g. "50 maternal outcomes..." -> "maternal outcomes..."
        text = re.sub(rf"^{page_num}\s+", "", text)

        dot_ratio = text.count(".") / max(len(text), 1)
        skip = len(text) < 150 or dot_ratio > 0.1

        pages.append({"page": page_num, "text": text, "skip": skip})

    doc.close()
    return pages
