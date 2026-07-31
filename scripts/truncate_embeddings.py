import json
import math
import os
import struct
import sys

BACKUP_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "embeddings-768d.bak.bin")
IN_FILE = BACKUP_FILE if os.path.exists(BACKUP_FILE) else os.path.join(
    os.path.dirname(__file__), "..", "data", "embeddings.bin"
)
OUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "embeddings.bin")
META_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "chunks-meta.json")

SRC_DIM = 768
DST_DIM = int(sys.argv[1]) if len(sys.argv) > 1 else 256


def normalize(vec):
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm > 0 else vec


def main():
    with open(META_FILE) as f:
        meta = json.load(f)

    with open(IN_FILE, "rb") as f:
        src = f.read()

    count = len(src) // (SRC_DIM * 4)
    if len(src) % (SRC_DIM * 4) != 0:
        raise ValueError(f"embeddings.bin size doesn't divide evenly by SRC_DIM={SRC_DIM}")
    if count != len(meta):
        raise ValueError(f"vector count ({count}) != meta entries ({len(meta)})")

    backup_path = os.path.join(os.path.dirname(__file__), "..", "data", f"embeddings-{SRC_DIM}d.bak.bin")
    if os.path.abspath(IN_FILE) != os.path.abspath(backup_path):
        with open(backup_path, "wb") as f:
            f.write(src)
        print(f"Backed up original to {backup_path} (not tracked by git, delete when done)")

    with open(OUT_FILE, "wb") as out:
        for i in range(count):
            vec = struct.unpack_from(f"<{SRC_DIM}f", src, i * SRC_DIM * 4)[:DST_DIM]
            vec = normalize(list(vec))
            out.write(struct.pack(f"<{DST_DIM}f", *vec))

    print(
        f"Wrote {OUT_FILE}: {count} vectors, {SRC_DIM}d -> {DST_DIM}d "
        f"({count * DST_DIM * 4 / 1024 / 1024:.1f}MB, was {len(src) / 1024 / 1024:.1f}MB)"
    )


if __name__ == "__main__":
    main()
