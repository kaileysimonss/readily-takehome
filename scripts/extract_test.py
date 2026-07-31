import os
import sys

from lib.narrative_pdf import extract_narrative_pages
from lib.gemini_client import extract_obligations
from lib.verify import quote_verified

FILE = os.path.join(os.path.dirname(__file__), "..", "docs", "Public Policies", "ECM Policy Guidelines.pdf")


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 15

    all_pages = extract_narrative_pages(FILE)
    pages = [p for p in all_pages[:limit] if not p["skip"]]

    page_tagged_text = "\n\n".join(f"[PAGE {p['page']}]\n{p['text']}" for p in pages)
    print(f"Sending {len(pages)} pages ({len(page_tagged_text)} chars) to Gemini...\n")

    obligations = extract_obligations(api_key, page_tagged_text)

    page_text_by_num = {p["page"]: p["text"] for p in pages}
    verified_count = 0

    for i, o in enumerate(obligations):
        page_text = page_text_by_num.get(o["page"], "")
        verified = quote_verified(o["sourceQuote"], page_text)
        verified_count += verified
        mark = "✓" if verified else "✗ QUOTE NOT FOUND"
        print(f"[{i + 1}] p.{o['page']} {mark}")
        print(f"    obligation: {o['obligation']}")
        print(f"    quote: \"{o['sourceQuote']}\"")
        print()

    print(f"\n{len(obligations)} obligations extracted, {verified_count} verified, {len(obligations) - verified_count} flagged.")


if __name__ == "__main__":
    main()
