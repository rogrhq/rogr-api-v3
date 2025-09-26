from __future__ import annotations
import hashlib, json
from typing import Any, Dict, List

def _canonical(obj: Any) -> bytes:
    """Canonical JSON bytes (sorted keys, no spaces)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def build_ledger_from_result(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten evidence into a deterministic ledger for audit/export."""
    ledger: List[Dict[str, Any]] = []
    for claim in result.get("claims", []):
        ctext = claim.get("text", "")
        ev = claim.get("evidence", {}) or {}
        for arm in ("A", "B"):
            for item in ev.get(arm, []) or []:
                src = item.get("source", {}) or {}
                ledger.append({
                    "claim_text": ctext,
                    "arm": arm,
                    "url": src.get("url", ""),
                    "title": src.get("title", ""),
                    "snippet": src.get("snippet", ""),
                    "stance": item.get("stance", ""),
                    "quality_letter": item.get("quality_letter", ""),
                })
    return ledger

def build_ifcn_bundle(*, result: Dict[str, Any], input_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construct a deterministic, self-checking IFCN export bundle with checksum.
    - schema_version: fixed "1.0"
    - input: minimal inputs (redacted text length, flags)
    - claims: condensed claim summaries (text/tier/score/label)
    - overall: numeric + label
    - methodology: verbatim from pipeline (already deterministic in test mode)
    - evidence_ledger: flattened per-claim items (url/title/stance/quality)
    - checksum: sha256 over the canonical form of everything except the checksum itself
    """
    claims_slim = []
    for c in result.get("claims", []):
        claims_slim.append({
            "text": c.get("text", ""),
            "tier": c.get("tier", "primary"),
            "score_numeric": c.get("score_numeric", 0),
            "label": c.get("label", ""),
        })
    bundle_wo_checksum = {
        "schema_version": "1.0",
        "input": input_meta,
        "claims": claims_slim,
        "overall": result.get("overall", {}),
        "methodology": result.get("methodology", {}),
        "evidence_ledger": build_ledger_from_result(result),
    }
    h = _sha256_bytes(_canonical(bundle_wo_checksum))
    return {**bundle_wo_checksum, "checksum": {"sha256": h}}