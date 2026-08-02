"""Re-embeds the P&P chunks with taskType=RETRIEVAL_DOCUMENT, to pair with
the questionnaire questions embedded as QUESTION_ANSWERING. This is a
separate embedding space from data/plan_policies/embeddings.bin (which is
task-type-neutral, used for the symmetric obligation-vs-P&P matching) - same
chunk text, different vectors, so it's stored alongside the questionnaire
data rather than overwriting the existing P&P embeddings. Reuses
chunks-meta.json for text/metadata (same order -> index-aligned vectors)."""
import json
import os
import struct
from concurrent.futures import ThreadPoolExecutor

from lib.gemini_client import embed_batch

PP_META_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "plan_policies", "chunks-meta.json")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "questionnaire")
VECS_OUT = os.path.join(OUT_DIR, "pp-embeddings.bin")

DIM = 768
BATCH_SIZE = 20
CONCURRENCY = 5
TASK_TYPE = "RETRIEVAL_DOCUMENT"


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    with open(PP_META_FILE) as f:
        chunks = json.load(f)

    print(f"Embedding {len(chunks)} P&P chunks (taskType={TASK_TYPE}, concurrency={CONCURRENCY})...")

    batches = [chunks[i : i + BATCH_SIZE] for i in range(0, len(chunks), BATCH_SIZE)]
    vectors = [None] * len(chunks)
    completed = 0

    def process(batch_idx):
        nonlocal completed
        batch = batches[batch_idx]
        texts = [c["text"] for c in batch]
        embeddings = embed_batch(api_key, texts, dim=DIM, task_type=TASK_TYPE)
        offset = batch_idx * BATCH_SIZE
        for j, emb in enumerate(embeddings):
            vectors[offset + j] = emb
        completed += len(batch)
        if completed % 200 < BATCH_SIZE or completed == len(chunks):
            print(f"  {completed}/{len(chunks)}", flush=True)

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        list(executor.map(process, range(len(batches))))

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(VECS_OUT, "wb") as f:
        for vec in vectors:
            f.write(struct.pack(f"<{DIM}f", *vec))

    print(f"Wrote {VECS_OUT} (dim={DIM}, {len(vectors)} vectors)")


if __name__ == "__main__":
    main()
