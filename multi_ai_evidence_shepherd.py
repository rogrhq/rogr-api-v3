import os
import json
import asyncio
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import requests
from evidence_shepherd import EvidenceShepherd, SearchStrategy, EvidenceCandidate, ProcessedEvidence, ClaimType
from claude_evidence_shepherd import ClaudeEvidenceShepherd
from ai_evidence_shepherd import OpenAIEvidenceShepherd
from evidence_shepherd import NoOpEvidenceShepherd
from evidence_quality_assessor import EvidenceQualityAssessor, EvidenceQualityMetrics

@dataclass
class AIConsensusResult:
    """Result from multi-AI consensus analysis"""
    consensus_score: float  # 0-100 weighted consensus confidence
    individual_scores: List[Tuple[str, float]]  # [(ai_name, score), ...]
    disagreement_level: float  # 0-100 how much AIs disagree
    consensus_stance: str  # overall stance consensus
    quality_weighted_score: float  # final score weighted by evidence quality
    uncertainty_indicators: List[str]  # areas of AI disagreement
    evidence_quality_summary: Dict[str, float]  # quality metrics summary

class MultiAIEvidenceShepherd(EvidenceShepherd):
    """Multi-AI Evidence Shepherd with consensus scoring for bias prevention"""
    
    def is_enabled(self) -> bool:
        """Check if Multi-AI Evidence Shepherd is enabled"""
        return len(self.ai_shepherds) > 0
    
    def analyze_claim(self, claim_text: str, claim_type: ClaimType) -> float:
        """Analyze claim - use first available shepherd"""
        if self.ai_shepherds:
            if hasattr(self.ai_shepherds[0], 'analyze_claim'):
                return self.ai_shepherds[0].analyze_claim(claim_text, claim_type)
        return 0.5  # Default neutral
    
    def filter_evidence_batch(self, evidence_candidates: List[EvidenceCandidate], max_count: int = 5) -> List[EvidenceCandidate]:
        """Filter evidence batch - use first available shepherd"""
        if self.ai_shepherds:
            if hasattr(self.ai_shepherds[0], 'filter_evidence_batch'):
                return self.ai_shepherds[0].filter_evidence_batch(evidence_candidates, max_count)
        return evidence_candidates[:max_count]  # Default limit
    
    def score_evidence_relevance(self, evidence: EvidenceCandidate, claim_text: str) -> float:
        """Score evidence relevance - use first available shepherd"""
        if self.ai_shepherds:
            if hasattr(self.ai_shepherds[0], 'score_evidence_relevance'):
                return self.ai_shepherds[0].score_evidence_relevance(evidence, claim_text)
        return 0.5  # Default medium relevance
    
    def __init__(self):
        # Initialize available AI shepherds
        self.ai_shepherds = []
        self.ai_names = []
        
        # Try to initialize Claude
        if os.getenv('ANTHROPIC_API_KEY'):
            try:
                claude_shepherd = ClaudeEvidenceShepherd()
                self.ai_shepherds.append(claude_shepherd)
                self.ai_names.append("Claude")
            except Exception as e:
                print(f"Could not initialize Claude shepherd: {e}")
        
        # Try to initialize OpenAI
        if os.getenv('OPENAI_API_KEY'):
            try:
                openai_shepherd = OpenAIEvidenceShepherd()
                self.ai_shepherds.append(openai_shepherd)
                self.ai_names.append("OpenAI")
            except Exception as e:
                print(f"Could not initialize OpenAI shepherd: {e}")
        
        # Fallback to NoOp if no AI available
        if not self.ai_shepherds:
            self.ai_shepherds.append(NoOpEvidenceShepherd())
            self.ai_names.append("NoOp")
        
        # Initialize evidence quality assessor
        self.quality_assessor = EvidenceQualityAssessor()
        
        print(f"Multi-AI Evidence Shepherd initialized with {len(self.ai_shepherds)} AI models: {self.ai_names}")
    
    def get_search_strategy(self, claim_text: str) -> SearchStrategy:
        """Get search strategy - use first available AI shepherd"""
        # ClaudeEvidenceShepherd uses analyze_claim() to return SearchStrategy
        if hasattr(self.ai_shepherds[0], 'analyze_claim'):
            return self.ai_shepherds[0].analyze_claim(claim_text)
        else:
            # Fallback to minimal strategy
            return SearchStrategy.SCIENTIFIC
    
    async def find_evidence_for_claim(self, claim_text: str, search_strategy: SearchStrategy, context: Dict = None) -> ProcessedEvidence:
        """Find evidence using multi-AI consensus approach adapted for ClaudeEvidenceShepherd interface"""
        
        print(f"Starting multi-AI consensus analysis for claim: {claim_text[:50]}...")
        
        # Collect evidence from all available AI shepherds using their actual methods
        ai_evidence_lists = []
        
        for i, (ai_shepherd, ai_name) in enumerate(zip(self.ai_shepherds, self.ai_names)):
            try:
                print(f"Getting evidence from {ai_name}...")
                
                # Use the actual methods available in ClaudeEvidenceShepherd
                if hasattr(ai_shepherd, 'search_real_evidence'):
                    # ClaudeEvidenceShepherd method
                    evidence_list = ai_shepherd.search_real_evidence(claim_text)
                    ai_evidence_lists.append((ai_name, evidence_list))
                    print(f"{ai_name} found {len(evidence_list)} pieces of evidence")
                elif hasattr(ai_shepherd, 'find_evidence_for_claim'):
                    # If other shepherds have this method
                    result = await ai_shepherd.find_evidence_for_claim(claim_text, search_strategy, context)
                    ai_evidence_lists.append((ai_name, result.evidence_pieces if hasattr(result, 'evidence_pieces') else []))
                    print(f"{ai_name} found evidence")
                else:
                    print(f"{ai_name} doesn't have supported evidence methods")
                    continue
                    
            except Exception as e:
                print(f"Error getting evidence from {ai_name}: {e}")
                continue
        
        if not ai_evidence_lists:
            print("No AI shepherds returned evidence - returning empty result")
            return ProcessedEvidence(
                claim_text=claim_text,
                evidence_pieces=[],
                confidence_score=0.0,
                search_queries_used=[],
                total_sources_found=0
            )
        
        # Convert evidence lists to the format expected by consensus analysis
        ai_results_converted = []
        for ai_name, evidence_list in ai_evidence_lists:
            # Create a mock ProcessedEvidence result for consensus analysis
            mock_result = ProcessedEvidence(
                claim_text=claim_text,
                evidence_pieces=evidence_list,
                confidence_score=50.0,  # Will be recalculated by consensus
                search_queries_used=[f"{ai_name}_search"],
                total_sources_found=len(evidence_list)
            )
            ai_results_converted.append((ai_name, mock_result))
        
        # Perform consensus analysis with quality assessment
        consensus_result = await self._analyze_consensus(claim_text, ai_results_converted)
        
        # Merge evidence pieces from all AIs
        all_evidence_pieces = []
        all_search_queries = []
        total_sources = 0
        
        for ai_name, evidence_list in ai_evidence_lists:
            all_evidence_pieces.extend(evidence_list)
            all_search_queries.append(f"{ai_name}_multi_search")
            total_sources += len(evidence_list)
        
        # Deduplicate evidence pieces by URL
        unique_evidence = {}
        for evidence in all_evidence_pieces:
            if evidence.source_url not in unique_evidence:
                unique_evidence[evidence.source_url] = evidence
            else:
                # Keep the one with higher relevance score
                if evidence.relevance_score > unique_evidence[evidence.source_url].relevance_score:
                    unique_evidence[evidence.source_url] = evidence
        
        final_evidence_pieces = list(unique_evidence.values())
        
        # Apply evidence quality weighting to final confidence score
        final_confidence_score = consensus_result.quality_weighted_score
        
        print(f"Multi-AI consensus complete - Final score: {final_confidence_score:.1f}, Evidence pieces: {len(final_evidence_pieces)}")
        
        return ProcessedEvidence(
            claim_text=claim_text,
            evidence_pieces=final_evidence_pieces,
            confidence_score=final_confidence_score,
            search_queries_used=list(set(all_search_queries)),
            total_sources_found=total_sources,
            # Store consensus metadata for advanced features
            consensus_metadata={
                'ai_consensus': consensus_result.consensus_score,
                'disagreement_level': consensus_result.disagreement_level,
                'individual_scores': consensus_result.individual_scores,
                'uncertainty_indicators': consensus_result.uncertainty_indicators,
                'evidence_quality_summary': consensus_result.evidence_quality_summary
            }
        )
    
    async def _analyze_consensus(self, claim_text: str, ai_results: List[Tuple[str, ProcessedEvidence]]) -> AIConsensusResult:
        """Analyze consensus between multiple AI assessments"""
        
        individual_scores = []
        stance_votes = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        all_evidence_pieces = []
        
        # Collect individual AI assessments
        for ai_name, result in ai_results:
            individual_scores.append((ai_name, result.confidence_score))
            all_evidence_pieces.extend(result.evidence_pieces)
            
            # Count stance votes based on evidence
            for evidence in result.evidence_pieces:
                if hasattr(evidence, 'ai_stance') and evidence.ai_stance:
                    stance_votes[evidence.ai_stance.lower()] = stance_votes.get(evidence.ai_stance.lower(), 0) + 1
                elif hasattr(evidence, 'stance') and evidence.stance:
                    stance_votes[evidence.stance.lower()] = stance_votes.get(evidence.stance.lower(), 0) + 1
        
        # Calculate consensus score (agreement level)
        if len(individual_scores) > 1:
            scores = [score for _, score in individual_scores]
            mean_score = sum(scores) / len(scores)
            score_variance = sum([(score - mean_score) ** 2 for score in scores]) / len(scores)
            disagreement_level = min(100.0, score_variance)
            consensus_score = max(0.0, 100.0 - disagreement_level)
        else:
            consensus_score = 100.0  # Perfect consensus with one AI
            disagreement_level = 0.0
        
        # Determine consensus stance
        max_stance = max(stance_votes.items(), key=lambda x: x[1])
        consensus_stance = max_stance[0] if max_stance[1] > 0 else 'neutral'
        
        # Apply evidence quality assessment
        quality_scores = []
        quality_weighted_impacts = []
        
        print(f"Assessing quality for {len(all_evidence_pieces)} evidence pieces...")
        
        for evidence in all_evidence_pieces[:6]:  # Limit to prevent timeout
            try:
                # Assess evidence quality using ProcessedEvidence attributes
                evidence_text = evidence.text if hasattr(evidence, 'text') else getattr(evidence, 'key_excerpt', '')
                evidence_url = evidence.source_url if hasattr(evidence, 'source_url') else ''
                evidence_title = evidence.source_title if hasattr(evidence, 'source_title') else ''
                
                quality_metrics = self.quality_assessor.assess_evidence_quality(
                    evidence_text,
                    evidence_url,
                    evidence_title
                )
                
                quality_scores.append(quality_metrics.overall_quality_score())
                
                # Calculate quality-weighted impact  
                evidence_stance = 'neutral'
                if hasattr(evidence, 'ai_stance') and evidence.ai_stance:
                    evidence_stance = evidence.ai_stance
                elif hasattr(evidence, 'stance') and evidence.stance:
                    evidence_stance = evidence.stance
                
                evidence_relevance = evidence.ai_relevance_score if hasattr(evidence, 'ai_relevance_score') else getattr(evidence, 'relevance_score', 50)
                
                weighted_impact = self.quality_assessor.quality_weighted_stance_score(
                    evidence_stance,
                    quality_metrics,
                    evidence_relevance
                )
                
                quality_weighted_impacts.append(weighted_impact)
                
            except Exception as e:
                print(f"Error assessing evidence quality: {e}")
                quality_scores.append(50.0)  # Default medium quality
                quality_weighted_impacts.append(0.0)  # Neutral impact
        
        # Calculate final quality-weighted score
        if quality_weighted_impacts:
            # Aggregate quality-weighted impacts
            total_impact = sum(quality_weighted_impacts)
            avg_quality = sum(quality_scores) / len(quality_scores)
            
            # Convert impact to confidence score
            # Positive impact (supporting) increases confidence
            # Negative impact (contradicting) decreases confidence
            # Weight by average evidence quality
            
            base_score = 50.0  # Neutral starting point
            impact_adjustment = total_impact * 30.0  # Scale impact
            quality_adjustment = (avg_quality - 50.0) * 0.3  # Quality bonus/penalty
            
            quality_weighted_score = base_score + impact_adjustment + quality_adjustment
            quality_weighted_score = max(0.0, min(100.0, quality_weighted_score))
        else:
            quality_weighted_score = sum([score for _, score in individual_scores]) / len(individual_scores)
        
        # Generate uncertainty indicators
        uncertainty_indicators = []
        if disagreement_level > 30:
            uncertainty_indicators.append(f"High AI disagreement ({disagreement_level:.1f})")
        if len(quality_scores) > 0 and min(quality_scores) < 40:
            uncertainty_indicators.append("Low quality evidence detected")
        if abs(total_impact) < 0.1:
            uncertainty_indicators.append("Weak evidence stance patterns")
        
        # Evidence quality summary
        evidence_quality_summary = {
            'avg_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 50.0,
            'high_quality_count': len([q for q in quality_scores if q >= 70]),
            'low_quality_count': len([q for q in quality_scores if q < 40]),
            'total_weighted_impact': total_impact
        }
        
        print(f"Consensus Analysis Complete:")
        print(f"  - Consensus Score: {consensus_score:.1f}")
        print(f"  - Quality Weighted Score: {quality_weighted_score:.1f}")
        print(f"  - Average Evidence Quality: {evidence_quality_summary['avg_quality_score']:.1f}")
        print(f"  - Disagreement Level: {disagreement_level:.1f}")
        
        return AIConsensusResult(
            consensus_score=consensus_score,
            individual_scores=individual_scores,
            disagreement_level=disagreement_level,
            consensus_stance=consensus_stance,
            quality_weighted_score=quality_weighted_score,
            uncertainty_indicators=uncertainty_indicators,
            evidence_quality_summary=evidence_quality_summary
        )
    
    def supports_focus_analysis(self) -> bool:
        """Check if any underlying shepherd supports focus analysis"""
        return any(hasattr(shepherd, 'supports_focus_analysis') and shepherd.supports_focus_analysis() 
                  for shepherd in self.ai_shepherds)
    
    async def perform_focus_analysis(self, original_evidence: ProcessedEvidence, focus_layers: List[str], context: Dict = None) -> ProcessedEvidence:
        """Perform focus analysis using consensus approach"""
        
        # Use the first available AI shepherd that supports focus analysis
        for shepherd in self.ai_shepherds:
            if hasattr(shepherd, 'perform_focus_analysis'):
                try:
                    return await shepherd.perform_focus_analysis(original_evidence, focus_layers, context)
                except Exception as e:
                    print(f"Focus analysis failed with {shepherd.__class__.__name__}: {e}")
                    continue
        
        # Fallback - return original evidence with version increment
        return ProcessedEvidence(
            claim_text=original_evidence.claim_text,
            evidence_pieces=original_evidence.evidence_pieces,
            confidence_score=original_evidence.confidence_score,
            search_queries_used=original_evidence.search_queries_used + ["focus analysis attempted"],
            total_sources_found=original_evidence.total_sources_found
        )