# path: intelligence/content/p20_wrapper.py
"""
P20 (LIVE): Deterministic reading & grading integration.
Wraps intelligence.gather.pipeline.build_evidence_for_claim to attach Finding Cards
(grade, stance, rationale, matched_spans) to each evidence item with content.
Idempotent and non-destructive (no filtering).
"""
from __future__ import annotations
from typing import Any, Dict, List, Tuple, Optional
import inspect
import os, sys, json

def _install():
    try:
        from intelligence.gather import pipeline  # the orchestrator we are wrapping
    except Exception as e:
        raise RuntimeError(f"P20 wrapper: cannot import intelligence.gather.pipeline: {e}")

    if getattr(pipeline, "_ROGR_P20_INSTALLED", False):
        return
    setattr(pipeline, "_ROGR_P20_INSTALLED", True)

    _ORIG = getattr(pipeline, "build_evidence_for_claim", None)
    if _ORIG is None:
        raise RuntimeError("P20 wrapper: pipeline.build_evidence_for_claim not found")

    from intelligence.content.grade import attach_finding_to_item

    def _diag(event: str, **fields: Any) -> None:
        if os.getenv("ROGR_DIAG_P20", "").lower() not in ("1","true","yes","on"):
            return
        try:
            rec = {"event": f"p20.{event}"}
            rec.update(fields)
            print(json.dumps(rec, ensure_ascii=False))
        except Exception:
            pass

    def _attach_to_arm(claim_text: str, arm_key: str, lst: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
        """
        Attach finding to every item (unconditionally). This is safe because we only annotate.
        Later API content enrichment will not remove existing annotation.
        """
        out: List[Dict[str,Any]] = []
        items = len(lst or [])
        attached = 0
        errors = 0
        for idx, it in enumerate(lst or []):
            try:
                it = attach_finding_to_item(claim_text, arm_key, it)
                if "finding" in it and isinstance(it.get("grade"), (int, float)):
                    attached += 1
                out.append(it)
            except Exception as e:
                errors += 1
                _diag("attach_item_error", arm=arm_key, idx=idx, error=str(e)[:240])
                out.append(it)
        _diag("attach_arm", arm=arm_key, items=items, eligible=items, attached=attached, errors=errors)
        return out

    def _extract_claim_text(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
        """
        Heuristically extract the claim text from common calling patterns:
          - kwargs["claim_text"]
          - kwargs["claim"]["text"]
          - kwargs["plan"]["claim"]["text"]
          - first positional arg if it's a string
          - search positional/keyword dicts for a key "text"
        """
        # direct kw
        v = kwargs.get("claim_text")
        if isinstance(v, str) and v.strip():
            return v
        # claim dict
        v = kwargs.get("claim")
        if isinstance(v, dict) and isinstance(v.get("text"), str):
            return v.get("text") or ""
        # plan.claim.text
        v = kwargs.get("plan")
        if isinstance(v, dict):
            cl = v.get("claim")
            if isinstance(cl, dict) and isinstance(cl.get("text"), str):
                return cl.get("text") or ""
        # first positional string
        if args and isinstance(args[0], str) and args[0].strip():
            return args[0]
        # search any dict in args for "text"
        for a in args:
            if isinstance(a, dict) and isinstance(a.get("text"), str):
                return a.get("text") or ""
        return ""

    def _get_arm_candidates(evidence: Dict[str, Any], key_aliases: List[str]) -> Tuple[str, Optional[str], Optional[str], List[Dict[str,Any]]]:
        """
        Return a tuple (shape, key, inner_key, items) where:
          shape    ∈ {"list","dict","missing"}
          key      is the evidence key matched (e.g., "arm_A", "A")
          inner_key is the field inside dict that holds the list (e.g., "candidates","items"), or None
          items    is the candidate list (possibly empty)
        Supports both shapes:
          - evidence[key] -> list
          - evidence[key] -> {"candidates": list} or {"items": list} or single-list dict
        """
        for k in key_aliases:
            if k in evidence:
                val = evidence.get(k)
                if isinstance(val, list):
                    return ("list", k, None, val)
                if isinstance(val, dict):
                    # preferred keys
                    for inner in ("candidates","items","results"):
                        li = val.get(inner)
                        if isinstance(li, list):
                            return ("dict", k, inner, li or [])
                    # fallback: first list-valued field
                    for inner, li in val.items():
                        if isinstance(li, list):
                            return ("dict", k, inner, li or [])
        return ("missing", None, None, [])

    def _set_arm_candidates(evidence: Dict[str, Any], shape: str, key: Optional[str], new_items: List[Dict[str,Any]], inner_key: Optional[str] = None) -> None:
        if not key:
            return
        if shape == "list":
            evidence[key] = new_items
        elif shape == "dict":
            obj = evidence.get(key) or {}
            if isinstance(obj, dict):
                if inner_key and isinstance(obj.get(inner_key), list):
                    obj[inner_key] = new_items
                else:
                    # default to candidates if no specific inner_key
                    obj["candidates"] = new_items
                evidence[key] = obj

    async def _wrap_async(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Async wrapper: await original coroutine, then annotate evidence with findings."""
        res = await _ORIG(*args, **kwargs)  # type: ignore[misc]
        try:
            claim_text = _extract_claim_text(args, kwargs)
            evidence = res if isinstance(res, dict) else {}

            # ----- ARM A -----
            shapeA, keyA, innerA, itemsA = _get_arm_candidates(evidence, ["arm_A","A"])
            if shapeA != "missing":
                newA = _attach_to_arm(claim_text, "A", itemsA)
                _set_arm_candidates(evidence, shapeA, keyA, newA, innerA)
                # mirror to both aliases if they exist
                if keyA != "arm_A" and "arm_A" in evidence:
                    _set_arm_candidates(evidence, "list" if isinstance(evidence.get("arm_A"), list) else "dict", "arm_A", newA, innerA)
                if keyA != "A" and "A" in evidence:
                    _set_arm_candidates(evidence, "list" if isinstance(evidence.get("A"), list) else "dict", "A", newA, innerA)

            # ----- ARM B -----
            shapeB, keyB, innerB, itemsB = _get_arm_candidates(evidence, ["arm_B","B"])
            if shapeB != "missing":
                newB = _attach_to_arm(claim_text, "B", itemsB)
                _set_arm_candidates(evidence, shapeB, keyB, newB, innerB)
                # mirror to both aliases if they exist
                if keyB != "arm_B" and "arm_B" in evidence:
                    _set_arm_candidates(evidence, "list" if isinstance(evidence.get("arm_B"), list) else "dict", "arm_B", newB, innerB)
                if keyB != "B" and "B" in evidence:
                    _set_arm_candidates(evidence, "list" if isinstance(evidence.get("B"), list) else "dict", "B", newB, innerB)

            # diagnostics summary
            try:
                a_count = len(evidence.get("arm_A", [])) if isinstance(evidence.get("arm_A"), list) else len((evidence.get("arm_A") or {}).get("candidates", []) if isinstance(evidence.get("arm_A"), dict) else [])
                b_count = len(evidence.get("arm_B", [])) if isinstance(evidence.get("arm_B"), list) else len((evidence.get("arm_B") or {}).get("candidates", []) if isinstance(evidence.get("arm_B"), dict) else [])
                _diag("attach", is_async=True, a_items=a_count, b_items=b_count, claim=bool(claim_text))
            except Exception:
                pass
            return evidence
        except Exception:
            return res

    def _wrap_sync(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Sync fallback (in case original is synchronous in some environments)."""
        res = _ORIG(*args, **kwargs)  # type: ignore[misc]
        try:
            claim_text = _extract_claim_text(args, kwargs)
            evidence = res if isinstance(res, dict) else {}

            shapeA, keyA, innerA, itemsA = _get_arm_candidates(evidence, ["arm_A","A"])
            if shapeA != "missing":
                newA = _attach_to_arm(claim_text, "A", itemsA)
                _set_arm_candidates(evidence, shapeA, keyA, newA, innerA)
                if keyA != "arm_A" and "arm_A" in evidence:
                    _set_arm_candidates(evidence, "list" if isinstance(evidence.get("arm_A"), list) else "dict", "arm_A", newA, innerA)
                if keyA != "A" and "A" in evidence:
                    _set_arm_candidates(evidence, "list" if isinstance(evidence.get("A"), list) else "dict", "A", newA, innerA)

            shapeB, keyB, innerB, itemsB = _get_arm_candidates(evidence, ["arm_B","B"])
            if shapeB != "missing":
                newB = _attach_to_arm(claim_text, "B", itemsB)
                _set_arm_candidates(evidence, shapeB, keyB, newB, innerB)
                if keyB != "arm_B" and "arm_B" in evidence:
                    _set_arm_candidates(evidence, "list" if isinstance(evidence.get("arm_B"), list) else "dict", "arm_B", newB, innerB)
                if keyB != "B" and "B" in evidence:
                    _set_arm_candidates(evidence, "list" if isinstance(evidence.get("B"), list) else "dict", "B", newB, innerB)

            try:
                a_count = len(evidence.get("arm_A", [])) if isinstance(evidence.get("arm_A"), list) else len((evidence.get("arm_A") or {}).get("candidates", []) if isinstance(evidence.get("arm_A"), dict) else [])
                b_count = len(evidence.get("arm_B", [])) if isinstance(evidence.get("arm_B"), list) else len((evidence.get("arm_B") or {}).get("candidates", []) if isinstance(evidence.get("arm_B"), dict) else [])
                _diag("attach", is_async=False, a_items=a_count, b_items=b_count, claim=bool(claim_text))
            except Exception:
                pass
            return evidence
        except Exception:
            return res

    # Install the appropriate wrapper based on the original's coroutine nature
    WRAPPED = _wrap_async if inspect.iscoroutinefunction(_ORIG) else _wrap_sync
    setattr(pipeline, "build_evidence_for_claim", WRAPPED)

    # Propagate wrapper to any modules that imported the original symbol directly.
    # Example: `from intelligence.gather.pipeline import build_evidence_for_claim`
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
