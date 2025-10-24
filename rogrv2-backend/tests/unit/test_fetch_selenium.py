"""
Unit tests for fetch_with_selenium() function.

Tests the Selenium-based content fetching functionality.
"""
import pytest
import asyncio
from intelligence.content.fetch_enrichment import fetch_with_selenium


@pytest.mark.asyncio
async def test_selenium_static_page():
    """Test Selenium fetch with a simple static page."""
    url = "https://www.example.com"
    content = await fetch_with_selenium(url, timeout=20)

    # Should get some content
    assert isinstance(content, str)
    assert len(content) > 0
    print(f"✓ Fetched {len(content)} chars from {url}")


@pytest.mark.asyncio
async def test_selenium_invalid_url():
    """Test Selenium fetch with invalid URL."""
    url = "https://this-domain-does-not-exist-12345.com"
    content = await fetch_with_selenium(url, timeout=10)

    # Should return empty string on failure
    assert isinstance(content, str)
    assert len(content) == 0
    print(f"✓ Invalid URL correctly returned empty string")


@pytest.mark.asyncio
async def test_selenium_timeout():
    """Test Selenium fetch with very short timeout."""
    url = "https://www.example.com"
    content = await fetch_with_selenium(url, timeout=1)

    # With 1 second timeout, might fail or succeed quickly
    assert isinstance(content, str)
    print(f"✓ Timeout test completed (got {len(content)} chars)")


if __name__ == "__main__":
    print("Running Selenium unit tests...")
    asyncio.run(test_selenium_static_page())
    asyncio.run(test_selenium_invalid_url())
    asyncio.run(test_selenium_timeout())
    print("✓ All tests passed!")
