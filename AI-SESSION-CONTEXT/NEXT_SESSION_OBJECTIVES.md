# Next AI Session Objectives: Architecture Migration Launch

## Session Priority: Phase 1 Implementation Start

### Hour 1 Objectives (Critical Foundation)
1. **Legacy System Preservation (20 min)**
   - Create `legacy_evidence_system/` directory
   - Move 13 shepherd files from root to legacy directory  
   - Update imports in main.py to maintain functionality
   - Test legacy system still works: `curl -X POST "BACKEND_URL/analyses" -H "Content-Type: application/json" -d '{"input": "test claim", "type": "text"}'`

2. **Parallel System Foundation (25 min)**
   - Create `parallel_evidence_system/` directory structure:
     ```
     parallel_evidence_system/
     ├── orchestrator/
     ├── workers/ 
     ├── resources/
     └── tests/
     ```
   - Implement basic `ThreadSafeResourcePool` class with thread-local storage pattern
   - Create `WorkerResourceBundle` for resource isolation

3. **Integration Framework (15 min)**
   - Implement `EvidenceSystemFactory` in main.py with feature flag support
   - Add `USE_PARALLEL_EVIDENCE` environment variable handling
   - Create basic A/B testing capability

### If Extra Time Available
4. **Worker Architecture Start (15-30 min)**
   - Implement `ThreadSafeEvidenceWorker` interface
   - Add basic `execute_strategy()` method signature
   - Create worker thread safety validation tests

## Success Criteria for Next Session
- [ ] Legacy system preserved and functional
- [ ] Parallel system directory structure created
- [ ] Basic resource pool implemented with thread isolation
- [ ] Feature flag integration working
- [ ] Git commit with "Phase 1: Legacy preservation + parallel foundation"

## Context Files to Update at Session End
- Update this file with Phase 2 objectives
- Update CURRENT_SESSION_STATE.md with implementation progress
- Create IMPLEMENTATION_PROGRESS.md with detailed completion tracking
- Document any new patterns in CODE_PATTERNS.md

## Architecture Reference
**Target Performance**: <30s total processing (87% improvement from 396s current)
**Key Innovation**: Complete thread-safety through resource isolation + parallel execution
**EEG Integration**: Methodology-first queries at orchestrator level
**ACI Integration**: Semantic analysis enhancing search strategy generation

## IMPORTANT: Complete Implementation Scope
**Total Phases**: 5 phases (not 4) - Phase 5 Integration is CRITICAL
**Phase 1-4**: Parallel evidence architecture implementation
**Phase 5**: ClaimMiner + FastAPI endpoint integration (REQUIRED for frontend compatibility)
**Without Phase 5**: System will not integrate with existing ClaimMiner or frontend