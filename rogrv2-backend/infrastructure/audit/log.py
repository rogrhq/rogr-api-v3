from __future__ import annotations
import datetime as _dt
import os
from typing import Any, Dict, List
from contextvars import ContextVar
from infrastructure.logging import jlog

# Per-request audit buffer
_AUDIT: ContextVar[List[Dict[str, Any]]] = ContextVar("_AUDIT", default=[])

def _now_iso() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def start(run_meta: Dict[str, Any] | None = None) -> None:
    _AUDIT.set([])
    event("start", **(run_meta or {}))

def event(stage: str, **kv: Any) -> None:
    rec = {"ts": _now_iso(), "stage": stage, **kv}
    buf = _AUDIT.get()
    buf.append(rec)
    _AUDIT.set(buf)
    # also emit structured log
    jlog("audit_event", **rec)

def get_events() -> List[Dict[str, Any]]:
    return list(_AUDIT.get())

def provider_set_from_env(test_mode: bool) -> List[str]:
    if test_mode:
        return ["offline-synth"]
    provs: List[str] = []
    if os.getenv("GOOGLE_CSE_API_KEY") and os.getenv("GOOGLE_CSE_ENGINE_ID"):
        provs.append("google_cse")
    if os.getenv("BING_API_KEY"):
        provs.append("bing")
    return provs or ["none"]

def finalize_capsule(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a compact, reproducible methodology capsule suitable for IFCN-style audits.
    """
    ev = get_events()
    capsule = {
        "version": "1.0",
        "provider_set": meta.get("provider_set", []),
        "strategy": "A/B",
        "test_mode": meta.get("test_mode", True),
        "counts": meta.get("counts", {}),
        "consensus_summary": meta.get("consensus_summary", {}),
        "scoring_rules": {
            "claim_numeric_0_100": True,
            "evidence_letter_A_to_F": True,
            "label_map": ["True","Mostly True","Mixed","Mostly False","False"]
        },
        "events": ev,  # ordered list
    }
    return capsule