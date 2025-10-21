"""Test tier-based credibility model"""
import sys
sys.path.insert(0, '/Users/txtk/Documents/ROGR/github/rogrv2-backend')

from intelligence.content.fullread import _credibility_from

print("="*80)
print("TIER-BASED CREDIBILITY MODEL TESTS")
print("="*80)

tests = [
    # (url, text, expected_tier, expected_score_min, expected_score_max, description)
    ("https://cdc.gov/report", "", 1, 0.85, 0.95, "Government (.gov)"),
    ("https://mit.edu/research", "", 2, 0.65, 0.75, "Education (.edu)"),
    ("https://nature.com/article", "peer-reviewed study", 1, 0.80, 0.90, "Peer-reviewed journal"),
    ("https://engineeringtoolbox.com/data", "", 2, 0.60, 0.70, "Whitelisted technical"),
    ("https://wikipedia.org/wiki/topic", "", 3, 0.50, 0.60, "Wikipedia (Tier 3)"),
    ("https://example.com/article", "Dr. Smith, PhD explains", 3, 0.45, 0.55, "Credentialed author"),
    ("https://blog.com/post", "Just some content", 4, 0.20, 0.35, "No signals (Tier 4)"),
    ("https://mit.edu/~student/page", "", 3, 0.45, 0.55, "Personal page on .edu"),
]

all_pass = True

for url, text, exp_tier, min_score, max_score, desc in tests:
    tier, score, category = _credibility_from(url, text)

    tier_match = (tier == exp_tier)
    score_match = (min_score <= score <= max_score)
    status = "✓" if (tier_match and score_match) else "✗"

    if not (tier_match and score_match):
        all_pass = False

    print(f"\n{status} {desc}")
    print(f"  URL: {url}")
    print(f"  Expected: Tier {exp_tier}, score {min_score}-{max_score}")
    print(f"  Got: Tier {tier}, score {score:.2f}")
    print(f"  Category: {category}")

print("\n" + "="*80)
if all_pass:
    print("✓ ALL TESTS PASSED")
else:
    print("✗ SOME TESTS FAILED - Review implementation")
print("="*80)
