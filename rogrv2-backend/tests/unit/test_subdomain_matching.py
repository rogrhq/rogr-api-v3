# FILE: tests/unit/test_subdomain_matching.py

def test_base_domain_extraction():
    """Test base domain extraction handles subdomains correctly."""
    from intelligence.content.fullread import _extract_base_domain

    # Standard subdomains
    assert _extract_base_domain("https://en.wikipedia.org/wiki/Test") == "wikipedia.org"
    assert _extract_base_domain("https://www.wikipedia.org/") == "wikipedia.org"
    assert _extract_base_domain("https://m.wikipedia.org/") == "wikipedia.org"
    assert _extract_base_domain("https://mobile.wikipedia.org/") == "wikipedia.org"

    # Compound TLDs
    assert _extract_base_domain("https://www.bbc.co.uk/news") == "bbc.co.uk"
    assert _extract_base_domain("https://news.bbc.co.uk/") == "bbc.co.uk"
    assert _extract_base_domain("https://www.abc.net.au/news") == "abc.net.au"

    # No subdomain
    assert _extract_base_domain("https://wikipedia.org/") == "wikipedia.org"
    assert _extract_base_domain("https://example.com/page") == "example.com"

    # Edge cases
    assert _extract_base_domain("https://deep.nested.subdomain.example.com/") == "example.com"

def test_credibility_subdomain_matching():
    """Test credibility scoring recognizes subdomains."""
    from intelligence.content.fullread import _credibility_from

    # Wikipedia (Tier 3, 0.55 credibility) should match regardless of subdomain
    tier, score, category = _credibility_from("https://en.wikipedia.org/wiki/Test", "")
    assert tier == 3, f"Expected tier 3 for en.wikipedia.org, got {tier}"
    assert score == 0.55, f"Expected score 0.55, got {score}"

    tier, score, category = _credibility_from("https://www.wikipedia.org/", "")
    assert tier == 3, f"Expected tier 3 for www.wikipedia.org, got {tier}"

    tier, score, category = _credibility_from("https://m.wikipedia.org/", "")
    assert tier == 3, f"Expected tier 3 for m.wikipedia.org, got {tier}"

    # Engineering Toolbox (Tier 2, 0.65)
    tier, score, category = _credibility_from("https://www.engineeringtoolbox.com/", "")
    assert tier == 2, f"Expected tier 2, got {tier}"
    assert score == 0.65, f"Expected score 0.65, got {score}"

    # .gov domain should be Tier 1 regardless of subdomain
    tier, score, category = _credibility_from("https://www.usda.gov/", "")
    assert tier == 1, f"Expected tier 1 for www.usda.gov, got {tier}"

    tier, score, category = _credibility_from("https://ask.usda.gov/", "")
    assert tier == 1, f"Expected tier 1 for ask.usda.gov, got {tier}"
