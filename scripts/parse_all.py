import json
import os
import re

from lib.pdf_utils import extract_pdf_lines, extract_doc_meta
from lib.chunker import chunk_document

POLICY_ROOT = os.path.join(os.path.dirname(__file__), "..", "docs", "Public Policies")
CATEGORY_DIRS = ["AA", "CMC", "DD", "EE", "FF", "GA", "GG", "HH", "MA", "PA"]
OUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "plan_policies", "chunks.json")

MAX_CHUNK_CHARS = 3000


def split_oversized(text, max_chars):
    """Safety net for the rare oversized chunk: split on sentence boundaries
    into ~max_chars pieces rather than sending one giant blob to embeddings."""
    if len(text) <= max_chars:
        return [text]
    sentences = re.findall(r"[^.!?]+[.!?]+(?:\s+|$)", text) or [text]
    pieces = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) > max_chars and current:
            pieces.append(current.strip())
            current = ""
        current += sentence
    if current.strip():
        pieces.append(current.strip())
    return pieces


def main():
    all_chunks = []
    failures = []
    file_count = 0

    for category in CATEGORY_DIRS:
        dir_path = os.path.join(POLICY_ROOT, category)
        if not os.path.isdir(dir_path):
            continue
        files = sorted(f for f in os.listdir(dir_path) if f.lower().endswith(".pdf"))

        for file in files:
            file_count += 1
            full_path = os.path.join(dir_path, file)
            try:
                meta = extract_doc_meta(full_path)
                lines = extract_pdf_lines(full_path)
                chunks = chunk_document(lines)
                doc_code = meta["policyCode"] or file[:-4]
                doc_title = meta["title"] or doc_code

                if not chunks:
                    failures.append({"file": full_path, "error": "zero chunks produced"})

                seen_ids = {}
                for c in chunks:
                    for piece in split_oversized(c["text"], MAX_CHUNK_CHARS):
                        base_id = f"{doc_code}-{c['section']}"
                        n = seen_ids.get(base_id, 0) + 1
                        seen_ids[base_id] = n
                        chunk_id = base_id if n == 1 else f"{base_id}#{n}"
                        all_chunks.append({
                            "chunkId": chunk_id,
                            "doc": doc_code,
                            "docTitle": doc_title,
                            "section": c["section"],
                            "page": c["page"],
                            "text": piece,
                        })
            except Exception as err:  # noqa: BLE001
                failures.append({"file": full_path, "error": str(err)})

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(all_chunks, f)

    print(f"Parsed {file_count} files -> {len(all_chunks)} chunks")
    print(f"Wrote {OUT_FILE}")
    if failures:
        print(f"\n{len(failures)} FAILURES:")
        for f in failures:
            print(f" - {f['file']}: {f['error']}")


if __name__ == "__main__":
    main()
