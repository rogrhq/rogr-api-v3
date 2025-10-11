"""
P21 wrapper: attach full-read evaluation per evidence item (both arms).
Installs over pipeline.build_evidence_for_claim with async awareness.
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple
import inspect
import sys, os, json

def _diag(event: str, **fields: Any) -> None:
    if os.getenv("ROGR_DIAG_P21", "").lower() not in ("1","true","yes","on"):
        return
    try:
        rec = {"event": f"p21.{event}"}
        rec.update(fields)
        print(json.dumps(rec, ensure_ascii=False))
    except Exception:
        pass

def _install():
    from intelligence.gather import pipeline  # import target
    from intelligence.content.fullread import evaluate_full_evidence

    _ORIG = getattr(pipeline, "build_evidence_for_claim", None)
    if _ORIG is None:
        raise RuntimeError("P21 wrapper: pipeline.build_evidence_for_claim not found")

    def _get_list(evidence: Dict[str, Any], key: str) -> Tuple[str, List[Dict[str,Any]]]:
        """Return ('list'|'dict'|'missing', items) where dict uses .candidates or any list field."""
        if key not in evidence:
            return ("missing", [])
        val = evidence.get(key)
        if isinstance(val, list):
            return ("list", val)
        if isinstance(val, dict):
            for inner in ("candidates","items","results"):
                li = val.get(inner)
                if isinstance(li, list):
                    return ("dict", li)
            for _, li in val.items():
                if isinstance(li, list):
                    return ("dict", li)
        return ("missing", [])

    def _set_list(evidence: Dict[str, Any], key: str, shape: str, new_items: List[Dict[str,Any]]) -> None:
        if key not in evidence:
            return
        if shape == "list":
            evidence[key] = new_items
        elif shape == "dict":
            obj = evidence.get(key) or {}
            if isinstance(obj, dict):
                if "candidates" in obj and isinstance(obj["candidates"], list):
                    obj["candidates"] = new_items
                else:
                    updated = False
                    for k2, v2 in obj.items():
                        if isinstance(v2, list):
                            obj[k2] = new_items
                            updated = True
                            break
                    if not updated:
                        obj["candidates"] = new_items
                evidence[key] = obj

    async def _wrap_async(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        res = await _ORIG(*args, **kwargs)  # type: ignore[misc]
        try:
            claim_text = kwargs.get("claim_text") or ""
            if not claim_text and args and isinstance(args[0], str):
                claim_text = args[0]

            evidence: Dict[str, Any] = res if isinstance(res, dict) else {}
            for arm_key in ("arm_A","A","arm_B","B"):
                shape, lst = _get_list(evidence, arm_key)
                if shape == "missing":
                    continue
                new_items: List[Dict[str,Any]] = []
                attached = 0
                for idx, it in enumerate(lst or []):
                    try:
                        it = evaluate_full_evidence(claim_text, it or {})
                        if "grade_full" in it and "stance_full" in it:
                            attached += 1
                        new_items.append(it)
                    except Exception as e:
                        _diag("item_error", arm=arm_key, idx=idx, error=str(e)[:240])
                        new_items.append(it)
                _set_list(evidence, arm_key, shape, new_items)
                _diag("arm_done", arm=arm_key, items=len(lst or []), attached=attached)

            _diag("attached", ok=True)
            return evidence
        except Exception as e:
            _diag("wrap_error", error=str(e)[:240])
            return res

    def _wrap_sync(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        res = _ORIG(*args, **kwargs)  # type: ignore[misc]
        try:
            claim_text = kwargs.get("claim_text") or ""
            if not claim_text and args and isinstance(args[0], str):
                claim_text = args[0]

            evidence: Dict[str, Any] = res if isinstance(res, dict) else {}
            for arm_key in ("arm_A","A","arm_B","B"):
                shape, lst = _get_list(evidence, arm_key)
                if shape == "missing":
                    continue
                new_items: List[Dict[str,Any]] = []
                attached = 0
                for idx, it in enumerate(lst or []):
                    try:
                        it = evaluate_full_evidence(claim_text, it or {})
                        if "grade_full" in it and "stance_full" in it:
                            attached += 1
                        new_items.append(it)
                    except Exception as e:
                        _diag("item_error", arm=arm_key, idx=idx, error=str(e)[:240])
                        new_items.append(it)
                _set_list(evidence, arm_key, shape, new_items)
                _diag("arm_done", arm=arm_key, items=len(lst or []), attached=attached)

            _diag("attached", ok=True)
            return evidence
        except Exception as e:
            _diag("wrap_error", error=str(e)[:240])
            return res

    WRAPPED = _wrap_async if inspect.iscoroutinefunction(_ORIG) else _wrap_sync
    setattr(pipeline, "build_evidence_for_claim", WRAPPED)

    replaced = 0
    for name, mod in list(sys.modules.items()):
        try:
            if getattr(mod, "build_evidence_for_claim", None) is _ORIG:
                setattr(mod, "build_evidence_for_claim", WRAPPED)
                replaced += 1
        except Exception:
            continue
    _diag("installed", async_wrap=inspect.iscoroutinefunction(_ORIG), replaced=replaced)

_install()
