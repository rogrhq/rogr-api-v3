"""
P22 — Full-Text Ingestion & Integrity (LIVE)
- Cache full text returned by canonical fetch layer.
- Enrich preview evidence items with: content, content_hash, coverage.
- Deterministic activation: wrap canonical fetcher; async fallback fetch for missing content;
  rebind pipeline globals used by api.analyses.preview so enrichment always executes.
- No API shape changes.
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import os
from importlib import import_module
from typing import Any, Dict, Callable, Optional, List, Tuple

_DIAG = os.getenv("ROGR_DIAG", "").lower() in ("1", "true", "yes", "on")
def _log(event: str, **fields: Any):
    if not _DIAG:
        return
    try:
        rec = {"event": f"p22.{event}"}
        rec.update(fields)
        print(json.dumps(rec, ensure_ascii=False))
    except Exception:
        pass

# ---------- Fetch cache ----------
_FETCH_CACHE: Dict[str, str] = {}

def _sha256_utf8(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode("utf-8", "ignore")).hexdigest()

def _coverage_for(item: Dict[str, Any]) -> str:
    content = item.get("content") or ""
    excerpt = item.get("content_excerpt") or ""
    chars = int(item.get("content_chars") or 0)
    if content and chars and len(content) >= chars * 0.98:
        return "full"
    if content or excerpt:
        return "partial"
    return "snippet_only"

def _attach_integrity(item: Dict[str, Any]) -> None:
    if (item.get("content") or "") and not item.get("content_hash"):
        item["content_hash"] = _sha256_utf8(item["content"])
    item["coverage"] = _coverage_for(item)

def _collect_missing_urls(evidence: Dict[str, Any]) -> List[str]:
    urls: List[str] = []
    for arm_key in ("arm_A", "arm_B"):
        for it in (evidence.get(arm_key) or []):
            if not isinstance(it, dict):
                continue
            url = it.get("url")
            if not url:
                continue
            if it.get("content"):
                continue
            if url in _FETCH_CACHE:
                continue
            urls.append(url)
    return urls

async def _fallback_fetch_into_cache(urls: List[str], *, per_timeout: float = 8.0) -> int:
    """
    Perform async fetch for any URLs still missing in cache, using the canonical fetcher.
    Returns number of entries populated.
    """
    if not urls:
        return 0
    try:
        fetch_mod = import_module("intelligence.content.fetch")
        fetch_text = getattr(fetch_mod, "fetch_text", None)
        if not callable(fetch_text):
            _log("fallback_missing_fetcher")
            return 0
    except Exception as e:
        _log("fallback_import_fail", error=str(e))
        return 0

    async def _one(u: str) -> Tuple[str, str]:
        try:
            res = await fetch_text(u, timeout=per_timeout)
            text = (res or {}).get("text") or ""
            return (u, text)
        except Exception:
            return (u, "")

    tasks = [asyncio.create_task(_one(u)) for u in urls]
    done = await asyncio.gather(*tasks, return_exceptions=False)
    count = 0
    for u, txt in done:
        if txt:
            _FETCH_CACHE[u] = txt
            count += 1
    _log("fallback_fetch", requested=len(urls), filled=count)
    return count

def _enrich_items(evidence: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(evidence, dict):
        return evidence
    for arm_key in ("arm_A", "arm_B"):
        items = evidence.get(arm_key) or []
        new_items = []
        for it in items:
            if isinstance(it, dict):
                url = it.get("url")
                if url and not it.get("content"):
                    txt = _FETCH_CACHE.get(url) or ""
                    if txt:
                        it["content"] = txt
                        it["content_chars"] = int(it.get("content_chars") or len(txt))
                _attach_integrity(it)
                new_items.append(it)
        evidence[arm_key] = new_items
    return evidence

def _wrap_fetch_text():
    """Wrap intelligence.content.fetch.fetch_text to cache full text by URL."""
    try:
        fetch_mod = import_module("intelligence.content.fetch")
    except Exception as e:
        _log("fetch_import_fail", error=str(e))
        return

    if getattr(fetch_mod, "__p22_fetch_wrapped__", False):
        return

    orig = getattr(fetch_mod, "fetch_text", None)
    if orig is None or not callable(orig):
        _log("fetch_missing")
        return

    is_coro = asyncio.iscoroutinefunction(orig)

    if is_coro:
        async def wrapped(*args, **kwargs):
            res = await orig(*args, **kwargs)
            try:
                url = kwargs.get("url")
                if url is None and args:
                    url = args[0]
                text = (res or {}).get("text") or ""
                if url and text:
                    _FETCH_CACHE[url] = text
                    _log("fetch_cached", url=url, chars=len(text))
            except Exception as e:
                _log("fetch_cache_error", error=str(e))
            return res
    else:
        def wrapped(*args, **kwargs):
            res = orig(*args, **kwargs)
            try:
                url = kwargs.get("url")
                if url is None and args:
                    url = args[0]
                text = (res or {}).get("text") or ""
                if url and text:
                    _FETCH_CACHE[url] = text
                    _log("fetch_cached", url=url, chars=len(text))
            except Exception as e:
                _log("fetch_cache_error", error=str(e))
            return res

    setattr(fetch_mod, "fetch_text", wrapped)
    setattr(fetch_mod, "__p22_fetch_wrapped__", True)
    _log("fetch_wrapped", async_fn=is_coro)

async def _wrap_run_preview_async(orig: Callable, *args, **kwargs):
    res = await orig(*args, **kwargs)
    try:
        claims = (res or {}).get("claims") or []
        # Collect all missing URLs (both arms) and fetch them if needed
        total_changed = 0
        for c in claims:
            ev = c.get("evidence")
            if not isinstance(ev, dict):
                continue
            missing = _collect_missing_urls(ev)
            if missing:
                await _fallback_fetch_into_cache(missing)
            _enrich_items(ev)
            total_changed += 1
        _log("preview_enriched", claims=len(claims), changed=total_changed)
    except Exception as e:
        _log("preview_enrich_error", error=str(e))
    return res

def _install_pipeline_wrappers():
    """
    Wrap intelligence.pipeline.run.run_preview (async) and/or build_evidence_for_claim (async).
    Returns tuple (wrapped_run_preview, wrapped_build) so callers can rebind api.analyses names.
    """
    try:
        run_mod = import_module("intelligence.pipeline.run")
    except Exception as e:
        _log("run_import_fail", error=str(e))
        return (None, None)

    wrapped_run = getattr(run_mod, "run_preview", None)
    wrapped_build = getattr(run_mod, "build_evidence_for_claim", None)

    if getattr(run_mod, "__p22_run_wrapped__", False):
        return (wrapped_run, wrapped_build)

    # Prefer wrapping run_preview
    orig_run = getattr(run_mod, "run_preview", None)
    if orig_run and asyncio.iscoroutinefunction(orig_run):
        async def wrapped(*args, **kwargs):
            return await _wrap_run_preview_async(orig_run, *args, **kwargs)
        setattr(run_mod, "run_preview", wrapped)
        wrapped_run = wrapped
        _log("run_wrapped", target="run_preview")
    else:
        # Fallback: wrap build_evidence_for_claim
        build = getattr(run_mod, "build_evidence_for_claim", None)
        if build and asyncio.iscoroutinefunction(build):
            async def wrapped_build_inner(*args, **kwargs):
                bundle = await build(*args, **kwargs)
                try:
                    if isinstance(bundle, dict):
                        # No claims container here—enrich the bundle dict itself
                        # Try to fetch any missing urls
                        missing = _collect_missing_urls(bundle)
                        if missing:
                            await _fallback_fetch_into_cache(missing)
                        _enrich_items(bundle)
                        _log("bundle_enriched")
                except Exception as e:
                    _log("bundle_enrich_error", error=str(e))
                return bundle
            setattr(run_mod, "build_evidence_for_claim", wrapped_build_inner)
            wrapped_build = wrapped_build_inner
            _log("run_wrapped", target="build_evidence_for_claim")
    setattr(run_mod, "__p22_run_wrapped__", True)
    return (wrapped_run, wrapped_build)

def _rebind_api_names(wrapped_run: Optional[Callable], wrapped_build: Optional[Callable]):
    """
    Rebind api.analyses module globals so preview() calls our wrapped functions.
    """
    try:
        api_mod = import_module("api.analyses")
    except Exception as e:
        _log("api_import_fail", error=str(e))
        return
    did_run = False
    did_build = False
    if wrapped_run is not None and getattr(api_mod, "run_preview", None) is not wrapped_run:
        setattr(api_mod, "run_preview", wrapped_run)
        did_run = True
    if wrapped_build is not None and getattr(api_mod, "build_evidence_for_claim", None) is not wrapped_build:
        setattr(api_mod, "build_evidence_for_claim", wrapped_build)
        did_build = True
    _log("rebound_api_names", run=did_run, build=did_build)

# Install wrappers at import time (idempotent)
try:
    _wrap_fetch_text()
    wr_run, wr_build = _install_pipeline_wrappers()
    _rebind_api_names(wr_run, wr_build)
    __installed__ = True
    _log("installed", ok=True)
except Exception as _e:
    _log("install_error", error=str(_e))
