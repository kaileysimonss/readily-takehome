import fs from "fs";
import path from "path";
import { extractPdfLines, extractDocMeta } from "./lib/pdf";
import { chunkDocument } from "./lib/chunker";

async function main() {
  const file = process.argv[2];
  const buffer = fs.readFileSync(file);
  const meta = await extractDocMeta(buffer);
  const { lines, numPages } = await extractPdfLines(buffer);
  const chunks = chunkDocument(lines);

  console.log("=== META ===", meta, "pages:", numPages);
  console.log("=== CHUNKS (%d) ===", chunks.length);
  for (const c of chunks) {
    console.log(`\n[${c.section}] p.${c.page}`);
    console.log(c.text.slice(0, 300));
  }
}

main();
