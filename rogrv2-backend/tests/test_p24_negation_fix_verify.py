import sys
sys.path.insert(0, '.')
from intelligence.content.semantic_frames import analyze_frames

print("="*70)
print("P24 NEGATION FIX VERIFICATION")
print("="*70)

# Test case from user requirements
claim = "California increased budget"
evidence = "California did not increase budget"

result = analyze_frames(claim, evidence)

print(f"\nClaim: {claim}")
print(f"Evidence: {evidence}")
print(f"\nResult:")
if result['frame_matches']:
    match = result['frame_matches'][0]
    print(f"  Label: {match['label']}")
    print(f"  Rules: {match['rules']}")
    print(f"  Score: {match['score']:.3f}")

    if match['label'] == "contradict":
        print(f"\n✅ FIX VERIFIED: Negation correctly triggers 'contradict'")
    else:
        print(f"\n❌ FIX FAILED: Expected 'contradict', got '{match['label']}'")
else:
    print("\n❌ No matches found")

# Additional negation tests
print("\n" + "-"*70)
print("Additional Negation Tests:")
print("-"*70)

test_cases = [
    ("Texas increased funding", "Texas did not increase funding", "contradict"),
    ("The bill passed", "The bill did not pass", "contradict"),
    ("Unemployment decreased", "Unemployment did not decrease", "contradict"),
]

passed = 0
for claim_t, evidence_t, expected in test_cases:
    result_t = analyze_frames(claim_t, evidence_t)
    label = result_t['frame_matches'][0]['label'] if result_t['frame_matches'] else 'none'
    status = "✓" if label == expected else "❌"
    if label == expected:
        passed += 1
    print(f"{status} Claim: '{claim_t[:30]}...'")
    print(f"  Evidence: '{evidence_t[:40]}...'")
    print(f"  Expected: {expected}, Got: {label}")

print(f"\n{passed}/{len(test_cases)} tests passed")
print("="*70)
