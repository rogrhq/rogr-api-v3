from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple

_APOS = re.compile(r"['׳`´]")
_PUNCT = re.compile(r"[^a-z0-9\s]")
_WS = re.compile(r"\s+")
_SENT_SPLIT = re.compile(r"(?<=[\.\!\?])\s+")

_NEG_TOKENS = {
    "not","no","never","none","without","fails","didn't","didnt","doesn't","doesnt","isn't","isnt",
    "false","untrue","incorrect","misleading","debunk","refute","contradict","dispute","challenge"
}
_SUPPORT_VERBS = {"confirm","shows","reports","states","announced","increased","approved","adopted","published","released"}
_STOP = {
    "the","a","an","of","in","on","for","to","and","or","by","with","from","as","at","this","that","be","is","are","was","were","it","its"
}

def _norm(s: str) -> str:
    s = (s or "").lower()
    s = _APOS.sub("'", s)
    s = s.replace("'s", " ")
    s = _PUNCT.sub(" ", s)
    s = _WS.sub(" ", s).strip()
    return s

def _tokens(s: str) -> List[str]:
    return [t for t in _norm(s).split() if t and t not in _STOP]

def _split_sentences(text: str) -> List[str]:
    text = text or ""
    parts = _SENT_SPLIT.split(text)
    # Collapse overly short fragments with neighbors
    sents: List[str] = []
    buf = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) < 40 and buf:
            buf = (buf + " " + p).strip()
        else:
            if buf:
                sents.append(buf)
            buf = p
    if buf:
        sents.append(buf)
    return sents[:500]

def _trigrams(toks: List[str]) -> List[Tuple[str,str,str]]:
    if len(toks) < 3:
        return []
    return [(toks[i], toks[i+1], toks[i+2]) for i in range(len(toks)-2)]

def _jaccard(a: List[Tuple[str,str,str]], b: List[Tuple[str,str,str]]) -> float:
    if not a or not b:
        return 0.0
    A = set(a); B = set(b)
    inter = len(A & B)
    union = len(A | B)
    return inter / union if union else 0.0

def _percent_numbers(text: str) -> List[str]:
    hits = []
    # 8% or 8 percent
    for m in re.finditer(r"\b(\d{1,3})\s*%\b", text):
        hits.append(m.group(1) + "%")
    for m in re.finditer(r"\b(\d{1,3})\s+percent\b", text):
        hits.append(m.group(1) + "%")
    return hits[:5]

def _years(text: str) -> List[str]:
    return [m.group(0) for m in re.finditer(r"\b(19|20)\d{2}\b", text)]

def _stance_for_window(win_norm: str) -> str:
    toks = set(win_norm.split())
    neg = bool(toks & _NEG_TOKENS)
    sup = bool(toks & _SUPPORT_VERBS)
    if neg and sup:
        return "mixed"
    if neg:
        return "challenge"
    if sup:
        return "support"
    return "unrelated"

def _best_offset(raw: str, snippet: str) -> Tuple[int,int]:
    if not raw or not snippet:
        return (-1,-1)
    # try exact
    idx = raw.find(snippet)
    if idx >= 0:
        return (idx, idx+len(snippet))
    # try a relaxed search on first 60 chars
    needle = snippet[:60]
    i2 = raw.find(needle)
    if i2 >= 0:
        return (i2, min(len(raw), i2+len(snippet)))
    return (-1,-1)

def analyze_item(claim_text: str, item: Dict[str,Any], *, window: int = 3) -> Dict[str,Any]:
    """
    Deterministic semantic pass for a single item.
    Returns an updated item with `findings` (list), `item_grade` (0..1), `grade_label`.
    Non-destructive: existing fields preserved.
    """
    content = item.get("content") or item.get("content_excerpt") or ""
    if not content:
        # still attach empty findings with low grade
        item.setdefault("findings", [])
        item.setdefault("item_grade", 0.15)
        item.setdefault("grade_label", "low")
        return item

    claim_norm = _norm(claim_text)
    c_toks = _tokens(claim_text)
    c_tris = _trigrams(c_toks)
    # pull simple "entities": longest proper-ish tokens from claim
    entities = [t for t in c_toks if len(t) > 2][:8]
    pct_targets = _percent_numbers(claim_norm)  # e.g., ["8%"]
    year_targets = _years(claim_norm)

    sents = _split_sentences(content)
    findings: List[Dict[str,Any]] = []
    best = 0.0

    # Handle short evidence: create at least one window
    if len(sents) < window:
        windows = [sents] if sents else []
    else:
        windows = [sents[i:i + window] for i in range(len(sents) - window + 1)]

    for win_sents in windows:
        win = " ".join(win_sents).strip()
        win_norm = _norm(win)
        w_toks = _tokens(win_norm)
        w_tris = _trigrams(w_toks)

        ent_hit = any(e in w_toks for e in entities)
        num_hit = False
        if pct_targets:
            # accept either exact percent string present or number+percent word nearby
            for p in pct_targets:
                n = p.rstrip("%")
                if n in w_toks or p in win_norm:
                    num_hit = True; break
        else:
            # any percent-like in window
            num_hit = bool(_percent_numbers(win_norm))
        year_hit = bool(set(year_targets) & set(_years(win_norm))) if year_targets else False

        stance = _stance_for_window(win_norm)
        j = _jaccard(c_tris, w_tris)

        # score:
        # base from signals
        base = 0.0
        if ent_hit: base += 0.25
        if num_hit: base += 0.25
        if year_hit: base += 0.15
        # similarity
        base += min(0.35, j * 0.7)  # cap contribution
        # stance adjustment (we keep both; stance used downstream)
        if stance == "mixed":
            base += 0.05
        score = max(0.0, min(1.0, base))

        snippet = win[:320]
        off_s, off_e = _best_offset(content, snippet)

        sigs: List[str] = []
        if ent_hit: sigs.append("entity")
        if num_hit: sigs.append("number")
        if year_hit: sigs.append("year")
        if stance in ("support","challenge","mixed"): sigs.append(f"stance:{stance}")

        findings.append({
            "quote": snippet,
            "offset_start": off_s,
            "offset_end": off_e,
            "stance": stance,
            "signals": sigs,
            "score": float(score),
        })
        if score > best:
            best = score

    # pick top findings (stable order by score desc then first occurrence)
    findings.sort(key=lambda f: f.get("score", 0.0), reverse=True)
    findings = findings[:5]
    item["findings"] = findings

    # item grade blends best score with coverage
    cov = item.get("coverage") or "snippet_only"
    cov_w = {"full": 1.0, "partial": 0.75, "snippet_only": 0.5}.get(cov, 0.5)
    item_grade = max(0.0, min(1.0, 0.6 * best + 0.4 * cov_w))
    item["item_grade"] = float(item_grade)
    item["grade_label"] = "high" if item_grade >= 0.67 else ("medium" if item_grade >= 0.4 else "low")
    return item
