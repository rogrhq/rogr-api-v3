import sys, re
sys.path.insert(0, '.')

# Copy the split logic from semantic_read.py
_SENT_SPLIT = re.compile(r"(?<=[\.\!\?])\s+")

def _split_sentences(text: str):
    text = text or ""
    parts = _SENT_SPLIT.split(text)
    # Collapse overly short fragments with neighbors
    sents = []
    buf = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) < 40 and buf:
            buf = (buf + " " + p).strip()
        else:
            if buf:
                sents.append(buf)
            buf = p
    if buf:
        sents.append(buf)
    return sents[:500]

# Test with our evidence
evidence1 = 'Water has a boiling point of 100 degrees Celsius at standard atmospheric pressure. This is a well-established scientific fact that has been verified through countless experiments. The boiling point can vary with altitude and pressure conditions.'

evidence2 = 'Research confirms that water boils at 100 degrees Celsius at sea level. Studies show this is a fundamental property of water.'

print("P23 Window Debug:\n")
print("Evidence 1 (longer):")
sents1 = _split_sentences(evidence1)
print(f"  Sentences: {len(sents1)}")
for i, s in enumerate(sents1, 1):
    print(f"    {i}. {s[:60]}...")
window = 3
windows1 = range(0, max(0, len(sents1) - window + 1))
print(f"  Window range (size={window}): {list(windows1)}")
print(f"  Number of windows: {len(list(windows1))}")

print("\nEvidence 2 (shorter):")
sents2 = _split_sentences(evidence2)
print(f"  Sentences: {len(sents2)}")
for i, s in enumerate(sents2, 1):
    print(f"    {i}. {s[:60]}...")
windows2 = range(0, max(0, len(sents2) - window + 1))
print(f"  Window range (size={window}): {list(windows2)}")
print(f"  Number of windows: {len(list(windows2))}")

if len(list(windows2)) == 0:
    print("\n⚠️ BUG FOUND: Same window sliding bug as P21!")
    print("   Short evidence creates 0 windows → 0 findings")
