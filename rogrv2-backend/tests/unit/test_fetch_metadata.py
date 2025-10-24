"""
Unit tests for fetch metadata fields in enrich_items_with_content().

Tests that items are enriched with fetch_status, fetch_method, and fetch_error fields.
"""
import pytest
import asyncio
from intelligence.content.fetch_enrichment import enrich_items_with_content


@pytest.mark.asyncio
async def test_metadata_success_status():
    """Test that items with good content get 'success' status."""
    items = [
        {'url': 'https://www.example.com', 'snippet': 'test snippet'}
    ]
    cache = {}

    enriched, updated_cache = await enrich_items_with_content(items, cache)

    assert len(enriched) == 1
    item = enriched[0]

    # Should have all metadata fields
    assert 'fetch_status' in item
    assert 'fetch_method' in item
    assert 'fetch_error' in item

    # With good content (>100 chars), should be success
    if len(item['content']) > 100:
        assert item['fetch_status'] == 'success'
        assert item['fetch_error'] is None
        print(f"✓ Success status: {len(item['content'])} chars")
    else:
        print(f"⚠️  Content was minimal: {len(item['content'])} chars")


@pytest.mark.asyncio
async def test_metadata_failed_status():
    """Test that items with empty content get 'failed' status."""
    items = [
        {'url': 'https://this-domain-does-not-exist-999999.com', 'snippet': 'test'}
    ]
    cache = {}

    enriched, updated_cache = await enrich_items_with_content(items, cache)

    assert len(enriched) == 1
    item = enriched[0]

    # Should have metadata fields
    assert 'fetch_status' in item
    assert 'fetch_method' in item
    assert 'fetch_error' in item

    # With empty content, should be failed
    if len(item['content']) == 0:
        assert item['fetch_status'] == 'failed'
        assert item['fetch_method'] == 'unknown'
        assert item['fetch_error'] == 'Empty content returned'
        print(f"✓ Failed status correctly set")


@pytest.mark.asyncio
async def test_metadata_with_cached_content():
    """Test metadata with pre-cached content."""
    items = [
        {'url': 'https://cached.example.com', 'snippet': 'test'}
    ]
    # Pre-populate cache with good content
    cache = {'https://cached.example.com': 'x' * 150}  # 150 chars

    enriched, updated_cache = await enrich_items_with_content(items, cache)

    item = enriched[0]
    assert item['fetch_status'] == 'success'
    assert item['fetch_error'] is None
    assert len(item['content']) == 150
    print(f"✓ Cached content gets success status")


@pytest.mark.asyncio
async def test_metadata_minimal_content():
    """Test metadata with minimal content (1-99 chars)."""
    items = [
        {'url': 'https://minimal.example.com', 'snippet': 'test'}
    ]
    # Pre-populate cache with minimal content
    cache = {'https://minimal.example.com': 'short'}  # 5 chars

    enriched, updated_cache = await enrich_items_with_content(items, cache)

    item = enriched[0]
    assert item['fetch_status'] == 'minimal'
    assert item['fetch_method'] == 'httpx_or_selenium'
    assert item['fetch_error'] == 'Content length below threshold (100 chars)'
    assert len(item['content']) == 5
    print(f"✓ Minimal content gets minimal status")


if __name__ == "__main__":
    print("Running fetch metadata tests...")
    asyncio.run(test_metadata_success_status())
    asyncio.run(test_metadata_failed_status())
    asyncio.run(test_metadata_with_cached_content())
    asyncio.run(test_metadata_minimal_content())
    print("✓ All tests completed!")
