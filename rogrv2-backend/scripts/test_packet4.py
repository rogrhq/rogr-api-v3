import os
from intelligence.gather.discovery import interleaved_candidates

print("Running provider test ...")
res = interleaved_candidates("site:example.com test", None)
assert isinstance(res, list), "interleaved_candidates must return a list"

have_google = bool(os.environ.get("GOOGLE_CSE_API_KEY") and os.environ.get("GOOGLE_CSE_ENGINE_ID"))
have_bing = bool(os.environ.get("BING_API_KEY"))
if not (have_google or have_bing):
    print(f"PASS (providers unconfigured): got {len(res)} candidates")
else:
    # With one provider, expect up to 10. With both, up to 20. Zero is still okay if queries return nothing.
    assert all(isinstance(x, dict) for x in res), "items must be dicts"
    print(f"PASS: got {len(res)} candidates")