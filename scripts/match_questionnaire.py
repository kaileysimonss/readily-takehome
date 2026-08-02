"""Matches each questionnaire question against the P&P corpus - same
retrieval + LLM-judgment pattern as match_all.py (top-10 + same-document
expansion, then judge_obligation for a supports/partial/contradicts/gap
verdict), but sourcing the question side from the QUESTION_ANSWERING-typed
embeddings and the P&P side from the RETRIEVAL_DOCUMENT-typed embeddings
built specifically for this pairing."""
import json
import os
from concurrent.futures import ThreadPoolExecutor

from lib.vectors import load_vectors, top_k, cosine
from lib.match_helpers import judge_with_verification

Q_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "questionnaire")
PP_META_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "plan_policies", "chunks-meta.json")
PP_QA_VECS_FILE = os.path.join(Q_DIR, "pp-embeddings.bin")
OUT_FILE = os.path.join(Q_DIR, "matches.json")

DIM = 256
TOP_K = 10
SAME_DOC_CAP = 50
CONCURRENCY = 5


def load_pp_for_qa():
    with open(PP_META_FILE) as f:
        pp_meta = json.load(f)
    with open(PP_QA_VECS_FILE, "rb") as f:
        raw = f.read()
    n = len(raw) // (DIM * 4)
    assert n == len(pp_meta), f"pp-embeddings.bin has {n} vectors but chunks-meta.json has {len(pp_meta)} entries"
    import struct
    pp_vecs = [struct.unpack_from(f"<{DIM}f", raw, i * DIM * 4) for i in range(n)]
    return pp_meta, pp_vecs


def build_candidates(q_vec, pp_meta, pp_vecs):
    top = top_k(q_vec, pp_vecs, TOP_K)
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
            "score": cosine(q_vec, pp_vecs[i]),
        }
        for i in all_indices
    ]


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    q_meta, q_vecs = load_vectors(Q_DIR, "questions-meta.json", dim=DIM)
    pp_meta, pp_vecs = load_pp_for_qa()
    pp_by_chunk_id = {c["chunkId"]: c for c in pp_meta}

    print(f"Matching {len(q_meta)} questions against {len(pp_meta)} P&P chunks (concurrency={CONCURRENCY})...")

    results = [None] * len(q_meta)
    failures = []
    completed = 0

    def process(idx):
        nonlocal completed
        q = q_meta[idx]
        try:
            candidates = build_candidates(q_vecs[idx], pp_meta, pp_vecs)
            verdict, citation_verified = judge_with_verification(api_key, q["question"], candidates)
            matched = pp_by_chunk_id.get(verdict.get("matchedChunkId", "")) if citation_verified else None
            candidates_sorted = sorted(candidates, key=lambda c: -c["score"])
            results[idx] = {
                "questionId": q["questionId"],
                "doc": q["doc"],
                "docTitle": q["docTitle"],
                "page": q["page"],
                "number": q["number"],
                "question": q["question"],
                "reference": q["reference"],
                "verdict": verdict["verdict"],
                "matchedChunkId": verdict.get("matchedChunkId") or None,
                "matchedDoc": matched["doc"] if matched else None,
                "matchedSection": matched["section"] if matched else None,
                "explanation": verdict["explanation"],
                "citationVerified": citation_verified,
                "candidates": [
                    {"chunkId": c["chunkId"], "doc": c["doc"], "section": c["section"], "score": round(c["score"], 4)}
                    for c in candidates_sorted
                ],
            }
            status = verdict["verdict"] if citation_verified else f"{verdict['verdict']} (UNVERIFIED CITATION)"
        except Exception as err:  # noqa: BLE001
            failures.append({"questionId": q["questionId"], "error": str(err)})
            results[idx] = {
                "questionId": q["questionId"],
                "doc": q["doc"],
                "docTitle": q["docTitle"],
                "page": q["page"],
                "number": q["number"],
                "question": q["question"],
                "reference": q["reference"],
                "verdict": "error",
                "matchedChunkId": None,
                "matchedDoc": None,
                "matchedSection": None,
                "explanation": str(err),
                "citationVerified": None,
                "candidates": [],
            }
            status = f"ERROR: {err}"
        completed += 1
        print(f"  [{completed}/{len(q_meta)}] {q['questionId']} ({status})", flush=True)

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        list(executor.map(process, range(len(q_meta))))

    with open(OUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    from collections import Counter
    tally = Counter(r["verdict"] for r in results)
    print(f"\nWrote {OUT_FILE}")
    print(f"Verdicts: {dict(tally)}")
    if failures:
        print(f"\n{len(failures)} failures:")
        for f in failures:
            print(f" - {f['questionId']}: {f['error']}")


if __name__ == "__main__":
    main()
