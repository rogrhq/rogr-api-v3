import sys
sys.path.insert(0, '.')
from intelligence.content.semantic_frames import analyze_frames

print("="*70)
print("P24 UNEXPECTED BEHAVIORS INVESTIGATION")
print("="*70)

# Unexpected 1: "decreased" claim matches "decreased" evidence = contradict?
print("\n1. INVESTIGATE: Decreased claim + decreased evidence = contradict")
print("-"*70)

claim1 = "Texas decreased spending by 5 percent"
evidence1 = "Texas decreased spending by 5 percent in new budget."

result1 = analyze_frames(claim1, evidence1)

print(f"Claim: {claim1}")
print(f"Evidence: {evidence1}")
print(f"\nResult:")
print(f"  Label: {result1['frame_matches'][0]['label']}")
print(f"  Rules: {result1['frame_matches'][0]['rules']}")
print(f"  Claim frame: {result1['frame_matches'][0]}")
print(f"  Item action: {result1['item_frame']['action']}")

# Extract claim frame to understand
from intelligence.content.semantic_frames import extract_claim_frame
claim_frame = extract_claim_frame(claim1)
print(f"\nClaim frame analysis:")
print(f"  Claim action: {claim_frame['action']}")
print(f"  Evidence action: {result1['item_frame']['action']}")

print("\nEXPLANATION:")
print("  Claim has 'decreased' → claim action = 'decrease'")
print("  Evidence has 'decreased' → evidence action = 'decrease'")
print("  Logic: decrease action + decrease action should = entail")
print("  But getting 'contradict' - checking entailment logic...")

# Let me manually check the logic
print("\n  Looking at _entail_contradict logic:")
print("  - Line 189: if action == 'decrease' → label = 'contradict'")
print("  - This triggers because evidence action is 'decrease'")
print("  - But claim ALSO has 'decrease', so this should be alignment!")
print("\n  BUG FOUND: Logic doesn't check if claim and evidence actions MATCH")
print("  It only checks evidence action, not whether it aligns with claim action")

# Unexpected 2: "did not decrease" with "increased" claim
print("\n\n2. INVESTIGATE: 'increased' claim + 'did not decrease' evidence")
print("-"*70)

claim2 = "California increased budget"
evidence2 = "California did not decrease budget"

result2 = analyze_frames(claim2, evidence2)

print(f"Claim: {claim2}")
print(f"Evidence: {evidence2}")
print(f"\nResult:")
print(f"  Label: {result2['frame_matches'][0]['label']}")
print(f"  Rules: {result2['frame_matches'][0]['rules']}")
print(f"  Negation detected: {'negation_present' in result2['frame_matches'][0]['rules']}")

print("\nEXPLANATION:")
print("  Claim: 'increased' (positive action)")
print("  Evidence: 'did not decrease' (negation + opposite action)")
print("  Current: contradict")
print("  This is complex: 'did not decrease' could mean 'stayed same' or 'increased'")
print("  Double negatives are semantically ambiguous - 'contradict' might be reasonable")

print("\n" + "="*70)
print("FINDINGS:")
print("="*70)
print("1. REAL BUG: Claim 'decrease' + Evidence 'decrease' → contradict ❌")
print("   - Logic doesn't compare claim action vs evidence action")
print("   - Only checks evidence action in isolation")
print("   - Needs action alignment check")
print()
print("2. NOT A BUG: Complex double negatives → contradict")
print("   - 'increased' vs 'did not decrease' = semantically ambiguous")
print("   - Current behavior (contradict) is defensible")
print("="*70)
