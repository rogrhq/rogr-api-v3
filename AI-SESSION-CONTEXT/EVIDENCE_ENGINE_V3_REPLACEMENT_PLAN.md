# **EVIDENCE ENGINE V3: COMPLETE REPLACEMENT ARCHITECTURE PLAN**
*Clean Room Approach - Zero Coexistence Model*

**Document Version**: 1.0
**Date Created**: December 17, 2024
**Last Updated**: December 17, 2024
**Author**: AI Analysis Session
**Status**: Ready for Implementation

---

## **EXECUTIVE SUMMARY**

**Current Problem**: The coexistence model has contaminated your Evidence Engine with architectural complexity, parallel systems, and confusing integration points. You need a **single, superior Evidence Engine** that incorporates the best of ACI and EEG improvements while eliminating all legacy confusion.

**Solution**: Build Evidence Engine V3 as a **complete replacement** that isolates all working components into a clean namespace, incorporates ACI semantic analysis and EEG enhanced gathering methodologies, and provides a simple integration interface.

**Key Benefits**:
- **Single Source of Truth**: One Evidence Engine, no fallbacks or coexistence confusion
- **Performance Optimized**: Target <15s processing per ROGR_PRIMER_v2.md requirements
- **IFCN Compliant**: Methodology-first approach throughout
- **Clean Integration**: Preserves all existing ClaimMiner→FastAPI→Frontend workflows
- **Enhanced Quality**: ACI semantic analysis + EEG evidence gathering improvements

---

## **CURRENT SYSTEM ANALYSIS**

### **Files Examined:**
- `rogr-api/main.py` - FastAPI integration and TrustCapsule generation
- `rogr-api/claim_miner.py` - Claim extraction and context analysis
- `rogr-api/legacy_evidence_system/rogr_dual_evidence_shepherd.py` - Dual AI consensus
- `rogr-api/rogr_fc_scoring_engine_zero_start.py` - Professional scoring
- `rogr-app/lib/` - Flutter frontend consuming TrustCapsules
- `rogr-api/parallel_evidence_system/` - Coexistence contamination
- `rogr-api/evidence_gathering/` - EEG Phase 1 implementation

### **Commands Run:**
- `find . -type f -name "*.py"` - Python codebase analysis
- `git log --oneline --since="30 days ago"` - Recent development history
- Multiple glob patterns for evidence-related components

### **Integration Points Identified:**
ClaimMiner → Evidence Engine → TrustCapsule → FastAPI → Frontend

### **Working Components Identified:**

#### **1. ClaimMiner (✅ KEEP)**
- **Location**: `rogr-api/claim_miner.py`
- **Function**: Extracts 1-3 checkable claims with context awareness
- **Integration**: Direct input to Evidence Engine
- **Quality**: Production-ready, handles URL/text/image inputs
- **Key Features**: MinedClaim dataclass, context-aware analysis, Claude API integration

#### **2. Dual Consensus Scoring (✅ KEEP)**
- **Location**: `rogr-api/legacy_evidence_system/rogr_dual_evidence_shepherd.py`
- **Function**: Multi-AI consensus with quality assessment
- **Integration**: Evidence processing and scoring
- **Quality**: Working but trapped in coexistence complexity
- **Key Features**: DualAIConsensusResult, uncertainty quantification

#### **3. ROGR Scoring Engine (✅ KEEP)**
- **Location**: `rogr-api/rogr_fc_scoring_engine_zero_start.py`
- **Function**: Professional fact-checking grade calculation (A+ through F)
- **Integration**: Final trust score generation
- **Quality**: IFCN-compliant scoring methodology
- **Key Features**: ROGRScoringResult, evidence grade thresholds

#### **4. FastAPI Integration (✅ KEEP)**
- **Location**: `rogr-api/main.py`
- **Function**: `/analyses` endpoint with TrustCapsule output
- **Integration**: Frontend API contract
- **Quality**: Complete implementation with proper error handling
- **Key Features**: AnalysisInput, TrustCapsule, ClaimAnalysis models

#### **5. Flutter Frontend (✅ KEEP)**
- **Location**: `rogr-app/lib/` directory
- **Function**: Mobile interface consuming TrustCapsules
- **Integration**: API consumer expecting TrustCapsule format
- **Quality**: Production-ready mobile application
- **Key Features**: Scanning screen, capsule display, evidence popup

### **Contaminated Systems to Isolate:**

#### **1. Coexistence Infrastructure (❌ REMOVE)**
- `parallel_evidence_system/` - Remove entirely
- `evidence_gathering/` - Extract valuable components only (MethodologySearchStrategist)
- Complex feature flags and fallback systems - Eliminate

#### **2. Legacy Evidence System Confusion (❌ REMOVE)**
- Multiple overlapping shepherds with unclear responsibilities
- Inconsistent interfaces and data structures
- Performance overhead from dual system management
- Feature flag complexity (`USE_PARALLEL_EVIDENCE`, `USE_EEG_PHASE_1`)

---

## **EVIDENCE ENGINE V3 ARCHITECTURE**

### **Core Design Principles:**

1. **Single Source of Truth**: One Evidence Engine, no fallbacks
2. **Clean Interfaces**: Clear input/output contracts
3. **Modular Enhancement**: ACI + EEG components as discrete modules
4. **Speed Optimized**: Target <15s processing per ROGR_PRIMER_v2.md
5. **IFCN Compliant**: Methodology-first approach throughout
6. **Integration Preservation**: Maintain all existing ClaimMiner→FastAPI→Frontend contracts

### **V3 Architecture Overview:**

```
evidence_engine_v3/
├── core/
│   ├── evidence_engine.py          # Main orchestrator
│   ├── interfaces.py               # Clean data structures
│   └── exceptions.py               # Error handling
├── claim_interpretation/           # ACI Module
│   ├── semantic_analyzer.py        # Subject/object distinction
│   ├── logical_analyzer.py         # Causation vs correlation
│   └── claim_classifier.py         # Domain classification
├── evidence_gathering/             # EEG Module
│   ├── methodology_strategist.py   # IFCN-compliant search
│   ├── search_executor.py          # Parallel evidence search
│   └── quality_validator.py        # Evidence quality assessment
├── consensus_analysis/             # Enhanced Dual AI
│   ├── dual_ai_processor.py        # Multi-AI consensus
│   ├── quality_assessor.py         # Evidence quality scoring
│   └── uncertainty_quantifier.py   # Confidence intervals
├── scoring/                        # ROGR FC Integration
│   ├── trust_calculator.py         # Final trust score
│   ├── grade_engine.py             # Evidence grade calculation
│   └── capsule_formatter.py        # TrustCapsule output
└── tests/                          # Comprehensive testing
    ├── test_integration.py         # End-to-end pipeline tests
    ├── test_aci_module.py          # ACI component tests
    ├── test_eeg_module.py          # EEG component tests
    └── test_performance.py         # Speed and quality benchmarks
```

### **Data Flow Architecture:**

```
ClaimMiner → Evidence Engine V3 → TrustCapsule → FastAPI → Frontend
     ↓              ↓                    ↓
   Claims    [ACI→EEG→Consensus]   Formatted Results
```

**Processing Pipeline:**
1. **Claim Input**: Receive claims from ClaimMiner (existing interface)
2. **ACI Processing**: Semantic & logical analysis for improved understanding
3. **EEG Search**: Enhanced evidence gathering with methodology-first approach
4. **Consensus Analysis**: Dual-AI quality assessment and uncertainty quantification
5. **Scoring**: ROGR FC professional grading (A+ through F)
6. **Output**: TrustCapsule to existing FastAPI (preserved interface)

---

## **COMPONENT SPECIFICATIONS**

### **1. Core Evidence Engine**

```python
# evidence_engine_v3/core/evidence_engine.py
class EvidenceEngineV3:
    """Clean room Evidence Engine - single source of truth"""

    def __init__(self):
        self.aci_processor = ClaimInterpretationProcessor()
        self.eeg_gatherer = EnhancedEvidenceGatherer()
        self.consensus_analyzer = DualAIConsensusAnalyzer()
        self.scoring_engine = ROGRScoringEngine()

    def process_claims(self, claims: List[str]) -> List[TrustCapsule]:
        """Main processing pipeline - replaces all legacy systems"""
        results = []
        for claim in claims:
            # ACI: Semantic and logical analysis
            interpretation = self.aci_processor.analyze_claim(claim)

            # EEG: Enhanced evidence gathering
            evidence_pool = self.eeg_gatherer.gather_evidence(claim, interpretation)

            # Consensus: Dual-AI quality assessment
            consensus = self.consensus_analyzer.analyze_evidence(claim, evidence_pool)

            # Scoring: Final trust score and grade
            trust_capsule = self.scoring_engine.score_claim(claim, consensus)
            results.append(trust_capsule)

        return results
```

### **2. ACI Module (Advanced Claim Interpretation)**

Based on `ES_ACI_PLAN.md`, implement:

**Semantic Analyzer:**
- Subject/object distinction in causal claims ("policies hurt economy" vs "climate change hurts economy")
- Temporal aspect analysis (will destroy vs has destroyed vs is destroying)
- Action type classification (destroy/improve/affect/cause)
- Certainty level detection (definitive/probable/speculative)

**Logical Analyzer:**
- Causation vs correlation detection ("causes" vs "associated with")
- Conditional statement analysis ("if X then Y" vs "X always causes Y")
- Universal vs particular scope identification ("all vaccines" vs "this vaccine")
- Qualifying language detection ("might", "could", "likely")

**Claim Classifier:**
- Domain classification (medical, economic, scientific, policy)
- Evidence requirement generation (what evidence would prove/disprove)
- Scope analysis (broad vs specific claims)

**Success Criteria:**
- 95% accuracy in subject/object distinction
- 90% accuracy in causation vs correlation
- 95% accuracy in temporal aspect identification
- Processing time <500ms per claim

### **3. EEG Module (Enhanced Evidence Gathering)**

Based on `ES_EEG_PLAN_v2.md` and existing `evidence_gathering/` implementation:

**Methodology Strategist:**
- IFCN-compliant search generation (methodology-first, not institution-first)
- Maximum 12 queries per claim for performance (75% reduction from current)
- Transparent criteria with complete audit trails
- Evidence methodology types: peer_reviewed, government_official, systematic_review

**Search Executor:**
- Parallel evidence gathering from multiple sources
- Quality-based filtering and relevance scoring
- Counter-evidence generation with equal methodology standards
- Performance safeguards with timeout protection

**Quality Validator:**
- Real-time IFCN compliance monitoring
- Performance validation and safeguard enforcement
- Quality scoring (0.0-1.0) with detailed reporting
- Issue categorization and actionable recommendations

**Success Criteria:**
- ≤12 queries per claim (performance target)
- ≤15 seconds total processing time (ROGR_PRIMER_v2.md requirement)
- 70%+ relevant evidence results (quality target)
- 100% IFCN compliance with audit trails
- Zero institutional bias (methodology-first approach)

### **4. Consensus Analysis Module**

Based on existing `rogr_dual_evidence_shepherd.py`:

**Dual AI Processor:**
- Multi-AI consensus analysis using existing ROGR shepherds
- Evidence quality assessment and uncertainty quantification
- Disagreement level calculation and confidence intervals

**Quality Assessor:**
- Evidence quality scoring with transparent criteria
- Source methodology validation
- Professional fact-checking protocol compliance

**Uncertainty Quantifier:**
- AI consensus measurement
- Evidence quality confidence bands
- Uncertainty indicator generation

### **5. Scoring Module**

Based on existing `rogr_fc_scoring_engine_zero_start.py`:

**Trust Calculator:**
- Professional fact-checking trust score (0-100)
- Evidence quality weighting
- IFCN-compliant scoring methodology

**Grade Engine:**
- Evidence grade calculation (A+ through F)
- Grade threshold management
- Professional grade descriptions

**Capsule Formatter:**
- TrustCapsule output generation
- Citation extraction and formatting
- Evidence summary generation

### **6. Integration Points**

**Input Interface (Preserved):**
```python
# FROM: ClaimMiner output (existing)
claims = [claim.text for claim in mining_result.primary_claims]

# TO: Evidence Engine V3
trust_capsules = evidence_engine.process_claims(claims)
```

**Output Interface (Preserved):**
```python
# FROM: Evidence Engine V3
trust_capsule = TrustCapsule(
    id=str,
    trust_score=int,
    evidence_grade=str,
    confidence=str,
    why=List[str],
    claims=List[ClaimAnalysis],
    overall_assessment=str,
    citations=List[Citation],
    capsule_version=int,
    signed=bool,
    created_at=str,
    input_type=str,
    mode=str
)

# TO: FastAPI endpoint (existing contract preserved)
return trust_capsule
```

---

## **STEP-BY-STEP IMPLEMENTATION PLAN**

### **Phase 1: Clean Room Setup (Week 1)**
*Foundation and Integration Stubs*

#### **Your Role:**
- **Review and Approve**: Validate architecture specifications meet requirements
- **Integration Validation**: Confirm all integration points correctly identified
- **Functionality Guarantee**: Verify no working functionality will be lost
- **Success Verification**: Test that FastAPI continues working with stub implementation

#### **AI Role:**
- **Clean Structure**: Create `evidence_engine_v3/` directory with clean namespace
- **Core Interfaces**: Implement interfaces.py with all data structures
- **Integration Stub**: Create stub implementation that connects to existing FastAPI
- **Testing Framework**: Set up comprehensive testing infrastructure
- **Documentation**: Create architecture documentation and integration guides

#### **Deliverables:**
- [ ] Clean `evidence_engine_v3/` directory structure created
- [ ] Core interfaces defined in `interfaces.py`
- [ ] Stub implementation connecting to FastAPI
- [ ] Integration tests passing with mock responses
- [ ] No contamination from legacy systems

#### **Success Criteria:**
- [ ] Clean namespace created with zero legacy contamination
- [ ] Core interfaces defined and fully documented
- [ ] Integration tests pass with stub implementation
- [ ] FastAPI continues to work with mock TrustCapsule responses
- [ ] No breaking changes to existing ClaimMiner→FastAPI contract

#### **Tests to Run:**
```bash
# Test clean namespace
find evidence_engine_v3/ -name "*.py" | grep -v __pycache__ | wc -l
# Should show new files only

# Test interface definitions
python -c "from evidence_engine_v3.core.interfaces import TrustCapsule; print('OK')"

# Test FastAPI integration
curl localhost:8000/analyses -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":"test claim","type":"text"}'
# Should return mock TrustCapsule with proper structure
```

#### **Validation Questions for You:**
1. Does the stub TrustCapsule output match expected format?
2. Are all required fields present in the response?
3. Does the FastAPI continue to respond without errors?
4. Is the clean namespace completely isolated from legacy code?

### **Phase 2: ACI Implementation (Week 2)**
*Advanced Claim Interpretation Module*

#### **Your Role:**
- **Accuracy Testing**: Test semantic analysis accuracy with provided test claims
- **Performance Validation**: Confirm processing time meets <500ms target
- **Quality Assessment**: Evaluate claim interpretation quality and edge cases
- **Integration Testing**: Verify ACI module integrates properly with pipeline

#### **AI Role:**
- **Semantic Analyzer**: Implement subject/object distinction and temporal analysis
- **Logical Analyzer**: Build causation vs correlation and conditional statement detection
- **Claim Classifier**: Create domain classification and evidence requirement generation
- **Pipeline Integration**: Connect ACI module to core Evidence Engine
- **Testing Suite**: Create comprehensive test cases for all ACI functionality

#### **Deliverables:**
- [ ] `claim_interpretation/semantic_analyzer.py` implemented
- [ ] `claim_interpretation/logical_analyzer.py` implemented
- [ ] `claim_interpretation/claim_classifier.py` implemented
- [ ] ACI module integrated with core pipeline
- [ ] Comprehensive test suite for all ACI features

#### **Success Criteria:**
- [ ] Semantic analysis achieves 95% accuracy on test claims
- [ ] Logical analysis correctly identifies causation vs correlation
- [ ] Domain classification provides appropriate evidence requirements
- [ ] Processing time <500ms per claim
- [ ] Integration with main pipeline successful

#### **Tests to Run:**
```python
# Test semantic analysis accuracy
test_claims = [
    "Climate change policies will destroy the economy",
    "Vaccines cause autism",
    "AI will replace human jobs",
    "The economy will be destroyed by climate change",
    "Social media definitely causes depression"
]

for claim in test_claims:
    result = aci_processor.analyze_claim(claim)
    print(f"Claim: {claim}")
    print(f"Subject: {result.subject}")
    print(f"Object: {result.object}")
    print(f"Relationship: {result.relationship_type}")
    print(f"Temporal: {result.temporal_aspect}")
    print(f"Certainty: {result.certainty_level}")
    print("---")

# Test processing performance
import time
start_time = time.time()
result = aci_processor.analyze_claim("Climate change policies will destroy the economy")
processing_time = time.time() - start_time
print(f"ACI processing time: {processing_time:.3f}s")
assert processing_time < 0.5, "ACI processing too slow"
```

#### **Validation Questions for You:**
1. Does semantic analysis correctly identify subjects and objects?
2. Are causation vs correlation distinctions accurate?
3. Do domain classifications make sense for test claims?
4. Is processing speed acceptable for production use?

### **Phase 3: EEG Implementation (Week 3)**
*Enhanced Evidence Gathering Module*

#### **Your Role:**
- **IFCN Compliance**: Verify search strategies meet methodology-first standards
- **Performance Testing**: Confirm evidence gathering meets <15 second target
- **Quality Validation**: Test evidence relevance and source methodology coverage
- **Search Strategy Review**: Validate that query generation follows IFCN guidelines

#### **AI Role:**
- **Methodology Strategist**: Implement IFCN-compliant search strategy generation
- **Search Executor**: Build parallel evidence search with quality filtering
- **Quality Validator**: Create evidence quality assessment and IFCN monitoring
- **Performance Optimization**: Optimize for ≤12 queries and ≤15 seconds processing
- **EEG Integration**: Connect enhanced evidence gathering to ACI and consensus modules

#### **Deliverables:**
- [ ] `evidence_gathering/methodology_strategist.py` implemented
- [ ] `evidence_gathering/search_executor.py` implemented
- [ ] `evidence_gathering/quality_validator.py` implemented
- [ ] Performance optimizations achieving speed targets
- [ ] IFCN compliance validation and audit trail generation

#### **Success Criteria:**
- [ ] Search strategies are IFCN compliant with complete audit trails
- [ ] Evidence gathering completes in ≤15 seconds (ROGR_PRIMER_v2.md target)
- [ ] Query count ≤12 per claim (75% reduction from current ~48 operations)
- [ ] Evidence relevance >70% (quality improvement target)
- [ ] Zero institutional bias (methodology-first approach maintained)

#### **Tests to Run:**
```python
# Test evidence gathering performance
import time
claim = "Climate change policies will destroy the economy"
interpretation = aci_processor.analyze_claim(claim)

start_time = time.time()
evidence_pool = eeg_gatherer.gather_evidence(claim, interpretation)
processing_time = time.time() - start_time

print(f"EEG processing time: {processing_time:.2f}s")
print(f"Evidence count: {len(evidence_pool)}")
print(f"Query count: {eeg_gatherer.last_query_count}")
print(f"Average relevance: {sum(e.relevance_score for e in evidence_pool) / len(evidence_pool):.2f}")

# Validate performance targets
assert processing_time <= 15, "EEG processing too slow"
assert eeg_gatherer.last_query_count <= 12, "Too many queries generated"
assert len([e for e in evidence_pool if e.relevance_score > 0.7]) > 0, "Low relevance evidence"

# Test IFCN compliance
validation_result = eeg_gatherer.validate_ifcn_compliance()
print(f"IFCN compliant: {validation_result.compliant}")
print(f"Audit trail entries: {len(validation_result.audit_trail)}")
assert validation_result.compliant, "IFCN compliance failure"
```

#### **Validation Questions for You:**
1. Are search strategies methodology-first rather than institution-biased?
2. Does evidence gathering complete within the 15-second target?
3. Is the evidence quality and relevance satisfactory?
4. Are audit trails sufficient for IFCN compliance verification?

### **Phase 4: Consensus & Scoring Integration (Week 4)**
*Complete Pipeline Integration*

#### **Your Role:**
- **Consensus Validation**: Test dual-AI consensus accuracy and quality scores
- **Scoring Verification**: Confirm ROGR scoring methodology produces appropriate grades
- **End-to-End Testing**: Validate complete pipeline functionality
- **Integration Validation**: Ensure all modules work together seamlessly

#### **AI Role:**
- **Consensus Integration**: Connect existing dual-AI system to new pipeline
- **Scoring Integration**: Integrate ROGR scoring engine with consensus results
- **Uncertainty Quantification**: Implement confidence intervals and disagreement metrics
- **TrustCapsule Formation**: Complete output formatting to match existing API contract
- **Pipeline Optimization**: Fine-tune end-to-end processing for optimal performance

#### **Deliverables:**
- [ ] `consensus_analysis/dual_ai_processor.py` integrated
- [ ] `consensus_analysis/quality_assessor.py` implemented
- [ ] `scoring/trust_calculator.py` connected to consensus results
- [ ] `scoring/capsule_formatter.py` generating proper TrustCapsules
- [ ] Complete end-to-end pipeline functional

#### **Success Criteria:**
- [ ] Dual-AI consensus produces quality scores with uncertainty quantification
- [ ] ROGR scoring integrates seamlessly with consensus results
- [ ] Complete pipeline processes claims end-to-end successfully
- [ ] TrustCapsule format matches existing FastAPI contract exactly
- [ ] Processing time meets <15 second target for complete pipeline

#### **Tests to Run:**
```python
# End-to-end integration test
test_claims = [
    "Vaccines are completely safe for all children",
    "Remote work increases productivity by 25%",
    "Nuclear energy produces zero carbon emissions"
]

for claim in test_claims:
    print(f"\n=== Testing: {claim[:50]}... ===")
    start_time = time.time()

    trust_capsules = evidence_engine.process_claims([claim])
    processing_time = time.time() - start_time

    capsule = trust_capsules[0]
    print(f"Processing time: {processing_time:.2f}s")
    print(f"Trust score: {capsule.trust_score}")
    print(f"Evidence grade: {capsule.evidence_grade}")
    print(f"Confidence: {capsule.confidence}")
    print(f"Claims analyzed: {len(capsule.claims)}")
    print(f"Citations: {len(capsule.citations)}")

    # Validate required fields
    assert capsule.trust_score is not None
    assert capsule.evidence_grade in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F']
    assert len(capsule.why) > 0
    assert processing_time <= 15

print("\n✅ All end-to-end tests passed!")
```

#### **Validation Questions for You:**
1. Do trust scores and evidence grades seem appropriate for test claims?
2. Is the TrustCapsule format identical to current API responses?
3. Are processing times acceptable across different claim types?
4. Does the uncertainty quantification provide useful information?

### **Phase 5: Production Deployment (Week 5)**
*Replace Legacy Systems*

#### **Your Role:**
- **Final User Acceptance Testing**: Conduct comprehensive testing with real-world claims
- **Performance Monitoring**: Verify system meets all performance targets in production
- **Quality Assessment**: Evaluate evidence quality and trust score accuracy
- **Go/No-Go Decision**: Approve production deployment and legacy system removal

#### **AI Role:**
- **FastAPI Integration**: Update main.py to use Evidence Engine V3 exclusively
- **Configuration Update**: Remove legacy environment variables and feature flags
- **Monitoring Implementation**: Add performance tracking and error monitoring
- **Documentation Update**: Update all documentation to reflect V3 architecture
- **Legacy Isolation**: Prepare legacy systems for removal (but don't delete yet)

#### **Deliverables:**
- [ ] `main.py` updated to use Evidence Engine V3
- [ ] All legacy feature flags removed
- [ ] Performance monitoring and error tracking implemented
- [ ] Documentation updated to reflect V3 architecture
- [ ] Legacy systems isolated but preserved for rollback

#### **Success Criteria:**
- [ ] FastAPI uses Evidence Engine V3 exclusively with no legacy fallbacks
- [ ] Performance metrics consistently meet targets (<15s processing)
- [ ] Error rates <5% in production testing environment
- [ ] Trust score quality maintained or improved vs legacy system
- [ ] Mobile frontend functionality completely preserved

#### **Tests to Run:**
```bash
# Production integration test - URL analysis
curl localhost:8000/analyses -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":"https://www.bbc.com/news/example-article","type":"url"}' \
  | jq '.'

# Production integration test - Text analysis
curl localhost:8000/analyses -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":"Climate change is a hoax created by China","type":"text"}' \
  | jq '.'

# Performance monitoring test
for i in {1..10}; do
  echo "Test $i:"
  time curl -s localhost:8000/analyses -X POST \
    -H "Content-Type: application/json" \
    -d '{"input":"Vaccines contain microchips","type":"text"}' \
    | jq '.trust_score, .evidence_grade'
done

# Error rate monitoring
# Run 50 requests and count failures
success_count=0
for i in {1..50}; do
  response=$(curl -s -w "%{http_code}" localhost:8000/analyses -X POST \
    -H "Content-Type: application/json" \
    -d '{"input":"Test claim '$i'","type":"text"}')
  if [[ $response =~ 200$ ]]; then
    ((success_count++))
  fi
done
echo "Success rate: $((success_count * 2))%"
```

#### **Validation Questions for You:**
1. Are response times consistently under 15 seconds?
2. Do trust scores and evidence grades look reasonable for test claims?
3. Is the mobile app functionality completely preserved?
4. Are you satisfied with the evidence quality and source diversity?

### **Phase 6: Legacy Cleanup (Week 6)**
*Complete System Replacement*

#### **Your Role:**
- **Final Functionality Verification**: Confirm all features work as expected
- **Rollback Validation**: Verify git history preserved for emergency rollback
- **Documentation Review**: Approve updated documentation and architecture guides
- **Legacy Deletion Approval**: Give final approval for legacy directory deletion

#### **AI Role:**
- **Legacy Directory Removal**: Delete `legacy_evidence_system/` directory
- **Parallel System Removal**: Delete `parallel_evidence_system/` directory
- **Import Cleanup**: Remove all unused legacy imports and dependencies
- **Documentation Finalization**: Complete architecture documentation update
- **Git Management**: Create clean V3 implementation tag for future reference

#### **Deliverables:**
- [ ] All legacy evidence system code removed
- [ ] All parallel evidence system code removed
- [ ] Unused imports and dependencies cleaned up
- [ ] Documentation fully updated to reflect V3 architecture
- [ ] Git tag created: `evidence_engine_v3_complete`

#### **Success Criteria:**
- [ ] All legacy code completely removed from repository
- [ ] No broken imports or references remaining anywhere in codebase
- [ ] Documentation accurately reflects new V3 architecture
- [ ] Git history preserved with clear V3 implementation tag
- [ ] System functions identically to Phase 5 deployment

#### **Tests to Run:**
```bash
# Verify legacy code removal
find . -name "*legacy*" -type d | wc -l  # Should be 0
find . -name "*parallel_evidence*" -type d | wc -l  # Should be 0

# Test for broken imports
python -m py_compile rogr-api/*.py
python -m py_compile evidence_engine_v3/**/*.py

# Verify system still works perfectly
curl localhost:8000/analyses -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":"Final test claim after cleanup","type":"text"}' \
  | jq '.trust_score, .evidence_grade'

# Check git status
git status  # Should be clean
git log --oneline -5  # Should show V3 implementation commits
git tag | grep evidence_engine_v3  # Should show completion tag
```

#### **Validation Questions for You:**
1. Is the system functioning identically to Phase 5?
2. Are you comfortable with the legacy code being permanently deleted?
3. Does the documentation accurately represent the new architecture?
4. Should we proceed with the permanent cleanup?

---

## **RISK MITIGATION & ROLLBACK PLAN**

### **Development Safeguards:**

1. **Isolated Development**: V3 built in completely separate namespace - zero contamination risk
2. **Progressive Integration**: Each phase tested independently before proceeding to next
3. **Performance Gates**: Each phase must meet speed and quality targets to proceed
4. **Compatibility Testing**: Continuous validation against existing API contract
5. **Git Management**: Clear commits and tags for easy rollback at any phase

### **Rollback Strategy:**

#### **Phase 1-4 Rollback**:
- Continue using existing legacy system
- Abandon V3 development in isolated namespace
- No impact on production system
- All existing functionality preserved

#### **Phase 5 Rollback**:
- Revert FastAPI integration to legacy system
- Preserve V3 implementation for future development
- Restore original environment variables and feature flags
- System returns to pre-V3 functionality

#### **Phase 6 Rollback**:
- Git revert to pre-cleanup state
- Restore legacy and parallel evidence directories
- All legacy functionality available again
- V3 implementation preserved in git history

### **Emergency Rollback Procedure:**
```bash
# Phase 5 emergency rollback
git checkout HEAD~1 rogr-api/main.py  # Restore legacy FastAPI integration
git add rogr-api/main.py
git commit -m "Emergency rollback to legacy evidence system"

# Phase 6 emergency rollback
git revert HEAD  # Revert cleanup commit
git tag evidence_engine_v3_rollback_$(date +%Y%m%d)
```

### **Success Validation Metrics:**

#### **Technical Performance:**
- **Processing Time**: <15 seconds (ROGR_PRIMER_v2.md requirement) ✅
- **Evidence Relevance**: >70% (EEG improvement target) ✅
- **Query Efficiency**: ≤12 queries per claim (75% reduction target) ✅
- **IFCN Compliance**: 100% methodology-first approach ✅
- **Error Rate**: <5% in production environment ✅

#### **Quality Metrics:**
- **Trust Score Accuracy**: Maintains or improves current dual-AI quality ✅
- **Evidence Diversity**: Improved source methodology coverage ✅
- **Semantic Analysis**: 95% accuracy in claim interpretation ✅
- **User Experience**: Zero degradation in mobile app functionality ✅

#### **Integration Metrics:**
- **API Contract**: 100% compatibility with existing FastAPI endpoints ✅
- **TrustCapsule Format**: Identical structure to current implementation ✅
- **ClaimMiner Integration**: Seamless claim processing pipeline ✅
- **Frontend Compatibility**: No changes required to Flutter application ✅

---

## **INTEGRATION PRESERVATION GUARANTEE**

### **Preserved Interfaces:**

#### **ClaimMiner → Evidence Engine:**
```python
# Input format (unchanged):
claims = [claim.text for claim in mining_result.primary_claims]

# Processing (V3 enhancement):
trust_capsules = evidence_engine_v3.process_claims(claims)
```

#### **Evidence Engine → FastAPI:**
```python
# Output format (unchanged):
TrustCapsule(
    id=str,
    trust_score=int,           # 0-100 range preserved
    evidence_grade=str,        # A+ through F scale preserved
    confidence=str,            # High/Medium/Low preserved
    why=List[str],            # Summary bullets preserved
    claims=List[ClaimAnalysis], # Detailed analysis preserved
    overall_assessment=str,    # Assessment text preserved
    citations=List[Citation],  # Source citations preserved
    capsule_version=int,       # Version tracking preserved
    signed=bool,              # Signature field preserved
    created_at=str,           # Timestamp preserved
    input_type=str,           # Input type tracking preserved
    mode=str                  # Analysis mode preserved
)
```

#### **FastAPI → Frontend:**
```dart
// Flutter app expects identical API response format
// No changes required to mobile application
// All existing screens and widgets continue to work
// Evidence popup, capsule display, scanning flow preserved
```

### **Enhanced Capabilities (New Features):**

#### **Performance Improvements:**
- **Processing Speed**: Target <15s vs current variable performance
- **Query Efficiency**: ≤12 queries vs current ~48 operations (75% reduction)
- **Resource Usage**: Optimized memory and CPU utilization

#### **Quality Enhancements:**
- **Claim Understanding**: ACI semantic analysis for better interpretation
- **Evidence Quality**: EEG methodology-first approach for better sources
- **IFCN Compliance**: Professional fact-checking methodology throughout
- **Transparency**: Complete audit trails for all decisions

#### **Architecture Benefits:**
- **Single System**: No coexistence confusion or feature flag complexity
- **Clean Codebase**: Modular design for easy maintenance and enhancement
- **Scalability**: Designed for future AI model improvements
- **Maintainability**: Clear separation of concerns and documented interfaces

---

## **CONCLUSION**

Evidence Engine V3 provides a **complete replacement solution** that:

✅ **Eliminates Complexity**: No more coexistence confusion, parallel systems, or feature flags
✅ **Preserves Functionality**: All existing ClaimMiner→FastAPI→Frontend workflows maintained
✅ **Enhances Performance**: <15s processing target with 75% query reduction
✅ **Improves Quality**: ACI semantic analysis + EEG methodology-first evidence gathering
✅ **Ensures Compliance**: IFCN-compliant professional fact-checking throughout
✅ **Enables Growth**: Clean, modular architecture for future enhancements

The six-phase implementation plan provides clear roles, success criteria, and comprehensive testing procedures. Each phase includes specific validation questions and rollback procedures to ensure successful deployment.

This approach delivers the "single, superior Evidence Engine" you requested while maintaining all existing integrations and providing a foundation for continued innovation in fact-checking technology.

---

## **NEXT STEPS**

1. **Review and Approval**: Review this plan and approve architecture approach
2. **Phase 1 Kickoff**: Begin clean room setup and stub implementation
3. **Progressive Implementation**: Execute phases 2-6 with continuous validation
4. **Production Deployment**: Replace legacy systems with Evidence Engine V3
5. **Continuous Improvement**: Use modular architecture for ongoing enhancements

**Ready for Phase 1 implementation upon your approval.**