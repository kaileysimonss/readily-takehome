import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

from lib.vectors import load_vectors, top_k, cosine
from lib.gemini_client import judge_obligation

PP_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "plan_policies")
ECM_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "ecm_guide")
OUT_FILE = os.path.join(ECM_DIR, "matches.json")

TOP_K = 10
SAME_DOC_CAP = 50  # guard against outlier docs (e.g. the 313-chunk glossary)
CONCURRENCY = 5
CHECKPOINT_FILE = os.path.join(ECM_DIR, "matches.partial.json")


def build_candidates(obl_vec, pp_meta, pp_vecs):
    top = top_k(obl_vec, pp_vecs, TOP_K)
    top_indices = [i for _, i in top]

    top_doc = pp_meta[top_indices[0]]["doc"]
    same_doc_indices = [i for i, c in enumerate(pp_meta) if c["doc"] == top_doc]
    if len(same_doc_indices) > SAME_DOC_CAP:
        same_doc_indices = same_doc_indices[:SAME_DOC_CAP]

    all_indices = list(dict.fromkeys(top_indices + same_doc_indices))
    return [
        {
            "chunkId": pp_meta[i]["chunkId"],
            "doc": pp_meta[i]["doc"],
            "section": pp_meta[i]["section"],
            "text": pp_meta[i]["text"],
            "score": cosine(obl_vec, pp_vecs[i]),
        }
        for i in all_indices
    ]


def judge_with_retry(api_key, obligation_text, candidates, max_attempts=4):
    for attempt in range(1, max_attempts + 1):
        try:
            return judge_obligation(api_key, obligation_text, candidates)
        except Exception:
            if attempt == max_attempts:
                raise
            time.sleep(2 ** attempt)


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    obl_meta, obl_vecs = load_vectors(ECM_DIR, "obligations-meta.json")
    pp_meta, pp_vecs = load_vectors(PP_DIR, "chunks-meta.json")
    pp_by_chunk_id = {c["chunkId"]: c for c in pp_meta}

    print(f"Matching {len(obl_meta)} obligations against {len(pp_meta)} P&P chunks (concurrency={CONCURRENCY})...")

    results = [None] * len(obl_meta)
    failures = []
    completed = 0

    def process(idx):
        nonlocal completed
        o = obl_meta[idx]
        t0 = time.time()
        try:
            candidates = build_candidates(obl_vecs[idx], pp_meta, pp_vecs)
            verdict = judge_with_retry(api_key, o["obligation"], candidates)
            matched = pp_by_chunk_id.get(verdict.get("matchedChunkId", ""))
            candidates_sorted = sorted(candidates, key=lambda c: -c["score"])
            results[idx] = {
                "obligationId": o["obligationId"],
                "doc": o["doc"],
                "docTitle": o["docTitle"],
                "page": o["page"],
                "obligation": o["obligation"],
                "verdict": verdict["verdict"],
                "matchedChunkId": verdict.get("matchedChunkId") or None,
                "matchedDoc": matched["doc"] if matched else None,
                "matchedSection": matched["section"] if matched else None,
                "explanation": verdict["explanation"],
                "candidates": [
                    {"chunkId": c["chunkId"], "doc": c["doc"], "section": c["section"], "score": round(c["score"], 4)}
                    for c in candidates_sorted
                ],
            }
            status = verdict["verdict"]
        except Exception as err:  # noqa: BLE001
            failures.append({"obligationId": o["obligationId"], "error": str(err)})
            results[idx] = {
                "obligationId": o["obligationId"],
                "doc": o["doc"],
                "docTitle": o["docTitle"],
                "page": o["page"],
                "obligation": o["obligation"],
                "verdict": "error",
                "matchedChunkId": None,
                "matchedDoc": None,
                "matchedSection": None,
                "explanation": str(err),
                "candidates": [],
            }
            status = f"ERROR: {err}"
        completed += 1
        print(f"  [{completed}/{len(obl_meta)}] {o['obligationId']} ({time.time()-t0:.1f}s) -> {status}", flush=True)
        if completed % 20 == 0 or completed == len(obl_meta):
            done_so_far = [r for r in results if r is not None]
            with open(CHECKPOINT_FILE, "w") as f:
                json.dump(done_so_far, f, indent=2)

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        list(executor.map(process, range(len(obl_meta))))

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    from collections import Counter
    tally = Counter(r["verdict"] for r in results)
    print(f"\nWrote {OUT_FILE}")
    print(f"Verdicts: {dict(tally)}")
    if failures:
        print(f"\n{len(failures)} failures:")
        for f in failures:
            print(f" - {f['obligationId']}: {f['error']}")


if __name__ == "__main__":
    main()
