"""Cheap hallucination check: verify a quoted string actually appears in the
page text it's claimed to come from. Strips ALL whitespace (not just
collapsing it) before comparing, since PDF extraction sometimes inserts a
stray space mid-word (e.g. "referral" -> "referr al") that would otherwise
cause a false-positive flag on an accurate quote."""
import re


def _normalize(s):
    s = s.lower()
    s = re.sub(r"[-‐-―]", "", s)  # hyphens/soft-hyphens
    s = re.sub(r"\s+", "", s)  # strip ALL whitespace for comparison
    return s


def quote_verified(quote, page_text):
    return _normalize(quote) in _normalize(page_text)
