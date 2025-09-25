from __future__ import annotations
import os
from typing import List, Dict, Any, Optional
import httpx

_API = "https://www.googleapis.com/customsearch/v1"

async def search(query: str, api_key: Optional[str] = None, engine_id: Optional[str] = None, max_results: int = 3) -> List[Dict[str, Any]]:
    key = api_key or os.getenv("GOOGLE_CSE_API_KEY") or ""
    cx = engine_id or os.getenv("GOOGLE_CSE_ENGINE_ID") or ""
    if not (key and cx):
        return []
    params = {"q": query, "key": key, "cx": cx, "num": max(1, min(10, max_results))}
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
        r = await client.get(_API, params=params)
        r.raise_for_status()
        data = r.json()
    items = data.get("items") or []
    out: List[Dict[str, Any]] = []
    for it in items[:max_results]:
        out.append({
            "url": it.get("link") or "",
            "title": it.get("title") or "",
            "snippet": (it.get("snippet") or "").strip(),
        })
    return [x for x in out if x["url"]]