"""Parser for the DHCS Submission Review Form: a structured Yes/No
questionnaire (unlike the narrative Policy Guide, this needs no LLM to
segment - each question is already explicitly numbered)."""
import re

import fitz  # PyMuPDF

QUESTION_ANCHOR_RE = re.compile(r"(\d{1,2})\.\s+Does the P&P")
REFERENCE_RE = re.compile(r"\(Reference:\s*(.*?)\)", re.DOTALL)


def extract_questions(path):
    """Returns list of {"number": int, "text": str, "reference": str, "page": int}."""
    doc = fitz.open(path)

    # Normalize each page's text independently, then track the character
    # offset range each page occupies in the concatenated full text - lets us
    # map a regex match's position back to the correct page.
    page_texts = []
    page_ranges = []  # (start_offset, end_offset) in the concatenated string
    offset = 0
    for page in doc:
        text = re.sub(r"\s+", " ", page.get_text()).strip()
        page_texts.append(text)
        page_ranges.append((offset, offset + len(text)))
        offset += len(text) + 1  # +1 for the joining space
    doc.close()

    full_text = " ".join(page_texts)

    def page_for_offset(pos):
        for i, (start, end) in enumerate(page_ranges):
            if start <= pos <= end:
                return i + 1
        return page_ranges and len(page_ranges)  # fallback: last page

    anchors = list(QUESTION_ANCHOR_RE.finditer(full_text))
    questions = []

    for i, anchor in enumerate(anchors):
        start = anchor.start()
        end = anchors[i + 1].start() if i + 1 < len(anchors) else len(full_text)
        block = full_text[start:end]

        number = int(anchor.group(1))
        ref_match = REFERENCE_RE.search(block)
        reference = ref_match.group(1).strip() if ref_match else None

        # block starts with "N. Does the P&P..."; take up to "(Reference:"
        # (or end of block) and strip the leading "N. " numbering.
        text_end = ref_match.start() if ref_match else len(block)
        question_text = block[:text_end].strip()
        question_text = re.sub(rf"^{number}\.\s*", "", question_text).strip()

        questions.append({
            "number": number,
            "text": question_text,
            "reference": reference,
            "page": page_for_offset(start),
        })

    return questions
