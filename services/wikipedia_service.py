import re
import requests
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
import json
from evidence_shepherd import EvidenceShepherd, NoOpEvidenceShepherd, EvidenceCandidate

class WikipediaService:
    """Service to search Wikipedia and extract outbound citations for evidence collection"""
    
    def __init__(self, evidence_shepherd: Optional[EvidenceShepherd] = None):
        self.base_url = "https://en.wikipedia.org/api/rest_v1"
        self.search_url = "https://en.wikipedia.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ROGR-FactCheck/1.0 (https://rogr.app; fact-checking service)'
        })
        
        # AI Evidence Shepherd - modular and optional
        self.shepherd = evidence_shepherd or NoOpEvidenceShepherd()
        print(f"Wikipedia service initialized with shepherd: {type(self.shepherd).__name__}")
    
    def search_evidence_for_claim(self, claim_text: str) -> List[Dict]:
        """
        AI-powered search for evidence related to a claim
        Returns list of evidence items with AI relevance scoring
        """
        try:
            # Use AI Shepherd to analyze claim and get search strategy
            search_strategy = self.shepherd.analyze_claim(claim_text)
            print(f"AI Strategy for '{claim_text[:50]}...': {search_strategy.claim_type.value}, {len(search_strategy.search_queries)} queries")
            
            # Collect raw evidence candidates using AI-optimized searches
            evidence_candidates = []
            
            # SPEED OPTIMIZATION: Limit search queries for faster processing
            max_queries = 2 if len(claim_text) > 100 else 3  # Longer claims = fewer queries
            
            for search_query in search_strategy.search_queries[:max_queries]:
                wiki_articles = self._search_wikipedia_articles([search_query])
                
                if not wiki_articles:
                    continue
                
                # SPEED OPTIMIZATION: Reduced processing limits for standard articles
                if search_strategy.claim_type.value in ['statistical', 'policy']:
                    articles_to_process = 2  # High-priority claims
                elif search_strategy.claim_type.value in ['scientific']:
                    articles_to_process = 3  # Need more sources for science
                else:
                    articles_to_process = 2  # Standard claims - optimized for speed
                
                for article in wiki_articles[:articles_to_process]:
                    try:
                        # Add Wikipedia article as evidence candidate
                        # FIXED: Proper URL encoding for Wikipedia titles
                        encoded_title = urllib.parse.quote(article['title'].replace(' ', '_'), safe='')
                        wiki_candidate = EvidenceCandidate(
                            text=article.get('extract', 'Wikipedia article content')[:400],
                            source_url=f"https://en.wikipedia.org/wiki/{encoded_title}",
                            source_domain='en.wikipedia.org',
                            source_title=article['title'],
                            found_via_query=search_query,
                            raw_relevance=0.5  # Initial relevance
                        )
                        evidence_candidates.append(wiki_candidate)
                        
                        # SPEED OPTIMIZATION: Reduced citation extraction for standard articles
                        try:
                            citations = self._extract_citations_from_article(article['title'])
                            # Optimize citation limits based on claim importance and processing speed
                            if search_strategy.claim_type.value in ['statistical', 'policy']:
                                citation_limit = 2  # Reduced from 3 to 2 for speed
                            elif search_strategy.claim_type.value in ['scientific']:
                                citation_limit = 2  # Scientific claims need quality sources
                            else:
                                citation_limit = 1  # Standard claims - fast processing
                        except Exception as e:
                            print(f"Citation extraction failed for {article['title']}: {e}")
                            citations = []
                            citation_limit = 0
                        
                        for citation_data in citations[:citation_limit]:
                            citation_candidate = EvidenceCandidate(
                                text=citation_data['statement'],
                                source_url=citation_data['source_url'],
                                source_domain=citation_data['source_domain'],
                                source_title=citation_data['source_title'],
                                found_via_query=search_query,
                                raw_relevance=citation_data.get('weight', 0.7)
                            )
                            evidence_candidates.append(citation_candidate)
                            
                    except Exception as e:
                        print(f"Error processing article {article.get('title', 'unknown')}: {e}")
                        continue
            
            if not evidence_candidates:
                return []
            
            # Use AI Shepherd to score and filter evidence for relevance (with timeout)
            try:
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("AI processing timeout")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(20)  # SPEED OPTIMIZATION: Reduced from 30 to 20 seconds
                
                processed_evidence = self.shepherd.filter_evidence_batch(claim_text, evidence_candidates)
                
                signal.alarm(0)  # Cancel timeout
                
            except TimeoutError:
                print(f"AI processing timed out for claim '{claim_text[:50]}...', using fallback")
                processed_evidence = []
                # Use top evidence candidates without AI scoring
                for candidate in evidence_candidates[:5]:
                    processed_evidence.append(type('ProcessedEvidence', (), {
                        'text': candidate.text,
                        'source_title': candidate.source_title,
                        'source_domain': candidate.source_domain,
                        'source_url': candidate.source_url,
                        'ai_relevance_score': 60,  # Default score
                        'ai_stance': 'neutral',
                        'ai_confidence': 0.5,
                        'ai_reasoning': 'Timeout fallback - AI processing took too long',
                        'highlight_text': candidate.text[:100],
                        'highlight_context': candidate.text[:300]
                    })())
            except Exception as e:
                print(f"AI processing failed for claim '{claim_text[:50]}...': {e}")
                processed_evidence = []
            
            # Convert back to the expected format
            evidence_items = []
            for processed in processed_evidence:
                evidence_items.append({
                    'statement': processed.text,
                    'source_title': processed.source_title,
                    'source_domain': processed.source_domain,
                    'source_url': processed.source_url,
                    'source_type': 'wikipedia' if 'wikipedia.org' in processed.source_domain else 'external',
                    'weight': self._calculate_source_weight(processed.source_domain),
                    'date_published': None,
                    'relevance_score': processed.ai_relevance_score / 100,  # Convert to 0-1
                    'ai_stance': processed.ai_stance,
                    'ai_confidence': processed.ai_confidence,
                    'ai_reasoning': processed.ai_reasoning,
                    'highlight_text': processed.highlight_text,
                    'highlight_context': processed.highlight_context
                })
            
            print(f"AI filtering: {len(evidence_candidates)} candidates → {len(evidence_items)} relevant evidence items")
            return evidence_items
            
        except Exception as e:
            print(f"AI-powered Wikipedia search error for claim '{claim_text}': {e}")
            # Fallback to original method
            return self._fallback_search(claim_text)
    
    def _extract_search_terms(self, claim_text: str) -> List[str]:
        """Extract key search terms from a claim"""
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
        
        # Extract words, focusing on nouns and key terms
        words = re.findall(r'\b[A-Za-z]+\b', claim_text.lower())
        
        # Filter out stop words and short words
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Look for specific entities, numbers, and important terms
        entities = []
        
        # Extract proper nouns (capitalized words in original text)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', claim_text)
        entities.extend(proper_nouns)
        
        # Extract phrases with specific patterns
        if re.search(r'renewable energy|solar|wind|climate', claim_text, re.IGNORECASE):
            entities.extend(['renewable energy', 'climate change', 'clean energy'])
        
        if re.search(r'percent|percentage|%', claim_text, re.IGNORECASE):
            entities.append('statistics')
        
        # Combine meaningful words and entities
        search_terms = list(set(meaningful_words[:5] + entities[:3]))
        
        return search_terms[:5]  # Max 5 search terms
    
    def _search_wikipedia_articles(self, search_terms: List[str]) -> List[Dict]:
        """Search Wikipedia for articles matching the search terms"""
        try:
            # Create search query
            query = " ".join(search_terms[:3])  # Use top 3 terms
            
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': 5,  # Get top 5 results
                'srinfo': 'totalhits',
                'srprop': 'size|wordcount|timestamp|snippet'
            }
            
            response = self.session.get(self.search_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'query' not in data or 'search' not in data['query']:
                return []
            
            articles = []
            for result in data['query']['search']:
                # Get additional info for each article
                article_info = self._get_article_extract(result['title'])
                if article_info:
                    article_info.update({
                        'search_snippet': result.get('snippet', ''),
                        'wordcount': result.get('wordcount', 0),
                        'size': result.get('size', 0)
                    })
                    articles.append(article_info)
            
            return articles
            
        except Exception as e:
            print(f"Wikipedia search error: {e}")
            return []
    
    def _get_article_extract(self, title: str) -> Optional[Dict]:
        """Get article extract/summary from Wikipedia"""
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'titles': title,
                'prop': 'extracts',
                'exintro': True,
                'explaintext': True,
                'exsectionformat': 'plain'
            }
            
            response = self.session.get(self.search_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'query' in data and 'pages' in data['query']:
                for page_id, page_data in data['query']['pages'].items():
                    if page_id != '-1' and 'extract' in page_data:
                        return {
                            'title': page_data['title'],
                            'extract': page_data['extract'][:500],  # First 500 chars
                            'page_id': page_id
                        }
            
            return None
            
        except Exception as e:
            print(f"Error getting article extract for '{title}': {e}")
            return None
    
    def _extract_citations_from_article(self, title: str) -> List[Dict]:
        """Extract external citations from a Wikipedia article"""
        try:
            # Get article HTML content with timeout
            url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            response = self.session.get(url, timeout=8)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find reference links
            citations = []
            
            # Look for reference links in various formats
            reference_selectors = [
                'span.reference a.external.text',  # Standard reference links
                'div.reflist a.external.text',     # Reference list links
                'li a.external.text',              # List item external links
                '.citation a.external.text',       # Citation class links
            ]
            
            external_links = set()  # Use set to avoid duplicates
            
            for selector in reference_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href and self._is_valid_external_source(href):
                        external_links.add(href)
            
            # Process external links and create evidence items (limited to prevent hanging)
            for i, link in enumerate(list(external_links)[:5]):  # Reduced to max 5 links
                try:
                    citation_info = self._analyze_external_source(link)
                    if citation_info:
                        citation_info.update({
                            'source_type': 'external',
                            'weight': self._calculate_source_weight(citation_info['source_domain']),
                            'found_via': f'Wikipedia: {title}'
                        })
                        citations.append(citation_info)
                except Exception as e:
                    print(f"Error analyzing citation {link}: {e}")
                    continue
            
            return citations[:5]  # Return top 5 citations
            
        except Exception as e:
            print(f"Error extracting citations from '{title}': {e}")
            return []
    
    def _is_valid_external_source(self, url: str) -> bool:
        """Check if URL is a valid external source for evidence"""
        if not url:
            return False
        
        # Skip Wikipedia internal links
        if 'wikipedia.org' in url:
            return False
        
        # Skip commons, wiktionary, etc.
        if any(domain in url for domain in ['commons.wikimedia', 'wiktionary.org', 'wikidata.org']):
            return False
        
        # Skip certain file types and fragments
        if any(ext in url.lower() for ext in ['.pdf#', '.jpg', '.png', '.gif', '#cite']):
            return False
        
        # Check for reputable domains
        reputable_domains = [
            'gov', 'edu', 'org', 
            'reuters.com', 'apnews.com', 'bbc.com', 'cnn.com',
            'nature.com', 'science.org', 'pnas.org',
            'nytimes.com', 'washingtonpost.com', 'guardian.com',
            'energy.gov', 'epa.gov', 'nasa.gov', 'cdc.gov'
        ]
        
        return any(domain in url for domain in reputable_domains)
    
    def _analyze_external_source(self, url: str) -> Optional[Dict]:
        """Analyze an external source URL and extract metadata with highlighting information"""
        try:
            # Get basic info from URL
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Try to fetch page title and snippet
            try:
                response = self.session.get(url, timeout=10, allow_redirects=True)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract title
                title_tag = soup.find('title')
                title = title_tag.get_text().strip() if title_tag else f"Article from {domain}"
                
                # Extract description
                description = ""
                desc_tag = soup.find('meta', attrs={'name': 'description'}) or \
                          soup.find('meta', attrs={'property': 'og:description'})
                if desc_tag:
                    description = desc_tag.get('content', '')[:200]
                
                # Try to extract content with paragraph tracking for highlighting
                content_text = ""
                highlight_text = ""
                highlight_context = ""
                paragraph_index = None
                
                paragraphs = soup.find_all('p')
                if paragraphs:
                    content_parts = []
                    for i, p in enumerate(paragraphs[:5]):
                        p_text = p.get_text().strip()
                        if p_text:
                            content_parts.append(p_text)
                            # Use first substantial paragraph for highlighting
                            if not highlight_text and len(p_text) > 50:
                                highlight_text = p_text[:150] + ("..." if len(p_text) > 150 else "")
                                highlight_context = p_text[:300]
                                paragraph_index = i
                    
                    content_text = " ".join(content_parts)[:300]
                
                statement = description if description else content_text if content_text else f"External source from {domain}"
                
                # If no highlight text yet, use the statement itself
                if not highlight_text:
                    highlight_text = statement[:100] + ("..." if len(statement) > 100 else "")
                    highlight_context = statement
                
            except Exception:
                # Fallback if we can't fetch the page
                title = f"External source from {domain}"
                statement = f"Reference from {domain} (content not accessible)"
                highlight_text = statement
                highlight_context = statement
                paragraph_index = None
            
            return {
                'statement': statement,
                'source_title': title,
                'source_domain': domain,
                'source_url': url,
                'date_published': None,  # Could enhance with date extraction
                'relevance_score': 0.7,   # Default relevance
                'highlight_text': highlight_text,
                'highlight_context': highlight_context,
                'paragraph_index': paragraph_index
            }
            
        except Exception as e:
            print(f"Error analyzing external source {url}: {e}")
            return None
    
    def _calculate_source_weight(self, domain: str) -> float:
        """Calculate weight/credibility score for a source domain"""
        # Government and educational sources
        if any(tld in domain for tld in ['.gov', '.edu']):
            return 1.0
        
        # Major news organizations
        major_news = ['reuters.com', 'apnews.com', 'bbc.com', 'npr.org']
        if any(news in domain for news in major_news):
            return 0.9
        
        # Scientific journals and organizations
        scientific = ['nature.com', 'science.org', 'pnas.org', 'nih.gov', 'cdc.gov']
        if any(sci in domain for sci in scientific):
            return 0.95
        
        # Other reputable organizations
        reputable_orgs = ['.org', 'nytimes.com', 'washingtonpost.com', 'guardian.com']
        if any(org in domain for org in reputable_orgs):
            return 0.8
        
        # Default for other external sources
        return 0.6
    
    def _fallback_search(self, claim_text: str) -> List[Dict]:
        """Fallback to original search method when AI fails"""
        try:
            search_terms = self._extract_search_terms(claim_text)
            if not search_terms:
                return []
            
            wiki_articles = self._search_wikipedia_articles(search_terms)
            if not wiki_articles:
                return []
            
            evidence_items = []
            
            for article in wiki_articles[:3]:
                try:
                    citations = self._extract_citations_from_article(article['title'])
                    
                    wikipedia_evidence = {
                        'statement': article.get('extract', 'Wikipedia article content'),
                        'source_title': article['title'],
                        'source_domain': 'en.wikipedia.org',
                        'source_url': f"https://en.wikipedia.org/wiki/{urllib.parse.quote(article['title'].replace(' ', '_'), safe='')}",
                        'source_type': 'wikipedia',
                        'weight': 0.3,
                        'date_published': None,
                        'relevance_score': 0.6,
                        'highlight_text': article.get('extract', '')[:100],
                        'highlight_context': article.get('extract', '')[:300]
                    }
                    evidence_items.append(wikipedia_evidence)
                    
                    for citation in citations[:5]:
                        evidence_items.append(citation)
                        
                except Exception as e:
                    print(f"Error in fallback processing {article.get('title', 'unknown')}: {e}")
                    continue
            
            evidence_items.sort(key=lambda x: (x.get('weight', 0), x.get('relevance_score', 0)), reverse=True)
            return evidence_items[:8]
            
        except Exception as e:
            print(f"Fallback search error: {e}")
            return []