import sys
sys.path.insert(0, '.')
from intelligence.content.semantic_read import analyze_item

# Test with clear, relevant evidence
claim = "Water boils at 100 degrees Celsius"
item = {
    'content': 'Water has a boiling point of 100 degrees Celsius at standard atmospheric pressure. This is a well-established scientific fact that has been verified through countless experiments. The boiling point can vary with altitude and pressure conditions.',
    'url': 'https://example.com'
}

print("BEFORE P23:")
print(f"  Item keys: {list(item.keys())}")

analyze_item(claim, item, window=3)

print("\nAFTER P23:")
print(f"  Item keys: {list(item.keys())}")
print(f"  findings: {item.get('findings', 'MISSING')}")
print(f"  item_grade: {item.get('item_grade', 'MISSING')}")

if isinstance(item.get('findings'), list):
    print(f"\n  Number of findings: {len(item['findings'])}")
    for i, finding in enumerate(item['findings'][:3], 1):
        print(f"\n  Finding {i}:")
        print(f"    summary: {finding.get('summary', 'no summary')[:80]}")
        print(f"    quote: {finding.get('quote', 'no quote')[:80]}")
        print(f"    stance: {finding.get('stance', 'no stance')}")
        print(f"    grade: {finding.get('grade', 'no grade')}")
else:
    print(f"  findings is not a list: {type(item.get('findings'))}")

# Test assertions
if 'findings' in item:
    print("\n✓ P23 added 'findings' field")
else:
    print("\n✗ P23 did NOT add 'findings' field")

if 'item_grade' in item:
    print("✓ P23 added 'item_grade' field")
else:
    print("✗ P23 did NOT add 'item_grade' field")

print("\n--- ANALYSIS ---")
print("Does P23 detect the clear support for boiling point claim?")
print("Are findings relevant and anchored to actual quotes?")
print("Does item_grade reflect the quality of evidence?")
