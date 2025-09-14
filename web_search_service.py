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
        
        response = requests.get(url, params=params, timeout=6)  # Reduced timeout for speed
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
        
        response = requests.get(url, headers=headers, params=params, timeout=6)  # Reduced timeout for speed
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
        
        # DuckDuckGo HTML search (since their API is limited)
        try:
            search_url = f"https://duckduckgo.com/html/?q={quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = self.session.get(search_url, headers=headers, timeout=6)  # Reduced timeout for speed
            response.raise_for_status()
            
            # Parse HTML results (basic implementation)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            
            # Find search result links
            result_links = soup.find_all('a', class_='result__a')
            
            for link in result_links[:max_results]:
                try:
                    title = link.get_text().strip()
                    url = link.get('href')
                    
                    if url and title:
                        # Get snippet from result snippet div
                        snippet_div = link.find_next('a', class_='result__snippet')
                        snippet = snippet_div.get_text().strip() if snippet_div else ""
                        
                        result = SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet[:200],
                            source_domain=self._extract_domain(url)
                        )
                        results.append(result)
                        
                except Exception as e:
                    print(f"Error parsing DuckDuckGo result: {e}")
                    continue
            
            print(f"DuckDuckGo HTML search parsed {len(results)} results for '{query}'")
            return results
            
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            # Fallback: create a basic search result that points to DuckDuckGo search
            try:
                fallback_result = SearchResult(
                    title=f"Search results for: {query}",
                    url=f"https://duckduckgo.com/?q={quote(query)}",
                    snippet=f"DuckDuckGo search results for '{query}' - click to view in browser",
                    source_domain="duckduckgo.com"
                )
                return [fallback_result]
            except:
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
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Alias for search_web() to maintain compatibility with parallel evidence workers
        Returns results as dictionaries for worker compatibility
        """
        search_results = self.search_web(query, max_results)

        # Convert SearchResult objects to dictionaries for worker compatibility
        dict_results = []
        for result in search_results:
            dict_results.append({
                'title': result.title,
                'url': result.url,
                'snippet': result.snippet,
                'source_domain': result.source_domain
            })

        return dict_results

    def is_enabled(self) -> bool:
        """Check if web search is available"""
        return bool(self.google_api_key or self.bing_api_key)  # DuckDuckGo always available as fallback