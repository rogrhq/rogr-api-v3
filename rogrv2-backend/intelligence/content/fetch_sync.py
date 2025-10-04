from __future__ import annotations
from typing import Dict, Any
import httpx
import re
import html as _html

__all__ = ["fetch_text", "html_to_text"]

_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(r"<script[\s\S]*?</script>", re.IGNORECASE)
_STYLE_RE = re.compile(r"<style[\s\S]*?</style>", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")

HEADERS = {
    "User-Agent": "ROGRv2/1.0 (+https://rogr.local)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


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
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=HEADERS) as client:
            r = client.get(url)
            ct = (r.headers.get("content-type") or "").lower()
            text = ""
            if r.status_code == 200 and ("text/html" in ct or "application/xhtml+xml" in ct or ct.startswith("text/")):
                # best-effort decoding via httpx
                text = html_to_text(r.text)
            return {"status": int(r.status_code), "content_type": ct, "text": text}
    except Exception:
        return {"status": 0, "content_type": "", "text": ""}
