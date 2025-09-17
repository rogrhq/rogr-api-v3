# ADR-001: Evidence Engine V3 Complete Replacement Architecture

**Status**: Proposed
**Date**: 2024-12-17
**Deciders**: Product Owner, AI Development Team
**Technical Story**: Replace coexistence-contaminated evidence processing with single, superior Evidence Engine V3

---

## **Context and Problem Statement**

The current evidence processing system suffers from architectural contamination due to a failed coexistence model between legacy and enhanced systems. This has resulted in:

- **Complexity Overhead**: Parallel systems with confusing feature flags and fallback mechanisms
- **Performance Issues**: Dual system management causing processing delays (current ~48 operations vs target ≤12)
- **Integration Confusion**: Multiple overlapping shepherds with unclear responsibilities
- **Maintenance Burden**: Two systems to maintain, debug, and enhance
- **Developer Confusion**: Unclear data flow and inconsistent interfaces

**Key Requirements:**
- Single evidence processing system (no coexistence)
- <15 second processing time (ROGR_PRIMER_v2.md requirement)
- IFCN-compliant methodology-first approach
- Preserve all existing ClaimMiner→FastAPI→Frontend integration contracts
- Incorporate ACI semantic analysis and EEG enhanced gathering improvements

---

## **Decision**

We will implement **Evidence Engine V3 as a complete replacement** of all legacy evidence systems, incorporating the best components from ACI and EEG v2 plans while eliminating coexistence complexity.

### **Architectural Approach: Clean Room Replacement**

**Core Decision**: Build Evidence Engine V3 in isolated namespace (`evidence_engine_v3/`) with zero legacy contamination, then perform atomic replacement of legacy systems.

**Key Architectural Decisions:**

#### **1. Single Source of Truth Architecture**
- **Decision**: One unified Evidence Engine, no fallbacks or parallel systems
- **Rationale**: Eliminates coexistence complexity and feature flag management
- **Alternative Considered**: Gradual migration with coexistence
- **Why Rejected**: Current coexistence model has proven problematic and contaminating

#### **2. Modular Pipeline Architecture**
```
ClaimMiner → Evidence Engine V3 → TrustCapsule → FastAPI → Frontend
              ↓
        [ACI → EEG → Consensus → Scoring]
```

- **Decision**: Linear pipeline with discrete modules for each processing stage
- **Rationale**: Clear separation of concerns, testable components, maintainable architecture
- **Alternative Considered**: Monolithic evidence processor
- **Why Rejected**: Difficult to test, maintain, and enhance individual capabilities

#### **3. Interface Preservation Strategy**
- **Decision**: Maintain 100% compatibility with existing ClaimMiner and FastAPI contracts
- **Rationale**: Zero impact on working frontend and claim processing
- **Alternative Considered**: Update all interfaces simultaneously
- **Why Rejected**: High risk of breaking working functionality

#### **4. Performance-First Design**
- **Decision**: Target ≤15 second processing with ≤12 queries per claim
- **Rationale**: ROGR_PRIMER_v2.md speed requirements for user adoption
- **Alternative Considered**: Quality-first with flexible performance
- **Why Rejected**: Speed is critical path for user adoption per product requirements

---

## **Architecture Components**

### **Component 1: Advanced Claim Interpretation (ACI)**
**Purpose**: Semantic and logical claim analysis
**Based On**: ES_ACI_PLAN.md specifications
**Key Features**:
- Subject/object distinction in causal claims
- Causation vs correlation detection
- Temporal aspect analysis
- Domain classification with evidence requirements

### **Component 2: Enhanced Evidence Gathering (EEG)**
**Purpose**: IFCN-compliant evidence search and collection
**Based On**: ES_EEG_PLAN_v2.md specifications
**Key Features**:
- Methodology-first search strategy (not institution-based)
- Parallel evidence gathering with quality filtering
- ≤12 queries per claim performance target
- Complete audit trails for transparency

### **Component 3: Consensus Analysis**
**Purpose**: Multi-AI evidence quality assessment
**Based On**: Existing rogr_dual_evidence_shepherd.py logic
**Key Features**:
- Dual-AI consensus with uncertainty quantification
- Evidence quality scoring and validation
- Professional fact-checking methodology compliance

### **Component 4: ROGR Scoring**
**Purpose**: Trust score and evidence grade calculation
**Based On**: Existing rogr_fc_scoring_engine_zero_start.py
**Key Features**:
- Professional fact-checking trust scores (0-100)
- Evidence grades (A+ through F)
- IFCN-compliant scoring methodology

---

## **Integration Strategy**

### **Phase 1: Clean Room Development**
- Build Evidence Engine V3 in isolated `rogr-api/evidence_engine_v3/` namespace
- Zero dependency on legacy systems during development
- Comprehensive testing with mock data and stub implementations

### **Phase 2: Atomic Replacement**
- Update `main.py` to use Evidence Engine V3 exclusively
- Remove all legacy system imports and feature flags
- Delete legacy directories after successful deployment

### **Phase 3: Performance Optimization**
- Profile and optimize complete pipeline for ≤15 second target
- Implement monitoring and error tracking
- Fine-tune quality vs speed balance

---

## **Consequences**

### **Positive Consequences**

**Architectural Benefits:**
- **Simplified Codebase**: Single evidence system eliminates parallel complexity
- **Clear Data Flow**: Linear pipeline with well-defined interfaces
- **Maintainable Design**: Modular components enable independent enhancement
- **Performance Optimization**: Designed from ground up for speed targets

**Development Benefits:**
- **Clear Ownership**: Each module has specific responsibilities
- **Testability**: Individual components can be unit tested in isolation
- **Scalability**: Architecture supports future AI model improvements
- **Documentation**: Complete specifications eliminate implementation assumptions

### **Negative Consequences**

**Development Risks:**
- **Implementation Time**: Complete rewrite requires significant development effort
- **Integration Risk**: Must maintain exact compatibility with existing interfaces
- **Performance Risk**: New system must meet aggressive ≤15 second target
- **Quality Risk**: Must maintain or improve existing evidence quality

**Operational Risks:**
- **Rollback Complexity**: Complete replacement makes rollback more complex than gradual migration
- **Testing Coverage**: Must comprehensively test all functionality before replacement
- **Learning Curve**: New architecture requires team familiarization

---

## **Risk Mitigation Strategies**

### **Development Risks:**
1. **Isolated Development**: Build in separate namespace to prevent contamination
2. **Progressive Integration**: Test each component individually before full pipeline
3. **Interface Validation**: Continuous testing against existing API contracts
4. **Performance Monitoring**: Regular benchmarking against speed targets

### **Deployment Risks:**
1. **Rollback Plan**: Preserve legacy systems until V3 proven stable
2. **Gradual Cutover**: Feature flag for V3 testing before full deployment
3. **Comprehensive Testing**: End-to-end validation before legacy system removal
4. **Performance Validation**: Load testing and monitoring before production

---

## **Alternative Approaches Considered**

### **Alternative 1: Gradual Coexistence Migration**
**Description**: Incrementally replace legacy components while maintaining parallel systems
**Pros**: Lower risk, gradual validation, easier rollback
**Cons**: Complexity overhead continues, feature flag management, unclear completion criteria
**Rejection Reason**: Current coexistence model has proven architecturally contaminating

### **Alternative 2: Legacy System Enhancement**
**Description**: Improve existing legacy systems with ACI/EEG features
**Pros**: Lower development effort, familiar codebase, incremental improvement
**Cons**: Cannot achieve performance targets, maintains architectural debt, limited enhancement potential
**Rejection Reason**: Legacy architecture cannot support required performance improvements

### **Alternative 3: Microservices Architecture**
**Description**: Break evidence processing into separate microservices
**Pros**: Independent scaling, technology diversity, clear service boundaries
**Cons**: Network latency, complexity overhead, operational burden
**Rejection Reason**: Performance requirements demand single-process optimization

---

## **Implementation Validation Criteria**

### **Technical Validation:**
- [ ] Processing time ≤15 seconds per claim (ROGR_PRIMER_v2.md requirement)
- [ ] Query efficiency ≤12 queries per claim (75% reduction from current)
- [ ] Evidence relevance >70% (quality improvement target)
- [ ] IFCN compliance with complete audit trails
- [ ] Error rate <5% in production testing

### **Integration Validation:**
- [ ] TrustCapsule format 100% compatible with existing FastAPI contract
- [ ] ClaimMiner integration unchanged from client perspective
- [ ] Flutter frontend requires zero modifications
- [ ] All existing API endpoints function identically

### **Quality Validation:**
- [ ] Trust score accuracy maintained or improved vs legacy system
- [ ] Evidence diversity increased through methodology-first approach
- [ ] Professional fact-checking methodology compliance (IFCN)
- [ ] Comprehensive error handling and graceful degradation

---

## **Success Metrics**

### **Performance Metrics:**
- **Baseline**: Current system averages 79s processing time
- **Target**: Evidence Engine V3 averages <15s processing time
- **Measurement**: 95th percentile processing time under load testing

### **Quality Metrics:**
- **Baseline**: Current evidence relevance ~40%
- **Target**: Evidence Engine V3 achieves >70% relevance
- **Measurement**: Human evaluation of evidence relevance scores

### **Operational Metrics:**
- **Baseline**: Complex dual-system maintenance burden
- **Target**: Single system with clear architectural documentation
- **Measurement**: Developer onboarding time and system comprehension

---

## **Related Decisions**

- **ADR-002**: [Planned] Component Interface Specifications
- **ADR-003**: [Planned] ACI Module Implementation Standards
- **ADR-004**: [Planned] EEG Module IFCN Compliance Framework
- **ADR-005**: [Planned] Performance Monitoring and Alerting Strategy

---

## **Notes**

**Context Documents Referenced:**
- `ROGR_PRIMER_v2.md` - Performance and integration requirements
- `ES_ACI_PLAN.md` - Advanced Claim Interpretation specifications
- `ES_EEG_PLAN_v2.md` - Enhanced Evidence Gathering methodology
- `RDT_v2.md` - Development methodology and compliance requirements
- `FLAWLESS_IMPLEMENTATION_METHODOLOGY.md` - Implementation validation framework

**Implementation Methodology:**
This ADR follows RDT v2.0 requirements for complete specification before implementation. All components must have detailed interfaces defined before any code development begins, following the 3-Layer Validation Framework from FLAWLESS_IMPLEMENTATION_METHODOLOGY.md.

**Approval Status**: Pending product owner review and technical team validation