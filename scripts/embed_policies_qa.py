"""Second embedding pass over the same P&P chunks, tagged as
taskType=RETRIEVAL_DOCUMENT so they pair correctly with the questionnaire's
QUESTION_ANSWERING-tagged question embeddings (Gemini trains these task
types as matched pairs, not independently comparable to untagged vectors).

Reuses chunks-meta.json as-is for text/metadata - only the vectors differ
from the existing embeddings.bin used by the obligation-matching flow.
"""
import json
import os
import struct
from concurrent.futures import ThreadPoolExecutor

from lib.gemini_client import embed_batch

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "plan_policies")
CHUNKS_META_FILE = os.path.join(DATA_DIR, "chunks-meta.json")
VECS_OUT = os.path.join(DATA_DIR, "embeddings-qa.bin")

DIM = 256  # requested directly via outputDimensionality; no separate truncation pass needed
BATCH_SIZE = 20
CONCURRENCY = 3
TASK_TYPE = "RETRIEVAL_DOCUMENT"


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    with open(CHUNKS_META_FILE) as f:
        chunks = json.load(f)

    print(f"Embedding {len(chunks)} P&P chunks (taskType={TASK_TYPE}, dim={DIM})...")

    batches = [chunks[i : i + BATCH_SIZE] for i in range(0, len(chunks), BATCH_SIZE)]
    vectors = [None] * len(chunks)
    completed = 0
    failed_batches = []

    def process(batch_idx):
        nonlocal completed
        batch = batches[batch_idx]
        texts = [c["text"] for c in batch]
        try:
            embeddings = embed_batch(api_key, texts, dim=DIM, task_type=TASK_TYPE)
        except Exception as err:  # noqa: BLE001
            failed_batches.append(batch_idx)
            print(f"  batch {batch_idx} failed: {err}")
            return
        offset = batch_idx * BATCH_SIZE
        for j, emb in enumerate(embeddings):
            vectors[offset + j] = emb
        completed += len(batch)
        if completed % 500 < BATCH_SIZE or completed == len(chunks):
            print(f"  {completed}/{len(chunks)}")

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        list(executor.map(process, range(len(batches))))

    # A batch that exhausted embed_batch's own retries gets one more serial
    # attempt here, rather than silently shipping a .bin with holes in it.
    for batch_idx in list(failed_batches):
        print(f"  retrying failed batch {batch_idx}...")
        batch = batches[batch_idx]
        texts = [c["text"] for c in batch]
        try:
            embeddings = embed_batch(api_key, texts, dim=DIM, task_type=TASK_TYPE)
        except Exception as err:  # noqa: BLE001
            print(f"  batch {batch_idx} failed again: {err}")
            continue
        offset = batch_idx * BATCH_SIZE
        for j, emb in enumerate(embeddings):
            vectors[offset + j] = emb
        failed_batches.remove(batch_idx)

    if failed_batches:
        missing = sum(len(batches[i]) for i in failed_batches)
        raise RuntimeError(
            f"{len(failed_batches)} batches ({missing} chunks) failed after retry - "
            f"refusing to write an incomplete embeddings-qa.bin. Batch indices: {failed_batches}"
        )

    with open(VECS_OUT, "wb") as f:
        for vec in vectors:
            f.write(struct.pack(f"<{DIM}f", *vec))

    print(f"Wrote {VECS_OUT} (dim={DIM}) - chunks-meta.json unchanged, same index order")


if __name__ == "__main__":
    main()
