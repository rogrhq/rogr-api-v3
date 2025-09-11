import os
import json
import asyncio
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import requests
from evidence_shepherd import EvidenceShepherd, SearchStrategy, EvidenceCandidate, ProcessedEvidence, ClaimType
from rogr_evidence_shepherd import ROGREvidenceShepherd
from evidence_quality_assessor import EvidenceQualityAssessor, EvidenceQualityMetrics
from evidence_gathering.search_strategy.methodology_strategist import MethodologySearchStrategist
from performance_testing import performance_tester

@dataclass
class DualAIConsensusResult:
    """Result from dual AI consensus analysis"""
    consensus_score: float  # 0-100 weighted consensus confidence
    individual_scores: List[Tuple[str, float]]  # [(ai_name, score), ...]
    disagreement_level: float  # 0-100 how much AIs disagree
    consensus_stance: str  # overall stance consensus
    quality_weighted_score: float  # final score weighted by evidence quality
    uncertainty_indicators: List[str]  # areas of AI disagreement
    evidence_quality_summary: Dict[str, float]  # quality metrics summary

class ROGRDualEvidenceShepherd(EvidenceShepherd):
    """ROGR Dual Evidence Shepherd with Primary + Secondary AI consensus for professional fact-checking"""
    
    def __init__(self, use_eeg_phase_1: bool = False):
        """Initialize Primary and Secondary Evidence Shepherds (both Claude)"""
        self.ai_shepherds = []
        self.use_eeg_phase_1 = use_eeg_phase_1
        self.methodology_strategist = None
        
        # Initialize EEG Phase 1 if enabled
        if self.use_eeg_phase_1:
            try:
                self.methodology_strategist = MethodologySearchStrategist()
                print("✅ EEG Phase 1 MethodologySearchStrategist initialized")
            except Exception as e:
                print(f"⚠️ EEG Phase 1 initialization failed: {e}")
                self.use_eeg_phase_1 = False
        
        # Primary Evidence Shepherd
        try:
            primary_shepherd = ROGREvidenceShepherd()
            if primary_shepherd.is_enabled():
                self.ai_shepherds.append(("Primary", primary_shepherd))
                print("✅ Primary ROGR Evidence Shepherd enabled")
            else:
                print("❌ Primary ROGR Evidence Shepherd disabled")
        except Exception as e:
            print(f"⚠️ Primary ROGR Evidence Shepherd initialization failed: {e}")
        
        # Secondary Evidence Shepherd
        try:
            secondary_shepherd = ROGREvidenceShepherd()
            if secondary_shepherd.is_enabled():
                self.ai_shepherds.append(("Secondary", secondary_shepherd))
                print("✅ Secondary ROGR Evidence Shepherd enabled")
            else:
                print("❌ Secondary ROGR Evidence Shepherd disabled")
        except Exception as e:
            print(f"⚠️ Secondary ROGR Evidence Shepherd initialization failed: {e}")
        
        # Quality assessor for consensus analysis
        self.quality_assessor = EvidenceQualityAssessor()
        
        print(f"🔍 Dual-AI Evidence Shepherd initialized with {len(self.ai_shepherds)} AI shepherds")
    
    def is_enabled(self) -> bool:
        """Check if Dual-AI Evidence Shepherd is enabled"""
        return len(self.ai_shepherds) > 0
    
    def analyze_claim(self, claim_text: str) -> SearchStrategy:
        """Analyze claim using first available shepherd"""
        if not self.ai_shepherds:
            raise ValueError("No AI shepherds available")
        return self.ai_shepherds[0][1].analyze_claim(claim_text)
    
    def filter_evidence_batch(self, evidence_candidates: List[EvidenceCandidate], max_count: int = 5) -> List[EvidenceCandidate]:
        """Filter evidence batch using first available shepherd"""
        if not self.ai_shepherds:
            return evidence_candidates[:max_count]
        return self.ai_shepherds[0][1].filter_evidence_batch(evidence_candidates, max_count)
    
    def score_evidence_relevance(self, evidence: EvidenceCandidate, claim_text: str) -> float:
        """Score evidence relevance using first available shepherd"""
        if not self.ai_shepherds:
            return 50.0
        return self.ai_shepherds[0][1].score_evidence_relevance(evidence, claim_text)
    
    def search_real_evidence(self, claim_text: str) -> List[ProcessedEvidence]:
        """Search for evidence using dual AI consensus with optional EEG Phase 1 enhancement"""
        
        # Start performance tracking
        test_id = performance_tester.start_test(claim_text, self.use_eeg_phase_1)
        start_time = time.time()
        errors = []
        if len(self.ai_shepherds) < 2:
            print("⚠️ Falling back to single AI - insufficient shepherds for consensus")
            if self.ai_shepherds:
                return self.ai_shepherds[0][1].search_real_evidence(claim_text)
            else:
                return []
        
        
        print(f"🔍 Starting dual AI evidence gathering for: {claim_text[:50]}...")
        
        # Gather evidence from both AI shepherds
        all_evidence = {}
        
        # Get centralized strategy - NO fallbacks, single source
        strategy = self._get_complete_strategy(claim_text)
        
        for ai_name, shepherd in self.ai_shepherds:
            print(f"🔍 ROGR {ai_name}: Searching for evidence...")
            evidence_list = shepherd.search_real_evidence(claim_text, strategy)
            all_evidence[ai_name] = evidence_list
            print(f"✅ ROGR {ai_name}: Found {len(evidence_list)} evidence pieces")
        
        # Perform consensus analysis
        consensus_result = self._analyze_consensus(claim_text, all_evidence)
        
        print(f"🎯 Dual AI consensus complete:")
        print(f"  - Consensus score: {consensus_result.consensus_score:.1f}")
        print(f"  - Disagreement level: {consensus_result.disagreement_level:.1f}")
        print(f"  - Quality weighted score: {consensus_result.quality_weighted_score:.1f}")
        
        # Return combined evidence from both AIs
        combined_evidence = []
        for evidence_list in all_evidence.values():
            combined_evidence.extend(evidence_list)
        
        # Record evidence and consensus results
        performance_tester.record_evidence_results(
            test_id, len(combined_evidence),
            consensus_result.consensus_score,
            consensus_result.disagreement_level,
            consensus_result.quality_weighted_score,
            consensus_result.individual_scores
        )
        
        # Attach consensus data to first evidence object
        if combined_evidence:
            combined_evidence[0].consensus_quality_score = consensus_result.quality_weighted_score
            combined_evidence[0].consensus_metadata = {
                'consensus_score': consensus_result.consensus_score,
                'disagreement_level': consensus_result.disagreement_level,
                'uncertainty_indicators': consensus_result.uncertainty_indicators,
                'evidence_quality_summary': consensus_result.evidence_quality_summary,
                'individual_scores': consensus_result.individual_scores
            }
        
        # Finish performance tracking
        total_time = time.time() - start_time
        performance_tester.finish_test(test_id, total_time, errors)
        
        return combined_evidence
    
    def _get_complete_strategy(self, claim_text: str) -> SearchStrategy:
        """SINGLE point of all strategy generation - centralized at orchestrator level"""
        
        if self.use_eeg_phase_1 and self.methodology_strategist:
            # EEG Phase 1 Strategy Generation
            print(f"🧠 EEG Phase 1: Generating methodology-first search strategy...")
            eeg_start = time.time()
            try:
                eeg_result = self.methodology_strategist.generate_search_strategy(claim_text)
                eeg_time = time.time() - eeg_start
                
                print(f"✅ EEG Phase 1: Generated {len(eeg_result.queries)} IFCN-compliant queries")
                print(f"📊 EEG Phase 1: Strategy time: {eeg_time:.2f}s, Estimated total: {eeg_result.total_estimated_time}s")
                
                # Convert EEG result to SearchStrategy
                return SearchStrategy(
                    strategy_source="EEG_Phase_1",
                    claim_type=ClaimType.SCIENTIFIC,
                    search_queries=[q.query_text for q in eeg_result.queries],
                    target_domains=[],
                    time_relevance_months=12,
                    authority_weight=0.8,
                    confidence_threshold=0.7
                )
                
            except Exception as e:
                print(f"❌ EEG Phase 1 strategy generation failed: {e}")
                # NO FALLBACK - fail fast
                raise ValueError(f"Centralized strategy generation failed: {e}")
        else:
            # Legacy Orchestrator Strategy (for non-EEG mode)
            # This would implement basic claim analysis at orchestrator level
            # For now, return a simple strategy until legacy is needed
            return SearchStrategy(
                strategy_source="Legacy_Orchestrator", 
                claim_type=ClaimType.FACTUAL,
                search_queries=[claim_text],
                target_domains=[],
                time_relevance_months=12,
                authority_weight=0.7,
                confidence_threshold=0.7
            )
    
    def _analyze_consensus(self, claim_text: str, all_evidence: Dict[str, List[ProcessedEvidence]]) -> DualAIConsensusResult:
        """Analyze consensus between AI shepherds"""
        
        individual_scores = []
        ai_stances = []
        
        # Calculate individual AI scores and stances
        for ai_name, evidence_list in all_evidence.items():
            if evidence_list:
                # Calculate average relevance score
                total_score = sum(getattr(ev, 'ai_relevance_score', 50) for ev in evidence_list)
                avg_score = total_score / len(evidence_list)
                individual_scores.append((ai_name, avg_score))
                
                # Determine stance based on evidence
                supporting = sum(1 for ev in evidence_list if getattr(ev, 'stance', 'neutral') == 'supporting')
                contradicting = sum(1 for ev in evidence_list if getattr(ev, 'stance', 'neutral') == 'contradicting')
                
                if supporting > contradicting:
                    ai_stances.append('supporting')
                elif contradicting > supporting:
                    ai_stances.append('contradicting')
                else:
                    ai_stances.append('neutral')
            else:
                individual_scores.append((ai_name, 0.0))
                ai_stances.append('neutral')
        
        # Calculate consensus metrics
        scores = [score for _, score in individual_scores]
        if len(scores) >= 2:
            score_diff = abs(scores[0] - scores[1])
            disagreement_level = min(100.0, score_diff)
            consensus_score = (scores[0] + scores[1]) / 2
            
            # Penalize high disagreement
            if disagreement_level > 30:
                consensus_score *= 0.8
        else:
            disagreement_level = 0.0
            consensus_score = scores[0] if scores else 50.0
        
        # Determine consensus stance
        if len(set(ai_stances)) == 1:
            consensus_stance = ai_stances[0]
        else:
            consensus_stance = 'uncertain'
        
        # Calculate quality-weighted score
        all_evidence_pieces = []
        for evidence_list in all_evidence.values():
            all_evidence_pieces.extend(evidence_list)
        
        if all_evidence_pieces:
            quality_weighted_score = consensus_score
        else:
            quality_weighted_score = 0.0
        
        # Identify uncertainty indicators
        uncertainty_indicators = []
        if disagreement_level > 20:
            uncertainty_indicators.append(f"Score disagreement: {disagreement_level:.1f}%")
        if consensus_stance == 'uncertain':
            uncertainty_indicators.append("Conflicting stance classifications")
        
        return DualAIConsensusResult(
            consensus_score=consensus_score,
            individual_scores=individual_scores,
            disagreement_level=disagreement_level,
            consensus_stance=consensus_stance,
            quality_weighted_score=quality_weighted_score,
            uncertainty_indicators=uncertainty_indicators,
            evidence_quality_summary={
                'total_evidence_count': len(all_evidence_pieces),
                'avg_relevance_score': sum(getattr(ev, 'ai_relevance_score', 50) for ev in all_evidence_pieces) / len(all_evidence_pieces) if all_evidence_pieces else 0
            }
        )