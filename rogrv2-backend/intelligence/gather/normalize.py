from __future__ import annotations
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse, urlunparse
import re, hashlib

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
from typing import Any, Dict, List, Tuple

_WS = re.compile(r"\s+")

def _clean_title(t: str) -> str:
    return _WS.sub(" ", (t or "").strip())

def canonical_url(url: str) -> str:
    u = urlparse(url or "")
    # strip fragments & queries for canonical form
    u = u._replace(fragment="", query="")
    # normalize scheme+host lowercasing
    scheme = (u.scheme or "https").lower()
    netloc = (u.netloc or "").lower()
    clean = urlunparse((scheme, netloc, u.path or "", "", "", ""))
    return clean

def _fingerprint(title: str, url: str) -> str:
    t = _clean_title(title).lower()
    u = canonical_url(url)
    return hashlib.sha1(f"{t}|{u}".encode("utf-8")).hexdigest()

def _similar(a: str, b: str) -> float:
    # very light similarity by token overlap (0..1)
    at = set(re.findall(r"[A-Za-z0-9]+", (a or "").lower()))
    bt = set(re.findall(r"[A-Za-z0-9]+", (b or "").lower()))
    if not at or not bt:
        return 0.0
    inter = len(at & bt)
    return inter / max(1, len(at | bt))

def normalize_candidates(cands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    1) Canonicalize URL & clean title
    2) Drop exact dupes
    3) Collapse near-duplicates by title similarity (≥0.8) keeping first
    """
    exact_seen = set()
    kept: List[Dict[str, Any]] = []
    for c in cands or []:
        url = canonical_url(c.get("url",""))
        title = _clean_title(c.get("title",""))
        key = (url, title)
        if key in exact_seen:
            continue
        exact_seen.add(key)
        kept.append({**c, "url": url, "title": title, "fp": _fingerprint(title, url)})

    # near-duplicate collapse by title similarity
    out: List[Dict[str, Any]] = []
    for cand in kept:
        if any(_similar(cand["title"], x["title"]) >= 0.80 for x in out):
            continue
        out.append(cand)
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