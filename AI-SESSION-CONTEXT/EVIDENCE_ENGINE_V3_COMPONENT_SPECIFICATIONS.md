# Evidence Engine V3: Complete Component Specifications

**Document Version**: 1.0
**Date Created**: 2024-12-17
**Status**: Specification Complete - Ready for Implementation
**Compliance**: RDT v2.0 + FLAWLESS_IMPLEMENTATION_METHODOLOGY.md

---

## **SPECIFICATION COMPLETENESS CHECKLIST**

- [x] **Component Interface Specification**: All referenced components have defined methods, parameters, return types
- [x] **Data Structure Definition**: All data classes/interfaces fully specified with field types
- [x] **Integration Point Documentation**: Component connections and data exchange fully defined
- [x] **Dependency Resolution**: All required components exist or specified for implementation
- [x] **Error Handling Specification**: Exception handling for all failure modes
- [x] **Performance Requirements**: Timing and resource constraints defined
- [x] **Testing Specifications**: Unit test requirements for each component

---

## **ARCHITECTURE OVERVIEW**

```
evidence_engine_v3/
├── core/
│   ├── evidence_engine.py          # Main orchestrator class
│   ├── interfaces.py               # All data structures and interfaces
│   └── exceptions.py               # Custom exception classes
├── claim_interpretation/           # ACI Module
│   ├── semantic_analyzer.py        # Subject/object/relationship analysis
│   ├── logical_analyzer.py         # Causation/correlation/scope analysis
│   └── claim_classifier.py         # Domain classification
├── evidence_gathering/             # EEG Module
│   ├── methodology_strategist.py   # IFCN-compliant search strategy
│   ├── search_executor.py          # Parallel evidence search
│   └── quality_validator.py        # Evidence quality assessment
├── consensus_analysis/             # Dual AI Module
│   ├── dual_ai_processor.py        # Multi-AI consensus analysis
│   ├── quality_assessor.py         # Evidence quality scoring
│   └── uncertainty_quantifier.py   # Confidence interval calculation
└── scoring/                        # ROGR FC Integration
    ├── trust_calculator.py         # Trust score calculation
    ├── grade_engine.py             # Evidence grade assignment
    └── capsule_formatter.py        # TrustCapsule output formatting
```

---

## **CORE DATA STRUCTURES**

### **Base Interfaces**

```python
# evidence_engine_v3/core/interfaces.py

from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Any
from enum import Enum
from datetime import datetime

@dataclass
class Citation:
    """Source citation for evidence"""
    title: str
    domain: str
    date: str
    url: str

@dataclass
class EvidenceStatement:
    """Individual piece of evidence"""
    statement: str
    source_title: str
    source_domain: str
    source_url: str
    stance: str  # "supporting", "contradicting", "neutral"
    relevance_score: float  # 0-1, how relevant to the claim
    highlight_text: Optional[str] = None
    highlight_context: Optional[str] = None
    paragraph_index: Optional[int] = None

@dataclass
class ClaimAnalysis:
    """Analysis of individual claim"""
    claim_text: str
    trust_score: int
    evidence_grade: str
    confidence: str
    evidence_summary: List[str]
    sources_count: int
    supporting_evidence: List[EvidenceStatement]
    contradicting_evidence: List[EvidenceStatement]
    neutral_evidence: List[EvidenceStatement]

@dataclass
class TrustCapsule:
    """Final output format - MUST match existing main.py exactly"""
    id: str
    trust_score: int
    evidence_grade: str
    confidence: str
    why: List[str]
    claims: List[ClaimAnalysis]
    overall_assessment: str
    citations: List[Citation]
    capsule_version: int
    signed: bool
    created_at: str
    input_type: str
    mode: str
```

### **ACI Module Data Structures**

```python
@dataclass
class SemanticAnalysisResult:
    """Output from semantic analyzer"""
    claim_subject: str          # "climate change policies"
    claim_object: str           # "economy"
    relationship_type: str      # "causal", "comparative", "descriptive"
    temporal_aspect: str        # "future", "past", "present"
    certainty_level: str        # "definitive", "probable", "speculative"
    action_type: str           # "destroy", "improve", "affect"
    processing_time: float     # Seconds taken for analysis
    confidence_score: float    # 0-1, confidence in analysis

@dataclass
class LogicalAnalysisResult:
    """Output from logical analyzer"""
    assertion_type: str         # "causal", "correlational", "descriptive"
    logical_operators: List[str] # ["if", "then", "because", "therefore"]
    claim_scope: str            # "universal", "particular", "conditional"
    qualifying_language: List[str] # ["might", "always", "never", "likely"]
    evidence_requirements: Dict[str, str] # What evidence would prove/disprove
    processing_time: float
    confidence_score: float

@dataclass
class DomainClassificationResult:
    """Output from domain classifier"""
    domain: str                 # "medical", "economic", "scientific", "policy"
    confidence: float          # 0-1, classification confidence
    keywords_matched: List[str] # Keywords that triggered classification
    evidence_strategy: List[str] # Recommended evidence types
    source_priorities: List[str] # Prioritized source types
    methodology_requirements: List[str] # Required methodology standards
    processing_time: float

@dataclass
class ClaimInterpretation:
    """Complete ACI module output"""
    semantic: SemanticAnalysisResult
    logical: LogicalAnalysisResult
    domain: DomainClassificationResult
    total_processing_time: float
    interpretation_id: str
    timestamp: datetime
```

### **EEG Module Data Structures**

```python
@dataclass
class SearchQuery:
    """Individual search query specification"""
    query_text: str
    methodology_type: str      # "peer_reviewed", "government_official", etc.
    priority: int             # 1-10, execution priority
    expected_sources: int     # Expected number of results
    timeout_seconds: int      # Maximum execution time

@dataclass
class SearchStrategy:
    """Complete search strategy from methodology strategist"""
    queries: List[SearchQuery]
    methodology_types: List[str]
    total_query_count: int
    estimated_processing_time: float
    ifcn_compliance_status: bool
    audit_trail: List[str]
    strategy_id: str
    timestamp: datetime

@dataclass
class EvidenceCandidate:
    """Raw evidence found by search executor"""
    text: str
    source_title: str
    source_domain: str
    source_url: str
    extraction_timestamp: datetime
    search_query_id: str
    raw_content_length: int
    extraction_method: str    # "web_scraping", "api", etc.

@dataclass
class ProcessedEvidence:
    """Evidence after quality validation and processing"""
    text: str
    source_title: str
    source_domain: str
    source_url: str
    ai_stance: str           # "supporting", "contradicting", "neutral"
    ai_relevance_score: float # 0-100, AI-assessed relevance
    quality_score: float     # 0-100, methodology quality
    methodology_type: str    # Source methodology classification
    highlight_text: str
    highlight_context: str
    processing_metadata: Dict[str, Any]
    validation_timestamp: datetime

@dataclass
class EvidencePool:
    """Complete evidence collection from EEG module"""
    evidence: List[ProcessedEvidence]
    strategy_used: SearchStrategy
    total_processing_time: float
    quality_score: float     # Overall pool quality 0-1
    ifcn_compliant: bool
    evidence_diversity_score: float # Methodology diversity 0-1
    pool_id: str
    timestamp: datetime
```

### **Consensus Analysis Data Structures**

```python
@dataclass
class AIConsensusScore:
    """Individual AI assessment"""
    ai_name: str             # "Primary", "Secondary"
    trust_score: float       # 0-100, AI's trust assessment
    confidence: float        # 0-100, AI's confidence in assessment
    reasoning: List[str]     # AI's reasoning for score
    processing_time: float
    model_version: str

@dataclass
class ConsensusResult:
    """Output from dual AI consensus analysis"""
    consensus_score: float   # 0-100, weighted consensus confidence
    individual_scores: List[AIConsensusScore]
    disagreement_level: float # 0-100, how much AIs disagree
    consensus_stance: str    # Overall stance consensus
    quality_weighted_score: float # Final score weighted by evidence quality
    uncertainty_indicators: List[str] # Areas of AI disagreement
    evidence_quality_summary: Dict[str, float] # Quality metrics summary
    processing_time: float
    consensus_id: str
    timestamp: datetime
```

### **Scoring Module Data Structures**

```python
@dataclass
class TrustScore:
    """Trust score calculation result"""
    score: float            # 0-100, final trust score
    base_score: float       # Pre-adjustment score
    quality_adjustment: float # Quality-based adjustment
    uncertainty_adjustment: float # Uncertainty penalty
    calculation_metadata: Dict[str, Any]
    calculation_timestamp: datetime

@dataclass
class EvidenceGrade:
    """Evidence grade calculation result"""
    grade: str              # "A+", "A", "B+", etc.
    grade_score: float      # 0-100, numerical grade
    grade_reasoning: str    # Human-readable explanation
    methodology_score: float # Evidence methodology quality
    source_quality_score: float # Source reliability score
    grading_timestamp: datetime
```

---

## **COMPONENT 1: CORE ORCHESTRATOR**

### **Class: EvidenceEngineV3**

**Location**: `evidence_engine_v3/core/evidence_engine.py`

```python
class EvidenceEngineV3:
    """Main orchestrator for Evidence Engine V3 pipeline"""

    def __init__(self):
        """Initialize all pipeline components"""
        self.aci_processor: ClaimInterpretationProcessor
        self.eeg_gatherer: EnhancedEvidenceGatherer
        self.consensus_analyzer: DualAIConsensusAnalyzer
        self.scoring_engine: ROGRScoringEngine
        self.processing_stats: Dict[str, float]
        self.error_handler: ErrorHandler
        self.logger: Logger

    def process_claims(self, claims: List[str]) -> List[TrustCapsule]:
        """
        Main processing pipeline - processes multiple claims

        Args:
            claims: List of claim text strings to process

        Returns:
            List of TrustCapsule objects with complete analysis

        Raises:
            EvidenceEngineError: If pipeline fails critically
            PerformanceError: If processing exceeds time limits

        Performance Requirements:
            - Total time ≤15 seconds per claim
            - Memory usage ≤200MB peak
            - Error rate <5%
        """

    def process_single_claim(self, claim: str) -> TrustCapsule:
        """
        Process single claim through complete pipeline

        Args:
            claim: Claim text to analyze

        Returns:
            TrustCapsule with complete analysis

        Processing Pipeline:
            1. ACI: Claim interpretation and analysis
            2. EEG: Evidence gathering and validation
            3. Consensus: Multi-AI quality assessment
            4. Scoring: Trust score and grade calculation
            5. Formatting: TrustCapsule creation
        """

    def get_processing_stats(self) -> Dict[str, Any]:
        """Return performance statistics for monitoring"""

    def health_check(self) -> Dict[str, bool]:
        """Check health status of all components"""
```

### **Error Handling Specification**

```python
# evidence_engine_v3/core/exceptions.py

class EvidenceEngineError(Exception):
    """Base exception for Evidence Engine V3"""
    pass

class ACIProcessingError(EvidenceEngineError):
    """ACI module processing failure"""
    pass

class EEGGatheringError(EvidenceEngineError):
    """EEG module evidence gathering failure"""
    pass

class ConsensusAnalysisError(EvidenceEngineError):
    """Consensus analysis module failure"""
    pass

class ScoringError(EvidenceEngineError):
    """Scoring module calculation failure"""
    pass

class PerformanceError(EvidenceEngineError):
    """Performance requirement violation"""
    pass

class IntegrationError(EvidenceEngineError):
    """Integration with external services failure"""
    pass
```

---

## **COMPONENT 2: ACI MODULE**

### **Class: SemanticAnalyzer**

**Location**: `evidence_engine_v3/claim_interpretation/semantic_analyzer.py`

```python
class SemanticAnalyzer:
    """Semantic analysis of claims for subject/object/relationship extraction"""

    def __init__(self):
        """Initialize semantic analysis components"""
        self.nlp_processor: NLPProcessor
        self.relationship_patterns: Dict[str, List[str]]
        self.temporal_patterns: Dict[str, List[str]]
        self.certainty_patterns: Dict[str, List[str]]

    def analyze(self, claim_text: str) -> SemanticAnalysisResult:
        """
        Perform complete semantic analysis of claim

        Args:
            claim_text: Text of claim to analyze

        Returns:
            SemanticAnalysisResult with complete analysis

        Raises:
            SemanticAnalysisError: If analysis fails

        Performance Requirements:
            - Processing time <200ms per claim
            - Accuracy >95% for subject/object identification
            - Accuracy >90% for relationship type classification
        """

    def extract_subject_object(self, claim_text: str) -> Tuple[str, str]:
        """Extract subject and object from causal claims"""

    def classify_relationship(self, claim_text: str) -> str:
        """Classify relationship type (causal, comparative, descriptive)"""

    def detect_temporal_aspect(self, claim_text: str) -> str:
        """Detect temporal aspect (future, past, present)"""

    def assess_certainty_level(self, claim_text: str) -> str:
        """Assess certainty level (definitive, probable, speculative)"""
```

### **Class: LogicalAnalyzer**

**Location**: `evidence_engine_v3/claim_interpretation/logical_analyzer.py`

```python
class LogicalAnalyzer:
    """Logical structure analysis for causation vs correlation detection"""

    def __init__(self):
        """Initialize logical analysis components"""
        self.causation_patterns: List[str]
        self.correlation_patterns: List[str]
        self.conditional_patterns: List[str]
        self.qualifier_patterns: List[str]

    def analyze(self, claim_text: str, semantic_result: SemanticAnalysisResult) -> LogicalAnalysisResult:
        """
        Perform complete logical analysis of claim

        Args:
            claim_text: Text of claim to analyze
            semantic_result: Results from semantic analysis

        Returns:
            LogicalAnalysisResult with complete analysis

        Performance Requirements:
            - Processing time <200ms per claim
            - Accuracy >90% for causation vs correlation
            - Accuracy >85% for conditional statement detection
        """

    def detect_causation_correlation(self, claim_text: str) -> str:
        """Distinguish causation claims from correlation claims"""

    def extract_logical_operators(self, claim_text: str) -> List[str]:
        """Extract logical operators and connectives"""

    def classify_claim_scope(self, claim_text: str) -> str:
        """Classify scope as universal, particular, or conditional"""

    def generate_evidence_requirements(self, claim_text: str, assertion_type: str) -> Dict[str, str]:
        """Generate evidence requirements based on logical structure"""
```

### **Class: ClaimClassifier**

**Location**: `evidence_engine_v3/claim_interpretation/claim_classifier.py`

```python
class ClaimClassifier:
    """Domain classification and evidence strategy generation"""

    def __init__(self):
        """Initialize classification system"""
        self.domain_keywords: Dict[str, List[str]]
        self.evidence_strategies: Dict[str, List[str]]
        self.source_priorities: Dict[str, List[str]]
        self.methodology_requirements: Dict[str, List[str]]

    def classify(self, claim_text: str, semantic_result: SemanticAnalysisResult,
                 logical_result: LogicalAnalysisResult) -> DomainClassificationResult:
        """
        Classify claim domain and generate evidence strategy

        Args:
            claim_text: Text of claim to classify
            semantic_result: Results from semantic analysis
            logical_result: Results from logical analysis

        Returns:
            DomainClassificationResult with classification and strategy

        Performance Requirements:
            - Processing time <100ms per claim
            - Classification accuracy >85%
            - Evidence strategy completeness >90%
        """

    def classify_domain(self, claim_text: str) -> Tuple[str, float]:
        """Classify claim into domain category"""

    def generate_evidence_strategy(self, domain: str, logical_type: str) -> List[str]:
        """Generate evidence strategy based on domain and logical type"""

    def prioritize_sources(self, domain: str) -> List[str]:
        """Generate source priority list for domain"""
```

### **Class: ClaimInterpretationProcessor**

**Location**: `evidence_engine_v3/claim_interpretation/__init__.py`

```python
class ClaimInterpretationProcessor:
    """Main orchestrator for ACI module"""

    def __init__(self):
        """Initialize all ACI components"""
        self.semantic_analyzer = SemanticAnalyzer()
        self.logical_analyzer = LogicalAnalyzer()
        self.claim_classifier = ClaimClassifier()
        self.error_handler = ACIErrorHandler()

    def analyze_claim(self, claim_text: str) -> ClaimInterpretation:
        """
        Complete claim interpretation pipeline

        Args:
            claim_text: Claim to analyze

        Returns:
            ClaimInterpretation with complete analysis

        Raises:
            ACIProcessingError: If any analysis stage fails

        Performance Requirements:
            - Total processing time <500ms per claim
            - Memory usage <50MB per claim
            - Success rate >95%
        """
```

---

## **COMPONENT 3: EEG MODULE**

### **Class: MethodologyStrategist**

**Location**: `evidence_engine_v3/evidence_gathering/methodology_strategist.py`

```python
class MethodologyStrategist:
    """IFCN-compliant search strategy generation"""

    def __init__(self):
        """Initialize methodology strategist"""
        self.methodology_types: Dict[str, Dict]
        self.ifcn_validator: IFCNComplianceValidator
        self.query_optimizer: QueryOptimizer
        self.max_queries_per_claim: int = 12

    def generate_search_strategy(self, claim_text: str,
                                interpretation: ClaimInterpretation) -> SearchStrategy:
        """
        Generate IFCN-compliant search strategy

        Args:
            claim_text: Claim text for evidence search
            interpretation: ACI analysis results

        Returns:
            SearchStrategy with optimized queries

        Raises:
            EEGGatheringError: If strategy generation fails

        Performance Requirements:
            - Query count ≤12 per claim
            - Generation time <2 seconds
            - IFCN compliance 100%
        """

    def generate_methodology_queries(self, claim_text: str, domain: str) -> List[SearchQuery]:
        """Generate queries based on methodology requirements"""

    def validate_ifcn_compliance(self, strategy: SearchStrategy) -> Tuple[bool, List[str]]:
        """Validate strategy meets IFCN standards"""

    def optimize_query_performance(self, queries: List[SearchQuery]) -> List[SearchQuery]:
        """Optimize queries for performance while maintaining quality"""
```

### **Class: SearchExecutor**

**Location**: `evidence_engine_v3/evidence_gathering/search_executor.py`

```python
class SearchExecutor:
    """Parallel evidence search execution"""

    def __init__(self):
        """Initialize search executor"""
        self.web_search_service: WebSearchService
        self.content_extractor: WebContentExtractor
        self.thread_pool: ThreadPoolExecutor
        self.max_concurrent_searches: int = 6
        self.timeout_per_query: int = 8

    def execute_search(self, strategy: SearchStrategy) -> List[EvidenceCandidate]:
        """
        Execute search strategy with parallel processing

        Args:
            strategy: Complete search strategy to execute

        Returns:
            List of evidence candidates found

        Raises:
            SearchExecutionError: If search execution fails

        Performance Requirements:
            - Total execution time ≤12 seconds
            - Parallel execution of up to 6 queries
            - Timeout protection for individual queries
        """

    def execute_single_query(self, query: SearchQuery) -> List[EvidenceCandidate]:
        """Execute single search query"""

    def extract_content_parallel(self, urls: List[str]) -> List[EvidenceCandidate]:
        """Extract content from multiple URLs in parallel"""

    def filter_candidates_by_relevance(self, candidates: List[EvidenceCandidate],
                                     claim_text: str) -> List[EvidenceCandidate]:
        """Filter candidates by relevance to claim"""
```

### **Class: QualityValidator**

**Location**: `evidence_engine_v3/evidence_gathering/quality_validator.py`

```python
class QualityValidator:
    """Evidence quality assessment and IFCN validation"""

    def __init__(self):
        """Initialize quality validator"""
        self.ifcn_compliance_checker: IFCNComplianceChecker
        self.methodology_assessor: MethodologyAssessor
        self.relevance_scorer: RelevanceScorer
        self.ai_processor: AIEvidenceProcessor

    def validate_evidence_pool(self, candidates: List[EvidenceCandidate],
                              claim_text: str, strategy: SearchStrategy) -> List[ProcessedEvidence]:
        """
        Validate and process evidence candidates

        Args:
            candidates: Raw evidence candidates
            claim_text: Original claim for relevance assessment
            strategy: Search strategy used

        Returns:
            List of validated and processed evidence

        Performance Requirements:
            - Processing time <3 seconds for up to 50 candidates
            - Quality accuracy >80%
            - Relevance scoring accuracy >75%
        """

    def assess_evidence_quality(self, candidate: EvidenceCandidate) -> float:
        """Assess methodology quality of evidence source"""

    def score_relevance_to_claim(self, candidate: EvidenceCandidate, claim_text: str) -> float:
        """Score relevance of evidence to specific claim"""

    def process_with_ai(self, candidate: EvidenceCandidate, claim_text: str) -> ProcessedEvidence:
        """Process evidence through AI for stance and relevance"""
```

### **Class: EnhancedEvidenceGatherer**

**Location**: `evidence_engine_v3/evidence_gathering/__init__.py`

```python
class EnhancedEvidenceGatherer:
    """Main orchestrator for EEG module"""

    def __init__(self):
        """Initialize all EEG components"""
        self.methodology_strategist = MethodologyStrategist()
        self.search_executor = SearchExecutor()
        self.quality_validator = QualityValidator()
        self.performance_monitor = PerformanceMonitor()

    def gather_evidence(self, claim_text: str,
                       interpretation: ClaimInterpretation) -> EvidencePool:
        """
        Complete evidence gathering pipeline

        Args:
            claim_text: Claim for evidence gathering
            interpretation: ACI analysis results

        Returns:
            EvidencePool with validated evidence

        Raises:
            EEGGatheringError: If evidence gathering fails

        Performance Requirements:
            - Total processing time ≤15 seconds
            - Evidence quality score >0.7
            - IFCN compliance 100%
        """
```

---

## **COMPONENT 4: CONSENSUS ANALYSIS MODULE**

### **Class: DualAIProcessor**

**Location**: `evidence_engine_v3/consensus_analysis/dual_ai_processor.py`

```python
class DualAIProcessor:
    """Multi-AI consensus analysis system"""

    def __init__(self):
        """Initialize dual AI processing"""
        self.primary_shepherd: ROGREvidenceShepherd
        self.secondary_shepherd: ROGREvidenceShepherd
        self.consensus_calculator: ConsensusCalculator
        self.uncertainty_quantifier: UncertaintyQuantifier

    def analyze_evidence(self, claim_text: str,
                        evidence_pool: EvidencePool) -> ConsensusResult:
        """
        Perform dual-AI consensus analysis on evidence pool

        Args:
            claim_text: Original claim text
            evidence_pool: Validated evidence for analysis

        Returns:
            ConsensusResult with multi-AI assessment

        Raises:
            ConsensusAnalysisError: If consensus analysis fails

        Performance Requirements:
            - Processing time <5 seconds
            - Minimum 2 AI assessments required
            - Uncertainty quantification accuracy >80%
        """

    def get_individual_assessments(self, claim_text: str,
                                  evidence_pool: EvidencePool) -> List[AIConsensusScore]:
        """Get individual AI assessments"""

    def calculate_consensus_score(self, individual_scores: List[AIConsensusScore]) -> float:
        """Calculate weighted consensus score"""

    def quantify_uncertainty(self, individual_scores: List[AIConsensusScore]) -> List[str]:
        """Quantify uncertainty and generate indicators"""
```

### **Class: QualityAssessor**

**Location**: `evidence_engine_v3/consensus_analysis/quality_assessor.py`

```python
class QualityAssessor:
    """Comprehensive evidence quality assessment"""

    def __init__(self):
        """Initialize quality assessment system"""
        self.methodology_scorer: MethodologyScorer
        self.source_evaluator: SourceEvaluator
        self.ifcn_validator: IFCNValidator

    def assess_evidence_quality(self, evidence_pool: EvidencePool) -> Dict[str, float]:
        """
        Comprehensive quality assessment of evidence pool

        Args:
            evidence_pool: Evidence pool to assess

        Returns:
            Dictionary with quality metrics

        Quality Metrics:
            - overall_score: 0-1, overall quality assessment
            - source_quality: 0-1, source reliability assessment
            - methodology_score: 0-1, methodology quality score
            - relevance_score: 0-1, relevance to claim score
            - ifcn_compliant: bool, IFCN compliance status
        """
```

---

## **COMPONENT 5: SCORING MODULE**

### **Class: TrustCalculator**

**Location**: `evidence_engine_v3/scoring/trust_calculator.py`

```python
class TrustCalculator:
    """Professional fact-checking trust score calculation"""

    def __init__(self):
        """Initialize trust calculation system"""
        self.base_scorer: BaseScorer
        self.quality_adjuster: QualityAdjuster
        self.uncertainty_processor: UncertaintyProcessor
        self.rogr_engine: ROGRFCScoringEngineZeroStart

    def calculate_trust_score(self, claim_text: str,
                             consensus_result: ConsensusResult) -> TrustScore:
        """
        Calculate final trust score using ROGR methodology

        Args:
            claim_text: Original claim text
            consensus_result: Consensus analysis results

        Returns:
            TrustScore with complete calculation details

        Scoring Methodology:
            1. Base score from AI consensus
            2. Quality adjustment based on evidence methodology
            3. Uncertainty penalty for low confidence
            4. ROGR professional scaling
        """

    def apply_quality_adjustments(self, base_score: float,
                                 quality_metrics: Dict[str, float]) -> float:
        """Apply evidence quality adjustments to base score"""

    def apply_uncertainty_penalties(self, score: float,
                                   uncertainty_level: float) -> float:
        """Apply uncertainty penalties to score"""
```

### **Class: GradeEngine**

**Location**: `evidence_engine_v3/scoring/grade_engine.py`

```python
class GradeEngine:
    """Evidence grade calculation (A+ through F)"""

    def __init__(self):
        """Initialize grade calculation system"""
        self.grade_thresholds: Dict[int, str] = {
            97: 'A+', 90: 'A', 87: 'A-', 80: 'B+',
            77: 'B', 73: 'B-', 70: 'C+', 67: 'C',
            63: 'C-', 60: 'D+', 50: 'D'
        }
        self.methodology_assessor: MethodologyAssessor

    def calculate_evidence_grade(self, trust_score: TrustScore,
                                evidence_pool: EvidencePool) -> EvidenceGrade:
        """
        Calculate evidence grade based on trust score and methodology quality

        Args:
            trust_score: Calculated trust score
            evidence_pool: Original evidence pool

        Returns:
            EvidenceGrade with grade and reasoning

        Grading Criteria:
            - Trust score: Primary factor (0-100)
            - Methodology quality: Secondary factor
            - Source diversity: Tertiary factor
            - IFCN compliance: Required for grades >C
        """
```

### **Class: CapsuleFormatter**

**Location**: `evidence_engine_v3/scoring/capsule_formatter.py`

```python
class CapsuleFormatter:
    """TrustCapsule output formatting"""

    def __init__(self):
        """Initialize capsule formatter"""
        self.citation_extractor: CitationExtractor
        self.summary_generator: SummaryGenerator
        self.id_generator: IDGenerator

    def format_capsule(self, claim_text: str, trust_score: TrustScore,
                      evidence_grade: EvidenceGrade, consensus_result: ConsensusResult,
                      evidence_pool: EvidencePool) -> TrustCapsule:
        """
        Format complete analysis into TrustCapsule

        Args:
            claim_text: Original claim
            trust_score: Calculated trust score
            evidence_grade: Evidence grade
            consensus_result: Consensus analysis
            evidence_pool: Evidence used

        Returns:
            TrustCapsule matching existing API contract exactly

        Format Requirements:
            - Must match main.py TrustCapsule structure 100%
            - All required fields populated
            - Citations from actual evidence sources
            - Summary bullets from evidence analysis
        """

    def extract_citations(self, evidence_pool: EvidencePool) -> List[Citation]:
        """Extract citations from evidence pool"""

    def generate_summary_bullets(self, consensus_result: ConsensusResult,
                                evidence_pool: EvidencePool) -> List[str]:
        """Generate summary bullets for why array"""

    def generate_overall_assessment(self, trust_score: TrustScore,
                                   evidence_grade: EvidenceGrade) -> str:
        """Generate overall assessment text"""
```

---

## **INTEGRATION SPECIFICATIONS**

### **Main Integration Point**

```python
# Integration with main.py - EXACT interface preservation

# BEFORE (existing main.py):
claim_analysis = await score_claim_with_evidence_shepherd(claim_text, claim_context)

# AFTER (Evidence Engine V3):
from evidence_engine_v3 import EvidenceEngineV3

evidence_engine = EvidenceEngineV3()
trust_capsules = evidence_engine.process_claims([claim_text])
claim_analysis = trust_capsules[0]  # Same ClaimAnalysis format
```

### **Data Format Compatibility**

```python
# CRITICAL: TrustCapsule format must match existing exactly

# Existing main.py TrustCapsule (lines 72-86):
TrustCapsule(
    id=str,
    trust_score=int,           # 0-100 range MUST be preserved
    evidence_grade=str,        # A+ through F scale MUST be preserved
    confidence=str,            # High/Medium/Low MUST be preserved
    why=List[str],            # Summary bullets MUST be preserved
    claims=List[ClaimAnalysis], # Detailed analysis MUST be preserved
    overall_assessment=str,    # Assessment text MUST be preserved
    citations=List[Citation],  # Source citations MUST be preserved
    capsule_version=int,       # Version tracking MUST be preserved
    signed=bool,              # Signature field MUST be preserved
    created_at=str,           # Timestamp MUST be preserved
    input_type=str,           # Input type MUST be preserved
    mode=str                  # Analysis mode MUST be preserved
)
```

---

## **PERFORMANCE SPECIFICATIONS**

### **Processing Time Requirements**

| Component | Time Limit | Measurement Method |
|-----------|------------|-------------------|
| ACI Module | <500ms per claim | End-to-end ACI processing |
| EEG Module | ≤15s per claim | Strategy + Search + Validation |
| Consensus Analysis | <5s per claim | Multi-AI processing |
| Scoring Module | <1s per claim | Trust score + Grade calculation |
| **Total Pipeline** | **≤15s per claim** | **Complete process_claims() execution** |

### **Resource Constraints**

| Resource | Limit | Monitoring Method |
|----------|--------|-------------------|
| Memory Usage | <200MB peak per claim | Memory profiling during processing |
| Concurrent Requests | ≥3 simultaneous claims | Load testing with parallel requests |
| Query Count | ≤12 queries per claim | EEG module query counting |
| Error Rate | <5% in production | Error tracking over time |

### **Quality Requirements**

| Quality Metric | Target | Validation Method |
|----------------|---------|-------------------|
| Evidence Relevance | >70% | Human evaluation of evidence quality |
| Trust Score Accuracy | >85% | Comparison with expert fact-checkers |
| IFCN Compliance | 100% | Automated compliance checking |
| API Compatibility | 100% | Automated testing against existing contracts |

---

## **TESTING SPECIFICATIONS**

### **Unit Test Requirements**

Each component must have comprehensive unit tests covering:

1. **Happy Path Testing**: All methods work correctly with valid inputs
2. **Edge Case Testing**: Boundary conditions and unusual inputs
3. **Error Handling Testing**: All exception paths covered
4. **Performance Testing**: Processing time and resource usage validation
5. **Integration Testing**: Component interaction validation

### **Test Coverage Requirements**

- **Code Coverage**: >90% line coverage for all components
- **Branch Coverage**: >85% branch coverage for decision logic
- **Error Path Coverage**: 100% of exception handling paths tested
- **Integration Coverage**: All component interfaces tested

### **Performance Test Specifications**

```python
# Required performance tests for each component

class TestPerformanceRequirements:

    def test_aci_processing_time(self):
        """ACI module must process claims in <500ms"""
        assert processing_time < 0.5

    def test_eeg_processing_time(self):
        """EEG module must complete in ≤15 seconds"""
        assert processing_time <= 15.0

    def test_complete_pipeline_time(self):
        """Complete pipeline must finish in ≤15 seconds per claim"""
        assert total_processing_time <= 15.0

    def test_memory_usage(self):
        """Memory usage must stay under 200MB peak"""
        assert peak_memory_usage < 200_000_000  # bytes

    def test_concurrent_processing(self):
        """Must handle ≥3 concurrent claims"""
        assert can_process_concurrent_claims >= 3
```

---

## **IMPLEMENTATION VALIDATION CHECKLIST**

### **Pre-Implementation Validation (Layer 1)**
- [ ] All component interfaces completely specified
- [ ] All data structures defined with exact field types
- [ ] All integration points documented with examples
- [ ] All dependencies identified and available
- [ ] All performance requirements quantified
- [ ] All error handling scenarios specified

### **Implementation Validation (Layer 2)**
- [ ] Each component implements exact interface specification
- [ ] All method signatures match specification exactly
- [ ] All data types comply with interface definitions
- [ ] All error handling follows specification patterns
- [ ] All integration points tested in isolation

### **Post-Implementation Validation (Layer 3)**
- [ ] Complete system meets all performance requirements
- [ ] All API contracts maintained exactly
- [ ] All quality metrics achieved
- [ ] All IFCN compliance requirements met
- [ ] All error scenarios handled gracefully
- [ ] Complete system ready for production deployment

---

**This specification document provides complete architectural and implementation details for Evidence Engine V3, ensuring zero assumptions during development and full compliance with RDT v2.0 and FLAWLESS_IMPLEMENTATION_METHODOLOGY.md requirements.**