"""Truncate an embeddings.bin to a smaller dimension using Matryoshka-style
prefix truncation + renormalization, instead of re-calling the embeddings API.

Usage: python3 truncate_embeddings.py <data_dir> <meta_filename> [dst_dim]
e.g.   python3 truncate_embeddings.py ../data/plan_policies chunks-meta.json 256
       python3 truncate_embeddings.py ../data/ecm_guide obligations-meta.json 256
"""
import json
import math
import os
import struct
import sys

SRC_DIM = 768


def normalize(vec):
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm > 0 else vec


def main():
    data_dir = sys.argv[1]
    meta_filename = sys.argv[2]
    dst_dim = int(sys.argv[3]) if len(sys.argv) > 3 else 256

    meta_file = os.path.join(data_dir, meta_filename)
    out_file = os.path.join(data_dir, "embeddings.bin")
    backup_path = os.path.join(data_dir, f"embeddings-{SRC_DIM}d.bak.bin")
    in_file = backup_path if os.path.exists(backup_path) else out_file

    with open(meta_file) as f:
        meta = json.load(f)

    with open(in_file, "rb") as f:
        src = f.read()

    count = len(src) // (SRC_DIM * 4)
    if len(src) % (SRC_DIM * 4) != 0:
        raise ValueError(f"embeddings.bin size doesn't divide evenly by SRC_DIM={SRC_DIM}")
    if count != len(meta):
        raise ValueError(f"vector count ({count}) != meta entries ({len(meta)})")

    if os.path.abspath(in_file) != os.path.abspath(backup_path):
        with open(backup_path, "wb") as f:
            f.write(src)
        print(f"Backed up original to {backup_path} (not tracked by git, delete when done)")

    with open(out_file, "wb") as out:
        for i in range(count):
            vec = struct.unpack_from(f"<{SRC_DIM}f", src, i * SRC_DIM * 4)[:dst_dim]
            vec = normalize(list(vec))
            out.write(struct.pack(f"<{dst_dim}f", *vec))

    print(
        f"Wrote {out_file}: {count} vectors, {SRC_DIM}d -> {dst_dim}d "
        f"({count * dst_dim * 4 / 1024 / 1024:.1f}MB, was {len(src) / 1024 / 1024:.1f}MB)"
    )


if __name__ == "__main__":
    main()
