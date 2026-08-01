import json
import os
import struct
import sys
from concurrent.futures import ThreadPoolExecutor

from lib.gemini_client import embed_batch

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "ecm_guide")
OBLIGATIONS_FILE = os.path.join(DATA_DIR, "obligations.json")
META_OUT = os.path.join(DATA_DIR, "obligations-meta.json")
VECS_OUT = os.path.join(DATA_DIR, "embeddings.bin")

DIM = 768
BATCH_SIZE = 20
CONCURRENCY = 3


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set (check .env.local)")

    with open(OBLIGATIONS_FILE) as f:
        obligations = json.load(f)

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if limit:
        obligations = obligations[:limit]

    print(f"Embedding {len(obligations)} obligations in batches of {BATCH_SIZE}...")

    # Embed the atomic "obligation" text (not the verbatim "sourceQuote" - the
    # quote is for traceability, the obligation is what gets matched against
    # the P&P chunks).
    batches = [obligations[i : i + BATCH_SIZE] for i in range(0, len(obligations), BATCH_SIZE)]
    vectors = [None] * len(obligations)
    completed = 0

    def process(batch_idx):
        nonlocal completed
        batch = batches[batch_idx]
        texts = [o["obligation"] for o in batch]
        embeddings = embed_batch(api_key, texts, dim=DIM)
        offset = batch_idx * BATCH_SIZE
        for j, emb in enumerate(embeddings):
            vectors[offset + j] = emb
        completed += len(batch)
        if completed % 200 < BATCH_SIZE or completed == len(obligations):
            print(f"  {completed}/{len(obligations)}")

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        list(executor.map(process, range(len(batches))))

    meta = [
        {
            "obligationId": o["obligationId"],
            "doc": o["doc"],
            "docTitle": o["docTitle"],
            "page": o["page"],
            "obligation": o["obligation"],
            "sourceQuote": o["sourceQuote"],
            "verified": o["verified"],
        }
        for o in obligations
    ]
    with open(META_OUT, "w") as f:
        json.dump(meta, f)

    with open(VECS_OUT, "wb") as f:
        for vec in vectors:
            f.write(struct.pack(f"<{DIM}f", *vec))

    print(f"Wrote {META_OUT} and {VECS_OUT} (dim={DIM})")


if __name__ == "__main__":
    main()
