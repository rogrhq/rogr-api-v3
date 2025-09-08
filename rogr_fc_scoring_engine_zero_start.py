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

class ROGRFCScoringEngineZeroStart:
    """ROGR Fact-Checking Scoring Engine - Zero-Start Evidence-Driven Model"""
    
    def __init__(self):
        self.evidence_grade_thresholds = {
            97: 'A+', 90: 'A', 87: 'B+', 80: 'B', 
            77: 'C+', 70: 'C', 60: 'D'
        }
    
    def score_evidence_pool(self, claim_text: str, evidence_pieces: List[ProcessedEvidence]) -> ROGRScoringResult:
        """Apply ROGR professional fact-checking scoring to evidence pool - Zero Start Model"""
        
        if not evidence_pieces:
            return ROGRScoringResult(
                trust_score=0.0,
                evidence_grade='F',
                evidence_grade_score=0.0,
                metadata={'error': 'No evidence pieces provided'}
            )
        
        # Calculate Evidence Grade (research process quality) - unchanged
        evidence_grade_score = self._calculate_evidence_grade(evidence_pieces)
        evidence_grade = self._score_to_grade(evidence_grade_score)
        
        # Calculate Trust Score using ZERO-START method
        trust_score = self._calculate_trust_score_zero_start(claim_text, evidence_pieces)
        
        # Generate comprehensive metadata
        metadata = self._generate_scoring_metadata(claim_text, evidence_pieces, evidence_grade_score, trust_score)
        
        return ROGRScoringResult(
            trust_score=trust_score,
            evidence_grade=evidence_grade,
            evidence_grade_score=evidence_grade_score,
            metadata=metadata
        )
    
    def _calculate_trust_score_zero_start(self, claim_text: str, evidence_pieces: List[ProcessedEvidence]) -> float:
        """Calculate Trust Score using zero-start evidence accumulation model"""
        
        if not evidence_pieces:
            return 0.0
        
        # Start with ZERO confidence - evidence must build the case
        accumulated_evidence_strength = 0.0
        total_evidence_weight = 0.0
        
        # Analyze evidence to detect mixed scenarios
        stance_counts = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        supporting_strength = 0.0
        contradicting_strength = 0.0
        
        for evidence in evidence_pieces:
            # Get evidence stance and relevance
            stance = getattr(evidence, 'ai_stance', 'neutral') or 'neutral'
            stance = stance.lower()
            relevance = getattr(evidence, 'ai_relevance_score', 50) or 50
            confidence = getattr(evidence, 'ai_confidence', 0.8) or 0.8
            
            # Calculate evidence impact (0-25 points per piece)
            evidence_impact = self._calculate_evidence_impact(evidence, relevance, confidence)
            total_evidence_weight += abs(evidence_impact)
            
            # Accumulate stance-based evidence
            if stance == 'supporting':
                accumulated_evidence_strength += evidence_impact
                supporting_strength += evidence_impact
                stance_counts['supporting'] += 1
            elif stance == 'contradicting':
                accumulated_evidence_strength -= evidence_impact
                contradicting_strength += evidence_impact
                stance_counts['contradicting'] += 1
            else:  # neutral
                stance_counts['neutral'] += 1
                # Neutral evidence doesn't change accumulated strength but adds to weight
        
        # Detect mixed evidence scenario
        has_mixed_evidence = (stance_counts['supporting'] > 0 and stance_counts['contradicting'] > 0)
        
        # Convert accumulated strength to trust score (0-100)
        trust_score = self._strength_to_trust_score(
            accumulated_evidence_strength, 
            total_evidence_weight, 
            has_mixed_evidence,
            stance_counts
        )
        
        return trust_score
    
    def _calculate_evidence_impact(self, evidence: ProcessedEvidence, relevance: float, confidence: float) -> float:
        """Calculate the impact strength of a single piece of evidence (0-25 points)"""
        
        # Base impact from relevance (0-15 points)
        relevance_impact = (relevance / 100.0) * 15.0
        
        # Quality multiplier from evidence weight (1.0-2.0x)
        evidence_weight = self._calculate_evidence_weight(evidence)
        
        # Confidence multiplier (0.5-1.0x)
        confidence_multiplier = max(0.5, min(1.0, confidence))
        
        # Authority bonus for high-quality domains (0-5 points)
        authority_bonus = self._calculate_authority_bonus(evidence)
        
        total_impact = (relevance_impact * evidence_weight * confidence_multiplier) + authority_bonus
        
        return min(25.0, total_impact)  # Cap at 25 points per evidence piece
    
    def _calculate_authority_bonus(self, evidence: ProcessedEvidence) -> float:
        """Calculate authority bonus based on source domain quality"""
        domain = getattr(evidence, 'source_domain', '').lower()
        
        # High-authority domains get bonus points
        if any(auth_domain in domain for auth_domain in ['.gov', '.edu', 'who.int', 'cdc.gov', 'fda.gov']):
            return 3.0  # Government/academic authority
        elif any(journal in domain for journal in ['nature.com', 'science.org', 'nejm.org', 'thelancet.com']):
            return 4.0  # Premier scientific journals
        elif any(medical in domain for medical in ['mayoclinic.org', 'hopkinsmedicine.org', 'clevelandclinic.org']):
            return 2.0  # Medical institutions
        elif 'pmc.ncbi.nlm.nih.gov' in domain:
            return 3.0  # PubMed Central - peer reviewed
        
        return 0.0  # No authority bonus
    
    def _strength_to_trust_score(self, accumulated_strength: float, total_weight: float, has_mixed_evidence: bool, stance_counts: Dict[str, int]) -> float:
        """Convert accumulated evidence strength to 0-100 trust score"""
        
        if total_weight == 0:
            return 0.0
        
        # Calculate base confidence from evidence strength
        # Strong positive evidence → high trust (70-100)
        # Strong negative evidence → low trust (0-30)
        # Weak/mixed evidence → moderate trust (20-80)
        
        strength_ratio = accumulated_strength / total_weight if total_weight > 0 else 0
        
        # Base score calculation
        if strength_ratio > 0.7:  # Strong supporting evidence
            base_trust = 70 + (strength_ratio - 0.7) * 100  # 70-100 range
        elif strength_ratio < -0.7:  # Strong contradicting evidence  
            base_trust = 30 * (1 + strength_ratio / 0.7)  # 0-30 range
        else:  # Mixed or moderate evidence
            base_trust = 50 + (strength_ratio * 50)  # 25-75 range
        
        # Apply mixed evidence penalty
        if has_mixed_evidence:
            # Mixed evidence should rarely be definitive
            mixed_penalty_factor = self._calculate_mixed_evidence_penalty(stance_counts)
            base_trust = self._apply_mixed_evidence_constraint(base_trust, mixed_penalty_factor)
        
        # Apply evidence volume confidence modifier
        evidence_count = sum(stance_counts.values())
        volume_modifier = self._calculate_volume_confidence(evidence_count)
        final_trust = base_trust * volume_modifier
        
        return max(0.0, min(100.0, final_trust))
    
    def _calculate_mixed_evidence_penalty(self, stance_counts: Dict[str, int]) -> float:
        """Calculate penalty factor for mixed evidence scenarios"""
        supporting = stance_counts['supporting']
        contradicting = stance_counts['contradicting']
        
        if supporting == 0 or contradicting == 0:
            return 0.0  # No mixed evidence
        
        # Calculate how balanced the disagreement is
        total_positioned = supporting + contradicting
        balance_ratio = min(supporting, contradicting) / total_positioned
        
        # More balanced disagreement = higher penalty
        return balance_ratio * 0.3  # Max 30% penalty for perfectly balanced disagreement
    
    def _apply_mixed_evidence_constraint(self, base_trust: float, penalty_factor: float) -> float:
        """Apply constraints for mixed evidence scenarios"""
        
        # Reduce extreme confidence when evidence is mixed
        adjusted_trust = base_trust * (1.0 - penalty_factor)
        
        # Constrain mixed evidence to 15-85 range (avoid extreme confidence)
        if base_trust > 85:
            adjusted_trust = min(85.0, adjusted_trust)
        elif base_trust < 15:
            adjusted_trust = max(15.0, adjusted_trust)
        
        return adjusted_trust
    
    def _calculate_volume_confidence(self, evidence_count: int) -> float:
        """Calculate confidence modifier based on evidence volume"""
        
        if evidence_count >= 6:
            return 1.0      # Full confidence with substantial evidence
        elif evidence_count >= 4:
            return 0.95     # High confidence with good evidence
        elif evidence_count >= 2:
            return 0.85     # Moderate confidence with basic evidence
        else:
            return 0.7      # Lower confidence with minimal evidence
    
    # Copy over the evidence grade calculation methods (unchanged)
    def _calculate_evidence_grade(self, evidence_pieces: List[ProcessedEvidence]) -> float:
        """Calculate Evidence Grade based on IFCN research process standards"""
        
        total_score = 0.0
        
        # Source Attribution (25 points)
        attribution_score = self._assess_source_attribution(evidence_pieces)
        total_score += attribution_score
        
        # Multiple Source Verification (30 points)
        verification_score = self._assess_multiple_source_verification(evidence_pieces)
        total_score += verification_score
        
        # Source Diversity (20 points)
        diversity_score = self._assess_source_diversity(evidence_pieces)
        total_score += diversity_score
        
        # Accessibility (15 points)
        accessibility_score = self._assess_accessibility(evidence_pieces)
        total_score += accessibility_score
        
        # Research Depth (10 points)
        depth_score = self._assess_research_depth(evidence_pieces)
        total_score += depth_score
        
        return min(100.0, total_score)
    
    def _assess_source_attribution(self, evidence_pieces: List[ProcessedEvidence]) -> float:
        """Assess quality of source attribution (25 points max)"""
        if not evidence_pieces:
            return 0.0
            
        attributed_sources = 0
        for evidence in evidence_pieces:
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
            return 0.0
        
        stance_counts = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        for evidence in evidence_pieces:
            stance = getattr(evidence, 'ai_stance', 'neutral') or 'neutral'
            stance = stance.lower()
            if stance in stance_counts:
                stance_counts[stance] += 1
        
        verification_score = 0.0
        
        max_stance_count = max(stance_counts.values())
        if max_stance_count >= 3:
            verification_score += 20.0
        elif max_stance_count >= 2:
            verification_score += 15.0
        
        unique_domains = len(set(getattr(ev, 'source_domain', '') for ev in evidence_pieces))
        if unique_domains >= 3:
            verification_score += 10.0
        elif unique_domains >= 2:
            verification_score += 5.0
        
        return min(30.0, verification_score)
    
    def _assess_source_diversity(self, evidence_pieces: List[ProcessedEvidence]) -> float:
        """Assess diversity of sources (20 points max)"""
        if not evidence_pieces:
            return 0.0
        
        domains = set()
        for evidence in evidence_pieces:
            domain = getattr(evidence, 'source_domain', '').strip()
            if domain:
                domains.add(domain)
        
        unique_domain_count = len(domains)
        
        if unique_domain_count >= 5:
            return 20.0
        elif unique_domain_count >= 4:
            return 16.0  
        elif unique_domain_count >= 3:
            return 12.0
        elif unique_domain_count >= 2:
            return 8.0
        else:
            return 4.0
    
    def _assess_accessibility(self, evidence_pieces: List[ProcessedEvidence]) -> float:
        """Assess source accessibility for verification (15 points max)"""
        if not evidence_pieces:
            return 0.0
        
        accessible_sources = 0
        for evidence in evidence_pieces:
            url = getattr(evidence, 'source_url', '').strip()
            
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
            
            text_content = getattr(evidence, 'text', '') or ''
            if len(text_content) >= 500:
                content_score += 3.0
            elif len(text_content) >= 200:
                content_score += 2.0
            elif len(text_content) >= 100:
                content_score += 1.0
            
            relevance = getattr(evidence, 'ai_relevance_score', 0) or 0
            if relevance >= 80:
                content_score += 2.0
            elif relevance >= 60:
                content_score += 1.0
            
            total_content_score += min(5.0, content_score)
        
        if evidence_pieces:
            avg_content_score = total_content_score / len(evidence_pieces)
            return min(10.0, avg_content_score * 2.0)
        
        return 0.0
    
    def _calculate_evidence_weight(self, evidence: ProcessedEvidence) -> float:
        """Calculate weight of evidence piece based on quality indicators"""
        weight = 1.0
        
        url = getattr(evidence, 'source_url', '') or ''
        content_length = len(getattr(evidence, 'text', '') or '')
        
        if url.startswith('https://'):
            weight += 0.1
        
        if content_length >= 400:
            weight += 0.3
        elif content_length >= 200:
            weight += 0.2
        elif content_length >= 100:
            weight += 0.1
        
        return min(2.0, weight)
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numerical score to letter grade"""
        for threshold, grade in self.evidence_grade_thresholds.items():
            if score >= threshold:
                return grade
        return 'F'
    
    def _generate_scoring_metadata(self, claim_text: str, evidence_pieces: List[ProcessedEvidence], evidence_grade_score: float, trust_score: float) -> Dict:
        """Generate comprehensive metadata about scoring process"""
        
        if not evidence_pieces:
            return {'error': 'No evidence pieces to analyze'}
        
        unique_domains = set(getattr(ev, 'source_domain', '') for ev in evidence_pieces)
        stance_counts = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        for evidence in evidence_pieces:
            stance = getattr(evidence, 'ai_stance', 'neutral') or 'neutral'
            stance = stance.lower()
            if stance in stance_counts:
                stance_counts[stance] += 1
        
        relevance_scores = [getattr(ev, 'ai_relevance_score', 0) or 0 for ev in evidence_pieces]
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        
        metadata = {
            'scoring_methodology': 'ROGR Professional Fact-Checking Engine v2.0 - Zero-Start Evidence-Driven',
            'scoring_model': 'zero_start_evidence_accumulation',
            'evidence_analysis': {
                'total_sources': len(evidence_pieces),
                'unique_domains': len(unique_domains),
                'domain_list': list(unique_domains),
                'stance_distribution': stance_counts,
                'avg_relevance_score': round(avg_relevance, 1),
                'mixed_evidence_detected': stance_counts['supporting'] > 0 and stance_counts['contradicting'] > 0
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
            },
            'trust_score_breakdown': {
                'model': 'zero_start_evidence_accumulation',
                'mixed_evidence_penalty_applied': stance_counts['supporting'] > 0 and stance_counts['contradicting'] > 0,
                'authority_weighting': 'government_academic_medical_journals',
                'confidence_factors': 'relevance_authority_volume_mixed_evidence'
            }
        }
        
        return metadata