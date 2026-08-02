"""Shared judgment-call wrapper for match_all.py / match_questionnaire.py.
Adds a citation-integrity guardrail on top of judge_obligation(): the LLM can
occasionally cite a matchedChunkId that's a real chunk in the corpus but
wasn't actually among the candidates it was shown for that call (same class
of failure as source-quote hallucination in the extraction step, just at the
judgment step instead). Retries a couple of times, then marks the record
verified=False for human review rather than silently trusting an unverified
citation."""
import time

from lib.gemini_client import judge_obligation


def judge_with_verification(api_key, text, candidates, max_attempts=4, verify_attempts=2):
    candidate_ids = {c["chunkId"] for c in candidates}
    last_verdict = None

    for attempt in range(1, verify_attempts + 1):
        last_verdict = _judge_with_retry(api_key, text, candidates, max_attempts)
        matched_id = last_verdict.get("matchedChunkId")
        if not matched_id or matched_id in candidate_ids:
            return last_verdict, True  # verdict is "gap" (no citation) or a real, shown candidate

    return last_verdict, False  # gave up after verify_attempts; flag for review


def _judge_with_retry(api_key, text, candidates, max_attempts):
    for attempt in range(1, max_attempts + 1):
        try:
            return judge_obligation(api_key, text, candidates)
        except Exception:
            if attempt == max_attempts:
                raise
            time.sleep(2 ** attempt)
