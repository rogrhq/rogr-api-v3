from typing import Dict, Tuple
from infrastructure.heuristics.text import token_set

def quality_for(source: Dict) -> Tuple[str, Dict]:
    """
    Letter: A (highest) .. F (lowest)
    Based on general, bias-neutral signals (no brand lists):
      - snippet richness (unique tokens)
      - title presence and length
      - url path depth
      - presence of year/numbers
    """
    title = source.get("title","").strip()
    snip = source.get("snippet","").strip()
    url = source.get("url","")
    # signals
    tlen = len(title)
    slen = len(snip)
    uniq = len(token_set(snip))
    depth = url.count("/") - 2 if "://" in url else url.count("/")
    has_year = any(y in snip for y in ["2020","2021","2022","2023","2024","2025"])
    has_num = any(ch.isdigit() for ch in snip)

    score = 0
    if tlen >= 8: score += 1
    if slen >= 80: score += 2
    elif slen >= 40: score += 1
    if uniq >= 12: score += 2
    elif uniq >= 6: score += 1
    if depth >= 2: score += 1
    if has_year: score += 1
    if has_num: score += 1

    letter = "F"
    if score >= 7: letter = "A"
    elif score >= 5: letter = "B"
    elif score >= 3: letter = "C"
    elif score >= 2: letter = "D"
    elif score >= 1: letter = "E"

    features = {
        "title_len": tlen, "snippet_len": slen, "unique_tokens": uniq,
        "url_depth": depth, "has_year": has_year, "has_number": has_num,
        "raw_score": score
    }
    return letter, features