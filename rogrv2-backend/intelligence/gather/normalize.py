from __future__ import annotations
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import hashlib

def canonical_url(raw: str) -> str:
    """
    Conservative URL canonicalizer: normalize scheme/host, drop fragments,
    sort query, and strip obvious tracking params.
    """
    if not raw:
        return raw
    u = urlparse(raw)
    scheme = (u.scheme or "http").lower()
    netloc = (u.netloc or "").lower()
    path = u.path or "/"
    # sort query params and drop common trackers
    DROP = {"utm_source","utm_medium","utm_campaign","utm_term","utm_content","gclid","fbclid","yclid"}
    q = [(k, v) for (k, v) in parse_qsl(u.query, keep_blank_values=True) if k not in DROP]
    q.sort()
    query = urlencode(q, doseq=True)
    return urlunparse((scheme, netloc, path, "", query, ""))

def _fingerprint(item: Dict[str, Any]) -> str:
    """Stable dedupe key across providers using canonical URL + title/snippet."""
    url = canonical_url(item.get("url",""))
    title = (item.get("title") or "").strip()
    snippet = (item.get("snippet") or "").strip()
    h = hashlib.sha256()
    h.update(url.encode("utf-8", errors="ignore"))
    h.update(b"\x00")
    h.update(title.encode("utf-8", errors="ignore"))
    h.update(b"\x00")
    h.update(snippet.encode("utf-8", errors="ignore"))
    return h.hexdigest()

def normalize_candidates(items: List[Dict[str, Any]], *, max_per_domain: int = 3) -> List[Dict[str, Any]]:
    """
    Input: list of dicts with at least {url,title,snippet}.
    Output: deterministic, deduped, lightly enriched list:
      - adds 'canonical_url'
      - enforces per-domain cap to avoid flooding from one site
      - removes exact dupes via fingerprint
    """
    seen_fps = set()
    per_domain: Dict[str, int] = {}
    out: List[Dict[str, Any]] = []

    for it in items or []:
        url = it.get("url") or ""
        if not url:
            continue
        cu = canonical_url(url)
        fp = _fingerprint({**it, "url": cu})
        if fp in seen_fps:
            continue
        seen_fps.add(fp)

        domain = urlparse(cu).netloc
        count = per_domain.get(domain, 0)
        if count >= max_per_domain:
            continue
        per_domain[domain] = count + 1

        norm = dict(it)
        norm["canonical_url"] = cu
        norm["dedupe_key"] = fp
        out.append(norm)

    return out

# Ensure these public helpers exist; keep signatures simple and total-order deterministic.
from typing import List, Dict, Any

def normalize_candidates(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize list of search candidates to {url,title,snippet} and strip obvious junk."""
    out: List[Dict[str, Any]] = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        url = (it.get("url") or "").strip()
        if not url:
            continue
        out.append({
            "url": url,
            "title": (it.get("title") or "").strip(),
            "snippet": (it.get("snippet") or "").strip(),
        })
    return out

def dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate URLs (case-insensitive)."""
    seen = set()
    out = []
    for it in items or []:
        u = (it.get("url") or "").strip().lower()
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(it)
    return out