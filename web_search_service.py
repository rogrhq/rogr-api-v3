import requests
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import os
from urllib.parse import quote

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source_domain: str

class WebSearchService:
    """Service for performing web searches to find real evidence sources"""
    
    def __init__(self):
        # Multiple search API options for redundancy
        self.google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.google_cse_id = os.getenv('GOOGLE_CSE_ID')
        self.bing_api_key = os.getenv('BING_SEARCH_API_KEY')
        
        # Fallback to DuckDuckGo (no API key required)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ROGR-FactCheck/1.0; Evidence discovery service)'
        })
        
        print(f"WebSearchService initialized - Google: {bool(self.google_api_key)}, Bing: {bool(self.bing_api_key)}")
    
    def search_web(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search the web and return results from multiple sources"""
        
        results = []
        
        # Try Google Custom Search first (most comprehensive)
        if self.google_api_key and self.google_cse_id:
            try:
                google_results = self._search_google(query, max_results)
                results.extend(google_results)
                print(f"Google search found {len(google_results)} results for '{query}'")
            except Exception as e:
                print(f"Google search failed: {e}")
        
        # Try Bing if Google failed or returned few results
        if len(results) < max_results // 2 and self.bing_api_key:
            try:
                bing_results = self._search_bing(query, max_results - len(results))
                results.extend(bing_results)
                print(f"Bing search found {len(bing_results)} results for '{query}'")
            except Exception as e:
                print(f"Bing search failed: {e}")
        
        # Fallback to DuckDuckGo (no API key needed)
        if len(results) < max_results // 3:
            try:
                ddg_results = self._search_duckduckgo(query, max_results - len(results))
                results.extend(ddg_results)
                print(f"DuckDuckGo search found {len(ddg_results)} results for '{query}'")
            except Exception as e:
                print(f"DuckDuckGo search failed: {e}")
        
        # Remove duplicates and return top results
        unique_results = self._deduplicate_results(results)
        return unique_results[:max_results]
    
    def _search_google(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using Google Custom Search API"""
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.google_api_key,
            'cx': self.google_cse_id,
            'q': query,
            'num': min(max_results, 10)  # Google API limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for item in data.get('items', []):
            result = SearchResult(
                title=item.get('title', ''),
                url=item.get('link', ''),
                snippet=item.get('snippet', ''),
                source_domain=self._extract_domain(item.get('link', ''))
            )
            results.append(result)
        
        return results
    
    def _search_bing(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using Bing Search API"""
        
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            'Ocp-Apim-Subscription-Key': self.bing_api_key
        }
        params = {
            'q': query,
            'count': min(max_results, 50),  # Bing API limit
            'textDecorations': False,
            'textFormat': 'Raw'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for item in data.get('webPages', {}).get('value', []):
            result = SearchResult(
                title=item.get('name', ''),
                url=item.get('url', ''),
                snippet=item.get('snippet', ''),
                source_domain=self._extract_domain(item.get('url', ''))
            )
            results.append(result)
        
        return results
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using DuckDuckGo (fallback, no API key required)"""
        
        # DuckDuckGo Instant Answer API
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # DuckDuckGo returns limited structured data
            # This is a simplified implementation - real implementation would need web scraping
            abstract_source = data.get('AbstractSource')
            abstract_url = data.get('AbstractURL')
            
            if abstract_url and abstract_source:
                result = SearchResult(
                    title=f"DuckDuckGo: {abstract_source}",
                    url=abstract_url,
                    snippet=data.get('Abstract', '')[:200],
                    source_domain=self._extract_domain(abstract_url)
                )
                results.append(result)
            
            return results[:max_results]
            
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "unknown"
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on URL"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results
    
    def is_enabled(self) -> bool:
        """Check if web search is available"""
        return bool(self.google_api_key or self.bing_api_key)  # DuckDuckGo always available as fallback