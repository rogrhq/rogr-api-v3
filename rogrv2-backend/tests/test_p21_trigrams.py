import sys, re
sys.path.insert(0, '.')

# Copy helper functions
_WORD = re.compile(r"[a-z0-9]+")
_APOS = re.compile(r"['׳`´]")
_PUNCT = re.compile(r"[^a-z0-9\s]")

def _norm(s: str) -> str:
    s = (s or "").lower()
    s = _APOS.sub("'", s)
    s = s.replace("'s", " ")
    s = _PUNCT.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _tokens(s: str):
    return _WORD.findall(_norm(s))

def _ngrams(tokens, n: int):
    return [tuple(tokens[i:i+n]) for i in range(0, max(0, len(tokens)-n+1))]

# Test with our evidence
claim = "Water boils at 100 degrees Celsius"
evidence = 'Water has a boiling point of 100 degrees Celsius at standard atmospheric pressure. This is a well-established scientific fact.'

claim_tokens = _tokens(claim)
evidence_tokens = _tokens(evidence)

print("Claim tokens:", claim_tokens)
print("Evidence tokens:", evidence_tokens)
print()

claim_tri = _ngrams(claim_tokens, 3)
evidence_tri = _ngrams(evidence_tokens, 3)

print(f"Claim trigrams ({len(claim_tri)}):")
for t in claim_tri:
    print(f"  {t}")

print(f"\nEvidence trigrams ({len(evidence_tri)}):")
for t in evidence_tri:
    print(f"  {t}")

# Check overlap
claim_set = set(claim_tri)
evidence_set = set(evidence_tri)
intersection = claim_set & evidence_set

print(f"\nIntersection ({len(intersection)}):")
for t in intersection:
    print(f"  {t}")

print(f"\nJaccard: {len(intersection)} / {len(claim_set | evidence_set)} = {len(intersection) / len(claim_set | evidence_set):.3f}")
