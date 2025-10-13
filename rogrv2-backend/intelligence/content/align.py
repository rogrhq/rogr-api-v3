from __future__ import annotations
from typing import List, Dict, Any, Tuple
import re
import os
import json

# Shared advanced text processing utilities
from intelligence.content.shared.text_utils import normalize_text_advanced as _normalize_sentence

__all__ = [
    "align_claim_to_text",
    "align_claim_to_text_windowed",
    "extract_claim_pieces",
    "split_sentences",
]

_SENT_SPLIT = re.compile(r"(?<=[\.!?])\s+")
_WORD = re.compile(r"[A-Za-z][A-Za-z\-']+")
_YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")
_PERCENT_IN_CLAIM = re.compile(r"(\d+(?:\.\d+)?)\s*%|(\d+)\s*percent", re.IGNORECASE)

INCREASE = re.compile(r"\b(increase|increased|raises?|raised|rise|rose|grow|grew|growth)\b", re.IGNORECASE)
DECREASE = re.compile(r"\b(decrease|decreased|cut|cuts|reduction|reduced|decline|fell|drop|dropped)\b", re.IGNORECASE)
NEG = re.compile(r"\b(no|not|did\s+not|does\s+not|never|without|deny|denies|false)\b", re.IGNORECASE)
FLAT = re.compile(
    r"\b(flat|unchanged|no\s+change|held?\s+steady|hold(?:s|ing)?\s+steady|freeze|frozen|maintain(?:ed)?|kept\s+(?:the\s+)?same)\b",
    re.IGNORECASE,
)

# Small map for number words (1..20) to support 'eight percent' matching
_NUM_WORDS = {
    "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
    "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten",
    "11": "eleven", "12": "twelve", "13": "thirteen", "14": "fourteen",
    "15": "fifteen", "16": "sixteen", "17": "seventeen", "18": "eighteen",
    "19": "nineteen", "20": "twenty",
}

# Local _normalize_sentence() removed - now using shared normalize_text_advanced from text_utils
# Stop words, apostrophe handling, and possessive removal handled by normalize_text_advanced()
# See intelligence/content/shared/text_utils.py for implementation

def _diag_enabled() -> bool:
    v = os.getenv("ROGR_DIAG_ALIGN", "")
    return v.lower() in ("1", "true", "yes", "on")

def _diag(event: str, **fields: Any) -> None:
    if not _diag_enabled():
        return
    try:
        rec = {"event": f"align.{event}"}
        rec.update(fields)
        print(json.dumps(rec, ensure_ascii=False))
    except Exception:
        pass

def _shingles(text: str, k: int = 3) -> set[str]:
    t = _normalize_sentence(text).replace(" ", "")
    if len(t) < k:
        return set()
    return { t[i:i+k] for i in range(0, len(t) - k + 1) }

def _jaccard(a: str, b: str, k: int = 3) -> float:
    A = _shingles(a, k)
    B = _shingles(b, k)
    if not A or not B:
        return 0.0
    inter = len(A & B)
    union = len(A | B)
    if union == 0:
        return 0.0
    return inter / union


def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    parts = _SENT_SPLIT.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def extract_claim_pieces(claim: str) -> Dict[str, Any]:
    claim_l = (claim or "").strip()
    # entities: capitalized tokens in claim
    entities: List[str] = []
    for m in _WORD.finditer(claim_l):
        w = m.group(0)
        if w[:1].isupper():
            entities.append(w.lower())
    entities = list(dict.fromkeys(entities))  # dedupe preserve order
    # percent number
    pct_num: str | None = None
    m = _PERCENT_IN_CLAIM.search(claim_l)
    if m:
        pct_num = (m.group(1) or m.group(2) or "").split(".")[0]
    years = [y for y in _YEAR.findall(claim_l)]
    return {"entities": entities, "percent": pct_num, "years": years}


def _percent_hit(sentence: str, num: str | None) -> bool:
    if not num:
        return False
    s_raw = sentence or ""
    s = _normalize_sentence(s_raw)
    # digit forms: 8%, 8 %, 8 percent, 8-percent
    if re.search(rf"\b{re.escape(num)}\s*%\b", s):
        return True
    if re.search(rf"\b{re.escape(num)}\s*percent\b", s):
        return True
    if re.search(rf"\b{re.escape(num)}\s*-\s*percent\b", s):
        return True
    # word form: eight percent (if num <= 20)
    word = _NUM_WORDS.get(num)
    if word and re.search(rf"\b{re.escape(word)}\s*percent\b", s):
        return True
    return False


def _entity_hit(sentence: str, entities: List[str]) -> bool:
    s = _normalize_sentence(sentence)
    if not s or not entities:
        return False
    # support 'city of <entity>' and possessives implicitly via normalization
    forms: List[str] = []
    for e in entities[:4]:
        e_norm = _normalize_sentence(e)
        if not e_norm:
            continue
        forms.append(e_norm)
        forms.append(f"city of {e_norm}")
    return any(re.search(rf"\b{re.escape(f)}\b", s) for f in forms)


def _year_hit(sentence: str, years: List[str]) -> bool:
    if not years:
        return False
    s = sentence or ""
    return any((y in s) for y in years)


def _stance_for_sentence(sentence: str) -> str:
    # Heuristic stance:
    # - decrease cues OR flat/unchanged cues -> challenge
    # - increase without negation -> support
    sent = sentence or ""
    if DECREASE.search(sent) is not None:
        return "challenge"
    if FLAT.search(sent) is not None:
        return "challenge"
    inc = INCREASE.search(sent) is not None
    neg = NEG.search(sent) is not None
    if inc and neg:
        return "challenge"
    if inc and not neg:
        return "support"
    return "unrelated"


def align_claim_to_text(claim: str, text: str) -> Dict[str, Any]:
    pieces = extract_claim_pieces(claim)
    entities = pieces.get("entities") or []
    pct = pieces.get("percent")
    years = pieces.get("years") or []
    matches: List[Dict[str, Any]] = []
    entity_hit = False
    number_hit = False
    year_hit = False
    best_score = 0.0
    best_stance = "unrelated"
    sents = split_sentences(text)
    for sent in sents:
        fields: List[str] = []
        eh = _entity_hit(sent, entities)
        nh = _percent_hit(sent, pct)
        yh = _year_hit(sent, years)
        if eh:
            fields.append("entity")
        if nh:
            fields.append("number")
        if yh:
            fields.append("year")
        if fields:
            stance = _stance_for_sentence(sent)
            score = 0.5 + 0.25 * min(2, len(fields))  # 0.75 or 1.0 for 2+ fields
            matches.append({"sentence": sent, "fields": fields, "stance": stance, "score": score})
            entity_hit = entity_hit or eh
            number_hit = number_hit or nh
            year_hit = year_hit or yh
            if score > best_score:
                best_score = score
                best_stance = stance
    # --- Fallback: excerpt-level alignment if no sentence-level matches ---
    if not matches and (text or "").strip():
        excerpt_norm = _normalize_sentence(text)
        # excerpt-level entity
        ex_entity = False
        for e in entities[:4]:
            e_norm = _normalize_sentence(e)
            if not e_norm:
                continue
            if re.search(rf"\b{re.escape(e_norm)}\b", excerpt_norm) or \
               re.search(rf"\bcity\s+of\s+{re.escape(e_norm)}\b", excerpt_norm):
                ex_entity = True
                break
        # excerpt-level percent & year
        ex_number = _percent_hit(excerpt_norm, pct)
        ex_year = any(y in (text or "") for y in years)
        # choose a stance-bearing sentence if present
        stance_sent = None
        for s in sents:
            st = _stance_for_sentence(s)
            if st in ("support", "challenge"):
                stance_sent = s
                stance_val = st
                break
        # require at least two excerpt-level signals and a stance sentence
        if stance_sent and (int(ex_entity) + int(ex_number) + int(ex_year) >= 2):
            matches.append({
                "sentence": stance_sent,
                "fields": [],  # fields are excerpt-level here
                "stance": stance_val,
                "score": 0.6,
            })
            entity_hit = entity_hit or ex_entity
            number_hit = number_hit or ex_number
            year_hit = year_hit or ex_year
            best_score = max(best_score, 0.6)
            best_stance = stance_val
    return {
        "entity_hit": bool(entity_hit),
        "number_hit": bool(number_hit),
        "year_hit": bool(year_hit),
        "matches": matches,
        "content_score": float(best_score),
        "item_stance": best_stance,
    }


def align_claim_to_text_windowed(claim: str, text: str) -> Dict[str, Any]:
    """Windowed alignment over the full (streamed) text.
    Slides a window of W sentences; aggregates fields across sentences in the window.
    Returns the best-scoring window as matches[0] with stance and content_score.
    Environment knobs:
      ROGR_ALIGN_WINDOW_S (default 3)
      ROGR_ALIGN_MAX_SENTS (default 140)
    """
    pieces = extract_claim_pieces(claim)
    entities = pieces.get("entities") or []
    pct = pieces.get("percent")
    years = pieces.get("years") or []

    try:
        W = max(2, int(os.getenv("ROGR_ALIGN_WINDOW_S", "3")))
    except Exception:
        W = 3
    try:
        MAX_S = max(20, int(os.getenv("ROGR_ALIGN_MAX_SENTS", "140")))
    except Exception:
        MAX_S = 140
    try:
        J_WITH_STANCE = float(os.getenv("ROGR_ALIGN_JACCARD_WITH_STANCE", "0.32"))
    except Exception:
        J_WITH_STANCE = 0.32
    try:
        J_STRONG = float(os.getenv("ROGR_ALIGN_JACCARD_STRONG", "0.42"))
    except Exception:
        J_STRONG = 0.42

    sents_all = split_sentences(text or "")
    sents = sents_all[:MAX_S]
    _diag("start", sentences=len(sents), window=W, max_sents=MAX_S)
    best_score = 0.0
    best_fields: List[str] = []
    best_stance = "unrelated"
    best_window: List[str] = []
    matches: List[Dict[str, Any]] = []

    topj: List[Tuple[float, str, str]] = []  # (jaccard, stance, snippet)
    for i in range(0, max(0, len(sents) - W + 1)):
        win = sents[i:i+W]
        # aggregate within window
        e_hit = any(_entity_hit(s, entities) for s in win)
        n_hit = any(_percent_hit(s, pct) for s in win)
        y_hit = any(_year_hit(s, years) for s in win)
        stance_vals = { _stance_for_sentence(s) for s in win }
        stance = "unrelated"
        if "support" in stance_vals and "challenge" in stance_vals:
            stance = "mixed"
        elif "support" in stance_vals:
            stance = "support"
        elif "challenge" in stance_vals:
            stance = "challenge"
        # score: start from hard fields, small bump for stance presence
        fields: List[str] = []
        if e_hit: fields.append("entity")
        if n_hit: fields.append("number")
        if y_hit: fields.append("year")
        # Jaccard fallback for paraphrases / split signals
        win_text = " ".join(win)
        j = _jaccard(claim, win_text, 3)
        # track top-jaccard windows for diagnostics
        if len(topj) < 3:
            topj.append((j, stance, win_text[:240]))
        else:
            topj.sort(key=lambda t: t[0])
            if j > topj[0][0]:
                topj[0] = (j, stance, win_text[:240])

        # Decide whether this window is a candidate
        hard_ok = bool(fields)
        hybrid_ok = (j >= J_WITH_STANCE and stance in ("support", "challenge", "mixed"))
        strong_ok = (j >= J_STRONG)
        if not (hard_ok or hybrid_ok or strong_ok):
            continue

        # scoring
        score = 0.4 + 0.2 * min(3, len(fields))
        if stance in ("support", "challenge"): score += 0.12
        if stance == "mixed": score += 0.08
        # jaccard contributes softly; capped to keep determinism predictable
        score += min(0.25, j * 0.35)
        if score > best_score:
            best_score = score
            best_fields = fields
            best_stance = stance
            best_window = win

    if best_window:
        matches.append({
            "sentence": " ".join(best_window)[:800],
            "fields": best_fields,
            "stance": best_stance,
            "score": float(best_score),
        })

    # excerpt-level flags for summary booleans
    entity_hit = any(_entity_hit(s, entities) for s in sents)
    number_hit = any(_percent_hit(s, pct) for s in sents)
    year_hit = any(_year_hit(s, years) for s in sents)

    # diagnostics summary
    try:
        topj_sorted = sorted(topj, key=lambda t: t[0], reverse=True)
        _diag(
            "summary",
            has_match=bool(matches),
            best_score=float(best_score),
            best_stance=best_stance,
            entity_any=bool(entity_hit),
            number_any=bool(number_hit),
            year_any=bool(year_hit),
            topj=[round(t[0], 3) for t in topj_sorted],
            topj_stances=[t[1] for t in topj_sorted],
        )
        if not matches:
            reason = "no_candidate"
            if not sents:
                reason = "no_sentences"
            elif len(sents) < W:
                reason = "insufficient_window"
            elif not (entity_hit or number_hit or year_hit) and (not topj_sorted or topj_sorted[0][0] < 0.2):
                reason = "low_signal_low_similarity"
            _diag("reject", reason=reason)
    except Exception:
        pass

    return {
        "entity_hit": bool(entity_hit),
        "number_hit": bool(number_hit),
        "year_hit": bool(year_hit),
        "matches": matches,
        "content_score": float(best_score),
        "item_stance": best_stance,
    }
# === BEGIN ROGR P19 DIAG INJECT (append-once at end of file) ===
from typing import Any, Dict, List, Tuple, Optional
import os, re, json

def _rogr_p19_diag_enabled() -> bool:
    v = os.getenv("ROGR_DIAG_ALIGN", "")
    return v.lower() in ("1","true","yes","on")

def _rogr_p19_diag(event: str, **fields: Any) -> None:
    if not _rogr_p19_diag_enabled():
        return
    try:
        rec = {"event": f"align.{event}"}
        rec.update(fields)
        print(json.dumps(rec, ensure_ascii=False))
    except Exception:
        # diagnostics must never break functional flow
        pass

# Try to capture the original aligner (if defined above)
try:
    _ROGR_P19_ORIG_ALIGN = align_claim_to_text_windowed  # type: ignore[name-defined]
except Exception:
    _ROGR_P19_ORIG_ALIGN = None  # type: ignore[assignment]

# Minimal fallbacks (only used if no original function is present)
def _rogr_p19_norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"['׳`´]", "'", s)
    s = s.replace("'s", " ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _rogr_p19_split(text: str) -> List[str]:
    try:
        # prefer existing splitter if available
        return split_sentences(text or "")  # type: ignore[name-defined]
    except Exception:
        return re.split(r"(?<=[.!?])\s+", text or "")

def _rogr_p19_jaccard(a: str, b: str, n: int = 3) -> float:
    try:
        return jaccard_ngrams(a, b, n)  # type: ignore[name-defined]
    except Exception:
        def ngrams(x: str, m: int) -> set:
            xs = _rogr_p19_norm(x).split()
            return set(tuple(xs[i:i+m]) for i in range(max(0, len(xs)-m+1)))
        A, B = ngrams(a, n), ngrams(b, n)
        if not A or not B:
            return 0.0
        return len(A & B) / float(len(A | B))

def _rogr_p19_align_fallback(claim: str, text: str) -> Dict[str, Any]:
    W, MAX_S = 3, 80
    sents = _rogr_p19_split(text)[:MAX_S]
    _rogr_p19_diag("start", sentences=len(sents), window=W, max_sents=MAX_S)

    best_score = 0.0
    best_window: List[str] = []
    topj: List[Tuple[float,str]] = []
    for i in range(0, max(0, len(sents)-W+1)):
        win = sents[i:i+W]
        win_text = " ".join(win)
        j = _rogr_p19_jaccard(claim, win_text, 3)
        if len(topj) < 3:
            topj.append((j, win_text[:200]))
        else:
            topj.sort(key=lambda t: t[0])
            if j > topj[0][0]:
                topj[0] = (j, win_text[:200])
        if j > best_score:
            best_score = j
            best_window = win

    matches: List[Dict[str, Any]] = []
    if best_window:
        matches.append({"sentence": " ".join(best_window)[:800],
                        "fields": [], "stance": "unrelated", "score": float(best_score)})

    try:
        topj_sorted = sorted(topj, key=lambda t: t[0], reverse=True)
        _rogr_p19_diag("summary",
                       has_match=bool(matches),
                       best_score=float(best_score),
                       entity_any=False, number_any=False, year_any=False,
                       topj=[round(t[0],3) for t,_ in topj_sorted])
        if not matches:
            _rogr_p19_diag("reject", reason="no_candidate")
    except Exception:
        pass

    return {
        "matches": matches,
        "entity_hit": False, "number_hit": False, "year_hit": False,
        "item_stance": "unrelated" if not matches else "support",
        "content_score": float(best_score),
    }

# Wrapper that preserves original behavior and adds diagnostics
def align_claim_to_text_windowed(claim: str, text: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:  # type: ignore[override]
    """
    Wrapped by ROGR P19 to emit diagnostics. Behavior of the original aligner is preserved.
    If original not found, uses a minimal fallback aligner.
    """
    W, MAX_S = 3, 80
    sents = _rogr_p19_split(text)[:MAX_S]
    _rogr_p19_diag("start", sentences=len(sents), window=W, max_sents=MAX_S)

    if _ROGR_P19_ORIG_ALIGN is not None:
        # Call original without adding new required parameters (maintain signature stability)
        try:
            res: Dict[str, Any] = _ROGR_P19_ORIG_ALIGN(claim, text, *args, **kwargs)  # type: ignore[misc]
        except TypeError:
            # In case original doesn't accept kwargs we added elsewhere, retry with minimal signature
            res = _ROGR_P19_ORIG_ALIGN(claim, text)  # type: ignore[misc]
    else:
        res = _rogr_p19_align_fallback(claim, text)

    # Emit summary/reject based on result shape
    try:
        matches = res.get("matches") or []
        best_score = float(res.get("content_score") or 0.0)
        entity_any = bool(res.get("entity_hit"))
        number_any = bool(res.get("number_hit"))
        year_any = bool(res.get("year_hit"))
        # we cannot recompute topj here; omit for wrapper summary
        _rogr_p19_diag("summary",
                       has_match=bool(matches),
                       best_score=best_score,
                       entity_any=entity_any, number_any=number_any, year_any=year_any,
                       topj=[])
        if not matches:
            _rogr_p19_diag("reject", reason="no_candidate")
    except Exception:
        pass

    return res
# === END ROGR P19 DIAG INJECT ===
