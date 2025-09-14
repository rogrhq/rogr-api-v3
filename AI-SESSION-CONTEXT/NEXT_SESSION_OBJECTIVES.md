# Next AI Session Objectives: Parallel System Error Handling Fix

## 🎯 CRITICAL FIX: Implement "Best-Effort" Content Extraction in Parallel System
**Root Cause:** Parallel system fails completely on partial extraction failures (0/F score)
**Legacy Behavior:** Continues with successful extractions despite 403 errors (86/A- score)
**Solution:** Modify parallel system to process partial successes like legacy system
**Commit:** 9c75793 - "TEST: Switch to legacy system to compare content extraction behavior"
**Backend:** 🔄 Currently on legacy system - https://69780239-96f5-4ce3-b826-d3453286c75d-00-2q5k9aqq28xtu.picard.replit.dev/

## 🎯 SESSION PRIORITY: Fix Parallel System Error Handling (45 min)

### Implementation Tasks Required (45 min)
1. **Parallel System Error Handling Fix (25 min)**
   - LOCATE: Where parallel system fails on extraction errors
   - MODIFY: Change "all-or-nothing" to "best-effort" approach
   - IMPLEMENT: Continue processing with successful extractions (8/10 pattern)
   - REFERENCE: Legacy system behavior in rogr_evidence_shepherd.py:75-85

2. **Testing and Validation (15 min)**
   - SWITCH: Set USE_PARALLEL_EVIDENCE=true after fix
   - TEST: "The Earth orbits around the Sun" should return 80+ score
   - VERIFY: Parallel system handles partial failures gracefully
   - CONFIRM: Performance matches legacy system results

3. **System Integration (5 min)**
   - DEPLOY: Push fixes and restart with parallel system active
   - MONITOR: Ensure consistent high scores for basic facts
   - DOCUMENT: Update implementation progress with completion status

### Investigation Summary from Previous Session (15 min review)
**ROOT CAUSE DISCOVERED:** Missing dedicated integration path for USE_PARALLEL_EVIDENCE=true
- Configuration fix works: USE_EVIDENCE_SHEPHERD=false ✅
- Parallel system created correctly ✅
- search_real_evidence method exists and works ✅
- BUT: System defaults to legacy scoring path when Evidence Shepherd disabled
- MISSING: Direct path to call evidence_system.process_claims_parallel()

## Success Criteria for Next Session
- [ ] **Parallel system error handling fixed** - continues processing despite 403 errors
- [ ] **Basic facts return 80+ scores** - "Earth orbits Sun" produces A/B grade results
- [ ] **Graceful degradation implemented** - processes 8/10 successful extractions like legacy
- [ ] **Performance parity achieved** - parallel system matches legacy system quality
- [ ] **System switched back to parallel** - USE_PARALLEL_EVIDENCE=true with working system
- [ ] **Git commit with error handling fix** - best-effort extraction implementation

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