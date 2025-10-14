import sys, re
sys.path.insert(0, '.')
from intelligence.content.fullread import evaluate_full_evidence, _window_sentences, _tokens, _ngrams, _jaccard, _stance_for_chunk, _entity_overlap, _percent_hits, _year_hit

# Test with clear support evidence
claim = "Water boils at 100 degrees Celsius"
item = {
    'content': 'Water has a boiling point of 100 degrees Celsius at standard atmospheric pressure. This is a well-established scientific fact.',
    'url': 'https://example.com'
}

# Debug window creation
windows = _window_sentences(item['content'], win=4)
print(f"Windows created: {len(windows)}")
for i, w in enumerate(windows):
    print(f"  Window {i}: {len(w)} sentences")

# Debug best window analysis
claim_tri = _ngrams(_tokens(claim), 3)
print(f"\nClaim trigrams: {len(claim_tri)}")

for chunk in windows:
    txt = " ".join(chunk)
    tri = _ngrams(_tokens(txt), 3)
    j = _jaccard(claim_tri, tri)
    stance = _stance_for_chunk(txt)
    ent = _entity_overlap(claim, txt)
    pct_any, pct_close = _percent_hits(claim, txt)
    yh = _year_hit(claim, txt)

    score = 0.0
    score += 2.0 * (1.0 if pct_close else 0.0) + 0.8 * (1.0 if pct_any else 0.0)
    score += 1.2 * (1.0 if yh else 0.0)
    score += 2.0 * min(ent, 1.0)
    score += 3.0 * j
    if stance in ("support", "challenge"):
        score += 0.8

    print(f"\nWindow analysis:")
    print(f"  Jaccard: {j:.3f}")
    print(f"  Stance: {stance}")
    print(f"  Entity overlap: {ent:.3f}")
    print(f"  Percent any/close: {pct_any}/{pct_close}")
    print(f"  Year hit: {yh}")
    print(f"  TOTAL SCORE: {score:.2f}")

# Now run full evaluation
evaluate_full_evidence(claim, item)

print("\n\nFinal P21 Output:")
print(f"  grade_full: {item.get('grade_full')}")
print(f"  stance_full: {item.get('stance_full')}")
print(f"  signals_full: {item.get('signals_full')}")
