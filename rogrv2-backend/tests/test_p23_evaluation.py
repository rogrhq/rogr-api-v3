import sys
sys.path.insert(0, '.')
from intelligence.content.semantic_read import analyze_item

print("="*70)
print("P23 SEMANTIC CAPABILITIES EVALUATION")
print("="*70)

# Test 1: Paraphrase detection (boils vs boiling point)
print("\n1. PARAPHRASE DETECTION")
print("-"*70)
claim1 = "Water boils at 100 degrees Celsius"
item1a = {
    'content': 'Water has a boiling point of 100 degrees Celsius at standard pressure.',
    'url': 'https://example.com'
}
item1b = {
    'content': 'Water boils at 100 degrees Celsius at sea level.',
    'url': 'https://example.com'
}

analyze_item(claim1, item1a)
analyze_item(claim1, item1b)

print(f"Claim: {claim1}")
print(f"\nEvidence A (paraphrase): 'boiling point of 100 degrees'")
print(f"  grade: {item1a['item_grade']:.3f}, stance: {item1a['findings'][0]['stance'] if item1a['findings'] else 'none'}")
print(f"  signals: {item1a['findings'][0]['signals'] if item1a['findings'] else []}")
print(f"  jaccard overlap: Check if 'boils' matches 'boiling point'")

print(f"\nEvidence B (exact): 'boils at 100 degrees'")
print(f"  grade: {item1b['item_grade']:.3f}, stance: {item1b['findings'][0]['stance'] if item1b['findings'] else 'none'}")
print(f"  signals: {item1b['findings'][0]['signals'] if item1b['findings'] else []}")

# Test 2: Number matching and tolerance
print("\n\n2. NUMBER MATCHING & TOLERANCE")
print("-"*70)
claim2 = "Unemployment is at 8 percent"
item2a = {
    'content': 'The unemployment rate is 8 percent according to latest data.',
    'url': 'https://example.gov'
}
item2b = {
    'content': 'The unemployment rate is 8.2 percent according to latest data.',
    'url': 'https://example.gov'
}
item2c = {
    'content': 'The unemployment rate is 12 percent according to latest data.',
    'url': 'https://example.gov'
}

analyze_item(claim2, item2a)
analyze_item(claim2, item2b)
analyze_item(claim2, item2c)

print(f"Claim: {claim2}")
print(f"\nExact match (8%): grade={item2a['item_grade']:.3f}, signals={item2a['findings'][0]['signals'] if item2a['findings'] else []}")
print(f"Close (8.2%): grade={item2b['item_grade']:.3f}, signals={item2b['findings'][0]['signals'] if item2b['findings'] else []}")
print(f"Different (12%): grade={item2c['item_grade']:.3f}, signals={item2c['findings'][0]['signals'] if item2c['findings'] else []}")

# Test 3: Stance keyword detection
print("\n\n3. STANCE KEYWORD DETECTION")
print("-"*70)
claim3 = "Climate change is real"
item3a = {
    'content': 'Scientists confirm that climate change is real and accelerating.',
    'url': 'https://example.edu'
}
item3b = {
    'content': 'Studies refute the claim that climate change is not real.',
    'url': 'https://example.edu'
}
item3c = {
    'content': 'Climate change is real according to data.',
    'url': 'https://example.edu'
}

analyze_item(claim3, item3a)
analyze_item(claim3, item3b)
analyze_item(claim3, item3c)

print(f"Claim: {claim3}")
print(f"\nWith 'confirm': stance={item3a['findings'][0]['stance'] if item3a['findings'] else 'none'}")
print(f"With 'refute': stance={item3b['findings'][0]['stance'] if item3b['findings'] else 'none'}")
print(f"Without keyword: stance={item3c['findings'][0]['stance'] if item3c['findings'] else 'none'}")

# Test 4: Entity matching
print("\n\n4. ENTITY MATCHING")
print("-"*70)
claim4 = "California passed new climate legislation"
item4a = {
    'content': 'California lawmakers approved sweeping climate legislation yesterday.',
    'url': 'https://example.com'
}
item4b = {
    'content': 'Texas lawmakers approved sweeping climate legislation yesterday.',
    'url': 'https://example.com'
}

analyze_item(claim4, item4a)
analyze_item(claim4, item4b)

print(f"Claim: {claim4}")
print(f"\nMatch (California): grade={item4a['item_grade']:.3f}, signals={item4a['findings'][0]['signals'] if item4a['findings'] else []}")
print(f"Mismatch (Texas): grade={item4b['item_grade']:.3f}, signals={item4b['findings'][0]['signals'] if item4b['findings'] else []}")

# Test 5: Trigram/Jaccard similarity
print("\n\n5. TRIGRAM SIMILARITY")
print("-"*70)
claim5 = "The economy is growing rapidly"
item5a = {
    'content': 'The economy is growing rapidly according to new data.',
    'url': 'https://example.com'
}
item5b = {
    'content': 'Economic growth is rapid based on new data.',
    'url': 'https://example.com'
}

analyze_item(claim5, item5a)
analyze_item(claim5, item5b)

print(f"Claim: {claim5}")
print(f"\nExact phrase: score={item5a['findings'][0]['score'] if item5a['findings'] else 0:.3f}")
print(f"Paraphrase: score={item5b['findings'][0]['score'] if item5b['findings'] else 0:.3f}")

print("\n" + "="*70)
print("SUMMARY OF P23 CAPABILITIES")
print("="*70)
print("1. Paraphrase: Does it match 'boils' with 'boiling point'?")
print("2. Numbers: Does it detect matching percentages?")
print("3. Stance: Does it recognize support/challenge keywords?")
print("4. Entities: Does it match key entities (California)?")
print("5. Similarity: How does trigram matching work?")
