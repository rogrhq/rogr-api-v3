from __future__ import annotations
from typing import Dict, List, Any, Union
import re
_DOMAIN_RE = re.compile(r"""(?ix)
    (?:^|[\s'"\]])            # start or space
    (?:site:|inurl:)?       # common operators we forbid too
    [\w-]+(?:\.[\w-]+)+     # looks like a.domain.tld
""")

def _uniq(seq: List[str]) -> List[str]:
    seen = set(); out=[]
    for s in seq:
        k = s.strip()
        if not k:
            continue
        if k.lower() in seen:
            continue
        seen.add(k.lower()); out.append(k)
    return out

def _norm_words(s: str) -> List[str]:
    return [w for w in re.split(r"[^\w%]+", s) if w]

def _percent_terms(numbers: Dict[str, Any]) -> List[str]:
    """
    Extract percentage terms from enrichment data.

    Handles both float values (8.0) and string formats ("8%").
    Converts floats to proper percentage strings to prevent domain filter issues.
    """
    out: List[str] = []
    if not numbers:
        return out

    for p in numbers.get("percents", []) or []:
        # Handle both float (8.0) and string ("8%") formats
        if isinstance(p, (int, float)):
            # Convert float to percent string
            # Use int() if it's a whole number (8.0 → 8%), else keep decimal (8.5 → 8.5%)
            val = int(p) if p == int(p) else p
            out.append(f"{val}%")
            out.append(f"{val} percent")
        else:
            # String format (already has %)
            s = str(p)
            out.append(s)
            # normalize "8%" -> "8 percent"
            m = re.match(r"^(\d+(?:\.\d+)?)%$", s)
            if m:
                out.append(f"{m.group(1)} percent")

    return out

def _time_terms(scope: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    if not scope:
        return out
    year = scope.get("year")
    if year:
        out.append(str(year))
    # could add month/quarter in later packets
    return out

def _entity_terms(entities: Union[List[str], List[Dict[str, Any]]]) -> List[str]:
    """
    Extract entity terms, handling both string list and dict list formats.

    Args:
        entities: List[str] (canonical) or List[Dict] with "name" key (legacy)

    Returns:
        List of entity name strings
    """
    if not entities:
        return []

    result = []
    for e in entities:
        if isinstance(e, str):
            # Canonical format: List[str]
            result.append(e)
        elif isinstance(e, dict) and "name" in e:
            # Legacy format: List[Dict] with "name" key
            name = (e.get("name") or "").strip()
            if name:
                result.append(name)
        # Ignore anything else (malformed input)

    return result

def _comparison_terms(cues: Dict[str, Any]) -> List[str]:
    if not cues:
        return []
    terms = []
    if bool(cues.get("has_comparison")):
        # neutral comparison lexicon, no domains
        terms.extend(["increase", "decrease", "change", "rise", "fall", "trend", "growth", "decline"])
        terms.extend(["year over year", "yoy", "compared to", "versus"])
    return terms

def _challenge_terms(kind_hint: str) -> List[str]:
    # neutral "challenge" lexicon (no domain bias)
    return ["dispute", "counterclaim", "contradict", "refute", "debunk", "controversy", "criticism", "fact check"]

def _support_terms(kind_hint: str) -> List[str]:
    return ["report", "press release", "official", "statement", "dataset", "document", "methodology"]

def _head_clause(text: str) -> str:
    # keep a short quoted clause to anchor semantics
    t = text.strip()
    if len(t) > 140:
        t = t[:140]
    return f"\"{t}\""

def build_search_plans_v2(claim: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input: claim dict with enrichment keys from S2 Packet 1.
    Output: normalized plan with two arms (A support-seeking, B challenge-seeking).
    """
    text = claim.get("text") or ""
    entities = _entity_terms(claim.get("entities") or [])
    percents = _percent_terms(claim.get("numbers") or {})
    time = _time_terms(claim.get("scope") or {})
    comps = _comparison_terms(claim.get("cues") or {})
    kind = claim.get("kind_hint") or ""

    head = _head_clause(text)

    common_pool = _uniq(entities + percents + time + comps + _norm_words(kind))
    # Arm A: Support-seeking
    a_queries: List[str] = []
    a_queries.append(" ".join(_uniq([head] + common_pool + _support_terms(kind))))
    if entities:
        a_queries.append(" ".join(_uniq([entities[0]] + percents + time + ["official statistics"])))
    if percents:
        a_queries.append(" ".join(_uniq([head] + percents + ["explainer"])))
    # Arm B: Challenge-seeking
    b_queries: List[str] = []
    b_queries.append(" ".join(_uniq([head] + common_pool + _challenge_terms(kind))))
    if entities:
        b_queries.append(" ".join(_uniq([entities[0]] + percents + time + ["dispute"])))
    b_queries.append(" ".join(_uniq(_challenge_terms(kind) + percents + time)))

    # prune empties, drop any query that contains a domain or site operator
    def _clean(queries: List[str]) -> List[str]:
        out = []
        for q in queries:
            q = q.strip()
            if not q:
                continue
            if _DOMAIN_RE.search(q):
                continue
            out.append(q)
        return out
    a_queries = _clean(a_queries)
    b_queries = _clean(b_queries)

    return {
        "version": "v2",
        "arms": {
            "A": {"intent": "support", "queries": a_queries[:5]},
            "B": {"intent": "challenge", "queries": b_queries[:5]},
        },
        "meta": {
            "claim_id": claim.get("id", "unknown"),
            "claim_type": claim.get("claim_type", "generic"),
            "concept": claim.get("concept", ""),
            "dimension": claim.get("dimension", "unknown")
        }
    }