"""
Search Quality Validator - IFCN Compliance & Performance Safeguards

Validates search strategies to ensure IFCN compliance, performance requirements,
and quality standards. Provides comprehensive validation with detailed reporting
for audit trails and system monitoring.

Key Features:
- IFCN compliance validation (bias detection, transparency requirements)
- Performance safeguards (query limits, time constraints)
- Quality metrics (methodology coverage, precision estimates)
- Detailed validation reporting for debugging and auditing
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from ..interfaces.search_strategy_interface import SearchStrategyResult, MethodologySearchQuery


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"    # IFCN compliance violations
    WARNING = "warning"      # Performance concerns
    INFO = "info"           # Quality recommendations


@dataclass
class ValidationIssue:
    """Individual validation issue with context"""
    severity: ValidationSeverity
    category: str           # "ifcn_compliance", "performance", "quality"
    issue: str             # Description of the issue
    recommendation: str    # How to fix the issue
    query_indexes: List[int] = None  # Which queries are affected (if applicable)
    
    def __post_init__(self):
        if self.query_indexes is None:
            self.query_indexes = []


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    passed: bool                           # Overall validation status
    critical_issues: List[ValidationIssue] # IFCN compliance violations
    warnings: List[ValidationIssue]        # Performance/quality concerns
    info_items: List[ValidationIssue]      # Recommendations
    performance_assessment: Dict[str, float] # Performance metrics
    ifcn_compliance_details: Dict[str, bool] # Detailed compliance breakdown
    quality_score: float                   # Overall quality rating (0.0-1.0)
    validation_timestamp: float            # When validation was performed
    
    def get_summary(self) -> str:
        """Get human-readable validation summary"""
        status = "PASSED" if self.passed else "FAILED"
        issues_count = len(self.critical_issues) + len(self.warnings)
        return f"Validation {status}: {issues_count} issues found (Quality Score: {self.quality_score:.2f})"


class SearchQualityValidator:
    """
    Comprehensive validator for search strategies
    
    Ensures search strategies meet IFCN compliance standards,
    performance requirements, and quality expectations
    """
    
    def __init__(self):
        """Initialize validator with configurable thresholds"""
        
        # Performance thresholds
        self.max_queries_per_claim = 12
        self.max_processing_time = 45  # seconds
        self.max_query_timeout = 10   # seconds per query
        
        # Quality thresholds
        self.min_methodology_types = 1
        self.min_precision_estimate = 0.6
        self.min_quality_score = 0.7
        
        # IFCN compliance requirements
        self.prohibited_institutional_terms = [
            "cdc.gov", "nih.gov", "fda.gov", "who.int", "reuters.com", 
            "ap.org", "bbc.com", "cnn.com", "foxnews.com"
        ]
        
        self.required_methodology_types = [
            "peer_reviewed", "government_official", "systematic_review",
            "experimental_study", "observational_research", "independent_research"
        ]
    
    def validate_search_strategy(self, strategy: SearchStrategyResult) -> ValidationReport:
        """
        Comprehensive validation of search strategy
        
        Args:
            strategy: Search strategy to validate
            
        Returns:
            ValidationReport with detailed analysis
        """
        
        import time
        validation_timestamp = time.time()
        
        # Collect all validation issues
        critical_issues = []
        warnings = []
        info_items = []
        
        # 1. IFCN Compliance Validation
        ifcn_issues, ifcn_details = self._validate_ifcn_compliance(strategy)
        critical_issues.extend(ifcn_issues)
        
        # 2. Performance Validation
        performance_issues, performance_metrics = self._validate_performance(strategy)
        warnings.extend(performance_issues)
        
        # 3. Quality Validation
        quality_issues, quality_score = self._validate_quality(strategy)
        info_items.extend(quality_issues)
        
        # Determine overall pass/fail
        passed = len(critical_issues) == 0
        
        return ValidationReport(
            passed=passed,
            critical_issues=critical_issues,
            warnings=warnings,
            info_items=info_items,
            performance_assessment=performance_metrics,
            ifcn_compliance_details=ifcn_details,
            quality_score=quality_score,
            validation_timestamp=validation_timestamp
        )
    
    def _validate_ifcn_compliance(
        self, 
        strategy: SearchStrategyResult
    ) -> Tuple[List[ValidationIssue], Dict[str, bool]]:
        """Validate IFCN compliance requirements"""
        
        issues = []
        details = {}
        
        # Check 1: No institutional bias in queries
        institutional_bias_queries = []
        for i, query in enumerate(strategy.queries):
            for term in self.prohibited_institutional_terms:
                if term in query.query_text.lower():
                    institutional_bias_queries.append(i)
                    break
        
        details["no_institutional_bias"] = len(institutional_bias_queries) == 0
        if institutional_bias_queries:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="ifcn_compliance",
                issue="Institutional bias detected in queries",
                recommendation="Remove specific domain references, focus on methodology types",
                query_indexes=institutional_bias_queries
            ))
        
        # Check 2: Methodology transparency
        queries_without_methodology = []
        for i, query in enumerate(strategy.queries):
            if not query.methodology_type or query.methodology_type == "unknown":
                queries_without_methodology.append(i)
        
        details["methodology_transparency"] = len(queries_without_methodology) == 0
        if queries_without_methodology:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="ifcn_compliance",
                issue="Queries missing methodology context",
                recommendation="Ensure all queries specify methodology type",
                query_indexes=queries_without_methodology
            ))
        
        # Check 3: Audit trail requirements
        details["has_audit_trail"] = len(strategy.audit_trail) > 0
        if not strategy.audit_trail:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="ifcn_compliance",
                issue="Missing audit trail for decision transparency",
                recommendation="Include decision audit trail in search strategy"
            ))
        
        # Check 4: Balanced methodology approach
        methodology_types = set(query.methodology_type for query in strategy.queries)
        details["methodology_diversity"] = len(methodology_types) >= self.min_methodology_types
        if len(methodology_types) < self.min_methodology_types:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="ifcn_compliance", 
                issue=f"Insufficient methodology diversity: {len(methodology_types)} types",
                recommendation=f"Include at least {self.min_methodology_types} methodology types"
            ))
        
        return issues, details
    
    def _validate_performance(
        self, 
        strategy: SearchStrategyResult
    ) -> Tuple[List[ValidationIssue], Dict[str, float]]:
        """Validate performance requirements"""
        
        issues = []
        metrics = {}
        
        # Query count validation
        query_count = len(strategy.queries)
        metrics["query_count"] = query_count
        if query_count > self.max_queries_per_claim:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="performance",
                issue=f"Excessive query count: {query_count} > {self.max_queries_per_claim}",
                recommendation="Reduce number of queries or implement prioritization"
            ))
        
        # Processing time validation
        estimated_time = strategy.total_estimated_time
        metrics["estimated_processing_time"] = estimated_time
        if estimated_time > self.max_processing_time:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="performance",
                issue=f"Excessive processing time: {estimated_time}s > {self.max_processing_time}s",
                recommendation="Optimize queries or reduce scope"
            ))
        
        # Individual query timeout validation
        slow_queries = []
        for i, query in enumerate(strategy.queries):
            if query.timeout_seconds > self.max_query_timeout:
                slow_queries.append(i)
        
        metrics["slow_query_count"] = len(slow_queries)
        if slow_queries:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="performance",
                issue=f"{len(slow_queries)} queries have excessive timeout",
                recommendation="Reduce individual query timeouts",
                query_indexes=slow_queries
            ))
        
        # Resource efficiency
        total_max_results = sum(query.max_results for query in strategy.queries)
        metrics["total_max_results"] = total_max_results
        metrics["efficiency_ratio"] = query_count / max(1, total_max_results) * 100
        
        return issues, metrics
    
    def _validate_quality(
        self, 
        strategy: SearchStrategyResult
    ) -> Tuple[List[ValidationIssue], float]:
        """Validate quality requirements and calculate quality score"""
        
        issues = []
        quality_factors = {}
        
        # Methodology coverage quality
        methodology_count = len(strategy.methodology_coverage)
        quality_factors["methodology_coverage"] = min(1.0, methodology_count / 3.0)  # 3 is ideal
        
        if methodology_count < self.min_methodology_types:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="quality",
                issue=f"Limited methodology coverage: {methodology_count} types",
                recommendation="Consider adding more methodology types for comprehensive coverage"
            ))
        
        # Precision estimate quality
        precision_estimate = strategy.performance_metrics.get("precision_estimate", 0.0)
        quality_factors["precision_estimate"] = precision_estimate
        
        if precision_estimate < self.min_precision_estimate:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="quality",
                issue=f"Low precision estimate: {precision_estimate:.2f}",
                recommendation="Refine queries for better precision targeting"
            ))
        
        # Query priority distribution
        priorities = [query.priority for query in strategy.queries]
        if priorities:
            priority_variance = max(priorities) - min(priorities)
            quality_factors["query_prioritization"] = min(1.0, priority_variance)
        else:
            quality_factors["query_prioritization"] = 0.0
        
        if priorities and priority_variance < 0.1:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="quality",
                issue="Queries lack proper prioritization",
                recommendation="Implement priority weighting for query optimization"
            ))
        
        # Context richness
        context_rich_queries = sum(
            1 for query in strategy.queries 
            if query.context_tags and len(query.context_tags) > 0
        )
        quality_factors["context_richness"] = context_rich_queries / max(1, len(strategy.queries))
        
        # Calculate overall quality score
        quality_score = sum(quality_factors.values()) / len(quality_factors)
        
        if quality_score < self.min_quality_score:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="quality",
                issue=f"Overall quality score below threshold: {quality_score:.2f}",
                recommendation="Review and improve query generation strategy"
            ))
        
        return issues, quality_score
    
    def validate_query_batch(self, queries: List[MethodologySearchQuery]) -> Dict[str, List[int]]:
        """
        Quick validation of query batch for specific issues
        
        Returns dict mapping issue types to affected query indexes
        """
        
        issues = {
            "missing_methodology": [],
            "excessive_timeout": [],
            "low_priority": [],
            "missing_context": []
        }
        
        for i, query in enumerate(queries):
            # Check methodology
            if not query.methodology_type or query.methodology_type == "unknown":
                issues["missing_methodology"].append(i)
            
            # Check timeout
            if query.timeout_seconds > self.max_query_timeout:
                issues["excessive_timeout"].append(i)
            
            # Check priority
            if query.priority < 0.3:  # Very low priority
                issues["low_priority"].append(i)
            
            # Check context
            if not query.context_tags:
                issues["missing_context"].append(i)
        
        return issues
    
    def get_validation_summary(self, report: ValidationReport) -> Dict[str, str]:
        """Get human-readable validation summary"""
        
        return {
            "status": "PASSED" if report.passed else "FAILED",
            "quality_score": f"{report.quality_score:.2f}",
            "critical_issues": str(len(report.critical_issues)),
            "warnings": str(len(report.warnings)),
            "recommendations": str(len(report.info_items)),
            "ifcn_compliant": str(report.ifcn_compliance_details.get("no_institutional_bias", False)),
            "performance_adequate": str(
                report.performance_assessment.get("estimated_processing_time", 999) <= self.max_processing_time
            )
        }