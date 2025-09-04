import os
import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import requests

@dataclass
class EvidenceQualityMetrics:
    """Multi-dimensional evidence quality assessment scores"""
    methodology_rigor: float  # 0-100: Study design, sample size, controls
    peer_review_status: float  # 0-100: Independent review process indicators
    reproducibility: float  # 0-100: Replication indicators and reproducible methods
    citation_impact: float  # 0-100: Citation patterns and academic impact
    transparency: float  # 0-100: Data/methods disclosure and accessibility
    temporal_consistency: float  # 0-100: Consistency over time and updates
    content_type: str = "general"  # Detected content type for quality assessment
    
    def overall_quality_score(self) -> float:
        """Calculate weighted overall quality score"""
        weights = {
            'methodology_rigor': 0.25,
            'peer_review_status': 0.20,
            'reproducibility': 0.20,
            'citation_impact': 0.15,
            'transparency': 0.15,
            'temporal_consistency': 0.05
        }
        
        return (
            self.methodology_rigor * weights['methodology_rigor'] +
            self.peer_review_status * weights['peer_review_status'] +
            self.reproducibility * weights['reproducibility'] +
            self.citation_impact * weights['citation_impact'] +
            self.transparency * weights['transparency'] +
            self.temporal_consistency * weights['temporal_consistency']
        )
    
    def quality_tier(self) -> str:
        """Determine quality tier based on overall score"""
        score = self.overall_quality_score()
        if score >= 85:
            return "exceptional"
        elif score >= 70:
            return "high"
        elif score >= 55:
            return "medium"
        elif score >= 40:
            return "low"
        else:
            return "very_low"

class EvidenceQualityAssessor:
    """AI-powered evidence quality assessment system - source agnostic, evidence-first"""
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-haiku-20240307"
        
        print("Evidence Quality Assessor initialized - focusing on intrinsic evidence quality")
    
    def _call_claude(self, messages: List[Dict], max_tokens: int = 1500) -> Optional[str]:
        """Make API call to Claude for quality assessment"""
        if not self.api_key:
            return None
            
        try:
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    user_messages.append(msg)
            
            payload = {
                'model': self.model,
                'max_tokens': max_tokens,
                'messages': user_messages,
                'system': system_message
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json()['content'][0]['text']
            else:
                print(f"Claude API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return None
    
    def assess_methodology_rigor(self, content: str, source_url: str) -> float:
        """Assess research methodology quality - sample size, controls, design"""
        
        methodology_indicators = {
            # Study design quality indicators
            'randomized_controlled': 15,
            'double_blind': 12,
            'placebo_controlled': 10,
            'peer_reviewed': 10,
            'systematic_review': 20,
            'meta_analysis': 25,
            'longitudinal': 8,
            'cross_sectional': 5,
            
            # Sample size and statistical rigor
            'large_sample': 10,  # n > 1000
            'medium_sample': 6,  # n > 100
            'statistical_significance': 8,
            'confidence_intervals': 6,
            'effect_size': 4,
            
            # Methodology disclosure
            'methods_section': 8,
            'protocol_described': 6,
            'inclusion_criteria': 5,
            'exclusion_criteria': 5,
        }
        
        content_lower = content.lower()
        
        # Base score starts at 20 (basic content)
        score = 20.0
        
        # Check for methodology indicators
        if 'systematic review' in content_lower or 'meta-analysis' in content_lower:
            score += methodology_indicators['systematic_review']
        elif 'randomized controlled trial' in content_lower or 'rct' in content_lower:
            score += methodology_indicators['randomized_controlled']
        elif 'double-blind' in content_lower:
            score += methodology_indicators['double_blind']
        
        # Sample size indicators
        sample_size_matches = re.findall(r'n\s*=\s*(\d+)', content_lower)
        if sample_size_matches:
            max_sample = max([int(n) for n in sample_size_matches])
            if max_sample > 1000:
                score += methodology_indicators['large_sample']
            elif max_sample > 100:
                score += methodology_indicators['medium_sample']
        
        # Statistical rigor indicators
        if any(phrase in content_lower for phrase in ['p <', 'p<', 'significant', 'confidence interval']):
            score += methodology_indicators['statistical_significance']
        
        # Methods section presence
        if 'method' in content_lower and ('procedure' in content_lower or 'protocol' in content_lower):
            score += methodology_indicators['methods_section']
        
        return min(100.0, score)
    
    def _detect_content_type(self, content: str, source_url: str, source_title: str) -> str:
        """Detect the primary content type for appropriate quality assessment"""
        content_lower = content.lower()
        url_lower = source_url.lower()
        title_lower = source_title.lower()
        
        # Research Content - academic papers, studies, journals
        research_indicators = [
            'abstract', 'methodology', 'results', 'conclusion', 'peer reviewed',
            'doi:', 'pmid:', 'journal', 'study', 'research', 'systematic review',
            'meta-analysis', 'statistical analysis', 'sample size', 'control group'
        ]
        if sum(1 for indicator in research_indicators if indicator in content_lower) >= 3:
            return 'research'
        
        # News Content - journalism, reporting, news outlets
        news_indicators = [
            'reported', 'according to', 'sources say', 'breaking news',
            'correspondent', 'journalist', 'news desk', 'editorial',
            'fact-check', 'verified', 'confirmed by'
        ]
        if sum(1 for indicator in news_indicators if indicator in content_lower) >= 2:
            return 'news'
        
        # Reference Content - encyclopedias, fact sheets, educational
        reference_indicators = [
            'encyclopedia', 'reference', 'overview', 'definition',
            'explanation', 'guide', 'fact sheet', 'educational',
            'summary', 'introduction to'
        ]
        if sum(1 for indicator in reference_indicators if indicator in content_lower) >= 2:
            return 'reference'
            
        # Official Content - government, institutions, organizations
        official_indicators = [
            'official', 'agency', 'department', 'administration',
            'government', 'federal', 'national', 'institute',
            'organization', 'foundation', 'authority'
        ]
        if sum(1 for indicator in official_indicators if indicator in content_lower) >= 2:
            return 'official'
        
        # Expert Content - professional analysis, expert opinion
        expert_indicators = [
            'expert', 'professor', 'dr.', 'phd', 'analysis',
            'professional', 'specialist', 'authority', 'experience'
        ]
        if sum(1 for indicator in expert_indicators if indicator in content_lower) >= 2:
            return 'expert'
        
        # Default to general content
        return 'general'

    def assess_peer_review_status(self, content: str, source_url: str, source_title: str) -> float:
        """Assess publication quality using content-type-aware evaluation"""
        
        content_lower = content.lower()
        content_type = self._detect_content_type(content, source_url, source_title)
        
        print(f"Content type detected: {content_type} for {source_title[:30]}...")
        
        score = 20.0  # Higher base score for all content types
        
        # Content-type-specific quality assessment
        if content_type == 'research':
            # Academic/Research Content Quality
            if any(indicator in content_lower for indicator in ['peer reviewed', 'refereed', 'editorial board']):
                score += 25
            if any(indicator in content_lower for indicator in ['doi:', 'pmid:', 'arxiv:']):
                score += 20
            if any(indicator in content_lower for indicator in ['methodology', 'statistical analysis', 'sample size']):
                score += 15
                
        elif content_type == 'news':
            # News Content Quality
            if any(indicator in content_lower for indicator in ['fact-check', 'verified', 'confirmed']):
                score += 20
            if any(indicator in content_lower for indicator in ['sources', 'according to', 'reported by']):
                score += 15
            if any(indicator in content_lower for indicator in ['editorial standards', 'news desk', 'correspondent']):
                score += 15
                
        elif content_type == 'reference':
            # Reference Content Quality  
            if any(indicator in content_lower for indicator in ['encyclopedia', 'curated', 'editorial oversight']):
                score += 20
            if any(indicator in content_lower for indicator in ['references', 'citations', 'sources']):
                score += 15
            if any(indicator in content_lower for indicator in ['fact-checked', 'verified', 'accuracy']):
                score += 15
                
        elif content_type == 'official':
            # Official/Institutional Content Quality
            if any(indicator in content_lower for indicator in ['official statement', 'agency report', 'government data']):
                score += 25
            if any(indicator in content_lower for indicator in ['statistics', 'data', 'findings']):
                score += 20
            if any(indicator in content_lower for indicator in ['transparency', 'accountability', 'public record']):
                score += 15
                
        elif content_type == 'expert':
            # Expert Content Quality
            if any(indicator in content_lower for indicator in ['credentials', 'qualifications', 'expertise']):
                score += 20
            if any(indicator in content_lower for indicator in ['analysis', 'assessment', 'evaluation']):
                score += 15
            if any(indicator in content_lower for indicator in ['evidence', 'research', 'studies']):
                score += 15
                
        else:
            # General Content Quality
            if any(indicator in content_lower for indicator in ['sources', 'references', 'citations']):
                score += 15
            if any(indicator in content_lower for indicator in ['fact-check', 'verified', 'confirmed']):
                score += 15
            if any(indicator in content_lower for indicator in ['evidence', 'data', 'research']):
                score += 10
        
        # Peer review indicators in content
        peer_review_indicators = [
            'peer reviewed', 'peer-reviewed', 'refereed journal',
            'editorial board', 'reviewer comments', 'submitted',
            'accepted for publication', 'journal of', 'proceedings of'
        ]
        
        if any(indicator in content_lower for indicator in peer_review_indicators):
            score += 20
        
        # DOI presence (indicates formal publication)
        if 'doi:' in content_lower or 'doi.org' in url_lower:
            score += 15
        
        # Publication metadata indicators
        if any(phrase in content_lower for phrase in ['volume', 'issue', 'pages', 'published']):
            score += 10
        
        # Authority indicators (content-based, not journal names)
        authority_indicators = [
            'expert consensus', 'scientific consensus', 'established science',
            'peer reviewed study', 'systematic review', 'meta-analysis',
            'authoritative source', 'definitive study', 'landmark research'
        ]
        
        if any(indicator in content_lower or indicator in title_lower for indicator in authority_indicators):
            score += 20
        
        # Publication stage indicators
        if 'preprint' in content_lower or 'pre-print' in content_lower:
            score += 5  # Still valuable, just not yet peer reviewed
        elif 'draft' in content_lower or 'preliminary' in content_lower:
            score += 2  # Early stage work
        
        return min(100.0, max(0.0, score))
    
    def assess_reproducibility(self, content: str, source_url: str) -> float:
        """Assess reproducibility indicators and methodological transparency"""
        
        content_lower = content.lower()
        score = 15.0  # Base score
        
        # Data availability indicators
        data_availability = [
            'data available', 'supplementary data', 'raw data',
            'dataset', 'data repository', 'github', 'figshare',
            'dryad', 'zenodo', 'open data'
        ]
        
        if any(indicator in content_lower for indicator in data_availability):
            score += 20
        
        # Code availability
        code_indicators = [
            'code available', 'github', 'source code', 'software',
            'reproducible', 'replication package'
        ]
        
        if any(indicator in content_lower for indicator in code_indicators):
            score += 15
        
        # Detailed methodology
        method_detail_indicators = [
            'detailed methods', 'protocol', 'step by step',
            'materials and methods', 'experimental design',
            'statistical analysis plan'
        ]
        
        if any(indicator in content_lower for indicator in method_detail_indicators):
            score += 15
        
        # Replication studies or validation
        replication_indicators = [
            'replicated', 'validated', 'confirmed', 'reproduced',
            'independent study', 'replication study'
        ]
        
        if any(indicator in content_lower for indicator in replication_indicators):
            score += 25
        
        # Multi-center or multi-site studies
        if any(phrase in content_lower for phrase in ['multi-center', 'multi-site', 'multicenter']):
            score += 10
        
        return min(100.0, score)
    
    def assess_citation_impact(self, content: str, source_url: str, source_title: str) -> float:
        """Assess citation patterns and academic impact indicators"""
        
        content_lower = content.lower()
        score = 20.0  # Base score
        
        # High citation count indicators (heuristic)
        citation_indicators = [
            'cited by', 'citations', 'highly cited', 'influential',
            'landmark study', 'seminal work', 'widely cited'
        ]
        
        if any(indicator in content_lower for indicator in citation_indicators):
            score += 15
        
        # Reference quality (many references indicates scholarly work)
        reference_count = len(re.findall(r'\[\d+\]|\(\d+\)|doi:', content_lower))
        if reference_count > 50:
            score += 20
        elif reference_count > 20:
            score += 15
        elif reference_count > 10:
            score += 10
        
        # Author credentials indicators
        credential_indicators = [
            'professor', 'phd', 'md', 'dr.', 'university',
            'institute', 'research center', 'department of'
        ]
        
        if any(indicator in content_lower for indicator in credential_indicators):
            score += 10
        
        # Multi-author collaboration (indicates peer review)
        author_indicators = re.findall(r'author|contributor|investigator', content_lower)
        if len(author_indicators) > 5:
            score += 10
        
        # Review article or authoritative source
        if any(phrase in content_lower for phrase in ['review article', 'comprehensive review', 'state of the art']):
            score += 15
        
        return min(100.0, score)
    
    def assess_transparency(self, content: str, source_url: str) -> float:
        """Assess transparency in methodology, funding, and conflicts of interest"""
        
        content_lower = content.lower()
        score = 25.0  # Base score
        
        # Funding disclosure
        funding_indicators = [
            'funded by', 'grant', 'funding', 'supported by',
            'financial support', 'acknowledgments', 'conflict of interest',
            'competing interests', 'no conflicts'
        ]
        
        if any(indicator in content_lower for indicator in funding_indicators):
            score += 15
        
        # Methodology transparency
        transparency_indicators = [
            'limitations', 'bias', 'assumptions', 'uncertainty',
            'confidence interval', 'margin of error', 'statistical power'
        ]
        
        if any(indicator in content_lower for indicator in transparency_indicators):
            score += 15
        
        # Data sharing and openness
        openness_indicators = [
            'open access', 'creative commons', 'free to read',
            'no paywall', 'publicly available'
        ]
        
        if any(indicator in content_lower for indicator in openness_indicators):
            score += 10
        
        # Author affiliations and contact
        if any(phrase in content_lower for phrase in ['corresponding author', 'contact', 'email', 'affiliation']):
            score += 5
        
        # Ethical approval
        if any(phrase in content_lower for phrase in ['ethics', 'irb', 'ethical approval', 'consent']):
            score += 10
        
        return min(100.0, score)
    
    def assess_temporal_consistency(self, content: str, source_url: str) -> float:
        """Assess temporal consistency and recency indicators"""
        
        content_lower = content.lower()
        score = 50.0  # Base score (neutral)
        
        # Publication date indicators (heuristic)
        current_year = 2024
        years = re.findall(r'\b(20\d{2})\b', content_lower)
        
        if years:
            most_recent_year = max([int(year) for year in years])
            years_old = current_year - most_recent_year
            
            if years_old <= 2:
                score += 25  # Very recent
            elif years_old <= 5:
                score += 15  # Recent
            elif years_old <= 10:
                score += 5   # Moderately recent
            else:
                score -= 10  # Older research
        
        # Update indicators
        update_indicators = [
            'updated', 'revised', 'amended', 'corrected',
            'latest version', 'current status'
        ]
        
        if any(indicator in content_lower for indicator in update_indicators):
            score += 10
        
        # Longitudinal or follow-up indicators
        if any(phrase in content_lower for phrase in ['follow-up', 'longitudinal', 'long-term']):
            score += 15
        
        return min(100.0, max(0.0, score))
    
    def assess_evidence_quality(self, content: str, source_url: str, source_title: str = "") -> EvidenceQualityMetrics:
        """Comprehensive evidence quality assessment using all dimensions"""
        
        print(f"Assessing evidence quality for: {source_title[:50]}...")
        
        # Detect content type for contextual assessment
        content_type = self._detect_content_type(content, source_url, source_title)
        
        # Assess all quality dimensions
        methodology_rigor = self.assess_methodology_rigor(content, source_url)
        peer_review_status = self.assess_peer_review_status(content, source_url, source_title)
        reproducibility = self.assess_reproducibility(content, source_url)
        citation_impact = self.assess_citation_impact(content, source_url, source_title)
        transparency = self.assess_transparency(content, source_url)
        temporal_consistency = self.assess_temporal_consistency(content, source_url)
        
        metrics = EvidenceQualityMetrics(
            methodology_rigor=methodology_rigor,
            peer_review_status=peer_review_status,
            reproducibility=reproducibility,
            citation_impact=citation_impact,
            transparency=transparency,
            temporal_consistency=temporal_consistency,
            content_type=content_type
        )
        
        print(f"Quality Assessment Complete - Overall: {metrics.overall_quality_score():.1f}, Tier: {metrics.quality_tier()}")
        
        return metrics
    
    def quality_weighted_stance_score(self, stance: str, quality_metrics: EvidenceQualityMetrics, relevance_score: float) -> float:
        """Calculate stance impact weighted by evidence quality"""
        
        overall_quality = quality_metrics.overall_quality_score()
        quality_weight = overall_quality / 100.0
        relevance_weight = relevance_score / 100.0 if relevance_score <= 1.0 else relevance_score / 100.0
        
        # Base stance impact
        stance_impacts = {
            'supporting': 1.0,
            'contradicting': -1.0,
            'neutral': 0.0
        }
        
        base_impact = stance_impacts.get(stance.lower(), 0.0)
        
        # Weight by quality and relevance
        weighted_impact = base_impact * quality_weight * relevance_weight
        
        print(f"Stance: {stance}, Quality: {overall_quality:.1f}, Relevance: {relevance_score:.1f}, Impact: {weighted_impact:.3f}")
        
        return weighted_impact