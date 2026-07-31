import type { PdfLine } from "./pdf";

export interface Chunk {
  section: string; // e.g. "II.A.1"
  page: number; // page where the chunk starts
  text: string;
}

const L0_RE = /^(I|II|III|IV|V|VI|VII|VIII|IX|X)\.\s+(.+)$/; // "II. POLICY"
const L1_RE = /^([A-Z])\.\s+(.+)$/; // "A. Prohibition on Receipt of Honoraria"
const L2_RE = /^(\d{1,2})\.\s+(.+)$/; // "1. A CalOptima Health Employee..."

// Administrative/boilerplate sections that aren't compliance obligations.
const SKIP_SECTION_RE =
  /REVISION HISTORY|GLOSSARY|REFERENCE|ATTACHMENT|BOARD ACTION|REGULATORY AGENCY APPROVAL/i;

interface Node {
  label: string;
  page: number;
  textLines: string[];
  hasChild: boolean;
  skip: boolean;
  path: string;
}

// Chunks by outline level: L0 (roman) and L1 (capital letter) sections become
// their own chunk only if they have no deeper numbered children (pure prose);
// L2 (numbered items, "1.", "2.") are always chunks, and absorb any lettered/
// roman sub-items ("a.", "i.") beneath them as plain continuation text.
export function chunkDocument(lines: PdfLine[]): Chunk[] {
  const chunks: Chunk[] = [];

  let l0: Node | null = null;
  let l1: Node | null = null;
  let l2: Node | null = null;

  const flush = (node: Node | null) => {
    if (!node) return;
    if (!node.hasChild && !node.skip) {
      const text = node.textLines.join(" ").replace(/\s+/g, " ").trim();
      if (text.length > 0) {
        chunks.push({ section: node.path, page: node.page, text });
      }
    }
  };

  const flushL2 = () => {
    flush(l2);
    l2 = null;
  };
  const flushL1 = () => {
    flushL2();
    flush(l1);
    l1 = null;
  };
  const flushL0 = () => {
    flushL1();
    flush(l0);
    l0 = null;
  };

  for (const line of lines) {
    const l0Match = line.text.match(L0_RE);
    const l1Match = !l0Match && line.text.match(L1_RE);
    const l2Match = !l0Match && !l1Match && line.text.match(L2_RE);

    if (l0Match) {
      flushL0();
      const label = l0Match[1];
      const skip = SKIP_SECTION_RE.test(l0Match[2]);
      l0 = { label, page: line.page, textLines: [l0Match[2]], hasChild: false, skip, path: label };
      continue;
    }

    if (l1Match) {
      if (l0) l0.hasChild = true;
      flushL1();
      const label = l1Match[1];
      l1 = {
        label,
        page: line.page,
        textLines: [l1Match[2]],
        hasChild: false,
        skip: l0?.skip ?? false,
        path: l0 ? `${l0.path}.${label}` : label,
      };
      continue;
    }

    if (l2Match) {
      const parent = l1 ?? l0;
      if (parent) parent.hasChild = true;
      flushL2();
      const label = l2Match[1];
      l2 = {
        label,
        page: line.page,
        textLines: [l2Match[2]],
        hasChild: false,
        skip: parent?.skip ?? false,
        path: parent ? `${parent.path}.${label}` : label,
      };
      continue;
    }

    // Continuation / sub-item text (including "a.", "i." style sub-lists) —
    // absorbed into the deepest currently open node.
    const target = l2 ?? l1 ?? l0;
    if (target) target.textLines.push(line.text);
  }

  flushL0();

  return chunks;
}
