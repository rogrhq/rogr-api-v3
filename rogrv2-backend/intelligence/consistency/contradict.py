from __future__ import annotations
from typing import Dict, List, Tuple
import re
from intelligence.content.shared.text_utils import tokenize_advanced as _tokens

_NEG_TOKENS = {
    "no","not","never","without","none","false","deny","denies","denied","refute","refutes","refuted",
    "decline","declines","declined","incorrect","inaccurate","myth","hoax"
}

def _has_neg_language(title: str, snippet: str) -> bool:
    toks = set(_tokens(title + " " + snippet))
    return any(t in toks for t in _NEG_TOKENS)

def _stance_from_item(it: Dict) -> str:
    """Very cheap stance proxy from negation cues in title/snippet."""
    title = it.get("title") or ""
    snip  = it.get("snippet") or ""
    return "contra" if _has_neg_language(title, snip) else "pro"

def _pairwise_contradictions(A: List[Dict], B: List[Dict], limit: int = 5) -> Tuple[int, List[Dict]]:
    c = 0
    examples: List[Dict] = []
    for a in A[:limit]:
        sa = _stance_from_item(a)
        for b in B[:limit]:
            sb = _stance_from_item(b)
            if sa != sb:
                c += 1
                if len(examples) < 3:
                    examples.append({"A_title": a.get("title",""), "B_title": b.get("title","")})
    return c, examples

def detect_contradiction(armA: List[Dict], armB: List[Dict]) -> Dict[str, object]:
    """
    Deterministic contradiction detector:
    - Derives crude stance (pro/contra) from negation cues.
    - Counts cross-arm pairs with opposing stance.
    - Emits small examples (titles) to aid transparency.
    Metrics are bounded and side-effect free.
    """
    pairs, samples = _pairwise_contradictions(armA or [], armB or [])
    total_pairs = min(len(armA or []), 5) * min(len(armB or []), 5)
    ratio = (pairs / total_pairs) if total_pairs else 0.0
    return {
        "pairs_opposed": int(pairs),
        "pairs_total": int(total_pairs),
        "opposition_ratio": round(float(ratio), 3),
        "samples": samples,
    }