"""Shared helpers for loading the packed float32 embedding files and doing
cosine similarity retrieval over them."""
import json
import struct


def load_vectors(data_dir, meta_filename, dim=256):
    with open(f"{data_dir}/{meta_filename}") as f:
        meta = json.load(f)
    with open(f"{data_dir}/embeddings.bin", "rb") as f:
        raw = f.read()
    n = len(raw) // (dim * 4)
    vectors = [struct.unpack_from(f"<{dim}f", raw, i * dim * 4) for i in range(n)]
    return meta, vectors


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def top_k(query_vec, corpus_vectors, k):
    scored = [(cosine(query_vec, v), i) for i, v in enumerate(corpus_vectors)]
    scored.sort(reverse=True)
    return scored[:k]
