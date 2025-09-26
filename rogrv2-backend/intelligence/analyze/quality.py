from __future__ import annotations
from typing import Dict, Set
import re

# --- helpers ---
def _letter(score: float) -> str:
    if score >= 0.90: return "A"
    if score >= 0.75: return "B"
    if score >= 0.60: return "C"
    if score >= 0.45: return "D"
    if score >= 0.30: return "E"
    return "F"

_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_MONTH = re.compile(r"\b(jan(uary)?|feb(ruary)?|mar(ch)?|apr(il)?|may|jun(e)?|jul(y)?|aug(ust)?|sep(t)?(ember)?|oct(ober)?|nov(ember)?|dec(ember)?)\b", re.I)
_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_.-]+")

def _tokens(s: str) -> Set[str]:
    return set(t.lower() for t in _TOKEN.findall(s or ""))

def _entities_like(s: str) -> Set[str]:
    # crude entity proxy: capitalized tokens merged from title/snippet
    # bias-neutral and deterministic
    toks = [t for t in _TOKEN.findall(s or "") if t[:1].isupper()]
    return set(t.lower() for t in toks if len(t) > 2)

def _date_presence(s: str) -> float:
    has_year = 1.0 if _YEAR.search(s or "") else 0.0
    has_month = 1.0 if _MONTH.search(s or "") else 0.0
    return 0.5 * has_year + 0.25 * has_month  # in [0, 0.75]

def _overlap(a: Set[str], b: Set[str]) -> float:
    if not a or not b: return 0.0
    inter = len(a & b)
    return inter / max(1, min(len(a), len(b)))  # in [0,1]

def assess_quality(item: Dict) -> str:
    """
    Deterministic heuristic quality score -> letter:
      - base from content length,
      - + date presence (year/month tokens),
      - + entity/keyword overlap between claim text and source title/snippet,
    All features are bias-neutral (no publisher/brand lists).
    """
    src = item.get("source", {}) or {}
    title = (src.get("title") or "").strip()
    snip  = (src.get("snippet") or "").strip()
    text  = (title + " " + snip).strip()
    ln = len(text)
    base = 0.35 + (0.15 if ln >= 60 else 0.05 if ln >= 20 else 0.0)  # 0.35..0.50

    # optional claim_text may be present (pipeline will attach it)
    claim_text = (item.get("claim_text") or "").strip()
    claim_toks = _tokens(claim_text)
    source_toks = _tokens(text)
    # favor capitalized tokens overlap a bit more
    ent_overlap = _overlap(_entities_like(claim_text), _entities_like(text))  # 0..1
    kw_overlap  = _overlap(claim_toks, source_toks) * 0.5  # dampen raw token overlap

    date_feat = _date_presence(text)  # 0..0.75

    score = base + 0.25 * date_feat + 0.25 * ent_overlap + 0.15 * kw_overlap
    # clamp
    if score > 1.0: score = 1.0
    if score < 0.0: score = 0.0
    return _letter(score)