import fs from "fs";
import path from "path";

const BACKUP_FILE = path.join(process.cwd(), "data", "embeddings-768d.bak.bin");
const IN_FILE = fs.existsSync(BACKUP_FILE)
  ? BACKUP_FILE
  : path.join(process.cwd(), "data", "embeddings.bin");
const OUT_FILE = path.join(process.cwd(), "data", "embeddings.bin");
const META_FILE = path.join(process.cwd(), "data", "chunks-meta.json");

const SRC_DIM = 768;
const DST_DIM = process.argv[2] ? parseInt(process.argv[2], 10) : 256;

function normalize(v: Float32Array): Float32Array {
  let norm = 0;
  for (let i = 0; i < v.length; i++) norm += v[i] * v[i];
  norm = Math.sqrt(norm);
  if (norm > 0) for (let i = 0; i < v.length; i++) v[i] /= norm;
  return v;
}

function main() {
  const meta = JSON.parse(fs.readFileSync(META_FILE, "utf-8"));
  const srcBuffer = fs.readFileSync(IN_FILE);
  const count = srcBuffer.length / (SRC_DIM * 4);

  if (!Number.isInteger(count)) {
    throw new Error(`embeddings.bin size doesn't divide evenly by SRC_DIM=${SRC_DIM}`);
  }
  if (count !== meta.length) {
    throw new Error(`vector count (${count}) != meta entries (${meta.length})`);
  }

  const backupPath = path.join(process.cwd(), "data", `embeddings-${SRC_DIM}d.bak.bin`);
  if (path.resolve(IN_FILE) !== path.resolve(backupPath)) {
    fs.copyFileSync(IN_FILE, backupPath);
    console.log(`Backed up original to ${backupPath} (not tracked by git, delete when done)`);
  }

  const dstBuffer = Buffer.alloc(count * DST_DIM * 4);
  for (let i = 0; i < count; i++) {
    const vec = new Float32Array(DST_DIM);
    for (let j = 0; j < DST_DIM; j++) {
      vec[j] = srcBuffer.readFloatLE((i * SRC_DIM + j) * 4);
    }
    normalize(vec);
    for (let j = 0; j < DST_DIM; j++) {
      dstBuffer.writeFloatLE(vec[j], (i * DST_DIM + j) * 4);
    }
  }

  fs.writeFileSync(OUT_FILE, dstBuffer);
  console.log(
    `Wrote ${OUT_FILE}: ${count} vectors, ${SRC_DIM}d -> ${DST_DIM}d ` +
      `(${(dstBuffer.length / 1024 / 1024).toFixed(1)}MB, was ${(srcBuffer.length / 1024 / 1024).toFixed(1)}MB)`
  );
}

main();
