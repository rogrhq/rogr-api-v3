"""
Integration tests for full content enrichment pipeline with fetch metadata.

Tests the complete flow: fetch -> metadata -> enrichment.
"""
import pytest
import asyncio
from intelligence.content.fetch_enrichment import enrich_items_with_content


@pytest.mark.asyncio
async def test_enrichment_with_good_content():
    """Test full enrichment pipeline with content that fetches successfully."""
    items = [{
        "url": "https://www.example.com",
        "snippet": "Example domain snippet",
        "title": "Example Domain"
    }]

    fetch_cache = {}

    enriched_items, updated_cache = await enrich_items_with_content(items, fetch_cache)

    item = enriched_items[0]

    # Check content was fetched
    assert len(item["content"]) > 0, "Content should not be empty"
    print(f"✓ Content fetched: {len(item['content'])} chars")

    # Check metadata fields exist
    assert "fetch_status" in item, "Missing fetch_status"
    assert "fetch_method" in item, "Missing fetch_method"
    assert "fetch_error" in item, "Missing fetch_error"
    print(f"✓ Metadata: status={item['fetch_status']}, method={item['fetch_method']}")

    # Check content fields exist
    assert "content_chars" in item, "Missing content_chars"
    assert "content_hash" in item, "Missing content_hash"
    assert "coverage" in item, "Missing coverage"
    print(f"✓ Content fields: chars={item['content_chars']}, coverage={item['coverage']}")

    # Check cache was updated
    assert item["url"] in updated_cache, "URL not in cache"
    print(f"✓ Cache updated")


@pytest.mark.asyncio
async def test_enrichment_with_failed_url():
    """Test enrichment pipeline with URL that fails to fetch."""
    items = [{
        "url": "https://this-domain-will-never-exist-999999.com",
        "snippet": "Test snippet",
        "title": "Test"
    }]

    fetch_cache = {}

    enriched_items, updated_cache = await enrich_items_with_content(items, fetch_cache)

    item = enriched_items[0]

    # Should have empty content
    assert len(item["content"]) == 0, "Failed fetch should have empty content"
    print(f"✓ Failed URL has empty content")

    # Should have failed status
    assert item["fetch_status"] == "failed", \
        f"Expected failed status, got: {item['fetch_status']}"
    assert item["fetch_error"] is not None, "Failed status should have error message"
    print(f"✓ Failed status correctly set")
    print(f"✓ Error message: {item['fetch_error']}")


@pytest.mark.asyncio
async def test_enrichment_with_cached_content():
    """Test enrichment pipeline with pre-cached content."""
    items = [{
        "url": "https://cached.example.com",
        "snippet": "Test snippet",
        "title": "Cached Test"
    }]

    # Pre-populate cache
    fetch_cache = {"https://cached.example.com": "x" * 200}

    enriched_items, updated_cache = await enrich_items_with_content(items, fetch_cache)

    item = enriched_items[0]

    # Should use cached content
    assert len(item["content"]) == 200, "Should use cached content"
    assert item["fetch_status"] == "success", \
        f"Cached good content should be success, got: {item['fetch_status']}"
    print(f"✓ Cached content used successfully")


@pytest.mark.asyncio
async def test_enrichment_with_multiple_items():
    """Test enrichment pipeline with multiple items."""
    items = [
        {"url": "https://www.example.com", "snippet": "s1", "title": "t1"},
        {"url": "https://www.github.com", "snippet": "s2", "title": "t2"},
        {"url": "https://invalid-domain-12345.com", "snippet": "s3", "title": "t3"},
    ]

    fetch_cache = {}

    enriched_items, updated_cache = await enrich_items_with_content(items, fetch_cache)

    # Should enrich all items
    assert len(enriched_items) == 3, f"Expected 3 items, got {len(enriched_items)}"

    # All should have metadata
    for i, item in enumerate(enriched_items):
        assert "fetch_status" in item, f"Item {i} missing fetch_status"
        assert "fetch_method" in item, f"Item {i} missing fetch_method"
        assert "fetch_error" in item, f"Item {i} missing fetch_error"

    print(f"✓ All {len(enriched_items)} items enriched with metadata")

    # Check status distribution
    statuses = [item["fetch_status"] for item in enriched_items]
    print(f"✓ Statuses: {statuses}")


if __name__ == "__main__":
    print("Running enrichment integration tests...")
    asyncio.run(test_enrichment_with_good_content())
    asyncio.run(test_enrichment_with_failed_url())
    asyncio.run(test_enrichment_with_cached_content())
    asyncio.run(test_enrichment_with_multiple_items())
    print("✓ All enrichment integration tests passed!")
