import sys
sys.path.insert(0, '.')
from intelligence.content.fullread import evaluate_full_evidence

print("P21 Test with stance keywords:\n")

# Test 1: Evidence with explicit support stance
claim = "Water boils at 100 degrees Celsius"
item1 = {
    'content': 'Studies confirm that water boils at 100 degrees Celsius at standard pressure. Research shows this is a well-established fact.',
    'url': 'https://example.gov'
}

evaluate_full_evidence(claim, item1)
print("Test 1 (with 'confirm' and 'shows'):")
print(f"  grade_full: {item1.get('grade_full')}")
print(f"  stance_full: {item1.get('stance_full')}")
print(f"  credibility: {item1.get('credibility')}")

# Test 2: Original evidence without stance keywords
claim2 = "Water boils at 100 degrees Celsius"
item2 = {
    'content': 'Water has a boiling point of 100 degrees Celsius at standard atmospheric pressure.',
    'url': 'https://example.com'
}

evaluate_full_evidence(claim2, item2)
print("\nTest 2 (no stance keywords):")
print(f"  grade_full: {item2.get('grade_full')}")
print(f"  stance_full: {item2.get('stance_full')}")
print(f"  credibility: {item2.get('credibility')}")

# Test 3: More direct paraphrase
claim3 = "Climate change is causing sea levels to rise"
item3 = {
    'content': 'Climate change is causing sea levels to rise rapidly. Studies confirm climate change causes sea level rise.',
    'url': 'https://example.edu'
}

evaluate_full_evidence(claim3, item3)
print("\nTest 3 (exact paraphrase + stance):")
print(f"  grade_full: {item3.get('grade_full')}")
print(f"  stance_full: {item3.get('stance_full')}")
print(f"  credibility: {item3.get('credibility')}")
print(f"  signals: {item3.get('signals_full')}")
