import sys
sys.path.insert(0, '.')
from intelligence.content.semantic_frames import analyze_frames

print("="*70)
print("P24 STRUCTURAL TEST - Following TESTING_METHODOLOGY.md")
print("="*70)

# Test 1: Window bug detection (short evidence < 3 sentences)
print("\n1. WINDOW BUG DETECTION")
print("-"*70)

claim = "California increased budget by 8 percent in 2024"
short_evidence = "California increased budget by 8 percent in 2024. This is significant."

result = analyze_frames(claim, short_evidence, window=3)

print(f"Claim: {claim}")
print(f"Evidence: {short_evidence}")
print(f"Evidence sentences: 2 (< window size 3)")
print(f"\nResult fields: {list(result.keys())}")
print(f"frame_matches: {len(result.get('frame_matches', []))} matches")
print(f"frame_confidence: {result.get('frame_confidence', 0)}")

if len(result.get('frame_matches', [])) == 0:
    print("\n⚠️  WINDOW BUG FOUND: 0 matches for 2-sentence evidence")
    print("   Expected: At least 1 match analyzing both sentences as one window")
else:
    print("\n✓ Short evidence handled correctly")

# Test 2: Field validation
print("\n\n2. FIELD VALIDATION")
print("-"*70)

claim2 = "Texas cut education funding by 5 percent"
evidence2 = "Texas reduced education funding by approximately 5 percent. The governor said this was necessary. Budget experts disagreed with the decision."

result2 = analyze_frames(claim2, evidence2, window=3)

expected_fields = ["item_frame", "frame_matches", "frame_confidence"]
missing = [f for f in expected_fields if f not in result2]

print(f"Expected fields: {expected_fields}")
print(f"Actual fields: {list(result2.keys())}")

if missing:
    print(f"\n❌ Missing fields: {missing}")
else:
    print("\n✓ All expected fields present")

# Test 3: frame_matches structure validation
print("\n\n3. FRAME_MATCHES STRUCTURE")
print("-"*70)

if result2.get('frame_matches'):
    match = result2['frame_matches'][0]
    expected_match_fields = ["label", "score", "slots", "rules", "quote", "offset_start", "offset_end"]
    match_missing = [f for f in expected_match_fields if f not in match]

    print(f"Expected match fields: {expected_match_fields}")
    print(f"Actual match fields: {list(match.keys())}")

    if match_missing:
        print(f"\n❌ Missing match fields: {match_missing}")
    else:
        print("\n✓ Match structure correct")
        print(f"\nSample match:")
        print(f"  label: {match['label']}")
        print(f"  score: {match['score']:.3f}")
        print(f"  slots: {match['slots']}")
        print(f"  rules: {match['rules']}")
else:
    print("❌ No frame_matches to validate structure")

# Test 4: item_frame structure validation
print("\n\n4. ITEM_FRAME STRUCTURE")
print("-"*70)

item_frame = result2.get('item_frame', {})
expected_frame_fields = ["entity", "action", "quantity", "year", "scope"]
frame_missing = [f for f in expected_frame_fields if f not in item_frame]

print(f"Expected frame fields: {expected_frame_fields}")
print(f"Actual frame fields: {list(item_frame.keys())}")

if frame_missing:
    print(f"\n❌ Missing frame fields: {frame_missing}")
else:
    print("\n✓ Frame structure correct")
    print(f"\nSample item_frame:")
    print(f"  entity: {item_frame['entity']}")
    print(f"  action: {item_frame['action']}")
    print(f"  quantity: {item_frame['quantity']}")
    print(f"  year: {item_frame['year']}")
    print(f"  scope: {item_frame['scope']}")

print("\n" + "="*70)
print("STRUCTURAL TEST COMPLETE")
print("="*70)
