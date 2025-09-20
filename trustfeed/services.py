from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import re

from trustfeed.models import TrustfeedEntry

def save_fact_check_to_trustfeed(
    claim_summary: str,
    trust_score: Optional[float] = None,
    grade: Optional[str] = None,
    source_url: Optional[str] = None,
    claims_analyzed: int = 0,
    scan_mode: Optional[str] = None,
    full_capsule_data: Optional[Dict[str, Any]] = None
) -> int:
    """
    Save a fact-check result to the trustfeed database.

    Args:
        claim_summary: Summary of the claim being fact-checked
        trust_score: Calculated trust score (0.0 to 1.0)
        grade: Letter grade (A+, A, B+, B, C+, C, D, F)
        source_url: Original URL of the content
        claims_analyzed: Number of claims analyzed
        scan_mode: Mode used for analysis (e.g., 'precision', 'comprehensive')
        full_capsule_data: Complete analysis data for archival

    Returns:
        ID of the created trustfeed entry
    """
    # Extract metadata
    source_domain = extract_domain_from_url(source_url) if source_url else None
    tags = extract_tags_from_data(full_capsule_data)
    categories = extract_categories_from_data(full_capsule_data)

    # Create and save entry
    entry = TrustfeedEntry(
        claim_summary=claim_summary,
        trust_score=trust_score,
        grade=grade,
        source_url=source_url,
        source_domain=source_domain,
        claims_analyzed=claims_analyzed,
        scan_mode=scan_mode,
        tags=tags,
        categories=categories,
        full_capsule_data=full_capsule_data
    )

    return entry.save()

def extract_domain_from_url(url: str) -> Optional[str]:
    """
    Extract domain name from a URL.

    Args:
        url: Full URL string

    Returns:
        Domain name or None if URL is invalid
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return None

def extract_tags_from_data(capsule_data: Optional[Dict[str, Any]]) -> Optional[List[str]]:
    """
    Extract relevant tags from the full capsule data.

    Args:
        capsule_data: Complete analysis data

    Returns:
        List of tags or None
    """
    if not capsule_data:
        return None

    tags = set()

    # Extract tags from various sources in the data
    if 'evidence' in capsule_data:
        evidence = capsule_data['evidence']
        if isinstance(evidence, list):
            for item in evidence:
                if isinstance(item, dict):
                    # Look for source types
                    if 'source_type' in item:
                        tags.add(item['source_type'].lower())
                    # Look for keywords in titles
                    if 'title' in item:
                        tags.update(extract_keywords_from_text(item['title']))

    # Extract from claim data
    if 'claims' in capsule_data:
        claims = capsule_data['claims']
        if isinstance(claims, list):
            for claim in claims:
                if isinstance(claim, dict) and 'claim_text' in claim:
                    tags.update(extract_keywords_from_text(claim['claim_text']))

    # Limit to most relevant tags
    return list(tags)[:10] if tags else None

def extract_categories_from_data(capsule_data: Optional[Dict[str, Any]]) -> Optional[List[str]]:
    """
    Extract content categories from the analysis data.

    Args:
        capsule_data: Complete analysis data

    Returns:
        List of categories or None
    """
    if not capsule_data:
        return None

    categories = set()

    # Define category mappings based on keywords
    category_keywords = {
        'politics': ['election', 'vote', 'candidate', 'government', 'policy', 'politician'],
        'health': ['medical', 'vaccine', 'disease', 'health', 'doctor', 'medicine'],
        'science': ['research', 'study', 'scientific', 'climate', 'environment'],
        'technology': ['ai', 'artificial intelligence', 'tech', 'digital', 'internet'],
        'finance': ['economy', 'market', 'financial', 'money', 'investment'],
        'social': ['social media', 'facebook', 'twitter', 'instagram', 'viral'],
        'news': ['breaking', 'report', 'journalist', 'media', 'press']
    }

    # Extract text for analysis
    all_text = ""
    if 'claims' in capsule_data:
        claims = capsule_data['claims']
        if isinstance(claims, list):
            for claim in claims:
                if isinstance(claim, dict) and 'claim_text' in claim:
                    all_text += " " + claim['claim_text'].lower()

    if 'evidence' in capsule_data:
        evidence = capsule_data['evidence']
        if isinstance(evidence, list):
            for item in evidence:
                if isinstance(item, dict):
                    if 'title' in item:
                        all_text += " " + item['title'].lower()
                    if 'content' in item:
                        all_text += " " + item['content'][:200].lower()  # Limit content length

    # Match categories based on keywords
    for category, keywords in category_keywords.items():
        if any(keyword in all_text for keyword in keywords):
            categories.add(category)

    return list(categories) if categories else None

def extract_keywords_from_text(text: str, max_keywords: int = 5) -> List[str]:
    """
    Extract keywords from text using simple heuristics.

    Args:
        text: Input text
        max_keywords: Maximum number of keywords to return

    Returns:
        List of keywords
    """
    if not text:
        return []

    # Simple keyword extraction - look for capitalized words and important terms
    words = re.findall(r'\b[A-Z][a-z]+\b', text)

    # Filter common words
    stop_words = {'The', 'This', 'That', 'With', 'For', 'And', 'But', 'Or'}
    keywords = [word.lower() for word in words if word not in stop_words]

    # Remove duplicates and limit
    return list(set(keywords))[:max_keywords]

def calculate_trust_grade(trust_score: float) -> str:
    """
    Convert trust score to letter grade.

    Args:
        trust_score: Trust score from 0.0 to 1.0

    Returns:
        Letter grade (A+ to F)
    """
    if trust_score >= 0.97:
        return 'A+'
    elif trust_score >= 0.93:
        return 'A'
    elif trust_score >= 0.90:
        return 'A-'
    elif trust_score >= 0.87:
        return 'B+'
    elif trust_score >= 0.83:
        return 'B'
    elif trust_score >= 0.80:
        return 'B-'
    elif trust_score >= 0.77:
        return 'C+'
    elif trust_score >= 0.73:
        return 'C'
    elif trust_score >= 0.70:
        return 'C-'
    elif trust_score >= 0.67:
        return 'D+'
    elif trust_score >= 0.60:
        return 'D'
    else:
        return 'F'