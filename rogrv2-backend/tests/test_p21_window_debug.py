import sys, re
sys.path.insert(0, '.')

# Copy the _window_sentences function to debug it
def _window_sentences(text: str, win: int = 4, max_sents: int = 80):
    raw = re.split(r"(?<=[\.\?\!])\s+", text or "")
    sents = [s.strip() for s in raw if s.strip()]
    sents = sents[:max_sents]
    out = []
    for i in range(0, max(0, len(sents)-win+1)):
        out.append(sents[i:i+win])
    return out

# Test with our evidence
evidence = 'Water has a boiling point of 100 degrees Celsius at standard atmospheric pressure. This is a well-established scientific fact.'

windows = _window_sentences(evidence, win=4)

sent_split = re.split(r'(?<=[\.\?\!])\s+', evidence)
num_sentences = len(sent_split)

print("P21 Window Debug:")
print(f"  Evidence sentences: {num_sentences}")
print(f"  Windows created: {len(windows)}")
print(f"  Window size requested: 4")
print()

if len(windows) == 0:
    print("BUG FOUND: No windows created!")
    print("  When text has < 4 sentences, range(0, max(0, len-4+1)) is empty")
    print("  This causes grade_full=0.0 and stance_full='unrelated'")
    print()
    print("  Fix needed: Create at least one window from ALL sentences when text is short")
else:
    print(f"Windows: {windows}")
