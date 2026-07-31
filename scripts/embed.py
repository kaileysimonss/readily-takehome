import json
import os
import struct
import sys
from concurrent.futures import ThreadPoolExecutor

from lib.gemini_client import embed_batch

CHUNKS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "chunks.json")
META_OUT = os.path.join(os.path.dirname(__file__), "..", "data", "chunks-meta.json")
VECS_OUT = os.path.join(os.path.dirname(__file__), "..", "data", "embeddings.bin")

DIM = 768
BATCH_SIZE = 20
CONCURRENCY = 3


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set (check .env.local)")

    with open(CHUNKS_FILE) as f:
        chunks = json.load(f)

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if limit:
        chunks = chunks[:limit]

    print(f"Embedding {len(chunks)} chunks in batches of {BATCH_SIZE}...")

    batches = [chunks[i : i + BATCH_SIZE] for i in range(0, len(chunks), BATCH_SIZE)]
    vectors = [None] * len(chunks)
    completed = 0

    def process(batch_idx):
        nonlocal completed
        batch = batches[batch_idx]
        texts = [c["text"] for c in batch]
        embeddings = embed_batch(api_key, texts, dim=DIM)
        offset = batch_idx * BATCH_SIZE
        for j, emb in enumerate(embeddings):
            vectors[offset + j] = emb
        completed += len(batch)
        if completed % 200 < BATCH_SIZE:
            print(f"  {completed}/{len(chunks)}")

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        list(executor.map(process, range(len(batches))))

    meta = [
        {
            "chunkId": c["chunkId"],
            "doc": c["doc"],
            "docTitle": c["docTitle"],
            "section": c["section"],
            "page": c["page"],
            "text": c["text"],
        }
        for c in chunks
    ]
    with open(META_OUT, "w") as f:
        json.dump(meta, f)

    with open(VECS_OUT, "wb") as f:
        for vec in vectors:
            f.write(struct.pack(f"<{DIM}f", *vec))

    print(f"Wrote {META_OUT} and {VECS_OUT} (dim={DIM})")


if __name__ == "__main__":
    main()
