import fs from "fs";
import path from "path";

const CHUNKS_FILE = path.join(process.cwd(), "data", "chunks.json");
const META_OUT = path.join(process.cwd(), "data", "chunks-meta.json");
const VECS_OUT = path.join(process.cwd(), "data", "embeddings.bin");

const MODEL = "gemini-embedding-001";
const DIM = 768;
const BATCH_SIZE = 20;
const CONCURRENCY = 3;

interface RawChunk {
  chunkId: string;
  doc: string;
  docTitle: string;
  section: string;
  page: number;
  text: string;
}

function normalize(v: number[]): number[] {
  const norm = Math.sqrt(v.reduce((s, x) => s + x * x, 0));
  return norm > 0 ? v.map((x) => x / norm) : v;
}

async function embedBatch(
  apiKey: string,
  texts: string[],
  attempt = 1
): Promise<number[][]> {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:batchEmbedContents?key=${apiKey}`;
  const body = {
    requests: texts.map((text) => ({
      model: `models/${MODEL}`,
      content: { parts: [{ text }] },
      outputDimensionality: DIM,
    })),
  };
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    if ((res.status === 429 || res.status >= 500) && attempt <= 5) {
      const wait = 1000 * 2 ** attempt;
      await new Promise((r) => setTimeout(r, wait));
      return embedBatch(apiKey, texts, attempt + 1);
    }
    const errText = await res.text();
    throw new Error(`Embedding request failed (${res.status}): ${errText}`);
  }

  const data = (await res.json()) as { embeddings: { values: number[] }[] };
  return data.embeddings.map((e) => normalize(e.values));
}

async function main() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new Error("GEMINI_API_KEY not set (check .env.local)");

  let chunks: RawChunk[] = JSON.parse(fs.readFileSync(CHUNKS_FILE, "utf-8"));
  const limit = process.argv[2] ? parseInt(process.argv[2], 10) : undefined;
  if (limit) chunks = chunks.slice(0, limit);
  console.log(`Embedding ${chunks.length} chunks in batches of ${BATCH_SIZE}...`);

  const batches: RawChunk[][] = [];
  for (let i = 0; i < chunks.length; i += BATCH_SIZE) {
    batches.push(chunks.slice(i, i + BATCH_SIZE));
  }

  const vectors: number[][] = new Array(chunks.length);
  let completed = 0;
  let nextBatchIdx = 0;

  async function worker() {
    while (nextBatchIdx < batches.length) {
      const idx = nextBatchIdx++;
      const batch = batches[idx];
      const embs = await embedBatch(apiKey!, batch.map((c) => c.text));
      const offset = idx * BATCH_SIZE;
      for (let j = 0; j < embs.length; j++) {
        vectors[offset + j] = embs[j];
      }
      completed += batch.length;
      if (completed % 200 < BATCH_SIZE) {
        console.log(`  ${completed}/${chunks.length}`);
      }
    }
  }

  await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));

  // Write metadata (no embeddings) and a packed binary of float32 vectors.
  const meta = chunks.map(({ chunkId, doc, docTitle, section, page, text }) => ({
    chunkId,
    doc,
    docTitle,
    section,
    page,
    text,
  }));
  fs.writeFileSync(META_OUT, JSON.stringify(meta));

  const buffer = Buffer.alloc(vectors.length * DIM * 4);
  for (let i = 0; i < vectors.length; i++) {
    const vec = vectors[i];
    for (let j = 0; j < DIM; j++) {
      buffer.writeFloatLE(vec[j], (i * DIM + j) * 4);
    }
  }
  fs.writeFileSync(VECS_OUT, buffer);

  console.log(`Wrote ${META_OUT} and ${VECS_OUT} (dim=${DIM})`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
