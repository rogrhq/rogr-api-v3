"""
Unit tests for fetch_missing_urls() function with Selenium fallback.

Tests the fallback chain: httpx -> Selenium -> empty
"""
import pytest
import asyncio
from intelligence.content.fetch_enrichment import fetch_missing_urls


@pytest.mark.asyncio
async def test_fetch_missing_urls_with_cache():
    """Test that cached URLs are not re-fetched."""
    urls = ["https://www.example.com", "https://www.github.com"]
    cache = {"https://www.example.com": "cached content"}

    result_cache = await fetch_missing_urls(urls, cache, timeout=8.0)

    # Should have both URLs now
    assert "https://www.example.com" in result_cache
    assert "https://www.github.com" in result_cache
    # Cached content should remain unchanged
    assert result_cache["https://www.example.com"] == "cached content"
    print(f"✓ Cached URL not re-fetched")
    print(f"✓ New URL fetched: {len(result_cache['https://www.github.com'])} chars")


@pytest.mark.asyncio
async def test_fetch_missing_urls_good_content():
    """Test httpx success with good content (>100 chars)."""
    urls = ["https://www.example.com"]
    cache = {}

    result_cache = await fetch_missing_urls(urls, cache, timeout=8.0)

    # Should have fetched content
    assert "https://www.example.com" in result_cache
    content = result_cache["https://www.example.com"]
    assert len(content) > 100  # example.com should have good content
    print(f"✓ httpx fetched {len(content)} chars (>100, good content)")


@pytest.mark.asyncio
async def test_fetch_missing_urls_empty_list():
    """Test with empty URL list."""
    urls = []
    cache = {}

    result_cache = await fetch_missing_urls(urls, cache, timeout=8.0)

    # Should return empty cache
    assert result_cache == {}
    print(f"✓ Empty URL list handled correctly")


@pytest.mark.asyncio
async def test_fetch_missing_urls_invalid_url():
    """Test with invalid URL that should fail."""
    urls = ["https://this-domain-definitely-does-not-exist-12345678.com"]
    cache = {}

    result_cache = await fetch_missing_urls(urls, cache, timeout=5.0)

    # Should have attempted but may have empty content
    assert urls[0] in result_cache
    content = result_cache[urls[0]]
    # Invalid domains typically return empty
    assert isinstance(content, str)
    print(f"✓ Invalid URL handled: {len(content)} chars")


if __name__ == "__main__":
    print("Running fetch_missing_urls() unit tests...")
    asyncio.run(test_fetch_missing_urls_with_cache())
    asyncio.run(test_fetch_missing_urls_good_content())
    asyncio.run(test_fetch_missing_urls_empty_list())
    asyncio.run(test_fetch_missing_urls_invalid_url())
    print("✓ All tests passed!")
