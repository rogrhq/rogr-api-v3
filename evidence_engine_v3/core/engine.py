import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import List, Optional
from dataclasses import dataclass

# Import our ACI components
from evidence_engine_v3.aci.components.semantic_analyzer import SemanticClaimAnalyzer
from evidence_engine_v3.aci.components.logical_analyzer import LogicalStructureAnalyzer
from evidence_engine_v3.aci.components.relevance_validator import (
    EvidenceRelevanceValidator, ProcessedEvidence
)
from evidence_engine_v3.eeg.components.search_optimizer import SearchOptimizer

# Import existing dual shepherd if available
try:
    from rogr_dual_evidence_shepherd import ROGRDualEvidenceShepherd
    DUAL_SHEPHERD_AVAILABLE = True
except ImportError:
    DUAL_SHEPHERD_AVAILABLE = False
    print("Warning: ROGRDualEvidenceShepherd not available")

class EvidenceEngineV3:
    def __init__(self):
        print("Initializing Evidence Engine V3...")

        # Initialize ACI components
        self.semantic_analyzer = SemanticClaimAnalyzer()
        self.logical_analyzer = LogicalStructureAnalyzer()
        self.relevance_validator = EvidenceRelevanceValidator()

        # Initialize EEG components
        self.search_optimizer = SearchOptimizer()

        # Initialize existing dual shepherd if available
        if DUAL_SHEPHERD_AVAILABLE:
            try:
                self.dual_shepherd = ROGRDualEvidenceShepherd()
                print("✓ ROGRDualEvidenceShepherd initialized")
            except Exception as e:
                print(f"Warning: Could not initialize ROGRDualEvidenceShepherd: {e}")
                self.dual_shepherd = None
        else:
            self.dual_shepherd = None
            print("Warning: Running without ROGRDualEvidenceShepherd")

        print("Evidence Engine V3 ready")

    def search_real_evidence(self, claim_text: str) -> List[ProcessedEvidence]:
        """
        Main method matching existing interface.
        This is called by main.py
        """
        print(f"\nEvidenceEngineV3 processing: {claim_text[:50]}...")

        # Step 1: Analyze claim semantics
        print("Step 1: Analyzing claim semantics...")
        semantic_result = self.semantic_analyzer.analyze(claim_text)
        print(f"  Subject: {semantic_result.claim_subject}")
        print(f"  Object: {semantic_result.claim_object}")
        print(f"  Temporal: {semantic_result.temporal_aspect}")

        # Step 2: Analyze logical structure
        print("Step 2: Analyzing logical structure...")
        logical_result = self.logical_analyzer.analyze(claim_text, semantic_result)
        print(f"  Assertion type: {logical_result.assertion_type}")
        print(f"  Scope: {logical_result.claim_scope}")

        # Step 3: Optimize searches (but we can't pass to dual shepherd)
        print("Step 3: Optimizing search strategy...")
        search_strategy = self.search_optimizer.optimize_searches(claim_text, semantic_result)
        print(f"  Generated {search_strategy.total_queries} optimized queries")

        # Step 4: Get evidence from dual shepherd
        if self.dual_shepherd:
            print("Step 4: Gathering evidence using dual shepherd...")
            try:
                # Note: We can't pass our optimized queries to dual shepherd
                # It will use its own search strategy
                raw_evidence = self.dual_shepherd.search_real_evidence(claim_text)
                print(f"  Retrieved {len(raw_evidence)} evidence pieces")
            except Exception as e:
                print(f"Error calling dual shepherd: {e}")
                raw_evidence = []
        else:
            print("Step 4: No dual shepherd available, returning empty evidence")
            raw_evidence = []

        # Step 5: Filter evidence by relevance
        print("Step 5: Filtering evidence by relevance...")
        filtered_evidence = []

        for evidence in raw_evidence:
            # Validate relevance
            relevance_result = self.relevance_validator.validate(
                evidence, claim_text, semantic_result
            )

            # Only keep highly relevant evidence
            if relevance_result.final_relevance_score > 50:
                filtered_evidence.append(evidence)
                print(f"  ✓ Kept evidence (score: {relevance_result.final_relevance_score:.1f})")
            else:
                print(f"  ✗ Filtered out (score: {relevance_result.final_relevance_score:.1f}): {relevance_result.relevance_reasoning}")

        print(f"Step 6: Returning {len(filtered_evidence)} relevant evidence pieces")

        # Return filtered evidence
        return filtered_evidence

    def test_basic_functionality(self):
        """Test that all components work"""
        print("\n=== Testing Evidence Engine V3 ===")

        test_claim = "Climate change policies will destroy the economy"

        try:
            # Test semantic analysis
            semantic = self.semantic_analyzer.analyze(test_claim)
            print(f"✓ Semantic analysis works: subject='{semantic.claim_subject}'")

            # Test logical analysis
            logical = self.logical_analyzer.analyze(test_claim, semantic)
            print(f"✓ Logical analysis works: type='{logical.assertion_type}'")

            # Test search optimization
            strategy = self.search_optimizer.optimize_searches(test_claim, semantic)
            print(f"✓ Search optimization works: {strategy.total_queries} queries")

            # Test relevance validation (with mock evidence)
            mock_evidence = ProcessedEvidence(
                text="Carbon tax reduced GDP by 2%",
                source_title="Test",
                source_domain="test.gov",
                source_url="http://test.com",
                ai_stance="supporting",
                ai_relevance_score=80.0,
                ai_confidence=0.8
            )

            relevance = self.relevance_validator.validate(mock_evidence, test_claim, semantic)
            print(f"✓ Relevance validation works: score={relevance.final_relevance_score:.1f}")

            print("\n✅ All components functional!")
            return True

        except Exception as e:
            print(f"\n❌ Component test failed: {e}")
            return False

def test_engine():
    """Test the complete engine"""
    engine = EvidenceEngineV3()

    # Test basic functionality
    if engine.test_basic_functionality():
        print("\n=== Testing full pipeline ===")

        # Test with real claim
        test_claim = "Climate change policies will destroy the economy"
        results = engine.search_real_evidence(test_claim)

        print(f"\nFinal result: {len(results)} relevant evidence pieces")

        if len(results) > 0:
            print("✅ Engine test completed successfully!")
        else:
            print("⚠️ Engine works but no evidence retrieved (check dual shepherd)")
    else:
        print("❌ Basic functionality test failed")

if __name__ == "__main__":
    test_engine()