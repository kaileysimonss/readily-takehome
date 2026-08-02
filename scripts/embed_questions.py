import json
import os
import struct
from concurrent.futures import ThreadPoolExecutor

from lib.gemini_client import embed_batch

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "questionnaire")
QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.json")
META_OUT = os.path.join(DATA_DIR, "questions-meta.json")
VECS_OUT = os.path.join(DATA_DIR, "embeddings.bin")

DIM = 768
BATCH_SIZE = 20
CONCURRENCY = 3
TASK_TYPE = "QUESTION_ANSWERING"  # query side; pair with RETRIEVAL_DOCUMENT on the P&P side


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    with open(QUESTIONS_FILE) as f:
        questions = json.load(f)

    print(f"Embedding {len(questions)} questions (taskType={TASK_TYPE})...")

    batches = [questions[i : i + BATCH_SIZE] for i in range(0, len(questions), BATCH_SIZE)]
    vectors = [None] * len(questions)

    def process(batch_idx):
        batch = batches[batch_idx]
        texts = [q["question"] for q in batch]
        embeddings = embed_batch(api_key, texts, dim=DIM, task_type=TASK_TYPE)
        offset = batch_idx * BATCH_SIZE
        for j, emb in enumerate(embeddings):
            vectors[offset + j] = emb

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        list(executor.map(process, range(len(batches))))

    with open(META_OUT, "w") as f:
        json.dump(questions, f)

    with open(VECS_OUT, "wb") as f:
        for vec in vectors:
            f.write(struct.pack(f"<{DIM}f", *vec))

    print(f"Wrote {META_OUT} and {VECS_OUT} (dim={DIM})")


if __name__ == "__main__":
    main()
