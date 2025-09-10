"""
Tests for MethodologySearchStrategist - Core EEG Phase 1 Implementation

Comprehensive test suite covering:
- Domain classification accuracy
- IFCN compliance validation
- Query generation quality
- Performance requirements
- Integration compatibility
"""

import unittest
from unittest.mock import patch, MagicMock
from ..search_strategy.methodology_strategist import (
    MethodologySearchStrategist, 
    DomainType, 
    MethodologyType,
    DomainClassificationResult
)
from ..interfaces.search_strategy_interface import (
    SearchStrategyResult,
    MethodologySearchQuery,
    ImplementationVersion
)


class TestMethodologySearchStrategist(unittest.TestCase):
    """Test suite for MethodologySearchStrategist"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.strategist = MethodologySearchStrategist()
        
        # Test claims covering different domains
        self.test_claims = {
            "medical": "COVID-19 vaccines are safe and effective for preventing severe illness",
            "economic": "Minimum wage increases reduce unemployment rates in small businesses",
            "scientific": "Climate change is primarily caused by human activities and fossil fuel emissions",
            "policy": "The Infrastructure Investment and Jobs Act will create 2 million new jobs",
            "statistical": "85% of Americans support universal background checks for gun purchases",
            "general": "The weather was nice yesterday in New York"
        }
    
    def test_domain_classification_medical(self):
        """Test medical domain classification accuracy"""
        
        claim = self.test_claims["medical"]
        result = self.strategist.classify_claim_domain(claim)
        
        # Assertions
        self.assertEqual(result.primary_domain, DomainType.MEDICAL)
        self.assertGreater(result.confidence, 0.1)
        self.assertIn("medical", result.reasoning.lower())
        self.assertTrue(len(result.keywords_matched) > 0)
        self.assertIn(MethodologyType.PEER_REVIEWED, result.methodology_requirements)
    
    def test_domain_classification_economic(self):
        """Test economic domain classification accuracy"""
        
        claim = self.test_claims["economic"]
        result = self.strategist.classify_claim_domain(claim)
        
        # Assertions
        self.assertEqual(result.primary_domain, DomainType.ECONOMIC)
        self.assertGreater(result.confidence, 0.1)
        self.assertTrue(any(keyword in claim.lower() for keyword in result.keywords_matched))
        self.assertIn(MethodologyType.GOVERNMENT_OFFICIAL, result.methodology_requirements)
    
    def test_domain_classification_scientific(self):
        """Test scientific domain classification accuracy"""
        
        claim = self.test_claims["scientific"]
        result = self.strategist.classify_claim_domain(claim)
        
        # Should classify as scientific or policy (both valid for climate change)
        self.assertIn(result.primary_domain, [DomainType.SCIENTIFIC, DomainType.POLICY])
        self.assertGreater(result.confidence, 0.1)
        self.assertTrue(len(result.methodology_requirements) > 0)
    
    def test_methodology_query_generation(self):
        """Test query generation for specific methodology types"""
        
        claim = self.test_claims["medical"]
        
        # Test peer-reviewed queries
        queries = self.strategist.generate_methodology_queries(
            claim, MethodologyType.PEER_REVIEWED, max_queries=3
        )
        
        # Assertions
        self.assertEqual(len(queries), 3)
        self.assertTrue(all(isinstance(q, MethodologySearchQuery) for q in queries))
        self.assertTrue(all(q.methodology_type == "peer_reviewed" for q in queries))
        self.assertTrue(all(claim in q.query_text for q in queries))
        self.assertTrue(all(q.priority > 0 for q in queries))
    
    def test_search_strategy_generation(self):
        """Test complete search strategy generation"""
        
        claim = self.test_claims["medical"]
        strategy = self.strategist.generate_search_strategy(claim)
        
        # Basic structure tests
        self.assertIsInstance(strategy, SearchStrategyResult)
        self.assertTrue(len(strategy.queries) > 0)
        self.assertTrue(len(strategy.methodology_coverage) > 0)
        self.assertEqual(strategy.version_used, ImplementationVersion.EEG_PHASE_1)
        
        # Query quality tests
        self.assertTrue(all(isinstance(q, MethodologySearchQuery) for q in strategy.queries))
        self.assertTrue(all(q.methodology_type != "unknown" for q in strategy.queries))
        self.assertTrue(all(claim in q.query_text for q in strategy.queries))
    
    def test_performance_limits_enforcement(self):
        """Test that performance limits are properly enforced"""
        
        claim = self.test_claims["medical"]
        strategy = self.strategist.generate_search_strategy(claim)
        
        # Performance assertions
        self.assertLessEqual(len(strategy.queries), self.strategist.max_queries_per_claim)
        self.assertLessEqual(strategy.total_estimated_time, self.strategist.max_processing_time)
        self.assertTrue(all(q.timeout_seconds <= 10 for q in strategy.queries))
    
    def test_ifcn_compliance_validation(self):
        """Test IFCN compliance validation"""
        
        claim = self.test_claims["medical"] 
        strategy = self.strategist.generate_search_strategy(claim)
        
        # IFCN compliance tests
        self.assertTrue(strategy.ifcn_compliance_status)
        
        # Check for institutional bias (should not be present)
        prohibited_terms = ["cdc.gov", "nih.gov", "fda.gov", "who.int"]
        for query in strategy.queries:
            for term in prohibited_terms:
                self.assertNotIn(term, query.query_text.lower(), 
                    f"Institutional bias detected: {term} in query")
        
        # Check methodology transparency
        for query in strategy.queries:
            self.assertNotEqual(query.methodology_type, "unknown")
            self.assertIsNotNone(query.methodology_type)
        
        # Check audit trail
        self.assertTrue(len(strategy.audit_trail) > 0)
    
    def test_strategy_validation(self):
        """Test search strategy validation functionality"""
        
        claim = self.test_claims["economic"]
        strategy = self.strategist.generate_search_strategy(claim)
        validation_result = self.strategist.validate_strategy(strategy)
        
        # Validation result structure
        self.assertIsInstance(validation_result, dict)
        required_keys = [
            "ifcn_compliant", "within_performance_limits", 
            "methodology_adequate", "has_audit_trail", "queries_have_context"
        ]
        for key in required_keys:
            self.assertIn(key, validation_result)
            self.assertIsInstance(validation_result[key], bool)
        
        # Should pass validation for properly generated strategy
        self.assertTrue(validation_result["ifcn_compliant"])
        self.assertTrue(validation_result["within_performance_limits"])
        self.assertTrue(validation_result["methodology_adequate"])
    
    def test_implementation_info(self):
        """Test implementation information retrieval"""
        
        info = self.strategist.get_implementation_info()
        
        # Structure tests
        self.assertIsInstance(info, dict)
        required_keys = [
            "version", "stage", "description", "capabilities",
            "ifcn_compliance_level", "max_queries", "methodology_types"
        ]
        for key in required_keys:
            self.assertIn(key, info)
            self.assertIsInstance(info[key], str)
        
        # Content tests  
        self.assertEqual(info["version"], "eeg_phase_1")
        self.assertEqual(info["stage"], "1")
        self.assertEqual(info["ifcn_compliance_level"], "full")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        
        # Empty claim
        empty_result = self.strategist.classify_claim_domain("")
        self.assertEqual(empty_result.primary_domain, DomainType.GENERAL)
        
        # Very long claim
        long_claim = "medical " * 100  # 100 repetitions
        long_result = self.strategist.generate_search_strategy(long_claim)
        self.assertLessEqual(len(long_result.queries), self.strategist.max_queries_per_claim)
        
        # Claim with special characters
        special_claim = "Does 50% increase in healthcare costs affect medical treatment outcomes?"
        special_result = self.strategist.generate_search_strategy(special_claim)
        self.assertTrue(len(special_result.queries) > 0)
    
    def test_multiple_domain_classification(self):
        """Test claims that could belong to multiple domains"""
        
        # Claim that could be medical, scientific, or policy
        ambiguous_claim = "Government health policy on vaccine mandates improves public health outcomes"
        result = self.strategist.classify_claim_domain(ambiguous_claim)
        
        # Should classify into one primary domain
        self.assertIsInstance(result.primary_domain, DomainType)
        self.assertGreater(result.confidence, 0.0)
        
        # Should identify alternative domains
        self.assertTrue(len(result.alternative_domains) > 0)
        
        # Should have comprehensive methodology requirements
        self.assertTrue(len(result.methodology_requirements) > 1)
    
    def test_query_prioritization(self):
        """Test that queries are properly prioritized"""
        
        claim = self.test_claims["scientific"]
        strategy = self.strategist.generate_search_strategy(claim)
        
        # Check priority distribution
        priorities = [q.priority for q in strategy.queries]
        self.assertTrue(len(set(priorities)) > 1)  # Should have different priorities
        self.assertTrue(all(0 <= p <= 1.0 for p in priorities))  # Valid range
        
        # Higher priority queries should come first (if sorted)
        sorted_queries = sorted(strategy.queries, key=lambda q: q.priority, reverse=True)
        self.assertGreaterEqual(sorted_queries[0].priority, sorted_queries[-1].priority)


class TestDomainClassificationEdgeCases(unittest.TestCase):
    """Specific tests for domain classification edge cases"""
    
    def setUp(self):
        self.strategist = MethodologySearchStrategist()
    
    def test_overlapping_keywords(self):
        """Test claims with keywords from multiple domains"""
        
        # Medical + Economic claim
        mixed_claim = "Healthcare spending increases economic burden on families"
        result = self.strategist.classify_claim_domain(mixed_claim)
        
        self.assertIn(result.primary_domain, [DomainType.MEDICAL, DomainType.ECONOMIC])
        self.assertTrue(len(result.alternative_domains) > 0)
    
    def test_no_clear_domain(self):
        """Test claims with no clear domain indicators"""
        
        generic_claim = "The meeting was scheduled for next Tuesday afternoon"
        result = self.strategist.classify_claim_domain(generic_claim)
        
        self.assertEqual(result.primary_domain, DomainType.GENERAL)
        self.assertEqual(result.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()