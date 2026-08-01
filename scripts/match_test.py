import os
import sys

from lib.vectors import load_vectors, cosine, top_k
from lib.gemini_client import judge_obligation

PP_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "plan_policies")
ECM_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "ecm_guide")

TOP_K = 10
SAME_DOC_CAP = 50  # guard against outlier docs (e.g. the 313-chunk glossary)


def build_candidates(obl_vec, pp_meta, pp_vecs):
    top = top_k(obl_vec, pp_vecs, TOP_K)
    top_indices = [i for _, i in top]

    # Same-document expansion: pull in the rest of the top-1 match's document
    # too, since Alex's own failure mode is a contradiction "two pages later"
    # in the *same* policy, which may not be the single closest sentence.
    top_doc = pp_meta[top_indices[0]]["doc"]
    same_doc_indices = [i for i, c in enumerate(pp_meta) if c["doc"] == top_doc]
    if len(same_doc_indices) > SAME_DOC_CAP:
        same_doc_indices = same_doc_indices[:SAME_DOC_CAP]

    all_indices = list(dict.fromkeys(top_indices + same_doc_indices))  # de-dup, preserve order
    return [
        {
            "chunkId": pp_meta[i]["chunkId"],
            "doc": pp_meta[i]["doc"],
            "section": pp_meta[i]["section"],
            "text": pp_meta[i]["text"],
        }
        for i in all_indices
    ]


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    obl_meta, obl_vecs = load_vectors(ECM_DIR, "obligations-meta.json")
    pp_meta, pp_vecs = load_vectors(PP_DIR, "chunks-meta.json")

    # Real obligations from the actual extracted data: one we expect strong
    # coverage for, one we suspect is a genuine gap, and a few unexamined ones
    # for a representative spread.
    moc_idx = next(i for i, o in enumerate(obl_meta) if "Provider capacity" in o["obligation"])
    aging_out_idx = next(i for i, o in enumerate(obl_meta) if "aging out" in o["obligation"])
    other_indices = [0, 50, 200, 400]
    indices = [moc_idx, aging_out_idx] + other_indices

    for idx in indices:
        o = obl_meta[idx]
        candidates = build_candidates(obl_vecs[idx], pp_meta, pp_vecs)
        result = judge_obligation(api_key, o["obligation"], candidates)

        print(f"=== obligation[{idx}] (p.{o['page']} of {o['doc']}) ===")
        print(f"  {o['obligation']}")
        print(f"  -> verdict: {result['verdict']}")
        if result.get("matchedChunkId"):
            match = next((c for c in candidates if c["chunkId"] == result["matchedChunkId"]), None)
            if match:
                print(f"  -> matched: [{match['chunkId']}] {match['doc']} {match['section']}")
                print(f"     {match['text'][:200]}")
        print(f"  -> explanation: {result['explanation']}")
        print()


if __name__ == "__main__":
    main()
