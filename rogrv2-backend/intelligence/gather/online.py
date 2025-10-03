from __future__ import annotations
import os
import asyncio
import random
from typing import Any, Dict, List, Tuple

import httpx

from intelligence.gather.normalize import dedupe  # preserved
from intelligence.gather.query_compactor import quote_conform_variants
from intelligence.util import diag

__all__ = ["run_plan"]

# -----------------------
# Provider enablement (LIVE defaults)
# -----------------------

def _enabled_providers_from_env() -> List[str]:
    brave = bool(os.getenv("BRAVE_API_KEY") or os.getenv("BRAVE_KEY"))
    google = bool(
        (os.getenv("GOOGLE_CSE_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_KEY"))
        and (os.getenv("GOOGLE_CSE_ENGINE_ID") or os.getenv("GOOGLE_CSE_ID") or os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID"))
    )
    bing = bool(os.getenv("BING_SUBSCRIPTION_KEY") or os.getenv("BING_API_KEY") or os.getenv("AZURE_BING_KEY"))
    enabled: List[str] = []
    if brave:
        enabled.append("brave")
    if google:
        enabled.append("google")
    if bing:
        enabled.append("bing")
    return enabled


def _providers_for_arm(arm: Dict[str, Any]) -> List[str]:
    explicit = [p for p in (arm.get("providers") or []) if isinstance(p, str)]
    if explicit:
        allowed = {"brave", "google", "bing"}
        return [p for p in explicit if p in allowed]
    return _enabled_providers_from_env()

# -----------------------
# Query normalization
# -----------------------

def _normalize_queries(qs: Any) -> List[str]:
    out: List[str] = []
    if isinstance(qs, list):
        for q in qs:
            if isinstance(q, str) and q.strip():
                out.append(q.strip())
            elif isinstance(q, dict):
                v = q.get("q") or q.get("query") or q.get("text")
                if isinstance(v, str) and v.strip():
                    out.append(v.strip())
    elif isinstance(qs, str) and qs.strip():
        out.append(qs.strip())
    return out

# -----------------------
# Provider adapters (LIVE)
# -----------------------

async def _brave_search(client: httpx.AsyncClient, query: str, *, count: int) -> List[Dict[str, Any]]:
    token = os.getenv("BRAVE_API_KEY") or os.getenv("BRAVE_KEY")
    if not token:
        return []
    url = "https://api.search.brave.com/res/v1/web/search"
    r = await client.get(
        url,
        params={"q": query, "count": max(1, min(count, 10))},
        headers={"X-Subscription-Token": token, "Accept": "application/json"},
        timeout=20.0,
    )
    r.raise_for_status()
    j = r.json()
    results = (j.get("web") or {}).get("results") or j.get("results") or []
    out: List[Dict[str, Any]] = []
    for it in results:
        if not isinstance(it, dict):
            continue
        out.append(
            {
                "url": it.get("url") or it.get("link") or "",
                "title": it.get("title") or it.get("name") or "",
                "snippet": it.get("description") or it.get("snippet") or it.get("meta_desc") or "",
                "provider": "brave",
                "query_used": query,
            }
        )
    if diag.enabled():
        diag.log("provider_result", provider="brave", status=getattr(r, "status_code", None), count=len(out), q_effective=query)
    return out


async def _google_cse_search(client: httpx.AsyncClient, query: str, *, count: int) -> List[Dict[str, Any]]:
    key = os.getenv("GOOGLE_CSE_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_KEY")
    cx = os.getenv("GOOGLE_CSE_ENGINE_ID") or os.getenv("GOOGLE_CSE_ID") or os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
    if not (key and cx):
        return []
    url = "https://www.googleapis.com/customsearch/v1"
    r = await client.get(
        url,
        params={"key": key, "cx": cx, "q": query, "num": max(1, min(count, 10))},
        headers={"Accept": "application/json"},
        timeout=20.0,
    )
    r.raise_for_status()
    j = r.json()
    items = j.get("items") or []
    out: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        out.append(
            {
                "url": it.get("link") or it.get("url") or "",
                "title": it.get("title") or "",
                "snippet": it.get("snippet") or it.get("htmlSnippet") or "",
                "provider": "google",
                "query_used": query,
            }
        )
    if diag.enabled():
        diag.log("provider_result", provider="google", status=getattr(r, "status_code", None), count=len(out), q_effective=query)
    return out


async def _bing_search(client: httpx.AsyncClient, query: str, *, count: int) -> List[Dict[str, Any]]:
    key = os.getenv("BING_SUBSCRIPTION_KEY") or os.getenv("BING_API_KEY") or os.getenv("AZURE_BING_KEY")
    if not key:
        return []
    url = "https://api.bing.microsoft.com/v7.0/search"
    r = await client.get(
        url,
        params={"q": query, "count": max(1, min(count, 10))},
        headers={"Ocp-Apim-Subscription-Key": key, "Accept": "application/json"},
        timeout=20.0,
    )
    r.raise_for_status()
    j = r.json()
    items = (j.get("webPages") or {}).get("value") or []
    out: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        out.append(
            {
                "url": it.get("url") or "",
                "title": it.get("name") or "",
                "snippet": it.get("snippet") or it.get("about") or "",
                "provider": "bing",
                "query_used": query,
            }
        )
    if diag.enabled():
        diag.log("provider_result", provider="bing", status=getattr(r, "status_code", None), count=len(out), q_effective=query)
    return out

# -----------------------
# Resilient execution helpers
# -----------------------

async def _with_retries(coro_func, *args, provider: str, query: str, attempts: int = 2, base_delay: float = 0.6, **kwargs) -> List[Dict[str, Any]]:
    """Run provider call with limited retries for 429/5xx and swallow failures to preserve other providers."""
    for i in range(attempts):
        try:
            return await coro_func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            if status in (429, 500, 502, 503, 504) and i + 1 < attempts:
                delay = base_delay * (2 ** i) * (0.5 + random.random())
                await asyncio.sleep(delay)
                continue
            if diag.enabled():
                diag.log("provider_error", provider=provider, status=status, query=query, attempt=i+1)
            return []
        except httpx.RequestError:
            if diag.enabled():
                diag.log("provider_error", provider=provider, status=None, query=query, attempt=i+1)
            return []
        except Exception:
            if diag.enabled():
                diag.log("provider_error", provider=provider, status=None, query=query, attempt=i+1)
            return []
    return []

# -----------------------
# Execution
# -----------------------

def _canonical_arm_label(arm_def: Dict[str, Any]) -> str:
    name = str(arm_def.get("name") or "").strip()
    intent = str(arm_def.get("intent") or "").strip().lower()
    if name.upper().startswith("A"):
        return "A"
    if name.upper().startswith("B"):
        return "B"
    if intent in ("support", "agree", "for"):
        return "A"
    if intent in ("challenge", "refute", "against"):
        return "B"
    return "A"


async def _gather_for_arm(arm: Dict[str, Any], *, max_per_query: int) -> List[Dict[str, Any]]:
    providers = _providers_for_arm(arm)
    if not providers:
        raise RuntimeError("No providers enabled for arm; set BRAVE_API_KEY and/or GOOGLE_CSE_API_KEY+GOOGLE_CSE_ENGINE_ID and/or BING_SUBSCRIPTION_KEY")

    queries = _normalize_queries(arm.get("queries"))
    if not queries:
        return []

    label = _canonical_arm_label(arm)

    async with httpx.AsyncClient() as client:
        tasks_meta: List[Tuple[str, str, str, asyncio.Task]] = []
        for q_orig in queries:
            pairs = quote_conform_variants(q_orig) or [(q_orig, q_orig)]
            for q_original, q_effective in pairs:
                if "brave" in providers:
                    t = asyncio.create_task(_with_retries(_brave_search, client, q_effective, count=max_per_query, provider="brave", query=q_effective))
                    tasks_meta.append(("brave", q_original, q_effective, t))
                if "google" in providers:
                    t = asyncio.create_task(_with_retries(_google_cse_search, client, q_effective, count=max_per_query, provider="google", query=q_effective))
                    tasks_meta.append(("google", q_original, q_effective, t))
                if "bing" in providers:
                    t = asyncio.create_task(_with_retries(_bing_search, client, q_effective, count=max_per_query, provider="bing", query=q_effective))
                    tasks_meta.append(("bing", q_original, q_effective, t))

        if diag.enabled():
            for prov, q_original, q_effective, _ in tasks_meta:
                diag.log("provider_call", provider=prov, arm=label, q_original=q_original, q_effective=q_effective)

        results: List[List[Dict[str, Any]]] = []
        if tasks_meta:
            results = await asyncio.gather(*[m[3] for m in tasks_meta], return_exceptions=False)

    out: List[Dict[str, Any]] = []
    for (provider, q_original, q_effective, _), batch in zip(tasks_meta, results):
        for it in (batch or []):
            if isinstance(it, dict):
                base = dict(it)
                base.setdefault("provider", provider)
                base["q_effective"] = q_effective
                base["query_used"] = q_original
                if "arm" not in base or not base.get("arm"):
                    base["arm"] = label
                out.append(base)
        if diag.enabled():
            diag.log("provider_batch", provider=provider, arm=label, count=len(batch or []), q_effective=q_effective)
    return out


async def run_plan(plan: Dict[str, Any], *, max_per_query: int = 2) -> Dict[str, Any]:
    arms = [a for a in (plan.get("arms") or []) if isinstance(a, dict)]
    if not arms:
        return {"candidates": []}

    all_items: List[Dict[str, Any]] = []
    for arm in arms:
        items = await _gather_for_arm(arm, max_per_query=max_per_query)
        all_items.extend(items)

    all_items = dedupe(all_items)
    return {"candidates": all_items}
