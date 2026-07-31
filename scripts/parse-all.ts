import fs from "fs";
import path from "path";
import { extractPdfLines, extractDocMeta } from "./lib/pdf";
import { chunkDocument } from "./lib/chunker";

const POLICY_ROOT = path.join(process.cwd(), "docs", "Public Policies");
const CATEGORY_DIRS = ["AA", "CMC", "DD", "EE", "FF", "GA", "GG", "HH", "MA", "PA"];
const OUT_FILE = path.join(process.cwd(), "data", "chunks.json");

interface OutChunk {
  chunkId: string;
  doc: string;
  docTitle: string;
  section: string;
  page: number;
  text: string;
}

const MAX_CHUNK_CHARS = 3000;

// Safety net for the rare oversized chunk (e.g. a "II." section that absorbs
// dozens of un-numbered sub-items with no further structural markers): split
// on sentence boundaries into ~MAX_CHUNK_CHARS pieces rather than sending one
// giant blob to the embeddings API.
function splitOversized(text: string, maxChars: number): string[] {
  if (text.length <= maxChars) return [text];
  const sentences = text.match(/[^.!?]+[.!?]+(\s+|$)/g) ?? [text];
  const pieces: string[] = [];
  let current = "";
  for (const sentence of sentences) {
    if (current.length + sentence.length > maxChars && current.length > 0) {
      pieces.push(current.trim());
      current = "";
    }
    current += sentence;
  }
  if (current.trim().length > 0) pieces.push(current.trim());
  return pieces;
}

async function main() {
  const allChunks: OutChunk[] = [];
  const failures: { file: string; error: string }[] = [];
  let fileCount = 0;

  for (const dir of CATEGORY_DIRS) {
    const dirPath = path.join(POLICY_ROOT, dir);
    if (!fs.existsSync(dirPath)) continue;
    const files = fs.readdirSync(dirPath).filter((f) => f.toLowerCase().endsWith(".pdf"));

    for (const file of files) {
      fileCount++;
      const fullPath = path.join(dirPath, file);
      try {
        const buffer = fs.readFileSync(fullPath);
        const meta = await extractDocMeta(buffer);
        const { lines } = await extractPdfLines(buffer);
        const chunks = chunkDocument(lines);
        const docCode = meta.policyCode ?? file.replace(/\.pdf$/i, "");
        const docTitle = meta.title ?? docCode;

        if (chunks.length === 0) {
          failures.push({ file: fullPath, error: "zero chunks produced" });
        }

        const seenIds = new Map<string, number>();
        for (const c of chunks) {
          for (const piece of splitOversized(c.text, MAX_CHUNK_CHARS)) {
            const baseId = `${docCode}-${c.section}`;
            const n = (seenIds.get(baseId) ?? 0) + 1;
            seenIds.set(baseId, n);
            const chunkId = n === 1 ? baseId : `${baseId}#${n}`;
            allChunks.push({
              chunkId,
              doc: docCode,
              docTitle,
              section: c.section,
              page: c.page,
              text: piece,
            });
          }
        }
      } catch (err: any) {
        failures.push({ file: fullPath, error: err?.message ?? String(err) });
      }
    }
  }

  fs.mkdirSync(path.dirname(OUT_FILE), { recursive: true });
  fs.writeFileSync(OUT_FILE, JSON.stringify(allChunks, null, 2));

  console.log(`Parsed ${fileCount} files -> ${allChunks.length} chunks`);
  console.log(`Wrote ${OUT_FILE}`);
  if (failures.length > 0) {
    console.log(`\n${failures.length} FAILURES:`);
    for (const f of failures) console.log(` - ${f.file}: ${f.error}`);
  }
}

main();
