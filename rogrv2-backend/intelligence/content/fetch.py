from __future__ import annotations
import asyncio
import html as htmlmod
import re
from typing import Any, Dict, Optional

import httpx

_UA = "ROGRv2/preview-fetch (+https://example.local; contact: engineering@local)"
_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_WS_RE = re.compile(r"\s+")

def _html_to_text(html: str) -> str:
    if not html:
        return ""
    # remove script/style first
    html = _SCRIPT_RE.sub(" ", html)
    # drop all tags
    text = _TAG_RE.sub(" ", html)
    # unescape entities, normalize whitespace
    text = htmlmod.unescape(text)
    text = _WS_RE.sub(" ", text).strip()
    return text

async def fetch_text(url: str, *, timeout: float = 10.0, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Canonical async fetcher.
    Returns:
      {
        "text": <str>,                # empty when non-HTML or error
        "status": <int|str>,          # HTTP status or "error"
        "mime": <str|None>,           # e.g., "text/html; charset=utf-8"
        "final_url": <str|None>,      # after redirects
      }
    """
    h = {"User-Agent": _UA}
    if headers:
        h.update(headers)
    try:
        async with httpx.AsyncClient(follow_redirects=True, headers=h, timeout=timeout) as client:
            resp = await client.get(url)
            mime = resp.headers.get("content-type", "")
            final_url = str(resp.url) if resp.url else url
            text = ""
            if "text/html" in mime.lower():
                # Try response.text (decoded); fallback to bytes decode
                try:
                    text = resp.text
                except Exception:
                    text = resp.content.decode("utf-8", "ignore")
                text = _html_to_text(text)
            # For non-HTML (pdf, etc.), leave text empty; upstream decides handling later
            return {"text": text or "", "status": resp.status_code, "mime": mime, "final_url": final_url}
    except Exception as e:
        return {"text": "", "status": "error", "mime": None, "final_url": None}
