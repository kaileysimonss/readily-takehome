"""Truncates data/questionnaire/pp-embeddings.bin (768d) to 256d. Separate
from truncate_embeddings.py because that script's filename conventions
(embeddings.bin / embeddings-768d.bak.bin) would collide with the questions'
own embeddings already in data/questionnaire/."""
import math
import os
import struct
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "questionnaire")
OUT_FILE = os.path.join(DATA_DIR, "pp-embeddings.bin")
BACKUP_FILE = os.path.join(DATA_DIR, "pp-embeddings-768d.bak.bin")

SRC_DIM = 768
DST_DIM = int(sys.argv[1]) if len(sys.argv) > 1 else 256


def normalize(vec):
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm > 0 else vec


def main():
    in_file = BACKUP_FILE if os.path.exists(BACKUP_FILE) else OUT_FILE
    with open(in_file, "rb") as f:
        src = f.read()

    count = len(src) // (SRC_DIM * 4)
    if len(src) % (SRC_DIM * 4) != 0:
        raise ValueError("pp-embeddings.bin size doesn't divide evenly by SRC_DIM")

    if os.path.abspath(in_file) != os.path.abspath(BACKUP_FILE):
        with open(BACKUP_FILE, "wb") as f:
            f.write(src)
        print(f"Backed up original to {BACKUP_FILE}")

    with open(OUT_FILE, "wb") as out:
        for i in range(count):
            vec = struct.unpack_from(f"<{SRC_DIM}f", src, i * SRC_DIM * 4)[:DST_DIM]
            vec = normalize(list(vec))
            out.write(struct.pack(f"<{DST_DIM}f", *vec))

    print(f"Wrote {OUT_FILE}: {count} vectors, {SRC_DIM}d -> {DST_DIM}d")


if __name__ == "__main__":
    main()
