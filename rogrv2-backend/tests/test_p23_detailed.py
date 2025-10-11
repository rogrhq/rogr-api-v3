import sys, json
sys.path.insert(0, '.')
from intelligence.content.semantic_read import analyze_item

print("P23 DETAILED ANALYSIS\n" + "="*60)

# Test 1: Evidence with stance keywords
print("\nTest 1: Evidence with explicit stance keywords")
claim1 = "Water boils at 100 degrees Celsius"
item1 = {
    'content': 'Research confirms that water boils at 100 degrees Celsius at sea level. Studies show this is a fundamental property of water.',
    'url': 'https://example.gov'
}

analyze_item(claim1, item1, window=3)
print(f"  item_grade: {item1.get('item_grade', 0):.3f}")
print(f"  grade_label: {item1.get('grade_label')}")
print(f"  Number of findings: {len(item1.get('findings', []))}")
for i, f in enumerate(item1['findings'][:2], 1):
    print(f"  Finding {i}:")
    print(f"    stance: {f.get('stance')}")
    print(f"    signals: {f.get('signals')}")
    print(f"    score: {f.get('score', 0):.3f}")
    print(f"    quote: {f.get('quote', '')[:80]}...")

# Test 2: Evidence with numbers
print("\n\nTest 2: Evidence with matching numbers")
claim2 = "Unemployment is at 8 percent"
item2 = {
    'content': 'The latest jobs report shows unemployment at 8 percent, down from previous months. Economists report this is a positive sign.',
    'url': 'https://example.gov'
}

analyze_item(claim2, item2, window=3)
print(f"  item_grade: {item2.get('item_grade', 0):.3f}")
print(f"  grade_label: {item2.get('grade_label')}")
print(f"  Number of findings: {len(item2.get('findings', []))}")
for i, f in enumerate(item2['findings'][:2], 1):
    print(f"  Finding {i}:")
    print(f"    stance: {f.get('stance')}")
    print(f"    signals: {f.get('signals')}")
    print(f"    score: {f.get('score', 0):.3f}")

# Test 3: Evidence with negation/challenge
print("\n\nTest 3: Evidence with challenge/negation")
claim3 = "Climate change is a hoax"
item3 = {
    'content': 'Scientists refute the claim that climate change is a hoax. Research shows overwhelming evidence contradicts this false narrative.',
    'url': 'https://example.edu'
}

analyze_item(claim3, item3, window=3)
print(f"  item_grade: {item3.get('item_grade', 0):.3f}")
print(f"  grade_label: {item3.get('grade_label')}")
print(f"  Number of findings: {len(item3.get('findings', []))}")
for i, f in enumerate(item3['findings'][:2], 1):
    print(f"  Finding {i}:")
    print(f"    stance: {f.get('stance')}")
    print(f"    signals: {f.get('signals')}")
    print(f"    score: {f.get('score', 0):.3f}")

print("\n" + "="*60)
print("P23 BEHAVIOR SUMMARY:")
print("- Adds: findings[], item_grade, grade_label")
print("- Finding structure: quote, offset_start/end, stance, signals[], score")
print("- Stance detection: Based on keyword matching")
print("- Scoring: Based on entity, number, year hits + jaccard similarity")
