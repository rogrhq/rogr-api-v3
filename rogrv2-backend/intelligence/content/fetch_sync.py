from __future__ import annotations
from typing import Dict, Any
import httpx
import re
import html as _html
import os

__all__ = ["fetch_text", "html_to_text"]

_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(r"<script[\s\S]*?</script>", re.IGNORECASE)
_STYLE_RE = re.compile(r"<style[\s\S]*?</style>", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")

HEADERS = {
    "User-Agent": "ROGRv2/1.0 (+https://rogr.local)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# simple in-process cache to avoid refetching the same URL within a test run
_CACHE: dict[str, Dict[str, Any]] = {}


def html_to_text(html: str) -> str:
    if not html:
        return ""
    s = _SCRIPT_RE.sub(" ", html)
    s = _STYLE_RE.sub(" ", s)
    s = _TAG_RE.sub(" ", s)
    s = _html.unescape(s)
    s = _WS_RE.sub(" ", s)
    return s.strip()


def fetch_text(url: str, *, timeout: float = 8.0) -> Dict[str, Any]:
    """Synchronous fetch for HTML-like content. Returns dict with keys:
    {status, content_type, text}  (text empty if not HTML or error)
    """
    try:
        # allow env override of timeout and max bytes
        try:
            timeout = float(os.getenv("ROGR_FETCH_TIMEOUT", str(timeout)))
        except Exception:
            pass
        try:
            max_bytes = int(os.getenv("ROGR_FETCH_MAX_BYTES", "80000"))
        except Exception:
            max_bytes = 80000

        # cache hit
        cached = _CACHE.get(url)
        if cached is not None:
            return cached

        with httpx.Client(timeout=httpx.Timeout(connect=timeout, read=timeout, write=timeout, pool=timeout), follow_redirects=True, headers=HEADERS) as client:
            text = ""
            ct = ""
            status = 0
            # stream and only read a limited amount to reduce latency
            with client.stream("GET", url) as r:
                status = int(r.status_code)
                ct = (r.headers.get("content-type") or "").lower()
                if status == 200 and ("text/html" in ct or "application/xhtml+xml" in ct or ct.startswith("text/")):
                    collected = bytearray()
                    for chunk in r.iter_bytes():
                        if not chunk:
                            break
                        collected.extend(chunk)
                        if len(collected) >= max_bytes:
                            break
                    try:
                        text = collected.decode(r.encoding or "utf-8", errors="ignore")
                    except Exception:
                        text = collected.decode("utf-8", errors="ignore")
            if status == 200 and text:
                text = html_to_text(text)
            res = {"status": status, "content_type": ct, "text": text}
            # populate cache (bounded)
            if len(_CACHE) > 200:
                # drop an arbitrary item (simple bound; deterministic not required here)
                _CACHE.pop(next(iter(_CACHE)))
            _CACHE[url] = res
            return res
    except Exception:
        return {"status": 0, "content_type": "", "text": ""}
