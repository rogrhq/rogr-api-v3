from __future__ import annotations
import os
from typing import List, Dict, Any, Optional
import httpx

_API = "https://api.search.brave.com/res/v1/web/search"

async def search(query: str, api_key: Optional[str] = None, max_results: int = 3) -> List[Dict[str, Any]]:
    key = api_key or os.getenv("BRAVE_API_KEY") or ""
    if not key:
        return []
    headers = {"X-Subscription-Token": key}
    params = {"q": query, "count": max(1, min(10, max_results))}
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
        r = await client.get(_API, headers=headers, params=params)
        r.raise_for_status()
        data = r.json() or {}
    web = data.get("web", {})
    results = web.get("results") or []
    out: List[Dict[str, Any]] = []
    for it in results[:max_results]:
        out.append({
            "url": it.get("url") or "",
            "title": it.get("title") or "",
            "snippet": (it.get("description") or "").strip(),
        })
    return [x for x in out if x["url"]]