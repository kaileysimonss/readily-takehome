"""Thin REST client for Gemini embeddings and structured-output extraction
(kept as plain HTTP calls via requests rather than the SDK, for transparency
and to avoid an extra dependency)."""
import json
import math
import time

import requests

EMBED_MODEL = "gemini-embedding-001"
EXTRACT_MODEL = "gemini-2.5-flash"


def normalize(values):
    norm = math.sqrt(sum(x * x for x in values))
    return [x / norm for x in values] if norm > 0 else values


def embed_batch(api_key, texts, dim=768, max_retries=5):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{EMBED_MODEL}:batchEmbedContents?key={api_key}"
    body = {
        "requests": [
            {
                "model": f"models/{EMBED_MODEL}",
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": dim,
            }
            for text in texts
        ]
    }

    for attempt in range(1, max_retries + 1):
        res = requests.post(url, json=body, timeout=90)
        if res.ok:
            data = res.json()
            return [normalize(e["values"]) for e in data["embeddings"]]
        if res.status_code == 429 or res.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        raise RuntimeError(f"Embedding request failed ({res.status_code}): {res.text}")

    raise RuntimeError("Embedding request failed after retries")


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "obligations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "obligation": {
                        "type": "string",
                        "description": (
                            "A single, atomic, checkable compliance requirement, rewritten "
                            "clearly and standalone (understandable without reading the "
                            "surrounding text)."
                        ),
                    },
                    "sourceQuote": {
                        "type": "string",
                        "description": (
                            "The exact verbatim sentence or clause from the source text that "
                            "this obligation was extracted from. Always the complete sentence "
                            "- never truncate or elide part of it with an ellipsis."
                        ),
                    },
                    "page": {
                        "type": "integer",
                        "description": "The page number (from the [PAGE N] marker) where the sourceQuote appears.",
                    },
                },
                "required": ["obligation", "sourceQuote", "page"],
            },
        }
    },
    "required": ["obligations"],
}

SYSTEM_PROMPT = """You are helping a Medi-Cal managed care plan's compliance analyst read a dense DHCS regulatory Policy Guide and pull out every concrete, checkable obligation buried in the narrative text.

Rules:
- Extract every discrete compliance obligation - a requirement a plan must, shall, or must not do. A single paragraph may contain one obligation or several; split them out individually rather than summarizing the paragraph as one item.
- Each "obligation" must be atomic (one checkable requirement) and self-contained (understandable on its own, without needing the surrounding paragraph for context). Rewrite for clarity if needed, but do not change the meaning or add requirements that aren't stated.
- PRESERVE THE MODAL STRENGTH of the source exactly. "Must" / "shall" / "is required to" = mandatory. "Should" = a recommendation, not mandatory. "May" = permissive/optional. Never upgrade a "should" or "may" into a "must" when rewriting - if the source says "should", the obligation must also say "should" (or equivalent recommendation language), not "must". This distinction is critical for compliance accuracy.
- "sourceQuote" must be the COMPLETE, exact verbatim sentence(s) copied character-for-character from the source. Never truncate it or insert "..." in the middle - if the supporting text is long, quote the full sentence(s) anyway, do not shorten it.
- Do NOT include background information, definitions, history, or purely descriptive statements that don't impose a requirement on the plan.
- Do NOT merge multiple distinct requirements into one obligation.
- For each obligation, include "page": the page number from the nearest preceding [PAGE N] marker in the source text.
- If a section contains no obligations (e.g. pure background/history), extract nothing from it.

The source text follows, with [PAGE N] markers inserted at page boundaries."""


def extract_obligations(api_key, page_tagged_text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{EXTRACT_MODEL}:generateContent?key={api_key}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{page_tagged_text}"}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
            "temperature": 0,
        },
    }

    res = requests.post(url, json=body, timeout=90)
    if not res.ok:
        raise RuntimeError(f"Gemini extraction failed ({res.status_code}): {res.text}")

    data = res.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(text)
    return parsed.get("obligations", [])


JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["supports", "partial", "contradicts", "gap"],
            "description": (
                "'supports' if a candidate EXPLICITLY and directly states the requirement "
                "(paraphrasing/different terminology is fine, but the requirement itself must "
                "be directly stated, not inferred through multi-step reasoning). "
                "'partial' if a candidate is relevant and suggests the requirement may be met, "
                "but only via indirect inference, incomplete coverage, or reasoning the "
                "candidate text doesn't spell out itself - needs human verification. "
                "'contradicts' if a candidate asserts something that conflicts with the "
                "obligation (different timeframe, opposite requirement, narrower/broader scope). "
                "'gap' if no candidate addresses the obligation at all, even indirectly."
            ),
        },
        "matchedChunkId": {
            "type": "string",
            "description": "The chunkId of the P&P excerpt driving the verdict. Empty string if verdict is 'gap'.",
        },
        "explanation": {
            "type": "string",
            "description": "One or two sentences explaining the verdict, referencing the specific language that drove the decision.",
        },
    },
    "required": ["verdict", "matchedChunkId", "explanation"],
}

JUDGE_PROMPT = """You are helping a Medi-Cal managed care plan's compliance analyst determine whether the plan's existing Policy & Procedure (P&P) documents already satisfy a specific regulatory obligation from a DHCS Policy Guide. Her own words: "I'd rather take three days than be fast and wrong" - findings from being wrong go to the state and her board. Be conservative accordingly.

You will be given:
1. An OBLIGATION extracted from the DHCS Policy Guide.
2. A list of CANDIDATE excerpts from the plan's own P&P documents (each with a chunkId, document code, section, and text), retrieved because they are semantically similar to the obligation.

Your job: read the candidates carefully and choose one of four verdicts:

- "supports": a candidate EXPLICITLY and directly states the same requirement as the obligation. Different terminology or phrasing is fine (e.g. "post-service review" may be the same thing as "retrospective request") - what matters is that the requirement itself is directly stated in the P&P, not something a reader has to infer or reason their way to. If you found yourself building a multi-step logical argument for why a candidate implies compliance, that is NOT "supports" - see "partial" below.

- "partial": a candidate is genuinely relevant and suggests the obligation may be met, but only through indirect inference (e.g. "this policy implies X because it says Y, and Y logically rules out not-X") or incomplete coverage (addresses part of the obligation but not all of it). This should be flagged for a human to verify, not treated as proven compliance - a DHCS reviewer typically wants an explicit statement, not an inferred argument.

- "contradicts": a candidate addresses the same topic but conflicts with the obligation - e.g. a different timeframe, an opposite requirement ("may" vs "may not"), or a narrower/broader scope than the obligation requires. This is critical to catch: two passages can look nearly identical on the surface (same topic, same vocabulary, even high semantic similarity) while asserting opposite requirements, so read for actual meaning, not topical overlap.

- "gap": no candidate addresses the obligation, even indirectly. Being topically related is not enough - the candidate must actually bear on the specific requirement.

When genuinely torn between two verdicts, prefer the more conservative one (partial over supports, gap over partial) - a compliance analyst would rather manually double-check a flagged item than have a real gap or inference silently presented as proven compliance."""


def judge_obligation(api_key, obligation_text, candidates):
    """candidates: list of {"chunkId", "doc", "section", "text"}."""
    candidates_text = "\n\n".join(
        f"[{c['chunkId']}] ({c['doc']} {c['section']})\n{c['text']}" for c in candidates
    )
    prompt = f"{JUDGE_PROMPT}\n\nOBLIGATION:\n{obligation_text}\n\nCANDIDATES:\n{candidates_text}"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{EXTRACT_MODEL}:generateContent?key={api_key}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": JUDGE_SCHEMA,
            "temperature": 0,
        },
    }

    res = requests.post(url, json=body, timeout=90)
    if not res.ok:
        raise RuntimeError(f"Gemini judgment failed ({res.status_code}): {res.text}")

    data = res.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)
