import sys
from lib.narrative_pdf import extract_narrative_pages


def main():
    path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    pages = extract_narrative_pages(path)
    if limit:
        pages = pages[:limit]
    for p in pages:
        print(f"p{p['page']} skip={p['skip']} len={len(p['text'])}: {p['text'][:120]!r}")


if __name__ == "__main__":
    main()
