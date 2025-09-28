from __future__ import annotations
import math, re, time
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

_WORD = re.compile(r"[A-Za-z0-9]+")

def _tokens(text: str) -> List[str]:
    return [t.lower() for t in _WORD.findall(text or "")]

def _lexical_score(query: str, title: str, snippet: str) -> float:
    q = set(_tokens(query))
    if not q:
        return 0.0
    doc = set(_tokens(title) + _tokens(snippet))
    if not doc:
        return 0.0
    inter = len(q & doc)
    return inter / max(1, len(q))

def _guess_source_type(url: str, title: str, snippet: str) -> str:
    """
    Heuristic, non-domain-specific. We look for structural cues and language patterns.
    Never whitelists/blacklists specific sites — reduces bias.
    """
    u = urlparse(url or "")
    path = (u.path or "").lower()
    host = (u.netloc or "").lower()

    text = f"{title} {snippet}".lower()

    # peer-reviewed-ish: DOI-like patterns, "journal", volume/issue cues
    if re.search(r"\bdoi:\s*10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", text) or \
       re.search(r"\bvol\.\s*\d+\b", text) and re.search(r"\bissue\b|\bno\.\b", text) or \
       "/article/" in path and ("journal" in host or "press" in host):
        return "peer_review"

    # government-ish: TLD or language cues in titles/snippets, not relying on exact domains
    if host.endswith(".gov") or " government" in text or "official site" in text:
        return "government"

    # newsroom/newswire-ish cues
    if any(k in text for k in ["breaking", "newsroom", "press release", "newswire", "ap photo", "reporting by"]):
        return "news"

    # social-like
    if any(k in host for k in ["twitter", "x.com", "facebook", "instagram", "tiktok"]) or \
       any(k in text for k in ["retweet", "posted", "followers", "likes"]):
        return "social"

    # blog/medium-like
    if any(k in path for k in ["/blog/", "/posts/", "/p/"]) or "subscribe" in text:
        return "blog"

    return "web"

# light priors by TYPE (not by specific site) — tunable, bounded, and documented
TYPE_PRIOR = {
    "peer_review": 1.00,
    "government":  0.85,
    "news":        0.70,
    "web":         0.55,
    "blog":        0.45,
    "social":      0.30,
}

def _recency_score(published_at_ts: float | None) -> float:
    if not published_at_ts:
        return 0.5
    # Half-life style: newer is better, but bounded
    age_days = max(0.0, (time.time() - published_at_ts) / 86400.0)
    return 1.0 / (1.0 + age_days / 90.0)

def rank_candidates(*, claim_text: str, query: str, candidates: List[Dict[str, Any]], top_k: int = 6) -> List[Dict[str, Any]]:
    scored: List[Tuple[float, Dict[str, Any]]] = []
    for c in candidates:
        url = c.get("url","")
        title = c.get("title","")
        snippet = c.get("snippet","")
        stype = _guess_source_type(url, title, snippet)
        prior = TYPE_PRIOR.get(stype, 0.5)

        lx = _lexical_score(query, title, snippet)
        rec = _recency_score(None)  # placeholder; if you later parse dates, pass ts here

        # Weighted sum; bounded to [0,1], then scaled to 0..100 for readability downstream
        score = min(1.0, max(0.0, 0.55*lx + 0.30*prior + 0.15*rec))
        scored.append((score, {**c, "rank_features": {"lexical": round(lx,3), "type": stype, "prior": prior, "recency": round(rec,3)}, "rank_score": round(score*100, 1)}))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:top_k]]