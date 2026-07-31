import { getDocument } from "pdfjs-dist/legacy/build/pdf.mjs";

export interface PdfLine {
  page: number;
  y: number;
  text: string;
}

// Groups positioned text items into lines (by y-coordinate) per page, drops the
// repeating "Page X of Y ... Revised: ..." footer, and drops the metadata table
// block at the top of page 1 (everything above the first ROMAN. HEADING line).
export async function extractPdfLines(buffer: Buffer): Promise<{
  lines: PdfLine[];
  numPages: number;
}> {
  const data = new Uint8Array(buffer);
  const doc = await getDocument({ data, disableFontFace: true }).promise;

  const allLines: PdfLine[] = [];

  for (let pageNum = 1; pageNum <= doc.numPages; pageNum++) {
    const page = await doc.getPage(pageNum);
    const viewport = page.getViewport({ scale: 1 });
    const content = await page.getTextContent();

    type Item = { str: string; x: number; y: number };
    const items: Item[] = (content.items as any[])
      .filter((i) => typeof i.str === "string")
      .map((i) => ({ str: i.str, x: i.transform[4], y: i.transform[5] }));

    // Group into lines by rounding y to nearest 2pt.
    const byY = new Map<number, Item[]>();
    for (const item of items) {
      const key = Math.round(item.y / 2) * 2;
      if (!byY.has(key)) byY.set(key, []);
      byY.get(key)!.push(item);
    }

    const pageLines = Array.from(byY.entries())
      .sort((a, b) => b[0] - a[0]) // top to bottom (high y -> low y)
      .map(([y, its]) => ({
        y,
        text: its
          .sort((a, b) => a.x - b.x)
          .map((i) => i.str)
          .join("")
          .replace(/\s+/g, " ")
          .trim(),
      }))
      .filter((l) => l.text.length > 0);

    // Drop the bottom-margin footer line, e.g. "Page 2 of 6 AA.1204: ... Revised: ..."
    const footerCutoff = 80;
    let filtered = pageLines.filter(
      (l) => !(l.y < footerCutoff && /^Page\s+\d+\s+of\s+\d+/i.test(l.text))
    );
    // Safety net: also drop any stray "Page X of Y" line regardless of position.
    filtered = filtered.filter((l) => !/^Page\s+\d+\s+of\s+\d+\b/i.test(l.text));

    for (const l of filtered) {
      allLines.push({ page: pageNum, y: l.y, text: l.text });
    }
  }

  // Drop the page-1 metadata table block: everything above the first top-level
  // heading line ("I. PURPOSE", "II. POLICY", etc.)
  const ROMAN_HEADING = /^(I|II|III|IV|V|VI|VII|VIII|IX|X)\.\s+[A-Z]/;
  const headingIdx = allLines.findIndex((l) => ROMAN_HEADING.test(l.text));
  const lines = headingIdx > 0 ? allLines.slice(headingIdx) : allLines;

  return { lines, numPages: doc.numPages };
}

// Extracts "Policy: AA.1204" / "Title: Gifts, Honoraria..." from the raw
// (pre-heading-cutoff) page-1 header block.
export async function extractDocMeta(
  buffer: Buffer
): Promise<{ policyCode: string | null; title: string | null }> {
  const data = new Uint8Array(buffer);
  const doc = await getDocument({ data, disableFontFace: true }).promise;
  const page = await doc.getPage(1);
  const content = await page.getTextContent();
  const raw = (content.items as any[])
    .filter((i) => typeof i.str === "string")
    .map((i) => i.str)
    .join(" ")
    .replace(/\s+/g, " ");

  const policyMatch = raw.match(/Policy:\s*([A-Za-z0-9.]+)/);
  const titleMatch = raw.match(/Title:\s*(.+?)\s*Department:/);

  return {
    policyCode: policyMatch ? policyMatch[1] : null,
    title: titleMatch ? titleMatch[1].trim() : null,
  };
}
