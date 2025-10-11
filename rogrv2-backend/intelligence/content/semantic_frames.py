from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple

# --- Basic text utilities (deterministic, no external deps) ---
_APOS = re.compile(r"['׳`´]")
_PUNCT = re.compile(r"[^a-z0-9\s]")
_WS = re.compile(r"\s+")
_SENT_SPLIT = re.compile(r"(?<=[\.\!\?])\s+")

_STOP = {
    "the","a","an","of","in","on","for","to","and","or","by","with","from","as","at",
    "this","that","be","is","are","was","were","it","its","their","his","her","they",
    "we","you"
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
    return sents[:600]

def _trigrams(toks: List[str]) -> List[Tuple[str,str,str]]:
    if len(toks) < 3:
        return []
    return [(toks[i], toks[i+1], toks[i+2]) for i in range(len(toks)-2)]

def _jaccard_tris(a: List[Tuple[str,str,str]], b: List[Tuple[str,str,str]]) -> float:
    if not a or not b:
        return 0.0
    A = set(a); B = set(b)
    inter = len(A & B)
    union = len(A | B)
    return inter / union if union else 0.0

def _best_offset(raw: str, snippet: str) -> Tuple[int,int]:
    if not raw or not snippet:
        return (-1,-1)
    idx = raw.find(snippet)
    if idx >= 0:
        return (idx, idx + len(snippet))
    needle = snippet[:60]
    i2 = raw.find(needle)
    if i2 >= 0:
        return (i2, min(len(raw), i2 + len(snippet)))
    return (-1,-1)

# --- Domain-ish lexica (minimal, deterministic) ---
BUDGET_CONTEXT = {"budget","general fund","operating budget","fy","fiscal","appropriation","spending","expenditure","revenue"}
INC_VERBS = {"increase","increased","raise","raised","boost","boosted","grow","grew","expand","expanded","approve","approved","adopt","adopted","pass","passed"}
DEC_VERBS = {"decrease","decreased","reduce","reduced","cut","cuts","lower","lowered","decline","declined","reject","rejected","fail","failed","vote down","voted down"}
NEG_WORDS  = {"not","no","never","without","deny","denied","false","untrue","incorrect","misleading","debunk","refute","contradict","dispute","challenge","rebut","didnt","didn't","doesnt","doesn't","isnt","isn't"}

def _has_budget_context(toks: List[str]) -> bool:
    return any(w in BUDGET_CONTEXT for w in toks)

def _detect_action(toks: List[str]) -> str:
    # prefer explicit increase/decrease, else unknown
    if any(w in INC_VERBS for w in toks):
        return "increase"
    if any(w in DEC_VERBS for w in toks):
        return "decrease"
    return "unknown"

def _percent_numbers(text: str) -> List[float]:
    hits: List[float] = []
    for m in re.finditer(r"\b(\d{1,3})\s*%\b", text):
        try: hits.append(float(m.group(1)))
        except: pass
    for m in re.finditer(r"\b(\d{1,3})\s+percent\b", text):
        try: hits.append(float(m.group(1)))
        except: pass
    return hits[:5]

def _years(text: str) -> List[int]:
    ys: List[int] = []
    for m in re.finditer(r"\b(19|20)\d{2}\b", text):
        try: ys.append(int(m.group(0)))
        except: pass
    return ys[:5]

def _entities_from_claim_tokens(toks: List[str]) -> List[str]:
    # crude: multi-token city/org names and proper-like tokens (length>2) excluding common words
    # Keep top 8
    out: List[str] = []
    for t in toks:
        if len(t) > 2 and t not in BUDGET_CONTEXT and t not in INC_VERBS and t not in DEC_VERBS:
            out.append(t)
    # dedupe order
    seen = set(); keep=[]
    for t in out:
        if t not in seen:
            seen.add(t); keep.append(t)
    return keep[:8]

# --- Frame extraction ---
def extract_claim_frame(claim_text: str) -> Dict[str, Any]:
    ctoks = _tokens(claim_text)
    c_norm = _norm(claim_text)
    frame: Dict[str, Any] = {
        "entity": _entities_from_claim_tokens(ctoks),
        "action": _detect_action(ctoks) or "increase",
        "quantity": _percent_numbers(c_norm)[:1],  # [8.0] if "8%"
        "year": _years(c_norm)[:1],                # [2024]
        "scope": "budget" if any(w in BUDGET_CONTEXT for w in ctoks) or "budget" in c_norm else "unknown",
    }
    return frame

def extract_window_frame(win_text: str) -> Dict[str, Any]:
    wtoks = _tokens(win_text)
    w_norm = _norm(win_text)
    return {
        "entity": _entities_from_claim_tokens(wtoks),
        "action": _detect_action(wtoks),
        "quantity": _percent_numbers(w_norm)[:1],
        "year": _years(w_norm)[:1],
        "scope": "budget" if _has_budget_context(wtoks) else "unknown",
        "neg": bool(set(wtoks) & NEG_WORDS),
        "toks": wtoks,
    }

def _quantity_compatible(cq: List[float], wq: List[float], tol_pp: float = 1.0) -> Tuple[bool, str]:
    if not cq:
        return (True, "no_claim_quantity")
    if not wq:
        return (False, "no_window_quantity")
    try:
        c = cq[0]; w = wq[0]
        if abs(c - w) <= tol_pp:
            return (True, "within_tolerance")
        return (False, "mismatch_quantity")
    except Exception:
        return (False, "quantity_error")

def _year_compatible(cy: List[int], wy: List[int]) -> Tuple[bool, str]:
    if not cy:
        return (True, "no_claim_year")
    if not wy:
        return (False, "no_window_year")
    return ((cy[0] == wy[0]), "year_match" if cy[0] == wy[0] else "year_mismatch")

def _entity_overlap(ce: List[str], we: List[str]) -> Tuple[bool, str]:
    if not ce:
        return (True, "no_claim_entity")
    inter = set(ce) & set(we)
    return (bool(inter), "entity_overlap" if inter else "entity_mismatch")

def _scope_ok(cs: str, ws: str) -> Tuple[bool, str]:
    if cs == "unknown":
        return (True, "no_claim_scope")
    return ((ws == "budget"), "budget_context" if ws == "budget" else "scope_mismatch")

def _entail_contradict(claim: Dict[str,Any], win: Dict[str,Any], sim: float) -> Tuple[str, List[str]]:
    rules: List[str] = []
    eok, ewhy = _entity_overlap(claim["entity"], win["entity"]); rules.append(ewhy)
    sok, swhy = _scope_ok(claim["scope"], win["scope"]); rules.append(swhy)
    yok, ywhy = _year_compatible(claim["year"], win["year"]); rules.append(ywhy)
    qok, qwhy = _quantity_compatible(claim["quantity"], win["quantity"]); rules.append(qwhy)

    action = win["action"]
    neg = win.get("neg", False)

    label = "unrelated"
    # Primary contradiction signals
    if action == "decrease" and (eok and sok):
        label = "contradict"; rules.append("antonym_action")
    elif neg and (eok and sok):
        label = "contradict"; rules.append("negation_present")
    # Primary entailment signals
    elif action == "increase" and (eok and sok and qok):
        label = "entail"; rules.append("aligned_action_quantity")
    # If still undecided, use similarity + partials
    if label == "unrelated":
        if sim >= 0.28 and eok and sok:
            label = "mixed"; rules.append("similarity_partial")

    # Year conflicts can downgrade
    if label in ("entail","mixed") and not yok and claim["year"]:
        rules.append("year_penalty")
        label = "mixed"

    return (label, rules)

def analyze_frames(claim_text: str, content: str, *, window: int = 3, max_windows: int = 500) -> Dict[str, Any]:
    """
    Return:
      {
        "item_frame": {entity[], action, quantity[], year[], scope},
        "frame_matches": [{label, score, slots[], rules[], quote, offset_start, offset_end}],
        "frame_confidence": float
      }
    """
    claim = extract_claim_frame(claim_text)
    sents = _split_sentences(content)
    ctoks = _tokens(claim_text)
    ctris = _trigrams(ctoks)

    matches: List[Dict[str,Any]] = []
    best_score = 0.0
    best_frame: Dict[str,Any] = {"entity": [], "action": "unknown", "quantity": [], "year": [], "scope": "unknown"}

    # Handle short evidence: create at least one window
    if len(sents) < window:
        windows = [sents] if sents else []
    else:
        num_windows = min(len(sents) - window + 1, max_windows)
        windows = [sents[i:i + window] for i in range(num_windows)]

    for win_sents in windows:
        win_text = " ".join(win_sents).strip()
        wframe = extract_window_frame(win_text)
        wtris = _trigrams(_tokens(win_text))
        sim = _jaccard_tris(ctris, wtris)
        label, rules = _entail_contradict(claim, wframe, sim)

        # slots matched count
        slots = []
        if (set(claim["entity"]) & set(wframe["entity"])): slots.append("entity")
        if wframe["action"] != "unknown": slots.append("action")
        if wframe["quantity"]: slots.append("quantity")
        if wframe["year"]: slots.append("year")
        if wframe["scope"] == "budget": slots.append("scope")

        # score combines similarity + slot coverage; contradiction doesn't zero score (we want strong contradict too)
        coverage = len(slots) / 5.0
        base = min(0.6, sim * 0.8) + 0.4 * coverage
        score = max(0.0, min(1.0, base))

        quote = win_text[:360]
        off_s, off_e = _best_offset(content, quote)

        matches.append({
            "label": label,             # entail/contradict/mixed/unrelated
            "score": float(score),
            "slots": slots,
            "rules": rules,
            "quote": quote,
            "offset_start": off_s,
            "offset_end": off_e,
        })
        if score > best_score:
            best_score = score
            best_frame = {
                "entity": wframe["entity"],
                "action": wframe["action"],
                "quantity": wframe["quantity"],
                "year": wframe["year"],
                "scope": wframe["scope"],
            }

    # keep top 5 matches by score
    matches.sort(key=lambda m: m.get("score", 0.0), reverse=True)
    matches = matches[:5]
    conf = float(best_score)
    return {
        "item_frame": best_frame,
        "frame_matches": matches,
        "frame_confidence": conf,
    }
