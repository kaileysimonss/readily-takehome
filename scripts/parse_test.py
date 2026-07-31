import sys
from lib.pdf_utils import extract_pdf_lines, extract_doc_meta
from lib.chunker import chunk_document


def main():
    path = sys.argv[1]
    meta = extract_doc_meta(path)
    lines = extract_pdf_lines(path)
    chunks = chunk_document(lines)

    print("=== META ===", meta)
    print(f"=== CHUNKS ({len(chunks)}) ===")
    for c in chunks:
        print(f"\n[{c['section']}] p.{c['page']}")
        print(c["text"][:300])


if __name__ == "__main__":
    main()
