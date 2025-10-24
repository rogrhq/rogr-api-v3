"""
Integration test for USDA.gov JavaScript-rendered content fetching.

Tests the real-world scenario that motivated Selenium support.
"""
import pytest
import asyncio
from intelligence.content.fetch_enrichment import fetch_with_selenium


@pytest.mark.asyncio
async def test_selenium_usda_gov():
    """Test Selenium can fetch USDA.gov JavaScript-rendered content."""
    url = "https://ask.usda.gov/s/article/What-is-the-boiling-point-of-water"
    content = await fetch_with_selenium(url, timeout=30)

    # Should get substantial content
    assert len(content) > 100, f"Content too short: {len(content)} chars"

    # Should contain relevant content about boiling
    content_lower = content.lower()
    assert "boil" in content_lower or "100" in content, \
        f"Content doesn't mention boiling. Got: {content[:200]}"

    print(f"✓ USDA.gov fetched successfully: {len(content)} chars")
    print(f"✓ Content preview: {content[:200]}...")


@pytest.mark.asyncio
async def test_selenium_wikipedia():
    """Test Selenium works on Wikipedia (static but large page)."""
    url = "https://en.wikipedia.org/wiki/Boiling_point"
    content = await fetch_with_selenium(url, timeout=30)

    # Wikipedia pages are large
    assert len(content) > 1000, f"Content too short: {len(content)} chars"
    assert "boiling point" in content.lower(), \
        "Content doesn't mention boiling point"

    print(f"✓ Wikipedia fetched successfully: {len(content)} chars")


if __name__ == "__main__":
    print("Running USDA.gov integration tests...")
    print("NOTE: These tests require internet connection and may be slow")
    asyncio.run(test_selenium_usda_gov())
    asyncio.run(test_selenium_wikipedia())
    print("✓ All integration tests passed!")
