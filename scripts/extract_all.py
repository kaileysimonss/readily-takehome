import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from lib.narrative_pdf import extract_narrative_pages
from lib.gemini_client import extract_obligations
from lib.verify import quote_verified

FILE = os.path.join(os.path.dirname(__file__), "..", "docs", "Public Policies", "ECM Policy Guidelines.pdf")
OUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "ecm_guide", "obligations.json")
DOC = "ECM Policy Guidelines"
DOC_TITLE = "CalAIM Enhanced Care Management (ECM) Policy Guide"
CONCURRENCY = 5


def extract_with_retry(api_key, text, max_attempts=4):
    for attempt in range(1, max_attempts + 1):
        try:
            return extract_obligations(api_key, text)
        except Exception:
            if attempt == max_attempts:
                raise
            time.sleep(2 ** attempt)


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

    all_pages = extract_narrative_pages(FILE)
    pages = [p for p in all_pages if not p["skip"]]
    if limit:
        pages = pages[:limit]

    print(f"Extracting obligations from {len(pages)} pages (concurrency={CONCURRENCY})...")

    results = [None] * len(pages)
    failures = []
    completed = 0

    def process(idx):
        nonlocal completed
        p = pages[idx]
        try:
            raw = extract_with_retry(api_key, f"[PAGE {p['page']}]\n{p['text']}")
            results[idx] = [
                {
                    "obligationId": f"ECM-p{p['page']}-{i + 1}",
                    "doc": DOC,
                    "docTitle": DOC_TITLE,
                    "page": p["page"],
                    "obligation": o["obligation"],
                    "sourceQuote": o["sourceQuote"],
                    "verified": quote_verified(o["sourceQuote"], p["text"]),
                }
                for i, o in enumerate(raw)
            ]
        except Exception as err:  # noqa: BLE001
            failures.append({"page": p["page"], "error": str(err)})
            results[idx] = []
        completed += 1
        if completed % 10 == 0 or completed == len(pages):
            print(f"  {completed}/{len(pages)} pages")

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        list(executor.map(process, range(len(pages))))

    obligations = [o for group in results for o in group]
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(obligations, f, indent=2)

    verified_count = sum(1 for o in obligations if o["verified"])
    print(f"\nWrote {OUT_FILE}")
    print(f"{len(obligations)} obligations ({verified_count} verified, {len(obligations) - verified_count} flagged)")
    if failures:
        print(f"\n{len(failures)} page failures:")
        for f in failures:
            print(f" - page {f['page']}: {f['error']}")


if __name__ == "__main__":
    main()
