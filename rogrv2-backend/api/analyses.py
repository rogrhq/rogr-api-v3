from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List
from infrastructure.auth.deps import require_user
from intelligence.pipeline.run import run_preview
from intelligence.analyze.enrich import enrich_claim_obj
from infrastructure.logging.jtrace import error_event, format_exc
import os
from intelligence.stance.verdict import compute_verdict, compute_verdict_content_first
from intelligence.content.align import align_claim_to_text
from intelligence.content.fetch_sync import fetch_text

router = APIRouter()

class PreviewBody(BaseModel):
    # MVP: text input; extensible for media later
    text: str
    test_mode: bool = False
    input_type: str | None = None
    original_uri: str | None = None

@router.get("/analyses/healthcheck")
def analyses_healthcheck(_user=Depends(require_user)):
    return {"ok": True}

def _ensure_claim_shape(c: Dict[str, Any]) -> Dict[str, Any]:
    # Always present keys
    c.setdefault("text", "")
    c.setdefault("tier", "primary")
    # Evidence: ensure structure even if pipeline produced none
    ev = c.get("evidence")
    if not isinstance(ev, dict):
        ev = {}
    ev.setdefault("arm_A", [])
    ev.setdefault("arm_B", [])
    ev.setdefault("selected", [])
    c["evidence"] = ev
    # Verdict: numeric grade + label + rationale
    vd = c.get("verdict")
    if not isinstance(vd, dict):
        vd = {}
    vd.setdefault("claim_score", 50)
    vd.setdefault("label", "Mixed")
    vd.setdefault("rationale", "")
    c["verdict"] = vd
    return c

def _ensure_preview_shape(res: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(res, dict):
        return {"overall": {"score": 50, "label": "Mixed"}, "claims": [], "methodology": {}}
    # overall
    ov = res.get("overall")
    if not isinstance(ov, dict):
        ov = {}
    ov.setdefault("score", 50)
    ov.setdefault("label", "Mixed")
    res["overall"] = ov
    # claims
    claims = res.get("claims")
    if not isinstance(claims, list):
        claims = []
    res["claims"] = [_ensure_claim_shape(dict(c) if isinstance(c, dict) else {"text": str(c)}) for c in claims]
    # methodology (keep existing; ensure dict)
    meth = res.get("methodology")
    if not isinstance(meth, dict):
        meth = {}
    # scoring bands default (True/Mostly True/Mixed/Mostly False/False) if absent
    sc = meth.get("scoring")
    if not isinstance(sc, dict):
        sc = {}
    bands = sc.get("bands")
    if not isinstance(bands, dict):
        bands = {"True": [90,100], "Mostly True": [75,89], "Mixed": [40,74], "Mostly False": [15,39], "False": [0,14]}
    sc["bands"] = bands
    meth["scoring"] = sc
    res["methodology"] = meth
    return res

@router.post("/analyses/preview")
async def preview(body: PreviewBody, _user=Depends(require_user)):
    # Async for async pipeline
    try:
        raw = await run_preview(text=body.text, test_mode=body.test_mode)
        res = _ensure_preview_shape(raw)
        # Ensure each claim has a verdict with confidence + rationale_refs
        try:
            claims = (res.get("claims") or [])
            for claim in claims:
                ev = (claim or {}).get("evidence") or {}
                armA = ev.get("arm_A") or []
                armB = ev.get("arm_B") or []
                v = (claim or {}).get("verdict") or {}
                # P18: prefer content-first verdict if any content_score present
                has_content_sig = any(isinstance((x or {}).get("content_score"), (int, float)) and (x.get("content_score") or 0) > 0 for x in (armA + armB))
                if has_content_sig:
                    v2 = compute_verdict_content_first(armA, armB, k=3)
                else:
                    v2 = compute_verdict(armA, armB, k=3)
                if "label" in v and v.get("label"):
                    v2["label"] = v["label"]
                claim["verdict"] = {**v, **v2}
                # --- P17: Attach full-text fetch for a small, neutral budget per arm ---
                try:
                    topk = int(os.getenv("ROGR_FETCH_TOPK_PER_ARM", "2"))
                    explore = int(os.getenv("ROGR_FETCH_EXPLORE_PER_ARM", "0"))
                    # helper to annotate selected items
                    def _enrich(items):
                        sel = list(items[:max(0, topk)])
                        # simple exploration: first N from the remainder
                        if explore > 0 and len(items) > topk:
                            sel += list(items[topk: topk+explore])
                        for it in sel:
                            if not isinstance(it, dict):
                                continue
                            if it.get("content_chars"):
                                continue  # already enriched
                            url = it.get("url")
                            if not url:
                                continue
                            res = fetch_text(url, timeout=8.0)
                            txt = res.get("text") or ""
                            if txt:
                                excerpt = txt[:600]
                                it["content_chars"] = len(txt)
                                it["content_excerpt"] = excerpt
                                it["content_status"] = res.get("status")
                                # P18: content-aware alignment & stance
                                claim_text = (claim or {}).get("text") or ""
                                al = align_claim_to_text(claim_text, excerpt)
                                if isinstance(al, dict):
                                    it["alignment"] = {
                                        "entity_hit": bool(al.get("entity_hit")),
                                        "number_hit": bool(al.get("number_hit")),
                                        "year_hit": bool(al.get("year_hit")),
                                    }
                                    it["matches"] = al.get("matches") or []
                                    cs = float(al.get("content_score") or 0.0)
                                    if cs > 0:
                                        it["content_score"] = cs
                                    stance = al.get("item_stance")
                                    if isinstance(stance, str):
                                        it["item_stance"] = stance
                            else:
                                it["content_status"] = res.get("status")
                    _enrich(armA)
                    _enrich(armB)
                except Exception:
                    pass
        except Exception:
            # Do not break preview if verdict enrichment fails
            pass
        return res
    except HTTPException:
        raise
    except Exception as e:
        rid = error_event(
            "preview_failed",
            text=body.text[:200],
            test_mode=body.test_mode,
            detail=str(e),
            traceback=format_exc(e),
        )
        raise HTTPException(
            status_code=500,
            detail={"error": "server_error", "request_id": rid, "hint": "see server logs"},
        )