from typing import Dict, List
from urllib.parse import urlparse
import hashlib

def _norm(s: str) -> str:
    return " ".join((s or "").split())

def _dedupe_key(url: str, title: str) -> str:
    h = hashlib.sha1((_norm(url) + "||" + _norm(title)).encode("utf-8")).hexdigest()
    return h[:16]

def _publisher_from_url(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
    except Exception:
        netloc = ""
    return netloc

def normalize_candidates(cands: List[Dict]) -> List[Dict]:
    out: List[Dict] = []
    seen = set()
    for c in cands or []:
        url = _norm(c.get("url",""))
        title = _norm(c.get("title",""))
        snippet = _norm(c.get("snippet",""))
        if not url:
            continue
        dk = _dedupe_key(url, title or url)
        if dk in seen:
            continue
        seen.add(dk)
        out.append({
            "url": url,
            "title": title,
            "snippet": snippet,
            "publisher": _publisher_from_url(url),
            "dedupe_key": dk,
        })
    return out