import sys, re
sys.path.insert(0, '.')

# Copy helper functions from semantic_read
_APOS = re.compile(r"['׳`´]")
_PUNCT = re.compile(r"[^a-z0-9\s]")
_WS = re.compile(r"\s+")
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

def _tokens(s: str):
    return [t for t in _norm(s).split() if t and t not in _STOP]

def _trigrams(toks):
    if len(toks) < 3:
        return []
    return [(toks[i], toks[i+1], toks[i+2]) for i in range(len(toks)-2)]

print("P23 TRIGRAM ANALYSIS")
print("="*70)

# Test 1: boils vs boiling point
print("\n1. Paraphrase: 'boils' vs 'boiling point'")
claim1 = "Water boils at 100 degrees Celsius"
evidence1a = "Water has a boiling point of 100 degrees Celsius"
evidence1b = "Water boils at 100 degrees Celsius"

c1_toks = _tokens(claim1)
e1a_toks = _tokens(evidence1a)
e1b_toks = _tokens(evidence1b)

print(f"Claim tokens: {c1_toks}")
print(f"Evidence A tokens: {e1a_toks}")
print(f"Evidence B tokens: {e1b_toks}")

c1_tri = _trigrams(c1_toks)
e1a_tri = _trigrams(e1a_toks)
e1b_tri = _trigrams(e1b_toks)

print(f"\nClaim trigrams: {c1_tri}")
print(f"Evidence A trigrams: {e1a_tri}")
print(f"Evidence B trigrams: {e1b_tri}")

overlap_a = set(c1_tri) & set(e1a_tri)
overlap_b = set(c1_tri) & set(e1b_tri)

print(f"\nOverlap A: {overlap_a}")
print(f"Overlap B: {overlap_b}")

# Test 2: economy growing rapidly
print("\n\n2. Paraphrase: 'economy is growing rapidly' vs 'economic growth is rapid'")
claim2 = "The economy is growing rapidly"
evidence2a = "The economy is growing rapidly according to new data"
evidence2b = "Economic growth is rapid based on new data"

c2_toks = _tokens(claim2)
e2a_toks = _tokens(evidence2a)
e2b_toks = _tokens(evidence2b)

print(f"Claim tokens: {c2_toks}")
print(f"Evidence A tokens (exact): {e2a_toks}")
print(f"Evidence B tokens (paraphrase): {e2b_toks}")

c2_tri = _trigrams(c2_toks)
e2a_tri = _trigrams(e2a_toks)
e2b_tri = _trigrams(e2b_toks)

print(f"\nClaim trigrams: {c2_tri}")
print(f"Evidence A trigrams: {e2a_tri}")
print(f"Evidence B trigrams: {e2b_tri}")

overlap_2a = set(c2_tri) & set(e2a_tri)
overlap_2b = set(c2_tri) & set(e2b_tri)

print(f"\nOverlap A: {overlap_2a}")
print(f"Overlap B: {overlap_2b}")

print("\n" + "="*70)
print("CONCLUSION:")
print("- P23 uses stopword filtering (removes 'the', 'is', 'at', etc.)")
print("- Trigrams must match EXACTLY (no paraphrase understanding)")
print("- 'boils' != 'boiling' (no stemming)")
print("- 'economy growing rapidly' != 'economic growth rapid' (no synonym matching)")
