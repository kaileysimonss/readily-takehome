"""P&P PDF text extraction: position-aware line reconstruction, matching the
layout of the CalOptima Health policy template (metadata table on page 1,
repeating "Page X of Y ... Revised: ..." footer on every page)."""
import re
from collections import defaultdict

import fitz  # PyMuPDF

ROMAN_HEADING_RE = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)\.\s+[A-Z]")
PAGE_FOOTER_RE = re.compile(r"^Page\s+\d+\s+of\s+\d+\b", re.IGNORECASE)


def _page_lines(page):
    """Group words into lines by y-coordinate (matches multi-column table
    layouts correctly, unlike PyMuPDF's own block_no/line_no grouping which
    splits same-row cells like "Policy:" / "AA.1204" into separate blocks)."""
    words = page.get_text("words")  # (x0, y0, x1, y1, word, block_no, line_no, word_no)
    grouped = defaultdict(list)
    for x0, y0, x1, y1, word, block_no, line_no, word_no in words:
        key = round(y0 / 2) * 2
        grouped[key].append((x0, word))

    lines = []
    for y0, items in grouped.items():
        items.sort(key=lambda t: t[0])
        text = " ".join(t[1] for t in items).strip()
        if text:
            lines.append((y0, text))
    lines.sort(key=lambda t: t[0])  # fitz: y increases downward, so this is top-to-bottom
    return lines


def extract_pdf_lines(path):
    """Returns list of {"page": int, "y": float, "text": str}, with the
    repeating footer stripped and the page-1 metadata table cut (everything
    above the first top-level roman-numeral heading)."""
    doc = fitz.open(path)
    all_lines = []

    for page_index in range(doc.page_count):
        page_num = page_index + 1
        page = doc[page_index]
        height = page.rect.height
        footer_cutoff = height - 80  # near the bottom of the page

        for y, text in _page_lines(page):
            if y > footer_cutoff and PAGE_FOOTER_RE.match(text):
                continue
            if PAGE_FOOTER_RE.match(text):  # safety net regardless of position
                continue
            all_lines.append({"page": page_num, "y": y, "text": text})

    heading_idx = next(
        (i for i, l in enumerate(all_lines) if ROMAN_HEADING_RE.match(l["text"])), 0
    )
    doc.close()
    return all_lines[heading_idx:] if heading_idx > 0 else all_lines


def extract_doc_meta(path):
    """Extracts 'Policy: AA.1204' / 'Title: ...' from the raw page-1 header."""
    doc = fitz.open(path)
    raw = re.sub(r"\s+", " ", doc[0].get_text())
    doc.close()

    policy_match = re.search(r"Policy:\s*([A-Za-z0-9.]+)", raw)
    title_match = re.search(r"Title:\s*(.+?)\s*Department:", raw)

    return {
        "policyCode": policy_match.group(1) if policy_match else None,
        "title": title_match.group(1).strip() if title_match else None,
    }
