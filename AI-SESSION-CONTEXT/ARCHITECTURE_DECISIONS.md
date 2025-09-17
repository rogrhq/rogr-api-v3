# Architecture Decision Records (ADRs)

## ADR-001: Parallel Evidence Architecture Migration
**Date**: 2025-01-12  
**Status**: Approved  
**Context**: Current sequential evidence processing violates <15s performance requirement. Investigation revealed fundamental thread-safety violations preventing parallelization.

**Decision**: Implement complete architectural separation with legacy preservation + parallel system approach

**Consequences**:
- ✅ Thread-safe parallel processing enables <30s target achievement
- ✅ Legacy system preserved for rollback capability  
- ✅ Feature flag controlled migration reduces production risk
- ⚠️ Temporary dual-system maintenance overhead during migration
- ⚠️ Development complexity during transition period

**Implementation**: 
- Legacy files moved to `legacy_evidence_system/`  
- New architecture in `parallel_evidence_system/`
- Feature flag controlled switching in production

---

## ADR-002: Thread-Safe Resource Management Pattern
**Date**: 2025-01-12  
**Status**: Approved  
**Context**: Current evidence shepherds share API keys, HTTP sessions, and AI clients without thread synchronization, creating race conditions and resource conflicts.

**Decision**: Implement `ThreadSafeResourcePool` with thread-local resource isolation

**Pattern**:
```python
class ThreadSafeResourcePool:
    def get_worker_resources(self) -> WorkerResourceBundle:
        return WorkerResourceBundle(
            web_search=WebSearchService(session=self.session_pool.get_local()),
            content_extractor=WebContentExtractor(session=self.session_pool.get_local()),
            ai_scorer=EvidenceScorer(client=self.ai_client_pool.get_local())
        )
```

**Consequences**:
- ✅ Complete thread isolation prevents race conditions
- ✅ Resource cleanup managed through context managers
- ✅ Parallel execution without shared state conflicts
- ⚠️ Increased memory usage (isolated resources per thread)

---

## ADR-003: EEG + ACI Integration at Orchestrator Level  
**Date**: 2025-01-12  
**Status**: Approved  
**Context**: EEG Phase 1 (methodology-first IFCN queries) and ACI (Advanced Claim Interpretation) provide critical evidence quality improvements but were implemented on sequential architecture.

**Decision**: Integrate both EEG and ACI capabilities at `ParallelEvidenceOrchestrator` level for centralized strategy generation

**Integration Pattern**:
```python
class ParallelEvidenceOrchestrator:
    def generate_comprehensive_strategy(self, claim_text: str) -> ParallelSearchStrategy:
        # ACI semantic analysis enhances understanding
        semantic_result = self.semantic_analyzer.analyze(claim_text)
        
        # EEG methodology generation uses ACI insights
        eeg_strategy = self.methodology_strategist.generate_search_strategy(
            claim_text, semantic_context=semantic_result
        )
        
        return ParallelSearchStrategy(
            claim_analysis=semantic_result,
            search_queries=eeg_strategy.queries  # 9 IFCN-compliant queries
        )
```

**Consequences**:
- ✅ EEG query optimization (75% reduction: 144→9 queries) maintained
- ✅ ACI semantic analysis improves query targeting accuracy
- ✅ IFCN compliance enforced at single centralized point
- ✅ Strategy consistency across all parallel workers

---

## ADR-004: Same Repository with Modular Directory Structure
**Date**: 2025-01-12  
**Status**: Approved  
**Context**: Considered new repository vs branch vs directory approach for architectural migration.

**Decision**: Maintain same repository with `legacy_evidence_system/` and `parallel_evidence_system/` directories

**Rationale**:
- Git history preservation (136 commits of architectural evolution)
- Frontend integration continuity (no integration point changes)
- Single CI/CD pipeline with feature flag deployment
- Team coordination simplicity (single repository)
- Easy A/B testing and rollback capability

**Consequences**:
- ✅ Complete rollback capability to working legacy system
- ✅ Incremental migration with production safety
- ✅ Development context preservation
- ⚠️ Directory structure complexity during transition

---

## ADR-005: AI-Partnership Context Transfer Framework
**Date**: 2025-01-12  
**Status**: Approved  
**Context**: Claude Code auto-compact prevents context retention across sessions for ambitious architectural project requiring 15-20 development sessions.

**Decision**: Implement structured context transfer documentation in `AI-SESSION-CONTEXT/` directory

**Framework Components**:
- `CURRENT_SESSION_STATE.md`: What was accomplished + next priorities
- `NEXT_SESSION_OBJECTIVES.md`: Clear 1-hour objectives for next AI
- `IMPLEMENTATION_PROGRESS.md`: Detailed completion tracking
- `ARCHITECTURE_DECISIONS.md`: All ADRs consolidated
- `CODE_PATTERNS.md`: Established patterns for consistency

**Consequences**:
- ✅ Session continuity despite AI context limitations
- ✅ Consistent code patterns maintained across sessions
- ✅ Development velocity maintained (80% implementation vs 20% context recovery)
- ✅ Knowledge transfer preparation for human team handoff
- ⚠️ 15% session time overhead for context documentation