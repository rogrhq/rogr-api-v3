from __future__ import annotations
import os
from typing import List, Dict, Any, Optional
import httpx

_API = "https://api.bing.microsoft.com/v7.0/search"

async def search(query: str, api_key: Optional[str] = None, max_results: int = 3) -> List[Dict[str, Any]]:
    key = api_key or os.getenv("BING_API_KEY") or ""
    if not key:
        return []
    headers = {"Ocp-Apim-Subscription-Key": key}
    params = {"q": query, "textDecorations": "false", "textFormat": "Raw", "count": max(1, min(10, max_results))}
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
        r = await client.get(_API, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
    web_pages = (data or {}).get("webPages", {})
    items = web_pages.get("value") or []
    out: List[Dict[str, Any]] = []
    for it in items[:max_results]:
        out.append({
            "url": it.get("url") or "",
            "title": it.get("name") or "",
            "snippet": (it.get("snippet") or "").strip(),
        })
    return [x for x in out if x["url"]]