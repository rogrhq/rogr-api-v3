import sys
sys.path.insert(0, '.')
from intelligence.content.p25_aggregate import aggregate_verdict

print("="*70)
print("P25 STRUCTURAL TEST - Following TESTING_METHODOLOGY.md")
print("="*70)

# Test 1: Field validation
print("\n1. FIELD VALIDATION")
print("-"*70)

claim = "California increased budget by 8 percent"
arm_a = [{"frame_matches": [{"score": 0.8}], "item_grade": 0.7, "coverage": "full"}]
arm_b = [{"frame_matches": [{"score": 0.3}], "item_grade": 0.2, "coverage": "partial"}]

result = aggregate_verdict(claim, arm_a, arm_b)

expected_fields = ["label", "confidence", "arm_strength"]
missing = [f for f in expected_fields if f not in result]

print(f"Expected fields: {expected_fields}")
print(f"Actual fields: {list(result.keys())}")

if missing:
    print(f"\n❌ Missing fields: {missing}")
else:
    print("\n✓ All expected fields present")

# Check arm_strength structure
if "arm_strength" in result:
    arm_fields = ["support", "challenge", "balance"]
    arm_missing = [f for f in arm_fields if f not in result["arm_strength"]]
    print(f"\narm_strength fields: {list(result['arm_strength'].keys())}")
    if arm_missing:
        print(f"❌ Missing arm_strength fields: {arm_missing}")
    else:
        print("✓ arm_strength structure correct")

# Test 2: Label validity
print("\n\n2. LABEL VALIDITY")
print("-"*70)

valid_labels = ["supports", "challenges", "mixed", "insufficient"]
print(f"Valid labels: {valid_labels}")
print(f"Result label: {result['label']}")

if result['label'] in valid_labels:
    print("✓ Label is valid")
else:
    print(f"❌ Invalid label: {result['label']}")

# Test 3: Value ranges
print("\n\n3. VALUE RANGES")
print("-"*70)

conf = result['confidence']
support = result['arm_strength']['support']
challenge = result['arm_strength']['challenge']
balance = result['arm_strength']['balance']

print(f"confidence: {conf:.3f} (should be 0-1)")
print(f"support: {support:.3f} (should be 0-1)")
print(f"challenge: {challenge:.3f} (should be 0-1)")
print(f"balance: {balance:.3f} (should be -1 to 1)")

ranges_ok = (
    0 <= conf <= 1 and
    0 <= support <= 1 and
    0 <= challenge <= 1 and
    -1 <= balance <= 1
)

if ranges_ok:
    print("\n✓ All values within expected ranges")
else:
    print("\n❌ Some values out of range")

# Test 4: Edge case - empty arms
print("\n\n4. EDGE CASE: Empty Arms")
print("-"*70)

result_empty = aggregate_verdict(claim, [], [])
print(f"Empty arms result:")
print(f"  Label: {result_empty['label']}")
print(f"  Confidence: {result_empty['confidence']:.3f}")

if result_empty['label'] == "insufficient":
    print("✓ Empty arms correctly labeled 'insufficient'")
else:
    print(f"❌ Expected 'insufficient', got '{result_empty['label']}'")

# Test 5: Edge case - single item
print("\n\n5. EDGE CASE: Single Item")
print("-"*70)

single_item = [{"frame_matches": [{"score": 0.9}], "item_grade": 0.8, "coverage": "full"}]
result_single = aggregate_verdict(claim, single_item, [])

print(f"Single item (arm_A only):")
print(f"  Label: {result_single['label']}")
print(f"  Confidence: {result_single['confidence']:.3f}")
print(f"  Support: {result_single['arm_strength']['support']:.3f}")
print(f"  Challenge: {result_single['arm_strength']['challenge']:.3f}")

if result_single['label'] == "supports" and result_single['arm_strength']['support'] > result_single['arm_strength']['challenge']:
    print("✓ Single strong support item correctly labeled 'supports'")
else:
    print("❌ Unexpected result for single strong item")

# Test 6: Edge case - missing fields in items
print("\n\n6. EDGE CASE: Missing Fields in Items")
print("-"*70)

incomplete_item = [{}]  # No fields
try:
    result_incomplete = aggregate_verdict(claim, incomplete_item, [])
    print(f"Incomplete item result:")
    print(f"  Label: {result_incomplete['label']}")
    print(f"  Confidence: {result_incomplete['confidence']:.3f}")
    print("✓ Handles missing fields without crashing")
except Exception as e:
    print(f"❌ Crashed on missing fields: {e}")

print("\n" + "="*70)
print("STRUCTURAL TEST COMPLETE")
print("="*70)
