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
        res = requests.post(url, json=body)
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

    res = requests.post(url, json=body)
    if not res.ok:
        raise RuntimeError(f"Gemini extraction failed ({res.status_code}): {res.text}")

    data = res.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(text)
    return parsed.get("obligations", [])
