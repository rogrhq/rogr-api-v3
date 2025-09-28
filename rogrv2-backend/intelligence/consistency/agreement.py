from __future__ import annotations
import re
from typing import Dict, List, Tuple
from urllib.parse import urlparse

_WORD_RE = re.compile(r"[A-Za-z0-9]+")

def _domain(u: str) -> str:
    try:
        netloc = urlparse(u).netloc.lower()
        # strip common prefixes
        for p in ("www.", "m.", "mobile."):
            if netloc.startswith(p):
                return netloc[len(p):]
        return netloc
    except Exception:
        return ""

def _tokens(s: str) -> List[str]:
    return [w.lower() for w in _WORD_RE.findall(s or "") if len(w) > 2]

def _content_tokens(item: Dict) -> List[str]:
    title = (item.get("title") or "")
    snip  = (item.get("snippet") or "")
    return _tokens(title + " " + snip)

def measure_agreement(armA: List[Dict], armB: List[Dict]) -> Dict[str, object]:
    """
    Deterministic, cheap signal of cross-arm agreement:
    - token_overlap_jaccard over top-1 items (if present)
    - shared_domains_count across both arms (unique)
    - url_exact_matches between arms
    Returns a normalized dict with small-integer or bounded-float metrics.
    """
    a0 = armA[0] if armA else {}
    b0 = armB[0] if armB else {}

    # Jaccard on tokens of top items
    A_tokens = set(_content_tokens(a0))
    B_tokens = set(_content_tokens(b0))
    inter = len(A_tokens & B_tokens)
    union = len(A_tokens | B_tokens) or 1
    jacc = round(inter / union, 3)

    # Domain overlaps (set-based across arms)
    A_domains = { _domain(x.get("url","")) for x in (armA or []) if x.get("url") }
    B_domains = { _domain(x.get("url","")) for x in (armB or []) if x.get("url") }
    shared_domains = len((A_domains & B_domains) - {""})

    # Exact URL overlaps
    A_urls = { (x.get("url") or "").strip() for x in (armA or []) if x.get("url") }
    B_urls = { (x.get("url") or "").strip() for x in (armB or []) if x.get("url") }
    exact_matches = len((A_urls & B_urls) - {""})

    return {
        "token_overlap_jaccard": jacc,
        "shared_domains": int(shared_domains),
        "exact_url_matches": int(exact_matches),
        "top_domains_A": sorted(list(A_domains - {""}))[:5],
        "top_domains_B": sorted(list(B_domains - {""}))[:5],
    }