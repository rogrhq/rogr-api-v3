import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import re
from urllib.parse import urljoin, urlparse
import concurrent.futures
import threading

class WebContentExtractor:
    """Extract and clean content from web pages for evidence analysis"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        # Balanced timeout - not too fast, not too slow
        self.timeout = 8  # Increased from 5 to 8 seconds for reliability
        self.max_workers = 6  # Parallel processing limit
        
    def extract_content(self, url: str) -> Dict[str, str]:
        """Extract title, content, and metadata from a web page"""
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            # Extract metadata
            description = self._extract_description(soup)
            author = self._extract_author(soup)
            publish_date = self._extract_publish_date(soup)
            
            return {
                'title': title,
                'content': content,
                'description': description,
                'author': author,
                'publish_date': publish_date,
                'url': url,
                'domain': self._extract_domain(url),
                'word_count': len(content.split()) if content else 0,
                'success': True
            }
            
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            return {
                'title': '',
                'content': '',
                'description': '',
                'author': '',
                'publish_date': '',
                'url': url,
                'domain': self._extract_domain(url),
                'word_count': 0,
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            print(f"Content extraction error for {url}: {e}")
            return {
                'title': '',
                'content': '',
                'description': '',
                'author': '',
                'publish_date': '',
                'url': url,
                'domain': self._extract_domain(url),
                'word_count': 0,
                'success': False,
                'error': str(e)
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        try:
            # Try multiple title sources with explicit attrs parameter
            title_sources = [
                soup.find('title'),
                soup.find('meta', attrs={'property': 'og:title'}),
                soup.find('meta', attrs={'name': 'twitter:title'}),
                soup.find('h1')
            ]
        except Exception as e:
            print(f"Title extraction error: {e}")
            title_sources = [soup.find('title')] if soup.find('title') else []
        
        for source in title_sources:
            if source:
                if source.name == 'meta':
                    title = source.get('content', '').strip()
                else:
                    title = source.get_text().strip()
                
                if title:
                    return title[:200]  # Limit title length
        
        return "Untitled"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
            element.decompose()
        
        # Try to find main content containers
        content_selectors = [
            'article',
            '[role="main"]',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            '.main-content',
            'main'
        ]
        
        content_text = ""
        
        # Try each selector
        for selector in content_selectors:
            content_container = soup.select_one(selector)
            if content_container:
                content_text = content_container.get_text(separator=' ', strip=True)
                if len(content_text) > 200:  # Found substantial content
                    break
        
        # Fallback: extract all paragraph text
        if len(content_text) < 200:
            paragraphs = soup.find_all('p')
            content_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        # Clean up the text
        content_text = re.sub(r'\s+', ' ', content_text)  # Normalize whitespace
        content_text = content_text.strip()
        
        # Limit content length (for processing efficiency)
        return content_text[:5000] if content_text else ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description/summary"""
        try:
            description_sources = [
                soup.find('meta', attrs={'name': 'description'}),
                soup.find('meta', attrs={'property': 'og:description'}),
                soup.find('meta', attrs={'name': 'twitter:description'})
            ]
        except Exception as e:
            print(f"Description extraction error: {e}")
            description_sources = []
        
        for source in description_sources:
            if source:
                description = source.get('content', '').strip()
                if description:
                    return description[:300]
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        try:
            author_sources = [
                soup.find('meta', attrs={'name': 'author'}),
                soup.find('meta', attrs={'property': 'article:author'}),
                soup.find('span', attrs={'class': 'author'}),
                soup.find('div', attrs={'class': 'author'}),
                soup.select('[rel="author"]')
            ]
            # Flatten the select result
            if author_sources[-1]:
                author_sources[-1] = author_sources[-1][0] if author_sources[-1] else None
        except Exception as e:
            print(f"Author extraction error: {e}")
            author_sources = []
        
        for source in author_sources:
            if source:
                if source.name == 'meta':
                    author = source.get('content', '').strip()
                else:
                    author = source.get_text().strip()
                
                if author:
                    return author[:100]
        
        return ""
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> str:
        """Extract article publish date"""
        try:
            date_sources = [
                soup.find('meta', attrs={'property': 'article:published_time'}),
                soup.find('meta', attrs={'name': 'date'}),
                soup.find('time'),
                soup.find('span', attrs={'class': 'date'}),
                soup.find('div', attrs={'class': 'date'})
            ]
        except Exception as e:
            print(f"Date extraction error: {e}")
            date_sources = []
        
        for source in date_sources:
            if source:
                if source.name == 'meta':
                    date = source.get('content', '').strip()
                elif source.name == 'time':
                    date = source.get('datetime') or source.get_text().strip()
                else:
                    date = source.get_text().strip()
                
                if date:
                    return date[:50]
        
        return ""
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "unknown"
    
    def extract_content_batch(self, urls: List[str]) -> List[Dict[str, str]]:
        """SPEED OPTIMIZATION: Extract content from multiple URLs in parallel"""
        
        if not urls:
            return []
        
        print(f"Extracting content from {len(urls)} URLs in parallel (max_workers={self.max_workers})")
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all URL extractions
            future_to_url = {
                executor.submit(self._extract_single_with_timeout, url): url 
                for url in urls
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url, timeout=15):  # 15 second total limit
                url = future_to_url[future]
                try:
                    result = future.result(timeout=2)  # Individual result timeout
                    results.append(result)
                    if result['success']:
                        print(f"✅ Extracted: {result['domain']} ({result['word_count']} words)")
                    else:
                        print(f"❌ Failed: {result['domain']} - {result.get('error', 'Unknown error')}")
                except concurrent.futures.TimeoutError:
                    print(f"⏱️ Timeout: {self._extract_domain(url)}")
                    results.append({
                        'title': '',
                        'content': '',
                        'description': '',
                        'author': '',
                        'publish_date': '',
                        'url': url,
                        'domain': self._extract_domain(url),
                        'word_count': 0,
                        'success': False,
                        'error': 'Extraction timeout'
                    })
                except Exception as e:
                    print(f"💥 Exception: {self._extract_domain(url)} - {str(e)}")
                    results.append({
                        'title': '',
                        'content': '',
                        'description': '',
                        'author': '',
                        'publish_date': '',
                        'url': url,
                        'domain': self._extract_domain(url),
                        'word_count': 0,
                        'success': False,
                        'error': str(e)
                    })
        
        successful_extractions = sum(1 for r in results if r['success'])
        print(f"Parallel extraction complete: {successful_extractions}/{len(urls)} successful")
        
        return results
    
    def _extract_single_with_timeout(self, url: str) -> Dict[str, str]:
        """Extract content with optimized timeout handling"""
        try:
            # Use shorter timeout for individual requests
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Quick extraction for speed
            title = self._extract_title(soup)
            content = self._extract_main_content(soup)
            
            # Skip metadata extraction for speed optimization
            return {
                'title': title,
                'content': content,
                'description': '',  # Skip for speed
                'author': '',       # Skip for speed
                'publish_date': '', # Skip for speed
                'url': url,
                'domain': self._extract_domain(url),
                'word_count': len(content.split()) if content else 0,
                'success': True
            }
            
        except Exception as e:
            return {
                'title': '',
                'content': '',
                'description': '',
                'author': '',
                'publish_date': '',
                'url': url,
                'domain': self._extract_domain(url),
                'word_count': 0,
                'success': False,
                'error': str(e)
            }