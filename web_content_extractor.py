import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import re
from urllib.parse import urljoin, urlparse

class WebContentExtractor:
    """Extract and clean content from web pages for evidence analysis"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ROGR-FactCheck/1.0; Evidence analysis service)'
        })
        # Common timeout for web requests
        self.timeout = 10
        
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
        # Try multiple title sources
        title_sources = [
            soup.find('title'),
            soup.find('meta', property='og:title'),
            soup.find('meta', name='twitter:title'),
            soup.find('h1')
        ]
        
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
        description_sources = [
            soup.find('meta', name='description'),
            soup.find('meta', property='og:description'),
            soup.find('meta', name='twitter:description')
        ]
        
        for source in description_sources:
            if source:
                description = source.get('content', '').strip()
                if description:
                    return description[:300]
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        author_sources = [
            soup.find('meta', name='author'),
            soup.find('meta', property='article:author'),
            soup.find('span', class_='author'),
            soup.find('div', class_='author'),
            soup.find('[rel="author"]')
        ]
        
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
        date_sources = [
            soup.find('meta', property='article:published_time'),
            soup.find('meta', name='date'),
            soup.find('time'),
            soup.find('span', class_='date'),
            soup.find('div', class_='date')
        ]
        
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