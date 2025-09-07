import os
import json
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import concurrent.futures
from evidence_shepherd import EvidenceShepherd, SearchStrategy, EvidenceCandidate, ProcessedEvidence, ClaimType
from claude_evidence_shepherd import ClaudeEvidenceShepherd
from evidence_quality_assessor import EvidenceQualityAssessor, EvidenceQualityMetrics

@dataclass
class DualClaudeConsensusResult:
    """Result from dual Claude consensus analysis"""
    consensus_score: float  # 0-100 agreement between Claude instances
    primary_evidence: List[ProcessedEvidence]  # Evidence from primary Claude
    secondary_evidence: List[ProcessedEvidence]  # Evidence from secondary Claude
    final_evidence_pieces: List[ProcessedEvidence]  # Combined consensus evidence
    processing_time: float  # Total processing time
    quality_metrics: Dict[str, float]  # Evidence quality summary
    agreement_level: str  # High/Medium/Low agreement description

class DualClaudeEvidenceShepherd(EvidenceShepherd):
    """Dual Claude evidence shepherd for unimpeachable consensus results"""
    
    def __init__(self):
        """Initialize two Claude instances with different search methodologies"""
        
        # Primary Claude: Standard broad web search
        self.primary_claude = ClaudeEvidenceShepherd()
        
        # Secondary Claude: Academic-focused search  
        self.secondary_claude = ClaudeAcademicFocusedShepherd()
        
        # Quality assessor for consensus analysis
        self.quality_assessor = EvidenceQualityAssessor()
        
        print("🔍 Dual Claude Evidence Shepherd initialized - Primary + Academic-focused consensus")
    
    def is_enabled(self) -> bool:
        """Check if dual Claude ES is enabled"""
        return bool(os.getenv('ANTHROPIC_API_KEY'))
    
    def analyze_claim(self, claim_text: str) -> SearchStrategy:
        """Analyze claim using primary Claude"""
        return self.primary_claude.analyze_claim(claim_text)
    
    def filter_evidence_batch(self, evidence_candidates: List[EvidenceCandidate], max_count: int = 5) -> List[EvidenceCandidate]:
        """Filter evidence batch using primary Claude"""
        return self.primary_claude.filter_evidence_batch(evidence_candidates, max_count)
    
    def score_evidence_relevance(self, evidence: EvidenceCandidate, claim_text: str) -> float:
        """Score evidence relevance using primary Claude"""
        return self.primary_claude.score_evidence_relevance(evidence, claim_text)
    
    def search_real_evidence(self, claim_text: str) -> List[ProcessedEvidence]:
        """Search for evidence using dual Claude consensus approach"""
        start_time = time.time()
        
        # Run dual Claude analysis
        result = self._dual_claude_consensus(claim_text)
        
        result.processing_time = time.time() - start_time
        
        print(f"🔍 Dual Claude consensus complete:")
        print(f"  - Primary evidence: {len(result.primary_evidence)} pieces")
        print(f"  - Secondary evidence: {len(result.secondary_evidence)} pieces")
        print(f"  - Final consensus: {len(result.final_evidence_pieces)} pieces")
        print(f"  - Agreement level: {result.agreement_level}")
        print(f"  - Processing time: {result.processing_time:.1f}s")
        
        return result.final_evidence_pieces
    
    def _dual_claude_consensus(self, claim_text: str) -> DualClaudeConsensusResult:
        """Perform parallel dual Claude evidence gathering and consensus analysis"""
        
        print(f"🔍 Starting dual Claude consensus for: {claim_text[:60]}...")
        
        # Run both Claude instances in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            primary_future = executor.submit(self._gather_primary_evidence, claim_text)
            secondary_future = executor.submit(self._gather_secondary_evidence, claim_text)
            
            # Wait for both to complete
            primary_evidence = primary_future.result()
            secondary_evidence = secondary_future.result()
        
        # Perform consensus analysis
        consensus_result = self._analyze_consensus(
            claim_text, primary_evidence, secondary_evidence
        )
        
        return consensus_result
    
    def _gather_primary_evidence(self, claim_text: str) -> List[ProcessedEvidence]:
        """Gather evidence using primary Claude (broad web search)"""
        print("🔵 Primary Claude: Broad web search...")
        return self.primary_claude.search_real_evidence(claim_text)
    
    def _gather_secondary_evidence(self, claim_text: str) -> List[ProcessedEvidence]:
        """Gather evidence using secondary Claude (academic-focused search)"""
        print("🟡 Secondary Claude: Academic-focused search...")
        return self.secondary_claude.search_real_evidence(claim_text)
    
    def _analyze_consensus(self, claim_text: str, 
                          primary_evidence: List[ProcessedEvidence],
                          secondary_evidence: List[ProcessedEvidence]) -> DualClaudeConsensusResult:
        """Analyze consensus between two Claude instances"""
        
        print(f"⚖️ Dual Claude consensus analysis...")
        print(f"  - Primary: {len(primary_evidence)} pieces")
        print(f"  - Secondary: {len(secondary_evidence)} pieces")
        
        # Quality filter both sets
        primary_quality = self._filter_quality_evidence(primary_evidence, "Primary")
        secondary_quality = self._filter_quality_evidence(secondary_evidence, "Secondary")
        
        print(f"⚖️ After quality filtering (≥60 threshold):")
        print(f"  - Primary quality: {len(primary_quality)} pieces")
        print(f"  - Secondary quality: {len(secondary_quality)} pieces")
        
        # Combine and deduplicate quality evidence
        final_evidence = self._combine_evidence(primary_quality, secondary_quality)
        
        # Calculate consensus metrics
        agreement_level, consensus_score = self._calculate_agreement(
            primary_quality, secondary_quality, final_evidence
        )
        
        quality_metrics = {
            'primary_quality_count': len(primary_quality),
            'secondary_quality_count': len(secondary_quality),
            'final_evidence_count': len(final_evidence),
            'avg_quality': sum(getattr(ev, 'quality_score', 50) for ev in final_evidence) / len(final_evidence) if final_evidence else 50.0,
            'consensus_score': consensus_score
        }
        
        print(f"🎯 Consensus complete:")
        print(f"  - Agreement level: {agreement_level}")
        print(f"  - Final evidence count: {len(final_evidence)}")
        print(f"  - Average quality: {quality_metrics['avg_quality']:.1f}")
        print(f"  - Consensus score: {consensus_score:.1f}")
        
        return DualClaudeConsensusResult(
            consensus_score=consensus_score,
            primary_evidence=primary_evidence,
            secondary_evidence=secondary_evidence,
            final_evidence_pieces=final_evidence,
            processing_time=0.0,  # Set by caller
            quality_metrics=quality_metrics,
            agreement_level=agreement_level
        )
    
    def _filter_quality_evidence(self, evidence_list: List[ProcessedEvidence], source_name: str) -> List[ProcessedEvidence]:
        """Filter evidence by quality threshold"""
        quality_filtered = []
        
        for evidence in evidence_list[:5]:  # Limit to 5 per source
            try:
                evidence_text = evidence.text if hasattr(evidence, 'text') else ""
                evidence_url = evidence.source_url if hasattr(evidence, 'source_url') else ""
                evidence_title = evidence.source_title if hasattr(evidence, 'source_title') else ""
                
                quality_metrics = self.quality_assessor.assess_evidence_quality(
                    evidence_text, evidence_url, evidence_title
                )
                
                quality_score = quality_metrics.overall_quality_score()
                
                # QUALITY THRESHOLD: Only include evidence ≥60 quality
                if quality_score >= 60.0:
                    evidence.quality_score = quality_score
                    quality_filtered.append(evidence)
                    print(f"  ✅ {source_name}: {evidence.source_domain} - Quality: {quality_score:.1f}")
                else:
                    print(f"  ❌ {source_name}: {evidence.source_domain} - Quality: {quality_score:.1f} (below 60.0 threshold)")
                    
            except Exception as e:
                print(f"  ⚠️ {source_name}: Quality assessment error - {e}")
                continue
        
        return quality_filtered
    
    def _combine_evidence(self, primary_quality: List[ProcessedEvidence], 
                         secondary_quality: List[ProcessedEvidence]) -> List[ProcessedEvidence]:
        """Combine evidence from both sources, removing duplicates"""
        combined = []
        seen_domains = set()
        
        # Add all primary evidence first
        for ev in primary_quality:
            domain = getattr(ev, 'source_domain', 'unknown')
            combined.append(ev)
            seen_domains.add(domain)
        
        # Add secondary evidence that doesn't duplicate domains
        for ev in secondary_quality:
            domain = getattr(ev, 'source_domain', 'unknown')
            if domain not in seen_domains:
                combined.append(ev)
                seen_domains.add(domain)
        
        # Limit to top 6 pieces total, sorted by quality
        combined.sort(key=lambda x: getattr(x, 'quality_score', 0), reverse=True)
        return combined[:6]
    
    def _calculate_agreement(self, primary_quality: List[ProcessedEvidence],
                           secondary_quality: List[ProcessedEvidence],
                           final_evidence: List[ProcessedEvidence]) -> Tuple[str, float]:
        """Calculate agreement level and consensus score"""
        
        primary_count = len(primary_quality)
        secondary_count = len(secondary_quality)
        final_count = len(final_evidence)
        
        # Agreement based on both finding quality evidence
        if primary_count > 0 and secondary_count > 0:
            if final_count >= 4:  # Both found good evidence
                agreement_level = "High"
                consensus_score = min(100.0, 80.0 + (final_count * 5))
            else:  # Both found some evidence
                agreement_level = "Medium"  
                consensus_score = min(90.0, 60.0 + (final_count * 8))
        elif primary_count > 0 or secondary_count > 0:  # Only one found evidence
            agreement_level = "Low"
            consensus_score = min(80.0, 40.0 + (final_count * 10))
        else:  # Neither found quality evidence
            agreement_level = "None"
            consensus_score = 30.0
        
        return agreement_level, consensus_score

class ClaudeAcademicFocusedShepherd(ClaudeEvidenceShepherd):
    """Claude shepherd focused on academic and authoritative sources"""
    
    def __init__(self):
        super().__init__()
        self.search_focus = "academic"
        print("🟡 Academic-focused Claude ES initialized - prioritizing authoritative sources")
    
    def analyze_claim(self, claim_text: str) -> SearchStrategy:
        """Override to add academic focus to search queries"""
        base_strategy = super().analyze_claim(claim_text)
        
        # Modify queries for academic focus
        academic_queries = []
        for query in base_strategy.search_queries:
            academic_queries.extend([
                f"{query} site:edu research study",
                f"{query} site:gov official report", 
                f"{query} peer reviewed academic"
            ])
        
        base_strategy.search_queries = academic_queries[:3]  # Limit to 3 academic queries
        return base_strategy