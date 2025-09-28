from __future__ import annotations
from typing import Dict, Any, Tuple
import re
from urllib.parse import urlparse

# Very small, explainable credibility heuristic:
#  - base by source_type (if present): peer_review > government > news > web > blog > social
#  - TLD bonus for .gov, .edu, .org (light)
#  - recency bonus (if item["age_days"] present)
#  - snippet length sanity (short = lower)
# Returns (score_0_100, details_dict) and never raises.

_TYPE_PRIOR = {
    "peer_review": 85,
    "government": 80,
    "news": 70,
    "web": 60,
    "blog": 55,
    "social": 45,
}

_TLD_BONUS = {
    ".gov": 8,
    ".edu": 6,
    ".org": 2,
}

def _tld_bonus(url: str) -> int:
    try:
        host = urlparse(url).hostname or ""
        m = re.search(r"(\.[A-Za-z]{2,})$", host)
        if not m:
            return 0
        return _TLD_BONUS.get(m.group(1).lower(), 0)
    except Exception:
        return 0

def _recency_bonus(item: Dict[str, Any]) -> int:
    # If pipeline/normalizer computed age_days, reward freshness (bounded)
    d = 0
    try:
        age = item.get("age_days")
        if isinstance(age, (int, float)):
            if age <= 3:
                d = 8
            elif age <= 14:
                d = 5
            elif age <= 60:
                d = 3
            elif age <= 365:
                d = 1
            else:
                d = 0
    except Exception:
        d = 0
    return d

def _snippet_adjust(item: Dict[str, Any]) -> int:
    try:
        sn = (item.get("snippet") or "").strip()
        n = len(sn)
        # reward reasonable context, penalize extremely short
        if n < 40:
            return -6
        if n < 80:
            return -2
        if n > 500:
            return 1
        return 3
    except Exception:
        return 0

def score_item(item: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    st = (item.get("source_type") or "").strip().lower()
    base = _TYPE_PRIOR.get(st, 58)  # default slightly below generic web
    bonus_tld = _tld_bonus(item.get("url") or "")
    bonus_recent = _recency_bonus(item)
    bonus_snip = _snippet_adjust(item)

    raw = base + bonus_tld + bonus_recent + bonus_snip
    # clamp to [0,100]
    score = max(0, min(100, int(round(raw))))
    details = {
        "base_from_type": base,
        "tld_bonus": bonus_tld,
        "recency_bonus": bonus_recent,
        "snippet_adjust": bonus_snip,
    }
    return score, details