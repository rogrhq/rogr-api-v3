# FILE: tests/integration/test_authority_with_subdomains.py

def test_authority_with_subdomains():
    """Test authority calculation with subdomain variants."""
    from intelligence.content.grade import calculate_authority_score
    from intelligence.content.fullread import _credibility_from

    # Wikipedia variants should get same authority
    urls = [
        "https://en.wikipedia.org/wiki/Test",
        "https://www.wikipedia.org/",
        "https://m.wikipedia.org/",
        "https://wikipedia.org/"
    ]

    authorities = []
    for url in urls:
        tier, cred, _ = _credibility_from(url, "")
        auth = calculate_authority_score(url, credibility=cred)
        authorities.append(auth)

    # All should be same
    assert len(set(authorities)) == 1, f"Different authorities for same base domain: {authorities}"
    assert authorities[0] > 0.58, f"Authority too low: {authorities[0]}"
