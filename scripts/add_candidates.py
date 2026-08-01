"""Backfills the 'candidates' field into an already-computed matches.json
without re-running any LLM calls - the candidate pool (top-10 + same-doc
expansion) is deterministic from the embeddings, so it can be recomputed
for free and attached to the existing verdicts."""
import json
import os

from lib.vectors import load_vectors
from match_all import PP_DIR, ECM_DIR, OUT_FILE, build_candidates

def main():
    obl_meta, obl_vecs = load_vectors(ECM_DIR, "obligations-meta.json")
    pp_meta, pp_vecs = load_vectors(PP_DIR, "chunks-meta.json")
    obl_vec_by_id = {o["obligationId"]: v for o, v in zip(obl_meta, obl_vecs)}

    with open(OUT_FILE) as f:
        matches = json.load(f)

    for m in matches:
        vec = obl_vec_by_id.get(m["obligationId"])
        if vec is None:
            m["candidates"] = []
            continue
        candidates = build_candidates(vec, pp_meta, pp_vecs)
        candidates.sort(key=lambda c: -c["score"])
        m["candidates"] = [
            {"chunkId": c["chunkId"], "doc": c["doc"], "section": c["section"], "score": round(c["score"], 4)}
            for c in candidates
        ]

    with open(OUT_FILE, "w") as f:
        json.dump(matches, f, indent=2)

    sizes = [len(m["candidates"]) for m in matches]
    print(f"Backfilled candidates for {len(matches)} matches (avg {sum(sizes)/len(sizes):.1f} candidates each)")
    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
