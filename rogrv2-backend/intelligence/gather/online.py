from __future__ import annotations
import os, hashlib
from typing import Any, Dict, List
from infrastructure.http.async_http import client as async_client, get_text
from infrastructure.storage.snapshots import save_snapshot_html
from search_providers.google_cse import search as google_search
from search_providers.bing import search as bing_search
from search_providers.brave import search as brave_search

def _norm(url: str, title: str, snippet: str) -> Dict[str, Any]:
    return {"url": url, "title": title or "", "snippet": snippet or ""}

async def live_candidates(query: str, max_per_arm: int = 3) -> List[Dict[str, Any]]:
    g_key = os.getenv("GOOGLE_CSE_API_KEY") or ""
    g_cx  = os.getenv("GOOGLE_CSE_ENGINE_ID") or ""
    b_key = os.getenv("BING_API_KEY") or ""
    br_key = os.getenv("BRAVE_API_KEY") or ""

    results: List[Dict[str, Any]] = []
    any_key = (g_key and g_cx) or b_key or br_key
    if not any_key:
        return results  # tests handle offline branch

    # Fetch per provider (only those enabled)
    g = await google_search(query, api_key=g_key, engine_id=g_cx, max_results=max_per_arm) if (g_key and g_cx) else []
    b = await bing_search(query, api_key=b_key, max_results=max_per_arm) if b_key else []
    br = await brave_search(query, api_key=br_key, max_results=max_per_arm) if br_key else []

    # Interleave across whatever is available (Google, Bing, Brave)
    arms = [lst for lst in (g, b, br) if lst]
    if not arms:
        return results
    max_len = max(len(a) for a in arms)
    for i in range(max_len):
        for arm in arms:
            if i < len(arm):
                it = arm[i]
                results.append(_norm(it["url"], it.get("title",""), it.get("snippet","")))
    return results[: max_per_arm * len(arms)]

async def snapshot(cands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    async with async_client() as c:
        for x in cands:
            try:
                html = await get_text(x["url"], client=c, timeout=10.0)
                sha = hashlib.sha256(html.encode("utf-8", errors="ignore")).hexdigest()
                path = save_snapshot_html(html=html, sha256=sha)
                out.append({**x, "snapshot": {"sha256": sha, "path": path}})
            except Exception:
                out.append({**x, "snapshot": None})
    return out

async def run(query: str, max_per_arm: int = 3) -> Dict[str, Any]:
    """
    Top-level entry: fetch candidates, snapshot HTML, return normalized payload.
    Always returns a dict with keys: query, candidates (list), count (int).
    """
    cands = await live_candidates(query=query, max_per_arm=max_per_arm)
    enriched = await snapshot(cands)
    return {
        "query": query,
        "candidates": enriched,
        "count": len(enriched),
    }