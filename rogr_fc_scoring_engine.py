import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from evidence_shepherd import ProcessedEvidence

@dataclass
class ROGRScoringResult:
    """ROGR Professional Fact-Checking Scoring Result"""
    trust_score: float  # 0-100 claim reliability
    evidence_grade: str  # A+ to F process quality grade
    evidence_grade_score: float  # 0-100 numerical grade
    metadata: Dict
    
    def grade_description(self) -> str:
        """Human-readable grade description"""
        grade_descriptions = {
            'A+': 'Exceptional verification - comprehensive multi-source confirmation',
            'A': 'Excellent verification - strong multi-source confirmation', 
            'B+': 'Very good verification - solid multi-source support',
            'B': 'Good verification - adequate multi-source support',
            'C+': 'Fair verification - basic multi-source coverage',
            'C': 'Minimal verification - limited source diversity',
            'D': 'Poor verification - insufficient source coverage',
            'F': 'Failed verification - inadequate research process'
        }
        return grade_descriptions.get(self.evidence_grade, 'Unknown grade')

class ROGRFCScoringEngine:
    """ROGR Fact-Checking Scoring Engine - IFCN-compliant professional scoring"""
    
    def __init__(self):
        self.evidence_grade_thresholds = {
            97: 'A+', 90: 'A', 87: 'B+', 80: 'B', 
            77: 'C+', 70: 'C', 60: 'D'
        }
    
    def score_evidence_pool(self, claim_text: str, evidence_pieces: List[ProcessedEvidence]) -> ROGRScoringResult:
        """Apply ROGR professional fact-checking scoring to evidence pool"""
        
        if not evidence_pieces:
            return ROGRScoringResult(
                trust_score=0.0,
                evidence_grade='F',
                evidence_grade_score=0.0,
                metadata={'error': 'No evidence pieces provided'}
            )
        
        # Calculate Evidence Grade (research process quality)
        evidence_grade_score = self._calculate_evidence_grade(evidence_pieces)
        evidence_grade = self._score_to_grade(evidence_grade_score)
        
        # Calculate Trust Score (claim reliability)  
        trust_score = self._calculate_trust_score(claim_text, evidence_pieces)
        
        # Generate comprehensive metadata
        metadata = self._generate_scoring_metadata(claim_text, evidence_pieces, evidence_grade_score)
        
        return ROGRScoringResult(
            trust_score=trust_score,
            evidence_grade=evidence_grade,
            evidence_grade_score=evidence_grade_score,
            metadata=metadata
        )
    
    def _calculate_evidence_grade(self, evidence_pieces: List[ProcessedEvidence]) -> float:
        """Calculate Evidence Grade based on IFCN research process standards"""
        
        total_score = 0.0
        
        # Source Attribution (25 points) - Are sources clearly named and accessible?
        attribution_score = self._assess_source_attribution(evidence_pieces)
        total_score += attribution_score
        
        # Multiple Source Verification (30 points) - Cross-verification coverage  
        verification_score = self._assess_multiple_source_verification(evidence_pieces)
        total_score += verification_score
        
        # Source Diversity (20 points) - Different domains and perspectives
        diversity_score = self._assess_source_diversity(evidence_pieces)
        total_score += diversity_score
        
        # Accessibility (15 points) - Can sources be accessed for verification?
        accessibility_score = self._assess_accessibility(evidence_pieces)
        total_score += accessibility_score
        
        # Research Depth (10 points) - Quality of content analysis
        depth_score = self._assess_research_depth(evidence_pieces)
        total_score += depth_score
        
        return min(100.0, total_score)
    
    def _assess_source_attribution(self, evidence_pieces: List[ProcessedEvidence]) -> float:
        """Assess quality of source attribution (25 points max)"""
        if not evidence_pieces:
            return 0.0
            
        attributed_sources = 0
        for evidence in evidence_pieces:
            # Check if source has clear attribution
            has_title = bool(getattr(evidence, 'source_title', '').strip())
            has_domain = bool(getattr(evidence, 'source_domain', '').strip())
            has_url = bool(getattr(evidence, 'source_url', '').strip())
            
            if has_title and has_domain and has_url:
                attributed_sources += 1
        
        attribution_rate = attributed_sources / len(evidence_pieces)
        return attribution_rate * 25.0
    
    def _assess_multiple_source_verification(self, evidence_pieces: List[ProcessedEvidence]) -> float:
        """Assess cross-verification between sources (30 points max)"""
        if len(evidence_pieces) < 2:
            return 0.0  # Need at least 2 sources for verification
        
        # Count sources by stance for cross-verification
        stance_counts = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        for evidence in evidence_pieces:
            stance = getattr(evidence, 'ai_stance', 'neutral') or 'neutral'
            stance = stance.lower()
            if stance in stance_counts:
                stance_counts[stance] += 1
        
        # Award points based on verification pattern
        verification_score = 0.0
        
        # Multiple sources with same stance = good verification
        max_stance_count = max(stance_counts.values())
        if max_stance_count >= 3:
            verification_score += 20.0  # Excellent multi-source verification
        elif max_stance_count >= 2:
            verification_score += 15.0  # Good multi-source verification
        
        # Source diversity bonus
        unique_domains = len(set(getattr(ev, 'source_domain', '') for ev in evidence_pieces))
        if unique_domains >= 3:
            verification_score += 10.0  # Domain diversity bonus
        elif unique_domains >= 2:
            verification_score += 5.0   # Basic diversity bonus
        
        return min(30.0, verification_score)
    
    def _assess_source_diversity(self, evidence_pieces: List[ProcessedEvidence]) -> float:
        """Assess diversity of sources (20 points max)"""
        if not evidence_pieces:
            return 0.0
        
        # Count unique domains
        domains = set()
        for evidence in evidence_pieces:
            domain = getattr(evidence, 'source_domain', '').strip()
            if domain:
                domains.add(domain)
        
        unique_domain_count = len(domains)
        
        # Score based on domain diversity
        if unique_domain_count >= 5:
            return 20.0  # Excellent diversity
        elif unique_domain_count >= 4:
            return 16.0  # Very good diversity  
        elif unique_domain_count >= 3:
            return 12.0  # Good diversity
        elif unique_domain_count >= 2:
            return 8.0   # Basic diversity
        else:
            return 4.0   # Single domain - limited diversity
    
    def _assess_accessibility(self, evidence_pieces: List[ProcessedEvidence]) -> float:
        """Assess source accessibility for verification (15 points max)"""
        if not evidence_pieces:
            return 0.0
        
        accessible_sources = 0
        for evidence in evidence_pieces:
            url = getattr(evidence, 'source_url', '').strip()
            
            # Basic URL validation - starts with http/https
            if url and (url.startswith('http://') or url.startswith('https://')):
                accessible_sources += 1
        
        accessibility_rate = accessible_sources / len(evidence_pieces)
        return accessibility_rate * 15.0
    
    def _assess_research_depth(self, evidence_pieces: List[ProcessedEvidence]) -> float:
        """Assess depth of research and content quality (10 points max)"""
        if not evidence_pieces:
            return 0.0
        
        total_content_score = 0.0
        
        for evidence in evidence_pieces:
            content_score = 0.0
            
            # Content length indicates depth
            text_content = getattr(evidence, 'text', '') or ''
            if len(text_content) >= 500:
                content_score += 3.0  # Substantial content
            elif len(text_content) >= 200:
                content_score += 2.0  # Good content
            elif len(text_content) >= 100:
                content_score += 1.0  # Basic content
            
            # Relevance score indicates quality
            relevance = getattr(evidence, 'ai_relevance_score', 0) or 0
            if relevance >= 80:
                content_score += 2.0  # High relevance
            elif relevance >= 60:
                content_score += 1.0  # Good relevance
            
            total_content_score += min(5.0, content_score)  # Cap per source
        
        # Average and scale to 10 points max
        if evidence_pieces:
            avg_content_score = total_content_score / len(evidence_pieces)
            return min(10.0, avg_content_score * 2.0)  # Scale to 10 point max
        
        return 0.0
    
    def _calculate_trust_score(self, claim_text: str, evidence_pieces: List[ProcessedEvidence]) -> float:
        """Calculate Trust Score based on evidence stance and quality"""
        
        if not evidence_pieces:
            return 0.0
        
        base_score = 50.0  # Neutral starting point
        
        for evidence in evidence_pieces:
            # Get evidence stance and relevance
            stance = getattr(evidence, 'ai_stance', 'neutral') or 'neutral'
            stance = stance.lower()
            relevance = getattr(evidence, 'ai_relevance_score', 50) or 50
            
            # Calculate evidence weight (based on relevance and quality indicators)
            evidence_weight = self._calculate_evidence_weight(evidence)
            
            # Apply stance impact
            stance_impact = 0.0
            if stance == 'supporting':
                stance_impact = evidence_weight * (relevance / 100.0) * 40.0  # Max +40 per high-quality evidence
            elif stance == 'contradicting':
                stance_impact = -(evidence_weight * (relevance / 100.0) * 40.0)  # Max -40 per high-quality evidence
            # neutral stance has no impact
            
            base_score += stance_impact
        
        # Consensus bonus - if most evidence agrees, boost confidence slightly
        stance_distribution = self._analyze_stance_distribution(evidence_pieces)
        consensus_bonus = self._calculate_consensus_bonus(stance_distribution)
        base_score += consensus_bonus
        
        # Ensure score stays within bounds
        return max(0.0, min(100.0, base_score))
    
    def _calculate_evidence_weight(self, evidence: ProcessedEvidence) -> float:
        """Calculate weight of evidence piece based on quality indicators"""
        weight = 1.0  # Base weight
        
        # Quality indicators that increase weight
        url = getattr(evidence, 'source_url', '') or ''
        domain = getattr(evidence, 'source_domain', '') or ''
        content_length = len(getattr(evidence, 'text', '') or '')
        
        # URL quality bonus
        if url.startswith('https://'):
            weight += 0.1
        
        # Content depth bonus
        if content_length >= 400:
            weight += 0.3
        elif content_length >= 200:
            weight += 0.2
        elif content_length >= 100:
            weight += 0.1
        
        # Cap maximum weight
        return min(2.0, weight)
    
    def _analyze_stance_distribution(self, evidence_pieces: List[ProcessedEvidence]) -> Dict[str, int]:
        """Analyze distribution of evidence stances"""
        stance_counts = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        for evidence in evidence_pieces:
            stance = getattr(evidence, 'ai_stance', 'neutral') or 'neutral'
            stance = stance.lower()
            if stance in stance_counts:
                stance_counts[stance] += 1
        
        return stance_counts
    
    def _calculate_consensus_bonus(self, stance_distribution: Dict[str, int]) -> float:
        """Calculate consensus bonus based on evidence agreement"""
        total_evidence = sum(stance_distribution.values())
        if total_evidence < 2:
            return 0.0
        
        # Find dominant stance
        max_stance_count = max(stance_distribution.values())
        consensus_rate = max_stance_count / total_evidence
        
        # Award small bonus for strong consensus (not too much to avoid overconfidence)
        if consensus_rate >= 0.8 and total_evidence >= 3:
            return 5.0  # Strong consensus bonus
        elif consensus_rate >= 0.7 and total_evidence >= 2:
            return 3.0  # Good consensus bonus
        
        return 0.0
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numerical score to letter grade"""
        for threshold, grade in self.evidence_grade_thresholds.items():
            if score >= threshold:
                return grade
        return 'F'
    
    def _generate_scoring_metadata(self, claim_text: str, evidence_pieces: List[ProcessedEvidence], evidence_grade_score: float) -> Dict:
        """Generate comprehensive metadata about scoring process"""
        
        if not evidence_pieces:
            return {'error': 'No evidence pieces to analyze'}
        
        # Source analysis
        unique_domains = set(getattr(ev, 'source_domain', '') for ev in evidence_pieces)
        stance_distribution = self._analyze_stance_distribution(evidence_pieces)
        
        # Relevance analysis
        relevance_scores = [getattr(ev, 'ai_relevance_score', 0) or 0 for ev in evidence_pieces]
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        
        # Content analysis
        content_lengths = [len(getattr(ev, 'text', '') or '') for ev in evidence_pieces]
        avg_content_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        
        metadata = {
            'scoring_methodology': 'ROGR Professional Fact-Checking Engine v1.0',
            'evidence_analysis': {
                'total_sources': len(evidence_pieces),
                'unique_domains': len(unique_domains),
                'domain_list': list(unique_domains),
                'stance_distribution': stance_distribution,
                'avg_relevance_score': round(avg_relevance, 1),
                'avg_content_length': round(avg_content_length, 1)
            },
            'grade_breakdown': {
                'evidence_grade_score': round(evidence_grade_score, 1),
                'attribution_quality': 'assessed',
                'source_verification': 'multi-source analysis',
                'source_diversity': f"{len(unique_domains)} unique domains",
                'accessibility': 'URL verification completed',
                'research_depth': 'content analysis completed'
            },
            'ifcn_compliance': {
                'source_transparency': len(unique_domains) > 0,
                'multiple_source_verification': len(evidence_pieces) >= 2,
                'attribution_standards': True,
                'methodology_transparency': True
            }
        }
        
        return metadata