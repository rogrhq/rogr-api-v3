import sys
sys.path.insert(0, '.')
from intelligence.content.fullread import evaluate_full_evidence

# Test with clear support evidence
claim = "Water boils at 100 degrees Celsius"
item = {
    'content': 'Water has a boiling point of 100 degrees Celsius at standard atmospheric pressure. This is a well-established scientific fact.',
    'url': 'https://example.com'
}

evaluate_full_evidence(claim, item)

print("P21 Full-Read Test:")
print(f"  grade_full: {item.get('grade_full')}")
print(f"  stance_full: {item.get('stance_full')}")
print(f"  credibility: {item.get('credibility')}")
print(f"  reasoning: {item.get('full_read_reasoning', 'none')}")

# Check if P21 adds expected fields
assert 'grade_full' in item, "P21 should add grade_full"
assert 'stance_full' in item, "P21 should add stance_full"

print("\n✓ P21 fields present")
