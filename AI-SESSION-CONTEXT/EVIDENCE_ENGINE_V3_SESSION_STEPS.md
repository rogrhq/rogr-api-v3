# **EVIDENCE ENGINE V3: AI SESSION IMPLEMENTATION STEPS**
*Granular Steps for Auto-Compact Window Management*

**Document Version**: 1.0
**Date Created**: December 17, 2024
**Purpose**: Break down Evidence Engine V3 implementation into context-independent AI session steps
**Session Duration Target**: 60-75 minutes per step
**Context Dependency**: Zero - each step is self-contained

---

## **STEP EXECUTION FRAMEWORK**

### **Pre-Session Requirements:**
1. Load this document + current progress from context management protocol
2. Verify step prerequisites are met
3. Identify specific deliverable for this session
4. Set 60-75 minute timer for auto-compact management

### **Post-Session Requirements:**
1. Update progress tracking document
2. Commit changes with descriptive messages
3. Document any deviations or issues encountered
4. Set up next session context handoff

---

## **PHASE 1: CLEAN ROOM SETUP**

### **STEP 1.1: Create Clean Directory Structure**
*Session Duration: 60 minutes*

#### **Goal:**
Create isolated `evidence_engine_v3/` directory with complete module structure and zero legacy contamination.

#### **AI Session Prompt:**
```
Create Evidence Engine V3 directory structure in rogr-api/evidence_engine_v3/ with the following exact layout:

evidence_engine_v3/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── evidence_engine.py
│   ├── interfaces.py
│   └── exceptions.py
├── claim_interpretation/
│   ├── __init__.py
│   ├── semantic_analyzer.py
│   ├── logical_analyzer.py
│   └── claim_classifier.py
├── evidence_gathering/
│   ├── __init__.py
│   ├── methodology_strategist.py
│   ├── search_executor.py
│   └── quality_validator.py
├── consensus_analysis/
│   ├── __init__.py
│   ├── dual_ai_processor.py
│   ├── quality_assessor.py
│   └── uncertainty_quantifier.py
├── scoring/
│   ├── __init__.py
│   ├── trust_calculator.py
│   ├── grade_engine.py
│   └── capsule_formatter.py
└── tests/
    ├── __init__.py
    ├── test_integration.py
    ├── test_aci_module.py
    ├── test_eeg_module.py
    └── test_performance.py

Create all files with proper Python docstrings and placeholder implementations. Each file must be syntactically valid Python.
```

#### **What AI Needs to Do:**
1. Create directory structure exactly as specified
2. Generate all __init__.py files with proper imports
3. Create placeholder classes/functions in each module file
4. Add comprehensive docstrings explaining each component's purpose
5. Ensure all files are syntactically valid (can be imported)

#### **What You Need to Monitor:**
- [ ] Directory structure matches specification exactly
- [ ] All files created and contain valid Python syntax
- [ ] No references to legacy systems anywhere
- [ ] Docstrings explain purpose of each component
- [ ] Import statements work without errors

#### **Success Criteria:**
```bash
# Verify structure
find evidence_engine_v3/ -name "*.py" | wc -l  # Should be 21 files
python -c "import evidence_engine_v3; print('Structure OK')"

# Verify no legacy contamination
grep -r "legacy_evidence" evidence_engine_v3/  # Should return nothing
grep -r "parallel_evidence" evidence_engine_v3/  # Should return nothing
```

#### **Troubleshooting:**
- **Import Errors**: Check __init__.py files have correct import statements
- **Missing Files**: Re-run file creation ensuring all paths are absolute
- **Syntax Errors**: Validate each .py file individually with `python -m py_compile`

---

### **STEP 1.2: Define Core Interfaces**
*Session Duration: 70 minutes*

#### **Goal:**
Implement complete data structures and interfaces in `core/interfaces.py` that match existing TrustCapsule API contract.

#### **AI Session Prompt:**
```
Implement evidence_engine_v3/core/interfaces.py with ALL data structures needed for Evidence Engine V3. Must include:

1. ClaimInterpretation - ACI module output
2. EvidencePool - EEG module output
3. ConsensusResult - Consensus module output
4. TrustCapsule - Final output (MUST match existing main.py TrustCapsule exactly)
5. All supporting dataclasses

Reference existing main.py lines 44-86 for TrustCapsule structure. The V3 TrustCapsule must be 100% compatible with existing FastAPI contract.

Also implement core/exceptions.py with custom exceptions for each module.
```

#### **What AI Needs to Do:**
1. Examine existing main.py TrustCapsule definition (lines 44-86)
2. Create identical TrustCapsule structure in interfaces.py
3. Define all intermediate data structures (ClaimInterpretation, EvidencePool, etc.)
4. Add comprehensive type hints and validation
5. Create custom exception classes for error handling

#### **What You Need to Monitor:**
- [ ] TrustCapsule structure 100% matches main.py definition
- [ ] All required fields present with correct types
- [ ] Type hints are comprehensive and accurate
- [ ] Custom exceptions cover all error scenarios
- [ ] Documentation explains each data structure's role

#### **Success Criteria:**
```python
# Test interface compatibility
from evidence_engine_v3.core.interfaces import TrustCapsule
from main import TrustCapsule as ExistingTrustCapsule

# Compare field names and types
v3_fields = set(TrustCapsule.__dataclass_fields__.keys())
existing_fields = set(ExistingTrustCapsule.__fields__.keys())
assert v3_fields == existing_fields, "TrustCapsule fields don't match"

# Test instantiation
test_capsule = TrustCapsule(
    id="test",
    trust_score=75,
    evidence_grade="B+",
    confidence="Medium",
    why=["Test reason"],
    claims=[],
    overall_assessment="Test assessment",
    citations=[],
    capsule_version=1,
    signed=True,
    created_at="2024-12-17T10:00:00",
    input_type="text",
    mode="both"
)
print("Interface compatibility: OK")
```

#### **Troubleshooting:**
- **Field Mismatch**: Compare with existing TrustCapsule line-by-line
- **Type Errors**: Ensure all type hints match expected data types
- **Import Issues**: Check that all dependencies are properly imported

---

### **STEP 1.3: Create Integration Stub**
*Session Duration: 65 minutes*

#### **Goal:**
Implement core/evidence_engine.py stub that connects to main.py and returns mock TrustCapsules.

#### **AI Session Prompt:**
```
Implement evidence_engine_v3/core/evidence_engine.py as a working stub that:

1. Implements EvidenceEngineV3 class with process_claims() method
2. Returns mock TrustCapsules that match exact format expected by main.py
3. Includes realistic mock data (trust scores, evidence grades, citations)
4. Processes multiple claims properly
5. Has proper error handling and logging

Also create evidence_engine_v3/__init__.py that exports EvidenceEngineV3 for easy import.

The stub should be production-ready (handles errors gracefully) but with mock data.
```

#### **What AI Needs to Do:**
1. Implement EvidenceEngineV3 class with all required methods
2. Create realistic mock TrustCapsule responses
3. Handle edge cases (empty claims, invalid input)
4. Add comprehensive logging for debugging
5. Ensure easy import from main.py

#### **What You Need to Monitor:**
- [ ] EvidenceEngineV3 class implements required interface
- [ ] Mock TrustCapsules have realistic data
- [ ] Error handling covers common failure modes
- [ ] Logging provides useful debugging information
- [ ] Import works cleanly from main.py

#### **Success Criteria:**
```python
# Test stub functionality
from evidence_engine_v3 import EvidenceEngineV3

engine = EvidenceEngineV3()
test_claims = ["Test claim 1", "Test claim 2"]
results = engine.process_claims(test_claims)

assert len(results) == 2, "Should process all claims"
assert all(isinstance(r.trust_score, int) for r in results), "Trust scores should be integers"
assert all(r.evidence_grade in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F'] for r in results), "Valid evidence grades"

# Test error handling
empty_results = engine.process_claims([])
assert len(empty_results) == 0, "Should handle empty input"

print("Stub implementation: OK")
```

#### **Troubleshooting:**
- **Import Errors**: Check __init__.py export and module structure
- **Data Type Issues**: Ensure mock data matches expected types exactly
- **Error Handling**: Test with various invalid inputs to verify graceful handling

---

### **STEP 1.4: Integrate Stub with FastAPI**
*Session Duration: 60 minutes*

#### **Goal:**
Modify main.py to use Evidence Engine V3 stub without breaking existing functionality.

#### **AI Session Prompt:**
```
Modify main.py to use Evidence Engine V3 as follows:

1. Add import for EvidenceEngineV3 at top of file
2. Initialize evidence_engine_v3 instance after existing service initialization
3. Add environment variable USE_EVIDENCE_ENGINE_V3 (default: false) for testing
4. Modify score_claim_with_evidence_shepherd() to use V3 when flag is enabled
5. Ensure fallback to existing system when V3 disabled
6. Add debug logging to show which system is being used

DO NOT modify existing Evidence Shepherd logic - only add V3 as optional alternative.
```

#### **What AI Needs to Do:**
1. Import Evidence Engine V3 without breaking existing imports
2. Add feature flag for V3 testing
3. Modify claim processing to conditionally use V3
4. Maintain all existing functionality as fallback
5. Add clear debug logging

#### **What You Need to Monitor:**
- [ ] Existing functionality unchanged when V3 disabled
- [ ] V3 integration works when flag enabled
- [ ] Debug logging clearly indicates which system is active
- [ ] No breaking changes to existing API responses
- [ ] Error handling preserves existing behavior

#### **Success Criteria:**
```bash
# Test with V3 disabled (default behavior)
export USE_EVIDENCE_ENGINE_V3=false
curl localhost:8000/analyses -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":"test claim","type":"text"}' | jq '.trust_score'
# Should work exactly as before

# Test with V3 enabled
export USE_EVIDENCE_ENGINE_V3=true
curl localhost:8000/analyses -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":"test claim","type":"text"}' | jq '.trust_score'
# Should return mock V3 response
```

#### **Troubleshooting:**
- **Import Errors**: Ensure Evidence Engine V3 path is correct
- **Environment Variable**: Verify flag is read correctly from environment
- **Response Format**: Compare V3 response structure with existing responses

---

## **PHASE 2: ACI IMPLEMENTATION**

### **STEP 2.1: Implement Semantic Analyzer**
*Session Duration: 75 minutes*

#### **Goal:**
Build semantic_analyzer.py that identifies subjects, objects, relationships, and temporal aspects in claims.

#### **AI Session Prompt:**
```
Implement evidence_engine_v3/claim_interpretation/semantic_analyzer.py with:

1. SemanticAnalyzer class with analyze() method
2. Extract subject/object from causal claims ("X affects Y")
3. Identify relationship types (causal, comparative, descriptive)
4. Detect temporal aspects (future, past, present)
5. Determine certainty levels (definitive, probable, speculative)

Test with these claims:
- "Climate change policies will destroy the economy"
- "Vaccines cause autism"
- "AI will replace human jobs"
- "The economy was destroyed by climate change"

Use regex patterns and NLP techniques. Target <500ms processing time.
```

#### **What AI Needs to Do:**
1. Create SemanticAnalyzer class with robust text analysis
2. Implement subject/object extraction using NLP patterns
3. Build relationship type classification logic
4. Add temporal aspect detection (tense analysis)
5. Create certainty level assessment
6. Optimize for speed (<500ms per claim)

#### **What You Need to Monitor:**
- [ ] Correctly identifies subjects and objects in test claims
- [ ] Relationship types are accurately classified
- [ ] Temporal aspects match claim tense/timing
- [ ] Certainty levels reflect claim confidence language
- [ ] Processing speed meets <500ms target

#### **Success Criteria:**
```python
from evidence_engine_v3.claim_interpretation.semantic_analyzer import SemanticAnalyzer
import time

analyzer = SemanticAnalyzer()
test_claims = [
    "Climate change policies will destroy the economy",
    "Vaccines cause autism",
    "AI will replace human jobs"
]

for claim in test_claims:
    start = time.time()
    result = analyzer.analyze(claim)
    duration = time.time() - start

    print(f"Claim: {claim}")
    print(f"Subject: {result.subject}")
    print(f"Object: {result.object}")
    print(f"Relationship: {result.relationship_type}")
    print(f"Temporal: {result.temporal_aspect}")
    print(f"Certainty: {result.certainty_level}")
    print(f"Processing: {duration:.3f}s")

    assert duration < 0.5, f"Too slow: {duration:.3f}s"
    assert result.subject and result.object, "Missing subject/object"

print("Semantic analysis: PASSED")
```

#### **Troubleshooting:**
- **Accuracy Issues**: Refine regex patterns or add more linguistic rules
- **Performance Issues**: Optimize text processing and reduce complex operations
- **Missing Fields**: Ensure all result fields are populated for every claim type

---

### **STEP 2.2: Implement Logical Analyzer**
*Session Duration: 70 minutes*

#### **Goal:**
Build logical_analyzer.py that distinguishes causation vs correlation and identifies logical structures.

#### **AI Session Prompt:**
```
Implement evidence_engine_v3/claim_interpretation/logical_analyzer.py with:

1. LogicalAnalyzer class with analyze() method
2. Detect causation vs correlation ("causes" vs "associated with")
3. Identify conditional statements ("if X then Y")
4. Classify claim scope (universal, particular, conditional)
5. Extract qualifying language ("might", "always", "never")
6. Generate evidence requirements for claim verification

Test with:
- "Smoking causes cancer" (causation)
- "Cancer rates are higher among smokers" (correlation)
- "If minimum wage increases, unemployment will rise" (conditional)
- "All vaccines are safe" (universal)
```

#### **What AI Needs to Do:**
1. Build logic for causation vs correlation detection
2. Implement conditional statement parsing
3. Create scope classification (universal/particular/conditional)
4. Extract qualifying language and hedging words
5. Generate appropriate evidence requirements for each claim type

#### **What You Need to Monitor:**
- [ ] Correctly distinguishes causation from correlation
- [ ] Identifies conditional statements properly
- [ ] Scope classification is accurate
- [ ] Qualifying language is captured
- [ ] Evidence requirements are appropriate for claim type

#### **Success Criteria:**
```python
from evidence_engine_v3.claim_interpretation.logical_analyzer import LogicalAnalyzer

analyzer = LogicalAnalyzer()
test_cases = [
    ("Smoking causes cancer", "causal"),
    ("Cancer rates are higher among smokers", "correlational"),
    ("If minimum wage increases, unemployment will rise", "conditional"),
    ("All vaccines are safe", "universal")
]

for claim, expected_type in test_cases:
    result = analyzer.analyze(claim)
    print(f"Claim: {claim}")
    print(f"Expected: {expected_type}, Got: {result.assertion_type}")
    print(f"Logic operators: {result.logical_operators}")
    print(f"Scope: {result.claim_scope}")
    print(f"Qualifying language: {result.qualifying_language}")
    print("---")

    assert result.assertion_type == expected_type, f"Wrong classification for: {claim}"

print("Logical analysis: PASSED")
```

#### **Troubleshooting:**
- **Classification Errors**: Review test cases and adjust detection logic
- **Missing Patterns**: Add more linguistic patterns for edge cases
- **Evidence Requirements**: Ensure requirements make sense for claim types

---

### **STEP 2.3: Implement Claim Classifier**
*Session Duration: 65 minutes*

#### **Goal:**
Build claim_classifier.py that categorizes claims by domain and generates evidence strategies.

#### **AI Session Prompt:**
```
Implement evidence_engine_v3/claim_interpretation/claim_classifier.py with:

1. ClaimClassifier class with classify() method
2. Domain classification (medical, economic, scientific, policy, historical)
3. Evidence strategy generation based on domain
4. Source priority recommendations
5. Methodology requirements for each domain type

Use keyword-based classification with domain-specific patterns:
- Medical: "health", "medicine", "treatment", "vaccine", "drug"
- Economic: "economy", "GDP", "employment", "inflation", "market"
- Scientific: "research", "study", "experiment", "data", "analysis"
- Policy: "government", "law", "regulation", "policy", "legislation"
```

#### **What AI Needs to Do:**
1. Build domain classification system using keyword patterns
2. Create evidence strategy templates for each domain
3. Generate source priority lists appropriate to domain
4. Define methodology requirements per domain type
5. Add confidence scoring for classification decisions

#### **What You Need to Monitor:**
- [ ] Domain classification is accurate for test claims
- [ ] Evidence strategies are appropriate for each domain
- [ ] Source priorities make sense for domain types
- [ ] Methodology requirements follow IFCN standards
- [ ] Classification confidence scores are reasonable

#### **Success Criteria:**
```python
from evidence_engine_v3.claim_interpretation.claim_classifier import ClaimClassifier

classifier = ClaimClassifier()
test_claims = [
    ("Vaccines cause autism", "medical"),
    ("Unemployment will rise with minimum wage increases", "economic"),
    ("Climate change is caused by human activity", "scientific"),
    ("The government announced new regulations", "policy")
]

for claim, expected_domain in test_claims:
    result = classifier.classify(claim)
    print(f"Claim: {claim}")
    print(f"Domain: {result.domain} (expected: {expected_domain})")
    print(f"Confidence: {result.confidence}")
    print(f"Evidence strategy: {len(result.evidence_strategy)} requirements")
    print(f"Source priorities: {result.source_priorities[:3]}")
    print("---")

    assert result.domain == expected_domain, f"Wrong domain for: {claim}"
    assert result.confidence > 0.7, f"Low confidence for: {claim}"

print("Claim classification: PASSED")
```

#### **Troubleshooting:**
- **Misclassification**: Expand keyword lists or add more sophisticated patterns
- **Low Confidence**: Review classification logic and threshold settings
- **Evidence Strategy**: Ensure strategies are practical and IFCN-compliant

---

### **STEP 2.4: Integrate ACI Pipeline**
*Session Duration: 60 minutes*

#### **Goal:**
Create integrated ACI processor that combines all three analyzers into unified claim interpretation.

#### **AI Session Prompt:**
```
Implement evidence_engine_v3/claim_interpretation/__init__.py with:

1. ClaimInterpretationProcessor class that orchestrates all analyzers
2. Combine semantic, logical, and classification results
3. Generate comprehensive ClaimInterpretation output
4. Add error handling for analysis failures
5. Optimize pipeline for <500ms total processing time

The processor should create a single ClaimInterpretation object containing all analysis results.
```

#### **What AI Needs to Do:**
1. Create orchestrator class that coordinates all three analyzers
2. Combine results into unified ClaimInterpretation dataclass
3. Add comprehensive error handling for each analyzer
4. Optimize processing pipeline for speed
5. Add debugging and logging capabilities

#### **What You Need to Monitor:**
- [ ] All analyzers integrate properly
- [ ] Combined results are coherent and complete
- [ ] Error handling covers analyzer failures gracefully
- [ ] Total processing time meets <500ms target
- [ ] ClaimInterpretation output is comprehensive

#### **Success Criteria:**
```python
from evidence_engine_v3.claim_interpretation import ClaimInterpretationProcessor
import time

processor = ClaimInterpretationProcessor()
test_claim = "Climate change policies will destroy the economy"

start = time.time()
interpretation = processor.analyze_claim(test_claim)
duration = time.time() - start

print(f"Processing time: {duration:.3f}s")
print(f"Semantic - Subject: {interpretation.semantic.subject}")
print(f"Semantic - Object: {interpretation.semantic.object}")
print(f"Logical - Type: {interpretation.logical.assertion_type}")
print(f"Domain - Classification: {interpretation.domain.domain}")

assert duration < 0.5, f"ACI pipeline too slow: {duration:.3f}s"
assert interpretation.semantic.subject, "Missing semantic analysis"
assert interpretation.logical.assertion_type, "Missing logical analysis"
assert interpretation.domain.domain, "Missing domain classification"

print("ACI Integration: PASSED")
```

#### **Troubleshooting:**
- **Performance Issues**: Profile each analyzer to identify bottlenecks
- **Integration Errors**: Check data flow between analyzers
- **Missing Results**: Verify all analyzers return complete data structures

---

## **PHASE 3: EEG IMPLEMENTATION**

### **STEP 3.1: Implement Methodology Strategist**
*Session Duration: 75 minutes*

#### **Goal:**
Build methodology_strategist.py that generates IFCN-compliant search strategies with ≤12 queries per claim.

#### **AI Session Prompt:**
```
Implement evidence_engine_v3/evidence_gathering/methodology_strategist.py based on existing evidence_gathering/search_strategy/methodology_strategist.py:

1. Extract the working MethodologySearchStrategist class
2. Adapt it for V3 interfaces and ClaimInterpretation input
3. Ensure IFCN compliance with methodology-first approach
4. Maintain ≤12 queries per claim performance target
5. Add audit trail generation for transparency

Reference existing implementation but clean it up for V3 architecture. Must generate search strategies based on claim interpretation results.
```

#### **What AI Needs to Do:**
1. Examine existing methodology_strategist.py implementation
2. Extract working components and adapt for V3 interfaces
3. Integrate with ClaimInterpretation input from ACI module
4. Ensure IFCN compliance and audit trail generation
5. Optimize for performance (≤12 queries target)

#### **What You Need to Monitor:**
- [ ] Search strategies are IFCN-compliant (methodology-first)
- [ ] Query count stays ≤12 per claim
- [ ] Integration with ClaimInterpretation works properly
- [ ] Audit trails provide transparency
- [ ] No institutional bias in source targeting

#### **Success Criteria:**
```python
from evidence_engine_v3.evidence_gathering.methodology_strategist import MethodologyStrategist
from evidence_engine_v3.claim_interpretation import ClaimInterpretationProcessor

aci_processor = ClaimInterpretationProcessor()
strategist = MethodologyStrategist()

claim = "Climate change policies will destroy the economy"
interpretation = aci_processor.analyze_claim(claim)
strategy = strategist.generate_search_strategy(claim, interpretation)

print(f"Query count: {len(strategy.queries)}")
print(f"Methodology types: {strategy.methodology_types}")
print(f"IFCN compliant: {strategy.ifcn_compliance_status}")
print(f"Audit trail entries: {len(strategy.audit_trail)}")

assert len(strategy.queries) <= 12, f"Too many queries: {len(strategy.queries)}"
assert strategy.ifcn_compliance_status, "Not IFCN compliant"
assert len(strategy.methodology_types) >= 2, "Insufficient methodology diversity"

print("Methodology strategist: PASSED")
```

#### **Troubleshooting:**
- **Query Explosion**: Add stricter limits and prioritization logic
- **IFCN Violations**: Review methodology-first approach implementation
- **Performance Issues**: Profile query generation and optimize bottlenecks

---

### **STEP 3.2: Implement Search Executor**
*Session Duration: 75 minutes*

#### **Goal:**
Build search_executor.py that performs parallel evidence search based on methodology strategies.

#### **AI Session Prompt:**
```
Implement evidence_engine_v3/evidence_gathering/search_executor.py with:

1. SearchExecutor class that executes search strategies
2. Parallel evidence gathering using asyncio/threading
3. Integration with existing web_search_service.py and web_content_extractor.py
4. Quality filtering and relevance scoring
5. Timeout protection (≤15 seconds total processing)

Use existing services but adapt for V3 interfaces. Focus on speed and parallel processing.
```

#### **What AI Needs to Do:**
1. Create SearchExecutor with parallel processing capabilities
2. Integrate with existing web search and content extraction services
3. Implement quality filtering and relevance scoring
4. Add timeout protection and resource management
5. Optimize for ≤15 second processing target

#### **What You Need to Monitor:**
- [ ] Parallel processing works correctly
- [ ] Integration with existing services functions
- [ ] Quality filtering improves evidence relevance
- [ ] Timeout protection prevents hanging
- [ ] Processing time meets ≤15 second target

#### **Success Criteria:**
```python
from evidence_engine_v3.evidence_gathering.search_executor import SearchExecutor
from evidence_engine_v3.evidence_gathering.methodology_strategist import MethodologyStrategist
import time

executor = SearchExecutor()
strategist = MethodologyStrategist()

# Generate strategy (from previous step)
strategy = strategist.generate_search_strategy("Vaccines cause autism", None)

start = time.time()
evidence_pool = executor.execute_search(strategy)
duration = time.time() - start

print(f"Processing time: {duration:.2f}s")
print(f"Evidence count: {len(evidence_pool)}")
print(f"Average relevance: {sum(e.relevance_score for e in evidence_pool) / len(evidence_pool):.2f}")

assert duration <= 15, f"Search too slow: {duration:.2f}s"
assert len(evidence_pool) > 0, "No evidence found"
assert sum(1 for e in evidence_pool if e.relevance_score > 0.7) > 0, "Low quality evidence"

print("Search executor: PASSED")
```

#### **Troubleshooting:**
- **Timeout Issues**: Reduce query complexity or increase timeout limits
- **No Results**: Check web service integration and network connectivity
- **Quality Problems**: Adjust relevance scoring algorithms

---

### **STEP 3.3: Implement Quality Validator**
*Session Duration: 65 minutes*

#### **Goal:**
Build quality_validator.py that validates evidence quality and IFCN compliance.

#### **AI Session Prompt:**
```
Implement evidence_engine_v3/evidence_gathering/quality_validator.py with:

1. QualityValidator class for evidence assessment
2. IFCN compliance validation with detailed reporting
3. Evidence quality scoring (methodology, source, relevance)
4. Performance validation (query count, processing time)
5. Issue categorization and recommendations

Based on existing evidence_gathering/search_strategy/quality_validator.py but adapted for V3.
```

#### **What AI Needs to Do:**
1. Examine existing quality validator implementation
2. Create comprehensive evidence quality assessment
3. Implement IFCN compliance checking with detailed reports
4. Add performance validation capabilities
5. Generate actionable recommendations for quality improvements

#### **What You Need to Monitor:**
- [ ] Quality scoring accurately reflects evidence value
- [ ] IFCN compliance validation is comprehensive
- [ ] Performance validation catches issues
- [ ] Recommendations are actionable
- [ ] Reporting provides useful insights

#### **Success Criteria:**
```python
from evidence_engine_v3.evidence_gathering.quality_validator import QualityValidator

validator = QualityValidator()

# Use evidence from previous step
validation_result = validator.validate_evidence_pool(evidence_pool, strategy)

print(f"Overall quality score: {validation_result.quality_score:.2f}")
print(f"IFCN compliant: {validation_result.ifcn_compliant}")
print(f"Critical issues: {len(validation_result.critical_issues)}")
print(f"Warnings: {len(validation_result.warnings)}")
print(f"Recommendations: {len(validation_result.recommendations)}")

assert validation_result.quality_score >= 0.7, "Quality too low"
assert validation_result.ifcn_compliant, "IFCN compliance failed"
assert len(validation_result.critical_issues) == 0, "Critical issues found"

print("Quality validator: PASSED")
```

#### **Troubleshooting:**
- **Low Quality Scores**: Review scoring criteria and thresholds
- **IFCN Failures**: Check methodology-first approach implementation
- **Validation Errors**: Ensure proper error handling and edge case coverage

---

### **STEP 3.4: Integrate EEG Pipeline**
*Session Duration: 70 minutes*

#### **Goal:**
Create integrated EEG processor that combines strategist, executor, and validator into unified evidence gathering.

#### **AI Session Prompt:**
```
Implement evidence_engine_v3/evidence_gathering/__init__.py with:

1. EnhancedEvidenceGatherer class that orchestrates all EEG components
2. Integrate methodology strategist, search executor, and quality validator
3. Generate comprehensive EvidencePool output
4. Add error handling and fallback strategies
5. Optimize end-to-end pipeline for ≤15 seconds processing

Create single interface that takes ClaimInterpretation and returns validated EvidencePool.
```

#### **What AI Needs to Do:**
1. Create orchestrator class for all EEG components
2. Integrate strategy generation, search execution, and quality validation
3. Handle errors gracefully with appropriate fallbacks
4. Optimize complete pipeline for speed target
5. Generate comprehensive EvidencePool with metadata

#### **What You Need to Monitor:**
- [ ] All EEG components integrate smoothly
- [ ] Error handling covers component failures
- [ ] Complete pipeline meets ≤15 second target
- [ ] EvidencePool output is comprehensive
- [ ] Quality validation results are included

#### **Success Criteria:**
```python
from evidence_engine_v3.evidence_gathering import EnhancedEvidenceGatherer
from evidence_engine_v3.claim_interpretation import ClaimInterpretationProcessor
import time

aci_processor = ClaimInterpretationProcessor()
eeg_gatherer = EnhancedEvidenceGatherer()

claim = "Climate change policies will destroy the economy"
interpretation = aci_processor.analyze_claim(claim)

start = time.time()
evidence_pool = eeg_gatherer.gather_evidence(claim, interpretation)
duration = time.time() - start

print(f"EEG processing time: {duration:.2f}s")
print(f"Evidence count: {len(evidence_pool.evidence)}")
print(f"Quality score: {evidence_pool.quality_score:.2f}")
print(f"IFCN compliant: {evidence_pool.ifcn_compliant}")

assert duration <= 15, f"EEG too slow: {duration:.2f}s"
assert evidence_pool.quality_score >= 0.7, "Quality too low"
assert evidence_pool.ifcn_compliant, "IFCN compliance failed"

print("EEG Integration: PASSED")
```

#### **Troubleshooting:**
- **Performance Issues**: Profile each component to find bottlenecks
- **Integration Errors**: Check data flow between components
- **Quality Problems**: Review end-to-end evidence processing

---

## **PHASE 4: CONSENSUS & SCORING INTEGRATION**

### **STEP 4.1: Integrate Dual AI Processor**
*Session Duration: 70 minutes*

#### **Goal:**
Adapt existing dual AI consensus system for V3 architecture and EvidencePool input.

#### **AI Session Prompt:**
```
Implement evidence_engine_v3/consensus_analysis/dual_ai_processor.py by adapting existing legacy_evidence_system/rogr_dual_evidence_shepherd.py:

1. Extract DualAIConsensusResult logic and consensus analysis
2. Adapt to work with V3 EvidencePool input
3. Maintain existing dual AI shepherds (Primary/Secondary)
4. Preserve uncertainty quantification and quality assessment
5. Optimize integration with V3 data structures

Keep the proven dual AI logic but adapt interfaces for V3.
```

#### **What AI Needs to Do:**
1. Extract working consensus logic from existing dual shepherd
2. Adapt input/output to V3 data structures (EvidencePool/ConsensusResult)
3. Preserve existing dual AI quality assessment capabilities
4. Maintain uncertainty quantification features
5. Ensure backward compatibility with existing AI shepherds

#### **What You Need to Monitor:**
- [ ] Dual AI consensus logic is preserved
- [ ] Integration with V3 EvidencePool works
- [ ] Uncertainty quantification functions properly
- [ ] Quality assessment produces reasonable results
- [ ] Performance is maintained or improved

#### **Success Criteria:**
```python
from evidence_engine_v3.consensus_analysis.dual_ai_processor import DualAIProcessor

processor = DualAIProcessor()

# Use evidence pool from previous step
consensus_result = processor.analyze_evidence(claim, evidence_pool)

print(f"Consensus score: {consensus_result.consensus_score:.2f}")
print(f"Individual scores: {consensus_result.individual_scores}")
print(f"Disagreement level: {consensus_result.disagreement_level:.2f}")
print(f"Quality weighted score: {consensus_result.quality_weighted_score:.2f}")
print(f"Uncertainty indicators: {len(consensus_result.uncertainty_indicators)}")

assert consensus_result.consensus_score > 0, "No consensus generated"
assert len(consensus_result.individual_scores) >= 2, "Insufficient AI consensus"

print("Dual AI processor: PASSED")
```

#### **Troubleshooting:**
- **Consensus Failures**: Check dual AI shepherd availability and configuration
- **Integration Issues**: Verify data structure compatibility between V3 and legacy
- **Performance Problems**: Profile consensus analysis for bottlenecks

---

### **STEP 4.2: Implement Quality Assessor**
*Session Duration: 65 minutes*

#### **Goal:**
Build quality_assessor.py that provides comprehensive evidence quality metrics for consensus analysis.

#### **AI Session Prompt:**
```
Implement evidence_engine_v3/consensus_analysis/quality_assessor.py based on existing evidence_quality_assessor.py:

1. Extract EvidenceQualityAssessor logic and adapt for V3
2. Integrate with ConsensusResult and EvidencePool
3. Generate comprehensive quality metrics and scoring
4. Add evidence source assessment and methodology validation
5. Maintain IFCN compliance in quality assessment

Adapt existing quality assessment but optimize for V3 data flow.
```

#### **What AI Needs to Do:**
1. Extract and adapt existing quality assessment logic
2. Create comprehensive quality metrics for evidence pools
3. Integrate source methodology assessment
4. Generate quality scores that inform consensus analysis
5. Maintain IFCN compliance standards in assessment

#### **What You Need to Monitor:**
- [ ] Quality metrics are comprehensive and accurate
- [ ] Source methodology assessment follows IFCN standards
- [ ] Integration with consensus results works properly
- [ ] Quality scores correlate with evidence reliability
- [ ] Assessment performance is acceptable

#### **Success Criteria:**
```python
from evidence_engine_v3.consensus_analysis.quality_assessor import QualityAssessor

assessor = QualityAssessor()
quality_metrics = assessor.assess_evidence_quality(evidence_pool)

print(f"Overall quality: {quality_metrics.overall_score:.2f}")
print(f"Source quality: {quality_metrics.source_quality:.2f}")
print(f"Methodology score: {quality_metrics.methodology_score:.2f}")
print(f"Relevance score: {quality_metrics.relevance_score:.2f}")
print(f"IFCN compliant: {quality_metrics.ifcn_compliant}")

assert quality_metrics.overall_score >= 0.6, "Quality assessment too low"
assert quality_metrics.ifcn_compliant, "IFCN compliance failed"

print("Quality assessor: PASSED")
```

#### **Troubleshooting:**
- **Low Quality Scores**: Review scoring criteria and calibration
- **IFCN Issues**: Check methodology assessment logic
- **Integration Problems**: Verify compatibility with evidence pool format

---

### **STEP 4.3: Implement ROGR Scoring Integration**
*Session Duration: 70 minutes*

#### **Goal:**
Build scoring module that integrates existing ROGR FC scoring engine with V3 consensus results.

#### **AI Session Prompt:**
```
Implement evidence_engine_v3/scoring/ module by integrating existing rogr_fc_scoring_engine_zero_start.py:

1. Create trust_calculator.py that adapts ROGRFCScoringEngineZeroStart
2. Implement grade_engine.py that converts scores to evidence grades
3. Build capsule_formatter.py that creates final TrustCapsule output
4. Integrate with ConsensusResult input and quality metrics
5. Ensure TrustCapsule output matches existing main.py format exactly

Preserve existing ROGR scoring methodology but adapt for V3 data flow.
```

#### **What AI Needs to Do:**
1. Extract and adapt existing ROGR scoring engine logic
2. Create trust score calculation based on consensus results
3. Implement evidence grade calculation (A+ through F)
4. Build TrustCapsule formatter that matches existing API contract
5. Integrate all scoring components into unified interface

#### **What You Need to Monitor:**
- [ ] Trust scores are calculated using proven ROGR methodology
- [ ] Evidence grades follow existing A+ through F scale
- [ ] TrustCapsule format matches main.py exactly
- [ ] Integration with consensus results works properly
- [ ] Scoring performance is acceptable

#### **Success Criteria:**
```python
from evidence_engine_v3.scoring.trust_calculator import TrustCalculator
from evidence_engine_v3.scoring.capsule_formatter import CapsuleFormatter

calculator = TrustCalculator()
formatter = CapsuleFormatter()

# Use consensus result from previous step
trust_score = calculator.calculate_trust_score(claim, consensus_result)
evidence_grade = calculator.calculate_evidence_grade(consensus_result)
trust_capsule = formatter.format_capsule(claim, trust_score, evidence_grade, consensus_result)

print(f"Trust score: {trust_score}")
print(f"Evidence grade: {evidence_grade}")
print(f"TrustCapsule ID: {trust_capsule.id}")
print(f"Citations count: {len(trust_capsule.citations)}")

assert 0 <= trust_score <= 100, "Trust score out of range"
assert evidence_grade in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F'], "Invalid evidence grade"
assert trust_capsule.trust_score == int(trust_score), "TrustCapsule score mismatch"

print("ROGR scoring integration: PASSED")
```

#### **Troubleshooting:**
- **Scoring Issues**: Compare with existing ROGR engine calculations
- **Grade Problems**: Verify grade threshold logic matches existing system
- **Format Errors**: Compare TrustCapsule structure field-by-field with main.py

---

### **STEP 4.4: Complete V3 Pipeline Integration**
*Session Duration: 75 minutes*

#### **Goal:**
Update core/evidence_engine.py to replace stub with complete V3 pipeline implementation.

#### **AI Session Prompt:**
```
Replace the stub implementation in evidence_engine_v3/core/evidence_engine.py with complete pipeline:

1. Integrate all modules: ACI → EEG → Consensus → Scoring
2. Implement proper error handling for each pipeline stage
3. Add comprehensive logging for debugging and monitoring
4. Optimize end-to-end processing for ≤15 seconds target
5. Generate realistic TrustCapsule outputs using actual processing

Complete the process_claims() method to orchestrate the entire V3 pipeline.
```

#### **What AI Needs to Do:**
1. Replace stub with complete pipeline orchestration
2. Integrate ACI, EEG, Consensus, and Scoring modules
3. Add comprehensive error handling for each stage
4. Implement logging for debugging and performance monitoring
5. Optimize complete pipeline for speed and reliability

#### **What You Need to Monitor:**
- [ ] Complete pipeline processes claims end-to-end
- [ ] Each module integrates properly with the next
- [ ] Error handling gracefully manages component failures
- [ ] Processing time meets ≤15 second target
- [ ] TrustCapsule outputs are comprehensive and accurate

#### **Success Criteria:**
```python
from evidence_engine_v3 import EvidenceEngineV3
import time

engine = EvidenceEngineV3()
test_claims = [
    "Climate change policies will destroy the economy",
    "Vaccines are completely safe for all children",
    "Remote work increases productivity by 25%"
]

start = time.time()
results = engine.process_claims(test_claims)
total_time = time.time() - start

print(f"Total processing time: {total_time:.2f}s")
print(f"Average per claim: {total_time/len(test_claims):.2f}s")

for i, capsule in enumerate(results):
    print(f"\nClaim {i+1}: {test_claims[i][:50]}...")
    print(f"Trust score: {capsule.trust_score}")
    print(f"Evidence grade: {capsule.evidence_grade}")
    print(f"Confidence: {capsule.confidence}")
    print(f"Claims analyzed: {len(capsule.claims)}")
    print(f"Citations: {len(capsule.citations)}")

assert len(results) == len(test_claims), "Missing results"
assert all(r.trust_score is not None for r in results), "Missing trust scores"
assert total_time <= 45, f"Pipeline too slow: {total_time:.2f}s"  # 15s per claim max

print("Complete V3 Pipeline: PASSED")
```

#### **Troubleshooting:**
- **Pipeline Failures**: Check integration between modules and error propagation
- **Performance Issues**: Profile each stage to identify bottlenecks
- **Output Problems**: Verify TrustCapsule format and completeness

---

## **PHASE 5: PRODUCTION DEPLOYMENT**

### **STEP 5.1: Update FastAPI Integration**
*Session Duration: 60 minutes*

#### **Goal:**
Replace Evidence Engine V3 stub with full implementation in main.py and remove legacy systems.

#### **AI Session Prompt:**
```
Update main.py to use complete Evidence Engine V3:

1. Replace stub evidence_engine_v3 with full implementation
2. Remove USE_EVIDENCE_ENGINE_V3 feature flag (always use V3)
3. Simplify score_claim_with_evidence_shepherd() to use V3 only
4. Remove references to legacy evidence systems in analysis endpoints
5. Maintain all existing API response formats exactly

Make V3 the single, primary evidence processing system.
```

#### **What AI Needs to Do:**
1. Update main.py imports to use full V3 implementation
2. Remove feature flag logic and legacy system references
3. Simplify evidence processing to use V3 exclusively
4. Ensure API response format remains identical
5. Add proper error handling for V3 failures

#### **What You Need to Monitor:**
- [ ] V3 is now the exclusive evidence processing system
- [ ] All legacy feature flags and references removed
- [ ] API response format unchanged from client perspective
- [ ] Error handling provides graceful failures
- [ ] Performance meets FastAPI response time requirements

#### **Success Criteria:**
```bash
# Test all main API endpoints
curl localhost:8000/analyses -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":"Climate change is a hoax","type":"text"}' | jq '.trust_score, .evidence_grade'

curl localhost:8000/analyses -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":"https://www.bbc.com/news/example","type":"url"}' | jq '.trust_score, .evidence_grade'

# Test performance
time curl -s localhost:8000/analyses -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":"Vaccines contain microchips","type":"text"}' > /dev/null
# Should complete in <20 seconds

# Verify no legacy imports remain
grep -r "legacy_evidence_system" rogr-api/main.py  # Should return nothing
grep -r "parallel_evidence_system" rogr-api/main.py  # Should return nothing
```

#### **Troubleshooting:**
- **API Response Changes**: Compare response structure with pre-V3 implementation
- **Performance Regressions**: Profile V3 performance vs expectations
- **Import Errors**: Ensure all legacy references are properly removed

---

### **STEP 5.2: Performance Testing & Optimization**
*Session Duration: 70 minutes*

#### **Goal:**
Conduct comprehensive performance testing and optimize V3 pipeline to meet all targets.

#### **AI Session Prompt:**
```
Create comprehensive performance testing suite for Evidence Engine V3:

1. Test processing time across various claim types and complexity
2. Measure memory usage and resource consumption
3. Test concurrent request handling
4. Validate ≤15 second processing target achievement
5. Identify and optimize any performance bottlenecks

Create performance_test_v3.py that measures all key metrics systematically.
```

#### **What AI Needs to Do:**
1. Create comprehensive performance testing framework
2. Test various claim types, lengths, and complexity levels
3. Measure processing time, memory usage, and resource consumption
4. Test concurrent processing capabilities
5. Generate performance reports and optimization recommendations

#### **What You Need to Monitor:**
- [ ] Processing times consistently meet ≤15 second target
- [ ] Memory usage is reasonable and doesn't grow excessively
- [ ] System handles concurrent requests properly
- [ ] Performance is consistent across different claim types
- [ ] Resource utilization is optimized

#### **Success Criteria:**
```python
# Run comprehensive performance test
python performance_test_v3.py

# Expected output:
# ✅ Average processing time: 8.3s (target: ≤15s)
# ✅ Memory usage: 145MB peak (acceptable)
# ✅ Concurrent requests: 5 handled successfully
# ✅ 95th percentile: 12.7s (target: ≤15s)
# ✅ Error rate: 1.2% (target: <5%)

# Performance benchmarks:
# - Simple claims: <8s average
# - Complex claims: <15s average
# - Peak memory: <200MB
# - Concurrent capacity: ≥3 requests
```

#### **Troubleshooting:**
- **Slow Performance**: Profile pipeline stages to identify bottlenecks
- **Memory Issues**: Check for memory leaks or excessive resource usage
- **Concurrency Problems**: Review thread safety and resource sharing

---

### **STEP 5.3: Error Handling & Monitoring**
*Session Duration: 65 minutes*

#### **Goal:**
Implement comprehensive error handling and monitoring for production deployment.

#### **AI Session Prompt:**
```
Add production-ready error handling and monitoring to Evidence Engine V3:

1. Implement graceful error handling for each pipeline stage
2. Add comprehensive logging for debugging and performance monitoring
3. Create health check endpoints for system monitoring
4. Add error rate tracking and alerting capabilities
5. Implement fallback responses for critical failures

Ensure system fails gracefully and provides useful diagnostic information.
```

#### **What AI Needs to Do:**
1. Add comprehensive error handling to each V3 module
2. Implement structured logging throughout the pipeline
3. Create monitoring endpoints and health checks
4. Add error tracking and performance metrics
5. Implement graceful fallback responses

#### **What You Need to Monitor:**
- [ ] Error handling covers all failure scenarios
- [ ] Logging provides useful debugging information
- [ ] Health checks accurately reflect system status
- [ ] Error rates are tracked and reasonable (<5%)
- [ ] Fallback responses maintain API contract

#### **Success Criteria:**
```bash
# Test error handling
curl localhost:8000/analyses -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":"","type":"text"}'  # Empty input
# Should return structured error response

# Test health check
curl localhost:8000/health/v3
# Should return detailed system status

# Check logs
tail -f logs/evidence_engine_v3.log
# Should show structured logging with timestamps and context

# Monitor error rates
curl localhost:8000/metrics/v3
# Should show error rates, processing times, success rates
```

#### **Troubleshooting:**
- **Unhandled Errors**: Add try-catch blocks around critical operations
- **Poor Logging**: Enhance log messages with more context and detail
- **Monitoring Gaps**: Ensure all critical metrics are tracked

---

## **PHASE 6: LEGACY CLEANUP**

### **STEP 6.1: Verify System Stability**
*Session Duration: 60 minutes*

#### **Goal:**
Conduct final comprehensive testing to verify V3 system stability before legacy cleanup.

#### **AI Session Prompt:**
```
Perform comprehensive final testing of Evidence Engine V3:

1. Test all API endpoints with various input types (text, URL, image)
2. Verify TrustCapsule format compatibility with frontend
3. Test error handling with edge cases and invalid inputs
4. Validate performance consistency over extended testing
5. Confirm all functionality matches pre-V3 implementation

Create final_verification_test.py that comprehensively validates system readiness.
```

#### **What AI Needs to Do:**
1. Create comprehensive test suite covering all functionality
2. Test API compatibility with various input types and edge cases
3. Verify performance consistency and reliability
4. Validate error handling and graceful degradation
5. Generate final system readiness report

#### **What You Need to Monitor:**
- [ ] All API endpoints function correctly
- [ ] TrustCapsule format is 100% compatible
- [ ] Error handling is robust and informative
- [ ] Performance is consistent and meets targets
- [ ] System is ready for production use

#### **Success Criteria:**
```python
# Run final verification test
python final_verification_test.py

# Expected comprehensive test results:
# ✅ API Compatibility: 100% (all endpoints working)
# ✅ TrustCapsule Format: 100% (frontend compatible)
# ✅ Error Handling: 98% (robust graceful failures)
# ✅ Performance: 96% (meets timing targets)
# ✅ Edge Cases: 94% (handles unusual inputs)
#
# Overall System Readiness: 97.6% ✅ READY FOR PRODUCTION
```

#### **Troubleshooting:**
- **Compatibility Issues**: Compare V3 outputs with pre-V3 system responses
- **Performance Problems**: Run extended load testing to identify issues
- **Error Handling Gaps**: Test more edge cases and unusual inputs

---

### **STEP 6.2: Remove Legacy Evidence Systems**
*Session Duration: 65 minutes*

#### **Goal:**
Safely remove all legacy evidence system code and clean up imports/dependencies.

#### **AI Session Prompt:**
```
Remove all legacy evidence system code:

1. Delete legacy_evidence_system/ directory entirely
2. Delete parallel_evidence_system/ directory entirely
3. Remove all imports and references to legacy systems
4. Clean up unused dependencies and configuration
5. Update all documentation to reflect V3-only architecture

Before deletion, verify no working code depends on legacy systems.
```

#### **What AI Needs to Do:**
1. Scan codebase for all legacy system dependencies
2. Safely remove legacy directories after dependency verification
3. Clean up imports, configuration, and unused dependencies
4. Update documentation and code comments
5. Ensure no functional regression from cleanup

#### **What You Need to Monitor:**
- [ ] Legacy directories are completely removed
- [ ] No broken imports or references remain
- [ ] System continues to function identically
- [ ] Documentation accurately reflects new architecture
- [ ] No unused dependencies or configuration remain

#### **Success Criteria:**
```bash
# Verify legacy systems are removed
find rogr-api/ -name "*legacy*" -type d | wc -l  # Should be 0
find rogr-api/ -name "*parallel_evidence*" -type d | wc -l  # Should be 0

# Test all imports still work
python -m py_compile rogr-api/*.py
python -m py_compile rogr-api/evidence_engine_v3/**/*.py

# Verify system still functions
curl localhost:8000/analyses -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":"Test after cleanup","type":"text"}' | jq '.trust_score'
# Should work identically to pre-cleanup

# Check git status
git status  # Should show deleted directories
git log --oneline -3  # Should show cleanup commits
```

#### **Troubleshooting:**
- **Broken Dependencies**: Check for any remaining references to deleted systems
- **Import Errors**: Verify all necessary imports are preserved
- **Functional Regression**: Test thoroughly to ensure no feature loss

---

### **STEP 6.3: Final Documentation & Git Management**
*Session Duration: 55 minutes*

#### **Goal:**
Complete final documentation updates and create clean git tags for V3 implementation.

#### **AI Session Prompt:**
```
Complete final documentation and git management:

1. Update README.md to reflect Evidence Engine V3 architecture
2. Create V3 architecture documentation in AI-SESSION-CONTEXT/
3. Update API documentation for any changes
4. Create git tag: evidence_engine_v3_complete
5. Generate final implementation summary for context handoff

Ensure all documentation accurately reflects the new V3-only system.
```

#### **What AI Needs to Do:**
1. Update project documentation to reflect V3 architecture
2. Create comprehensive V3 documentation
3. Update API documentation and examples
4. Create appropriate git tags and commit messages
5. Generate implementation summary and lessons learned

#### **What You Need to Monitor:**
- [ ] Documentation accurately describes V3 system
- [ ] Architecture documentation is comprehensive
- [ ] Git history is clean with descriptive commits
- [ ] Implementation summary captures key decisions
- [ ] All context is preserved for future development

#### **Success Criteria:**
```bash
# Verify documentation updates
ls -la AI-SESSION-CONTEXT/*V3*  # Should show V3 documentation
grep -i "evidence.engine.v3" README.md  # Should reference V3

# Check git management
git tag | grep evidence_engine_v3  # Should show completion tag
git log --oneline -5  # Should show clean commit history

# Final system verification
curl localhost:8000/health && echo "System operational"
curl localhost:8000/analyses -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":"Final verification test","type":"text"}' | jq '.evidence_grade'
```

#### **Troubleshooting:**
- **Documentation Issues**: Ensure all references to legacy systems are updated
- **Git Problems**: Clean up commit history if needed
- **Missing Context**: Ensure implementation decisions are documented

---

## **SESSION MANAGEMENT GUIDELINES**

### **Pre-Session Checklist:**
- [ ] Load progress tracking document
- [ ] Verify prerequisites for current step are met
- [ ] Set 60-75 minute timer for auto-compact management
- [ ] Have specific success criteria ready for validation

### **During Session:**
- [ ] Focus exclusively on single step deliverable
- [ ] Monitor progress against success criteria continuously
- [ ] Document any deviations or issues immediately
- [ ] Test functionality incrementally as work progresses

### **Post-Session Checklist:**
- [ ] Run all success criteria tests
- [ ] Update progress tracking document
- [ ] Commit changes with descriptive messages
- [ ] Set up context handoff for next session
- [ ] Document any troubleshooting insights

### **Context Handoff Template:**
```
## Session [X.X] Completion Status

**Step Completed**: [Step Title]
**Status**: [Completed/Partial/Blocked]
**Success Criteria Met**: [X/Y]
**Time Taken**: [XX minutes]

**Key Deliverables**:
- [ ] [Deliverable 1]
- [ ] [Deliverable 2]
- [ ] [Deliverable 3]

**Issues Encountered**:
- [Issue 1 and resolution]
- [Issue 2 and resolution]

**Next Session**:
- **Step**: [Next Step Title]
- **Prerequisites**: [Any setup needed]
- **Key Focus**: [Main objective]

**Files Modified**:
- [file1.py] - [description of changes]
- [file2.py] - [description of changes]

**Git Commits**:
- [commit hash] - [commit message]
```

This granular approach ensures each AI session can be productive within auto-compact windows while maintaining complete context independence and clear success validation.