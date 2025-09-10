"""
Tests for SearchQualityValidator - IFCN Compliance & Performance Validation

Comprehensive test suite covering:
- IFCN compliance validation 
- Performance safeguard enforcement
- Quality metric calculations
- Validation reporting
"""

import unittest
from unittest.mock import patch, MagicMock
from ..search_strategy.quality_validator import (
    SearchQualityValidator,
    ValidationSeverity,
    ValidationIssue,
    ValidationReport
)
from ..interfaces.search_strategy_interface import (
    SearchStrategyResult,
    MethodologySearchQuery,
    ImplementationVersion
)


class TestSearchQualityValidator(unittest.TestCase):
    """Test suite for SearchQualityValidator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = SearchQualityValidator()
        
        # Create test queries
        self.good_queries = [
            MethodologySearchQuery(
                query_text="COVID-19 vaccine efficacy peer reviewed study",
                methodology_type="peer_reviewed",
                priority=1.0,
                max_results=8,
                timeout_seconds=8,
                context_tags=["transparency_score:0.9", "methodology_type:peer_reviewed"]
            ),
            MethodologySearchQuery(
                query_text="vaccine safety government analysis",
                methodology_type="government_official", 
                priority=0.9,
                max_results=8,
                timeout_seconds=8,
                context_tags=["transparency_score:0.85", "methodology_type:government_official"]
            )
        ]
        
        # Create test strategy with good qualities
        self.good_strategy = SearchStrategyResult(
            queries=self.good_queries,
            total_estimated_time=20.0,
            methodology_coverage=["peer_reviewed", "government_official"],
            performance_metrics={"precision_estimate": 0.8},
            ifcn_compliance_status=True,
            version_used=ImplementationVersion.EEG_PHASE_1,
            audit_trail=["Domain classification completed", "Queries generated with methodology focus"]
        )
    
    def test_ifcn_compliance_validation_pass(self):
        """Test IFCN compliance validation for compliant strategy"""
        
        report = self.validator.validate_search_strategy(self.good_strategy)
        
        # Should pass IFCN compliance
        self.assertTrue(report.ifcn_compliance_details["no_institutional_bias"])
        self.assertTrue(report.ifcn_compliance_details["methodology_transparency"])
        self.assertTrue(report.ifcn_compliance_details["has_audit_trail"])
        self.assertTrue(report.ifcn_compliance_details["methodology_diversity"])
        
        # Should have no critical issues
        self.assertEqual(len(report.critical_issues), 0)
    
    def test_institutional_bias_detection(self):
        """Test detection of institutional bias in queries"""
        
        # Create queries with institutional bias
        biased_queries = [
            MethodologySearchQuery(
                query_text="COVID-19 vaccine safety cdc.gov study",  # Institutional bias
                methodology_type="peer_reviewed",
                priority=1.0,
                max_results=8,
                timeout_seconds=8,
                context_tags=["transparency_score:0.9"]
            )
        ]
        
        biased_strategy = SearchStrategyResult(
            queries=biased_queries,
            total_estimated_time=10.0,
            methodology_coverage=["peer_reviewed"],
            performance_metrics={"precision_estimate": 0.8},
            ifcn_compliance_status=False,  # Should be marked as non-compliant
            version_used=ImplementationVersion.EEG_PHASE_1,
            audit_trail=["Strategy generated"]
        )
        
        report = self.validator.validate_search_strategy(biased_strategy)
        
        # Should fail IFCN compliance
        self.assertFalse(report.ifcn_compliance_details["no_institutional_bias"])
        self.assertFalse(report.passed)
        
        # Should have critical issues
        bias_issues = [issue for issue in report.critical_issues 
                      if "institutional bias" in issue.issue.lower()]
        self.assertTrue(len(bias_issues) > 0)
    
    def test_methodology_transparency_validation(self):
        """Test validation of methodology transparency"""
        
        # Create queries without methodology context
        unclear_queries = [
            MethodologySearchQuery(
                query_text="COVID-19 vaccine study",
                methodology_type="",  # Missing methodology type
                priority=1.0,
                max_results=8,
                timeout_seconds=8,
                context_tags=[]
            )
        ]
        
        unclear_strategy = SearchStrategyResult(
            queries=unclear_queries,
            total_estimated_time=10.0,
            methodology_coverage=[],
            performance_metrics={"precision_estimate": 0.8},
            ifcn_compliance_status=False,
            version_used=ImplementationVersion.EEG_PHASE_1,
            audit_trail=["Strategy generated"]
        )
        
        report = self.validator.validate_search_strategy(unclear_strategy)
        
        # Should fail methodology transparency
        self.assertFalse(report.ifcn_compliance_details["methodology_transparency"])
        self.assertFalse(report.passed)
    
    def test_performance_validation(self):
        """Test performance requirement validation"""
        
        # Create strategy exceeding performance limits
        excessive_queries = [
            MethodologySearchQuery(
                query_text=f"test query {i}",
                methodology_type="peer_reviewed",
                priority=1.0,
                max_results=8,
                timeout_seconds=8,
                context_tags=[]
            ) for i in range(15)  # Exceeds max_queries_per_claim (12)
        ]
        
        excessive_strategy = SearchStrategyResult(
            queries=excessive_queries,
            total_estimated_time=120.0,  # Exceeds max_processing_time (45)
            methodology_coverage=["peer_reviewed"],
            performance_metrics={"precision_estimate": 0.8},
            ifcn_compliance_status=True,
            version_used=ImplementationVersion.EEG_PHASE_1,
            audit_trail=["Strategy generated"]
        )
        
        report = self.validator.validate_search_strategy(excessive_strategy)
        
        # Should have performance warnings
        performance_warnings = [w for w in report.warnings if w.category == "performance"]
        self.assertTrue(len(performance_warnings) > 0)
        
        # Check specific performance metrics
        self.assertEqual(report.performance_assessment["query_count"], 15)
        self.assertEqual(report.performance_assessment["estimated_processing_time"], 120.0)
    
    def test_quality_score_calculation(self):
        """Test quality score calculation"""
        
        report = self.validator.validate_search_strategy(self.good_strategy)
        
        # Should have reasonable quality score
        self.assertGreater(report.quality_score, 0.0)
        self.assertLessEqual(report.quality_score, 1.0)
        
        # High-quality strategy should score well
        self.assertGreater(report.quality_score, 0.7)
    
    def test_validation_report_structure(self):
        """Test validation report structure and completeness"""
        
        report = self.validator.validate_search_strategy(self.good_strategy)
        
        # Check report structure
        self.assertIsInstance(report, ValidationReport)
        self.assertIsInstance(report.passed, bool)
        self.assertIsInstance(report.critical_issues, list)
        self.assertIsInstance(report.warnings, list)
        self.assertIsInstance(report.info_items, list)
        self.assertIsInstance(report.performance_assessment, dict)
        self.assertIsInstance(report.ifcn_compliance_details, dict)
        self.assertIsInstance(report.quality_score, float)
        self.assertIsInstance(report.validation_timestamp, float)
        
        # Check summary functionality
        summary = report.get_summary()
        self.assertIsInstance(summary, str)
        self.assertIn("PASSED" if report.passed else "FAILED", summary)
    
    def test_query_batch_validation(self):
        """Test quick validation of query batches"""
        
        issues = self.validator.validate_query_batch(self.good_queries)
        
        # Check return structure
        self.assertIsInstance(issues, dict)
        expected_keys = ["missing_methodology", "excessive_timeout", "low_priority", "missing_context"]
        for key in expected_keys:
            self.assertIn(key, issues)
            self.assertIsInstance(issues[key], list)
        
        # Good queries should have no issues
        self.assertEqual(len(issues["missing_methodology"]), 0)
        self.assertEqual(len(issues["excessive_timeout"]), 0)
    
    def test_validation_summary(self):
        """Test validation summary generation"""
        
        report = self.validator.validate_search_strategy(self.good_strategy)
        summary = self.validator.get_validation_summary(report)
        
        # Check summary structure
        self.assertIsInstance(summary, dict)
        required_keys = [
            "status", "quality_score", "critical_issues", "warnings",
            "recommendations", "ifcn_compliant", "performance_adequate"
        ]
        for key in required_keys:
            self.assertIn(key, summary)
            self.assertIsInstance(summary[key], str)
        
        # Check content for good strategy
        self.assertEqual(summary["status"], "PASSED")
        self.assertEqual(summary["critical_issues"], "0")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        
        # Empty strategy
        empty_strategy = SearchStrategyResult(
            queries=[],
            total_estimated_time=0.0,
            methodology_coverage=[],
            performance_metrics={},
            ifcn_compliance_status=False,
            version_used=ImplementationVersion.EEG_PHASE_1,
            audit_trail=[]
        )
        
        report = self.validator.validate_search_strategy(empty_strategy)
        self.assertFalse(report.passed)  # Should fail due to no methodology coverage
        
        # Strategy with None values
        none_strategy = SearchStrategyResult(
            queries=[],
            total_estimated_time=0.0,
            methodology_coverage=[],
            performance_metrics={},
            ifcn_compliance_status=False,
            version_used=ImplementationVersion.EEG_PHASE_1,
            audit_trail=[]
        )
        
        # Should handle gracefully without crashing
        report = self.validator.validate_search_strategy(none_strategy)
        self.assertIsInstance(report, ValidationReport)


class TestValidationIssues(unittest.TestCase):
    """Test validation issue creation and handling"""
    
    def test_validation_issue_creation(self):
        """Test ValidationIssue creation and properties"""
        
        issue = ValidationIssue(
            severity=ValidationSeverity.CRITICAL,
            category="ifcn_compliance",
            issue="Test issue description",
            recommendation="Test recommendation",
            query_indexes=[0, 1, 2]
        )
        
        # Check properties
        self.assertEqual(issue.severity, ValidationSeverity.CRITICAL)
        self.assertEqual(issue.category, "ifcn_compliance")
        self.assertEqual(len(issue.query_indexes), 3)
    
    def test_validation_issue_defaults(self):
        """Test ValidationIssue default values"""
        
        issue = ValidationIssue(
            severity=ValidationSeverity.WARNING,
            category="performance", 
            issue="Test issue",
            recommendation="Test recommendation"
        )
        
        # Should have empty query_indexes by default
        self.assertEqual(len(issue.query_indexes), 0)


if __name__ == "__main__":
    unittest.main()