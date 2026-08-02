"""One-off repair: adds citationVerified to every existing ECM match record,
and re-processes only the specific records where matchedChunkId wasn't
actually in the candidates shown to the LLM (a hallucinated citation),
using the new judge_with_verification guardrail - rather than re-running
all 518 (already-correct) records again."""
import json
import os

from lib.vectors import load_vectors
from lib.match_helpers import judge_with_verification
from match_all import PP_DIR, ECM_DIR, OUT_FILE, build_candidates


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    obl_meta, obl_vecs = load_vectors(ECM_DIR, "obligations-meta.json")
    pp_meta, pp_vecs = load_vectors(PP_DIR, "chunks-meta.json")
    pp_by_chunk_id = {c["chunkId"]: c for c in pp_meta}
    obl_vec_by_id = {o["obligationId"]: v for o, v in zip(obl_meta, obl_vecs)}
    obl_by_id = {o["obligationId"]: o for o in obl_meta}

    with open(OUT_FILE) as f:
        matches = json.load(f)

    repaired = 0
    for m in matches:
        candidate_ids = {c["chunkId"] for c in m["candidates"]}
        is_consistent = not m["matchedChunkId"] or m["matchedChunkId"] in candidate_ids

        if is_consistent:
            m["citationVerified"] = True
            continue

        print(f"Repairing {m['obligationId']} (was citing unshown chunk {m['matchedChunkId']})...")
        obligation = obl_by_id[m["obligationId"]]
        vec = obl_vec_by_id[m["obligationId"]]
        candidates = build_candidates(vec, pp_meta, pp_vecs)
        verdict, citation_verified = judge_with_verification(api_key, obligation["obligation"], candidates)
        matched = pp_by_chunk_id.get(verdict.get("matchedChunkId", "")) if citation_verified else None
        candidates_sorted = sorted(candidates, key=lambda c: -c["score"])

        m["verdict"] = verdict["verdict"]
        m["matchedChunkId"] = verdict.get("matchedChunkId") or None
        m["matchedDoc"] = matched["doc"] if matched else None
        m["matchedSection"] = matched["section"] if matched else None
        m["explanation"] = verdict["explanation"]
        m["citationVerified"] = citation_verified
        m["candidates"] = [
            {"chunkId": c["chunkId"], "doc": c["doc"], "section": c["section"], "score": round(c["score"], 4)}
            for c in candidates_sorted
        ]
        repaired += 1
        print(f"  -> new verdict: {m['verdict']}, verified: {citation_verified}")

    with open(OUT_FILE, "w") as f:
        json.dump(matches, f, indent=2)

    print(f"\nRepaired {repaired} record(s). Wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
