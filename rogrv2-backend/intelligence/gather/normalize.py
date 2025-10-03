from __future__ import annotations
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import re

__all__ = ["dedupe", "normalize_candidates"]

_TRACKING_PREFIXES = (
    "utm_", "gclid", "fbclid", "mc_cid", "mc_eid", "igshid", "ref", "ref_src",
)

_DEF_PROVIDER_WEIGHT = {
    # Equal weights to preserve zero-bias; do not privilege providers
    "brave": 1.0,
    "google": 1.0,
    "bing": 1.0,
}

_WORD_RE = re.compile(r"[A-Za-z0-9%]+")


def _extract_domain(u: str) -> str:
    try:
        p = urlparse(u or "")
        host = (p.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def _canonical_url(u: str) -> str:
    try:
        p = urlparse(u or "")
        host = (p.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        path = p.path or "/"
        # Drop fragments
        frag = ""
        # Filter tracking params, keep stable ordering
        q_pairs = [(k, v) for (k, v) in parse_qsl(p.query, keep_blank_values=False) if not any(k.startswith(pref) for pref in _TRACKING_PREFIXES)]
        query = urlencode(q_pairs)
        return urlunparse((p.scheme or "https", host, path, "", query, frag))
    except Exception:
        return u or ""


def _text_score(title: str, snippet: str) -> float:
    """Lightweight, neutral signal based only on textual self-evidence.
    - counts presence of numbers/% and repeated claim-like tokens
    - does not use domain or source priors
    """
    t = (title or "") + "\n" + (snippet or "")
    toks = _WORD_RE.findall(t.lower())
    if not toks:
        return 0.0
    has_percent = any("%" in w or w.endswith("percent") for w in toks)
    has_number = any(c.isdigit() for c in "".join(toks))
    # prefer items with some structure in title
    title_boost = 0.2 if (title and len(title) > 30) else 0.0
    base = 0.2 * float(has_percent) + 0.2 * float(has_number) + title_boost
    # light token density signal
    density = min(0.6, 0.6 * (len(toks) / 60.0))
    return max(0.0, min(1.0, base + density))


def _penalize_duplicates(order_idx: int) -> float:
    # small monotonic penalty for repeated domains/urls later in the list
    # keeps earlier unique domains higher without hard filters
    return max(0.0, 1.0 - 0.05 * order_idx)


def _score_item(it: Dict[str, Any], seen_for_domain: int) -> float:
    prov = (it.get("provider") or "").lower()
    p_w = _DEF_PROVIDER_WEIGHT.get(prov, 1.0)
    s_txt = _text_score(it.get("title"), it.get("snippet"))
    dup_pen = _penalize_duplicates(seen_for_domain)
    score = p_w * (0.6 + 0.4 * s_txt) * dup_pen
    return max(0.0, min(1.0, score))


def dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate, annotate, and order evidence neutrally.
    - Canonicalize URL and compute domain
    - Remove exact duplicate canonical URLs (keep first)
    - Score items using neutral textual/self-evidence signals (no source priors)
    - Order within arms by score desc; add per-arm rank starting at 1
    """
    items = [it for it in (items or []) if isinstance(it, dict)]
    # Canonicalize and drop exact dup URLs
    seen_url = set()
    domain_counts: Dict[str, int] = {}
    cleaned: List[Dict[str, Any]] = []
    for it in items:
        url = it.get("url") or it.get("link") or ""
        can = _canonical_url(url)
        if not can or can in seen_url:
            continue
        seen_url.add(can)
        dom = _extract_domain(can)
        it2 = dict(it)
        it2["url"] = can
        it2.setdefault("domain", dom)
        # Count domain occurrences so far to set duplicate penalty order
        cnt = domain_counts.get(dom, 0)
        domain_counts[dom] = cnt + 1
        # score will be set later per-arm to ensure fair ordering
        cleaned.append(it2)

    # Split by arm label
    armA: List[Dict[str, Any]] = []
    armB: List[Dict[str, Any]] = []
    for it in cleaned:
        arm = (it.get("arm") or "A").upper()
        if arm.startswith("B"):
            armB.append(it)
        else:
            armA.append(it)

    # Score per arm with per-domain sequence consideration
    def _score_and_sort(lst: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        domain_seen: Dict[str, int] = {}
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for it in lst:
            d = (it.get("domain") or "")
            ord_idx = domain_seen.get(d, 0)
            domain_seen[d] = ord_idx + 1
            sc = _score_item(it, ord_idx)
            it3 = dict(it)
            it3["score"] = sc
            scored.append((sc, it3))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = [it for (_sc, it) in scored]
        # assign rank starting at 1
        for i, it in enumerate(out, start=1):
            it["rank"] = i
        return out

    armA = _score_and_sort(armA)
    armB = _score_and_sort(armB)

    # Recombine; order A then B (downstream groups preserve order per arm)
    return armA + armB


def normalize_candidates(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize and return a FLAT list of candidate dicts, as expected by rankers.
    Items are deduped, canonicalized, scored, and include their original arm labels.
    """
    return dedupe(items or [])
