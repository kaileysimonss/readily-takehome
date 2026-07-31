"""Chunks P&P body lines by outline level. L0 (roman numeral) and L1 (capital
letter) sections become their own chunk only if they have no deeper numbered
children (pure prose); L2 (numbered items, "1.", "2.") are always chunks and
absorb any lettered/roman sub-items ("a.", "i.") beneath them as plain
continuation text."""
import re

L0_RE = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)\.\s+(.+)$")  # "II. POLICY"
L1_RE = re.compile(r"^([A-Z])\.\s+(.+)$")  # "A. Prohibition on Receipt of Honoraria"
L2_RE = re.compile(r"^(\d{1,2})\.\s+(.+)$")  # "1. A CalOptima Health Employee..."

SKIP_SECTION_RE = re.compile(
    r"REVISION HISTORY|GLOSSARY|REFERENCE|ATTACHMENT|BOARD ACTION|REGULATORY AGENCY APPROVAL",
    re.IGNORECASE,
)


class _Node:
    def __init__(self, label, page, text, skip, path):
        self.label = label
        self.page = page
        self.text_lines = [text]
        self.has_child = False
        self.skip = skip
        self.path = path


def chunk_document(lines):
    """lines: list of {"page": int, "text": str}. Returns list of
    {"section": str, "page": int, "text": str}."""
    chunks = []
    l0 = l1 = l2 = None

    def flush_node(node):
        if node is None:
            return
        if not node.has_child and not node.skip:
            text = re.sub(r"\s+", " ", " ".join(node.text_lines)).strip()
            if text:
                chunks.append({"section": node.path, "page": node.page, "text": text})

    def flush_l2():
        nonlocal l2
        flush_node(l2)
        l2 = None

    def flush_l1():
        nonlocal l1
        flush_l2()
        flush_node(l1)
        l1 = None

    def flush_l0():
        nonlocal l0
        flush_l1()
        flush_node(l0)
        l0 = None

    for line in lines:
        text = line["text"]
        page = line["page"]

        l0_match = L0_RE.match(text)
        l1_match = None if l0_match else L1_RE.match(text)
        l2_match = None if (l0_match or l1_match) else L2_RE.match(text)

        if l0_match:
            flush_l0()
            label = l0_match.group(1)
            skip = bool(SKIP_SECTION_RE.search(l0_match.group(2)))
            l0 = _Node(label, page, l0_match.group(2), skip, label)
            continue

        if l1_match:
            if l0:
                l0.has_child = True
            flush_l1()
            label = l1_match.group(1)
            l1 = _Node(
                label, page, l1_match.group(2),
                l0.skip if l0 else False,
                f"{l0.path}.{label}" if l0 else label,
            )
            continue

        if l2_match:
            parent = l1 or l0
            if parent:
                parent.has_child = True
            flush_l2()
            label = l2_match.group(1)
            l2 = _Node(
                label, page, l2_match.group(2),
                parent.skip if parent else False,
                f"{parent.path}.{label}" if parent else label,
            )
            continue

        target = l2 or l1 or l0
        if target:
            target.text_lines.append(text)

    flush_l0()
    return chunks
