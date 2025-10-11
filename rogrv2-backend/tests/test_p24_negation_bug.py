import sys
sys.path.insert(0, '.')
from intelligence.content.semantic_frames import analyze_frames

print("="*70)
print("P24 NEGATION BUG ANALYSIS")
print("="*70)

claim = "The bill passed"
evidence_positive = "The bill passed in the senate with strong support."
evidence_negative = "The bill did not pass in the senate despite support."

result_pos = analyze_frames(claim, evidence_positive)
result_neg = analyze_frames(claim, evidence_negative)

print(f"\nClaim: {claim}")
print(f"\nPOSITIVE Evidence: {evidence_positive}")
print(f"  Label: {result_pos['frame_matches'][0]['label']}")
print(f"  Rules: {result_pos['frame_matches'][0]['rules']}")
print(f"  Action: {result_pos['item_frame']['action']}")

print(f"\nNEGATIVE Evidence: {evidence_negative}")
print(f"  Label: {result_neg['frame_matches'][0]['label']}")
print(f"  Rules: {result_neg['frame_matches'][0]['rules']}")
print(f"  Action: {result_neg['item_frame']['action']}")

print("\n" + "="*70)
print("BUG FOUND:")
print("  Claim: 'The bill passed'")
print("  Evidence: 'The bill did not pass'")
print(f"  Current label: {result_neg['frame_matches'][0]['label']} ❌")
print("  Expected label: contradict ✓")
print("\nROOT CAUSE:")
print("  Rules show 'negation_present' was detected")
print("  But logic still produced 'entail' or 'mixed'")
print("  Negation detection exists but doesn't properly trigger contradiction")
print("="*70)

# Test with more negation examples
print("\n\nMORE NEGATION TESTS:")
print("-"*70)

test_cases = [
    ("California increased funding", "California did not increase funding"),
    ("Unemployment decreased", "Unemployment did not decrease"),
    ("The budget grew", "The budget did not grow"),
]

for claim, evidence in test_cases:
    result = analyze_frames(claim, evidence)
    label = result['frame_matches'][0]['label'] if result['frame_matches'] else 'none'
    rules = result['frame_matches'][0]['rules'] if result['frame_matches'] else []
    has_neg = 'negation_present' in rules
    print(f"\nClaim: {claim}")
    print(f"Evidence: {evidence}")
    print(f"  Label: {label} {'❌' if label != 'contradict' else '✓'}")
    print(f"  Negation detected: {has_neg}")
