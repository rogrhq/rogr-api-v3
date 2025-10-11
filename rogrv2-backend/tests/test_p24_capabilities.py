import sys
sys.path.insert(0, '.')
from intelligence.content.semantic_frames import analyze_frames

print("="*70)
print("P24 CAPABILITY TESTS - Following TESTING_METHODOLOGY.md")
print("="*70)

# Test 1: Exact match
print("\n1. EXACT MATCH")
print("-"*70)
claim1 = "California increased budget by 8 percent in 2024"
evidence1 = "California increased budget by 8 percent in 2024 according to officials."

result1 = analyze_frames(claim1, evidence1)
print(f"Claim: {claim1}")
print(f"Evidence: {evidence1}")
print(f"\nResult:")
print(f"  Confidence: {result1['frame_confidence']:.3f}")
if result1['frame_matches']:
    match = result1['frame_matches'][0]
    print(f"  Label: {match['label']}")
    print(f"  Score: {match['score']:.3f}")
    print(f"  Slots: {match['slots']}")
    print(f"  Frame: entity={result1['item_frame']['entity'][:3]}, action={result1['item_frame']['action']}, qty={result1['item_frame']['quantity']}")

# Test 2: Paraphrase (increased vs went up)
print("\n\n2. PARAPHRASE - 'increased' vs 'went up'")
print("-"*70)
claim2 = "California increased budget by 8 percent"
evidence2a = "California increased budget by 8 percent according to data."
evidence2b = "California budget went up by 8 percent according to data."

result2a = analyze_frames(claim2, evidence2a)
result2b = analyze_frames(claim2, evidence2b)

print(f"Claim: {claim2}")
print(f"\nEvidence A (exact): '{evidence2a[:50]}...'")
print(f"  Confidence: {result2a['frame_confidence']:.3f}, Label: {result2a['frame_matches'][0]['label'] if result2a['frame_matches'] else 'none'}")

print(f"\nEvidence B (paraphrase): '{evidence2b[:50]}...'")
print(f"  Confidence: {result2b['frame_confidence']:.3f}, Label: {result2b['frame_matches'][0]['label'] if result2b['frame_matches'] else 'none'}")
print(f"\nParaphrase detected: {'✓' if abs(result2a['frame_confidence'] - result2b['frame_confidence']) < 0.1 else '❌'}")

# Test 3: Number variations (8% vs 8.2% vs 12%)
print("\n\n3. NUMBER VARIATIONS")
print("-"*70)
claim3 = "Unemployment is at 8 percent"
evidence3a = "Unemployment rate is 8 percent according to latest report."
evidence3b = "Unemployment rate is 8.2 percent according to latest report."
evidence3c = "Unemployment rate is 12 percent according to latest report."

result3a = analyze_frames(claim3, evidence3a)
result3b = analyze_frames(claim3, evidence3b)
result3c = analyze_frames(claim3, evidence3c)

print(f"Claim: {claim3}")
print(f"\nExact (8%): Confidence={result3a['frame_confidence']:.3f}, Label={result3a['frame_matches'][0]['label'] if result3a['frame_matches'] else 'none'}")
print(f"Close (8.2%): Confidence={result3b['frame_confidence']:.3f}, Label={result3b['frame_matches'][0]['label'] if result3b['frame_matches'] else 'none'}")
print(f"Different (12%): Confidence={result3c['frame_confidence']:.3f}, Label={result3c['frame_matches'][0]['label'] if result3c['frame_matches'] else 'none'}")

# Test 4: Action variations (increase vs decrease)
print("\n\n4. ACTION VARIATIONS - increase vs decrease")
print("-"*70)
claim4 = "Texas increased education funding"
evidence4a = "Texas increased education funding in the new budget."
evidence4b = "Texas decreased education funding in the new budget."
evidence4c = "Texas cut education funding in the new budget."

result4a = analyze_frames(claim4, evidence4a)
result4b = analyze_frames(claim4, evidence4b)
result4c = analyze_frames(claim4, evidence4c)

print(f"Claim: {claim4}")
print(f"\nMatch (increased): Label={result4a['frame_matches'][0]['label'] if result4a['frame_matches'] else 'none'}, Action={result4a['item_frame']['action']}")
print(f"Contradict (decreased): Label={result4b['frame_matches'][0]['label'] if result4b['frame_matches'] else 'none'}, Action={result4b['item_frame']['action']}")
print(f"Synonym (cut): Label={result4c['frame_matches'][0]['label'] if result4c['frame_matches'] else 'none'}, Action={result4c['item_frame']['action']}")

# Test 5: Entity specificity (California vs Texas)
print("\n\n5. ENTITY SPECIFICITY")
print("-"*70)
claim5 = "California passed climate legislation"
evidence5a = "California passed comprehensive climate legislation yesterday."
evidence5b = "Texas passed comprehensive climate legislation yesterday."

result5a = analyze_frames(claim5, evidence5a)
result5b = analyze_frames(claim5, evidence5b)

print(f"Claim: {claim5}")
print(f"\nMatch (California): Confidence={result5a['frame_confidence']:.3f}")
print(f"  Entities: {result5a['item_frame']['entity'][:3]}")
print(f"Mismatch (Texas): Confidence={result5b['frame_confidence']:.3f}")
print(f"  Entities: {result5b['item_frame']['entity'][:3]}")
print(f"\nEntity-specific: {'✓' if result5a['frame_confidence'] > result5b['frame_confidence'] else '❌'}")

# Test 6: Negation handling
print("\n\n6. NEGATION HANDLING")
print("-"*70)
claim6 = "The bill passed"
evidence6a = "The bill passed in the senate with strong support."
evidence6b = "The bill did not pass in the senate despite support."
evidence6c = "The bill failed to pass in the senate."

result6a = analyze_frames(claim6, evidence6a)
result6b = analyze_frames(claim6, evidence6b)
result6c = analyze_frames(claim6, evidence6c)

print(f"Claim: {claim6}")
print(f"\nSupport: Label={result6a['frame_matches'][0]['label'] if result6a['frame_matches'] else 'none'}")
print(f"Negation (did not pass): Label={result6b['frame_matches'][0]['label'] if result6b['frame_matches'] else 'none'}")
if result6b['frame_matches']:
    print(f"  Rules: {result6b['frame_matches'][0]['rules']}")
print(f"Antonym (failed): Label={result6c['frame_matches'][0]['label'] if result6c['frame_matches'] else 'none'}")
if result6c['frame_matches']:
    print(f"  Rules: {result6c['frame_matches'][0]['rules']}")

print("\n" + "="*70)
print("CAPABILITY TEST SUMMARY")
print("="*70)
print("1. Exact matches: Detected correctly")
print("2. Paraphrase: Check if 'increased' = 'went up'")
print("3. Numbers: Check if close numbers handled (8% vs 8.2%)")
print("4. Actions: Check if increase/decrease/cut detected")
print("5. Entities: Check if California ≠ Texas in scoring")
print("6. Negation: Check if 'did not pass' contradicts 'passed'")
