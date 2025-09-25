import re
from typing import List
from intelligence.claims.models import ExtractedClaim, ClaimTier

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_ALPHA = re.compile(r"[A-Za-z]")

def _split_sentences(text: str) -> List[str]:
    text = (text or "").strip()
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    # If no punctuation, treat whole as one sentence
    if "." not in text and "!" not in text and "?" not in text:
        return [text] if text else []
    parts = _SENT_SPLIT.split(text)
    # Keep only non-empty, alphabetic-containing sentences
    return [p.strip() for p in parts if p.strip() and _ALPHA.search(p)]

def _tier_for_sentence(s: str, idx: int) -> ClaimTier:
    """Simple, deterministic tiering:
    - First 1–2 declarative sentences with a copula or numeric evidence → primary
    - Remaining sentences with verbs → secondary
    - Short/contextual sentences → tertiary
    """
    s_lower = s.lower()
    has_copula = any(w in s_lower for w in [" is ", " are ", " was ", " were ", " will be ", " has ", " have "])
    has_digit = any(ch.isdigit() for ch in s)
    longish = len(s) >= 60

    if idx <= 1 and (has_copula or has_digit or longish):
        return ClaimTier.primary
    # Secondary if contains common verbs or causal connectors
    if any(w in s_lower for w in [" because ", " suggests ", " indicates ", " claims ", " says ", " shows ", "finds", " found "]) or longish:
        return ClaimTier.secondary
    return ClaimTier.tertiary

def _extract_entities_simple(s: str) -> List[str]:
    """Very light, language-agnostic entity heuristic: consecutive Capitalized words (<=4 tokens)."""
    ents: List[str] = []
    tokens = s.split()
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t[:1].isupper() and t[1:].islower():
            start = i
            j = i + 1
            while j < len(tokens) and tokens[j][:1].isupper() and tokens[j][1:].islower() and (j - start) < 4:
                j += 1
            ent = " ".join(tokens[start:j]).strip(",.;:()[]")
            if len(ent) >= 2:
                ents.append(ent)
            i = j
        else:
            i += 1
    # Deduplicate preserving order
    seen = set()
    out: List[str] = []
    for e in ents:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out

def extract_claims(text: str) -> List[ExtractedClaim]:
    sents = _split_sentences(text)
    claims: List[ExtractedClaim] = []
    for idx, s in enumerate(sents):
        tier = _tier_for_sentence(s, idx)
        entities = _extract_entities_simple(s)
        priority = 0 if tier == ClaimTier.primary else (1 if tier == ClaimTier.secondary else 2)
        claims.append(ExtractedClaim(text=s, tier=tier, priority=priority, entities=entities or None))

    # --- Post-pass: guarantee at least one primary, secondary, tertiary when feasible ---
    if not claims:
        return claims

    # Ensure a primary
    if not any(c.tier == ClaimTier.primary for c in claims):
        claims[0].tier = ClaimTier.primary
        claims[0].priority = 0

    # Ensure a secondary
    if not any(c.tier == ClaimTier.secondary for c in claims) and len(claims) >= 2:
        # pick the first non-primary sentence with some "verbiness"/length; else first non-primary
        verbish = (" because ", " suggests ", " indicates ", " claims ", " says ", " shows ", " find ", " found ", " will ")
        cand_idx = None
        for i, c in enumerate(claims):
            if c.tier != ClaimTier.primary and (len(c.text) >= 50 or any(v in c.text.lower() for v in verbish)):
                cand_idx = i; break
        if cand_idx is None:
            cand_idx = next((i for i,c in enumerate(claims) if c.tier != ClaimTier.primary), 1)
        claims[cand_idx].tier = ClaimTier.secondary
        claims[cand_idx].priority = 1

    # Ensure a tertiary
    if not any(c.tier == ClaimTier.tertiary for c in claims) and len(claims) >= 3:
        # prefer the last non-primary/non-secondary, else the last one
        cand_idx = None
        for i in range(len(claims)-1, -1, -1):
            if claims[i].tier not in (ClaimTier.primary, ClaimTier.secondary):
                cand_idx = i; break
        if cand_idx is None:
            cand_idx = len(claims) - 1
        claims[cand_idx].tier = ClaimTier.tertiary
        claims[cand_idx].priority = 2

    return claims