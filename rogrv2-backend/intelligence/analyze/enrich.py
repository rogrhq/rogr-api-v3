from __future__ import annotations
from typing import Any, Dict, List

def _default_quality(stance: str | None) -> str:
    # extremely conservative placeholder
    if stance == "support": return "B"
    if stance == "refute":  return "B"
    return "C"

def enrich_evidence(evidence: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    """Ensure each evidence item has minimally-required fields.
    This is a no-op shim that fills defaults so the pipeline can run.
    """
    out: List[Dict[str, Any]] = []
    for ev in (evidence or []):
        e = dict(ev)
        e.setdefault("quality_letter", _default_quality(e.get("stance")))
        e.setdefault("features_json", {})
        e.setdefault("publisher", (e.get("publisher") or "") )
        e.setdefault("title", (e.get("title") or "") )
        e.setdefault("snippet", (e.get("snippet") or "") )
        out.append(e)
    return out

def enrich(base: Dict[str, Any]) -> Dict[str, Any]:
    """Top-level shim: attach minimally enriched evidence back onto the base dict."""
    ev = base.get("evidence")
    base["evidence"] = enrich_evidence(ev)
    return base