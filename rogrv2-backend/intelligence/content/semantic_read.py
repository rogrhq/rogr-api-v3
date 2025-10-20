from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple

# Shared utilities
from intelligence.content.shared.text_utils import (
    normalize_text_advanced,
    tokenize_advanced,
    trigrams as shared_trigrams,
    jaccard_similarity as shared_jaccard
)
from intelligence.content.shared.entities import extract_entities, entity_overlap
from intelligence.content.shared.paraphrases import paraphrase_match_score, find_paraphrases_in_text
# Phase 9: Semantic depth and numeric precision (ADDED)
from intelligence.content.shared.semantic_depth import check_negation_agreement, detect_hedging
from intelligence.content.shared.numeric_precision import extract_and_match_numbers
from intelligence.content.shared.embeddings import get_entailment_stance

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
    """Now uses shared normalize_text_advanced"""
    return normalize_text_advanced(s)

def _tokens(s: str) -> List[str]:
    """Now uses shared tokenize_advanced"""
    return tokenize_advanced(s)

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
    """Now uses shared trigrams"""
    return shared_trigrams(toks)

def _jaccard(a: List[Tuple[str,str,str]], b: List[Tuple[str,str,str]]) -> float:
    """Now uses shared jaccard_similarity"""
    return shared_jaccard(a, b)

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

def analyze_item(claim_text: str, item: Dict[str,Any], *, window: int = 3, stance_threshold: float = 0.60) -> Dict[str,Any]:
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

        # Enhanced: Add paraphrase matching
        para_score = paraphrase_match_score(claim_text, win)

        # score:
        # base from signals
        base = 0.0
        if ent_hit: base += 0.25
        if num_hit: base += 0.25
        if year_hit: base += 0.15
        # similarity: 70% jaccard, 30% paraphrase
        base += min(0.35, (0.7 * j + 0.3 * para_score) * 0.7)  # cap contribution
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

    # Re-compute stance on top findings using cross-encoder entailment
    for finding in findings:
        quote = finding.get("quote", "")
        if quote and quote.strip():
            try:
                entailment_result = get_entailment_stance(claim_text, quote)
                stance_value = entailment_result.get("stance", "unrelated")
                # Map contextual_support to support for downstream compatibility
                if stance_value == "contextual_support":
                    stance_value = "support"
                finding["stance"] = stance_value
            except Exception as e:
                # Keep existing keyword-based stance on error
                pass

    item["findings"] = findings

    # item grade blends best score with coverage
    cov = item.get("coverage") or "snippet_only"
    cov_w = {"full": 1.0, "partial": 0.75, "snippet_only": 0.5}.get(cov, 0.5)
    item_grade = max(0.0, min(1.0, 0.6 * best + 0.4 * cov_w))

    # Phase 9: Apply precision checks to grade (ADDED)
    if findings:
        # Use the best finding's window for Phase 9 checks
        best_finding = findings[0]
        evidence_window = best_finding.get("quote", "")

        # Phase 9.1: Numeric precision check
        # Extract numbers from claim (simple extraction)
        claim_numbers = _percent_numbers(claim_norm) + [str(y) for y in _years(claim_norm)]
        if claim_numbers:
            number_match = extract_and_match_numbers(claim_text, evidence_window)
            # Penalty for numeric mismatch
            if number_match.get('unmatched_claim_count', 0) > 0:
                item_grade = item_grade * 0.7
                item["numeric_mismatch"] = True
                item["numeric_precision"] = number_match

        # Phase 9.2: Negation agreement check
        negation_check = check_negation_agreement(claim_text, evidence_window)
        if negation_check.get('semantic_flip'):
            # Flip stance of best finding if negation mismatch
            if best_finding.get('stance') == 'support':
                best_finding['stance'] = 'challenge'
            elif best_finding.get('stance') == 'challenge':
                best_finding['stance'] = 'support'
            item["negation_flip"] = True

        # Phase 9.3: Hedging penalty
        evidence_hedging = detect_hedging(evidence_window)
        if evidence_hedging.get('has_hedging', False):
            item_grade = item_grade * 0.9
            item["hedging_detected"] = True

    item["item_grade"] = float(item_grade)
    item["grade_label"] = "high" if item_grade >= 0.67 else ("medium" if item_grade >= 0.4 else "low")
    return item
