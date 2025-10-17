from typing import List, Dict, Tuple, Any
import hashlib
import asyncio


async def enrich_items_with_content(items: List[Dict[str, Any]], fetch_cache: Dict[str, str]) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Enrich evidence items with full-text content.

    Args:
        items: List of evidence items (each has 'url', 'snippet', etc.)
        fetch_cache: Request-scoped cache {url: content}

    Returns:
        Tuple of (enriched_items, updated_fetch_cache)
    """
    # Identify missing URLs
    missing_urls = []
    for item in items:
        url = item.get('url')
        if url and url not in fetch_cache:
            missing_urls.append(url)

    # Fetch missing URLs if needed
    if missing_urls:
        fetch_cache = await fetch_missing_urls(missing_urls, fetch_cache)

    # Enrich each item with content fields
    enriched_items = []
    for item in items:
        enriched_item = item.copy()
        url = item.get('url', '')

        # Get content from cache
        content = fetch_cache.get(url, '')
        enriched_item['content'] = content
        enriched_item['content_chars'] = len(content)
        enriched_item['content_hash'] = _compute_content_hash(content)
        enriched_item['coverage'] = _determine_coverage(enriched_item)

        enriched_items.append(enriched_item)

    return (enriched_items, fetch_cache)


async def fetch_missing_urls(urls: List[str], fetch_cache: Dict[str, str], timeout: float = 8.0) -> Dict[str, str]:
    """
    Fetch URLs not in cache using async.

    Args:
        urls: List of URLs to fetch
        fetch_cache: Current cache to update
        timeout: Timeout for each fetch

    Returns:
        Updated fetch_cache
    """
    from intelligence.content.fetch import fetch_text

    async def fetch_one(url: str) -> Tuple[str, str]:
        """Fetch a single URL and return (url, content)."""
        try:
            content = await fetch_text(url, timeout)
            return (url, content)
        except Exception:
            return (url, '')

    # Create tasks for all URLs
    tasks = [fetch_one(url) for url in urls]

    # Fetch all concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Update cache with results
    for result in results:
        if isinstance(result, Exception):
            continue
        url, content = result
        fetch_cache[url] = content

    return fetch_cache


def _compute_content_hash(content: str) -> str:
    """
    Compute SHA256 hash of content.

    Args:
        content: Content to hash

    Returns:
        Hash in format "sha256:{hex_digest}"
    """
    hash_obj = hashlib.sha256(content.encode('utf-8'))
    hex_digest = hash_obj.hexdigest()
    return f"sha256:{hex_digest}"


def _determine_coverage(item: Dict[str, Any]) -> str:
    """
    Determine coverage level for an item.

    Args:
        item: Evidence item with content fields

    Returns:
        Coverage level: "full", "partial", or "snippet_only"
    """
    content = item.get('content', '')
    content_chars = item.get('content_chars', 0)

    # Full coverage: content exists and is at least 98% of expected length
    if content and content_chars > 0 and len(content) >= 0.98 * content_chars:
        return "full"

    # Partial coverage: has content or content_excerpt
    if content or item.get('content_excerpt'):
        return "partial"

    # Only snippet available
    return "snippet_only"


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

    import asyncio

    async def test():
        items = [
            {'url': 'https://www.example.com', 'snippet': 'test'},
            {'url': 'https://www.github.com', 'snippet': 'test2'}
        ]
        cache = {}

        print("Testing enrich_items_with_content...")
        enriched, updated_cache = await enrich_items_with_content(items, cache)

        print(f"✓ Enriched {len(enriched)} items")
        print(f"✓ Cache has {len(updated_cache)} entries")

        for item in enriched:
            has_hash = 'content_hash' in item
            has_coverage = 'coverage' in item
            print(f"  {item['url'][:40]}... hash={has_hash} coverage={has_coverage}")

        assert all('content_hash' in i for i in enriched), "Missing content_hash"
        assert all('coverage' in i for i in enriched), "Missing coverage"

        print("✓ PASS: Standalone test")

    asyncio.run(test())
