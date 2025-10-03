from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

__all__ = ["normalize_candidates", "dedupe"]

# -----------------------
# Helpers
# -----------------------

def _first(*vals: Optional[str]) -> Optional[str]:
    for v in vals:
        if v:
            return v
    return None


def _normalize_url(url: Optional[str]) -> str:
    """
    Normalize a URL for deduping:
      - lower-case scheme/host
      - strip default ports
      - drop common tracking params (utm_*, gclid, fbclid, ref)
      - keep path and essential query parameters order-insensitively
    """
    if not url:
        return ""
    try:
        p = urlparse(url.strip())
        netloc = (p.hostname or "").lower()
        if p.port and ((p.scheme == "http" and p.port != 80) or (p.scheme == "https" and p.port != 443)):
            netloc = f"{netloc}:{p.port}"
        # filter query params
        drop = {"gclid", "fbclid", "ref"}
        qs = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not (k.startswith("utm_") or k in drop)]
        qs.sort()
        q = urlencode(qs)
        norm = urlunparse((p.scheme.lower(), netloc, p.path or "/", "", q, ""))
        return norm
    except Exception:
        return url.strip()


def _domain_from_url(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""

# -----------------------
# Public API
# -----------------------

def normalize_candidates(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Production-safe normalizer that PRESERVES critical metadata:
      - 'arm' (canonical 'A'/'B' if upstream stamped; otherwise left as-is)
      - 'provider' (engine/source tag)
      - 'query_used' (original query)
      - 'age_days' (if present upstream)
    It also ensures core fields exist: url, title, snippet.
    """
    out: List[Dict[str, Any]] = []
    for it in items or []:
        if not isinstance(it, dict):
            continue

        url = _first(
            it.get("url"),
            it.get("link"),
            it.get("source_url"),
            it.get("resolved_url"),
        )
        title = _first(
            it.get("title"),
            it.get("name"),
            it.get("headline"),
        ) or ""
        snippet = _first(
            it.get("snippet"),
            it.get("summary"),
            it.get("description"),
            it.get("text"),
        ) or ""

        provider = _first(
            it.get("provider"),
            it.get("engine"),
            it.get("source"),
        ) or "unknown"

        arm_raw = str(it.get("arm") or "").upper()
        if arm_raw.startswith("A"):
            arm = "A"
        elif arm_raw.startswith("B"):
            arm = "B"
        else:
            # Leave non-canonical labels as-is; upstream should stamp 'A'/'B'
            arm = it.get("arm") or ""

        norm: Dict[str, Any] = {
            "url": url or "",
            "title": title,
            "snippet": snippet,
            "provider": provider,
            "arm": arm,
            "query_used": _first(it.get("query_used"), it.get("q"), it.get("query")) or "",
        }

        # Preserve optional/diagnostic metadata if present
        for key in ("age_days", "published_at", "domain", "score", "stance", "stance_score"):
            if key in it:
                norm[key] = it[key]

        # Derived convenience fields (non-invasive)
        if norm["url"] and "domain" not in norm:
            norm["domain"] = _domain_from_url(norm["url"])

        out.append(norm)
    return out


def dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deterministic, stable de-duplication for provider candidates.
    Priority keys:
      1) normalized URL
      2) (title, domain) tuple when URL absent or different mirrors
    Preserves input order; keeps the first occurrence.
    """
    out: List[Dict[str, Any]] = []
    seen_url: set[str] = set()
    seen_title_domain: set[Tuple[str, str]] = set()

    for it in items or []:
        if not isinstance(it, dict):
            continue

        url = _normalize_url(it.get("url") or it.get("link") or it.get("source_url") or it.get("resolved_url") or "")
        title = (it.get("title") or it.get("name") or it.get("headline") or "").strip().lower()
        domain = _domain_from_url(url) if url else (it.get("domain") or "").strip().lower()

        key_url = url
        key_td = (title, domain)

        # Decide if duplicate
        is_dup = False
        if key_url:
            if key_url in seen_url:
                is_dup = True
            else:
                seen_url.add(key_url)

        # If no URL or still potentially mirror content, check title/domain
        if not is_dup and title:
            if key_td in seen_title_domain:
                is_dup = True
            else:
                seen_title_domain.add(key_td)

        if not is_dup:
            out.append(it)

    return out
