# NLP ENRICHMENT IMPLEMENTATION - RISK ANALYSIS

**Date:** 2025-10-29
**Branch:** refactor_6_nlp_enrichment
**Purpose:** Analyze implementation risks and mitigation strategies before building NLP enrichment

---

## EXECUTIVE SUMMARY

**Risk Level:** 🟢 **LOW** (with proper implementation strategy)

**Key Findings:**
- ✅ Clean insertion point identified (`parse_claim()` function)
- ✅ Deterministic fallback ensures no regressions
- ✅ Backward compatibility maintained (all existing fields preserved)
- ⚠️ Performance impact manageable (200ms vs 1ms)
- ⚠️ Model loading requires memory management

**Recommendation:** Proceed with phased implementation using fallback pattern

---

## ARCHITECTURE ANALYSIS

### Current Flow

```
run_preview(text)
  ↓
enrich_claim_obj(claim)
  ↓
parse_claim(text)  ← INSERTION POINT
  ↓
extract_concept(text, parsed)
  ↓
Returns: {
    text, entities, numbers, cues, scope,
    concept, dimension, kind_hint
}
  ↓
build_search_plans_v2(claim)  ← CONSUMER
  ↓
Query generation uses: entities, numbers, scope, cues, kind_hint
```

### Critical Touch Points

**1. Entry Point:** `intelligence/analyze/enrich.py:enrich_claim_obj()`
- Called from: `intelligence/pipeline/run.py:180`
- Frequency: Once per claim (start of pipeline)

**2. Core Function:** `intelligence/claims/interpret.py:parse_claim()`
- Current: Pure deterministic (8 verbs, regex-based)
- Proposed: Hybrid (NLP + deterministic fallback)

**3. Downstream Consumers:**
- `intelligence/strategy/plan_v2.py:build_search_plans_v2()`
  - Expects: entities, numbers, scope, cues, kind_hint
  - **Risk:** None (fields preserved)

- `intelligence/pipeline/run.py:detect_claim_type()`
  - Expects: text, entities, numbers
  - **Risk:** None (fields preserved)

- `intelligence/preprocess/classify.py:classify_claim()`
  - Expects: text, entities, numbers
  - **Risk:** None (fields preserved)

---

## RISK ASSESSMENT BY CATEGORY

### 1. BREAKING CHANGES RISK: 🟢 **MINIMAL**

**Current Output Schema:**
```python
{
    "text": str,
    "entities": List[str],           # ["Water", "Celsius"]
    "numbers": {
        "percents": List[float],
        "years": List[int],
        "number_units": List[Tuple]
    },
    "cues": {
        "has_negation": bool,
        "has_comparison": bool,
        "has_attribution": bool
    },
    "scope": {
        "year_hint": int,
        "geo_hint": str
    },
    "concept": str,                   # "water boiling point"
    "dimension": str,                 # "temperature"
    "kind_hint": str                  # "comparative" | "attribution" | "statement"
}
```

**NLP Enhancement Strategy:**
- ✅ **Preserve all existing fields**
- ✅ **Add optional fields** (not breaking):
  - `nlp_confidence`: float (0-1)
  - `enrichment_method`: "deterministic" | "nlp" | "hybrid"
  - `nlp_metadata`: dict (optional debug info)

**Mitigation:**
- All existing fields remain unchanged
- Downstream consumers don't need modification
- Fields only get BETTER data (empty → populated)

### 2. REGRESSION RISK: 🟢 **NONE**

**Current Working Claims:** "Water boils at 100 degrees Celsius"
- Current: ✅ Works (concept='water boiling point', dimension='temperature')
- After NLP: ✅ Still works (deterministic fallback triggers first)

**Strategy:**
```python
def parse_claim_with_nlp(text: str) -> Dict[str, Any]:
    # 1. Try deterministic first (fast, proven)
    result = parse_claim_deterministic(text)

    # 2. If enrichment succeeded, return it
    if result["concept"] and result["entities"]:
        return {**result, "enrichment_method": "deterministic"}

    # 3. If enrichment failed, try NLP
    nlp_result = parse_claim_nlp(text)

    # 4. If NLP confidence too low, return deterministic (safe)
    if nlp_result["confidence"] < 0.7:
        return {**result, "enrichment_method": "deterministic"}

    # 5. Merge NLP improvements with deterministic base
    return {**result, **nlp_result, "enrichment_method": "nlp"}
```

**Guarantee:** Working claims can NEVER regress because deterministic runs first

### 3. PERFORMANCE RISK: 🟡 **MODERATE** (manageable)

**Current Performance:**
- `parse_claim()`: <1ms (deterministic regex)
- Total pipeline: ~5-10 seconds per claim

**NLP Performance:**
- First call (model loading): 2-5 seconds
- Subsequent calls: 50-200ms per claim
- Total pipeline impact: +200ms (~2-4% increase)

**Mitigation Strategies:**

**A. Lazy Loading (Recommended):**
```python
_nlp_model = None

def get_nlp_model():
    global _nlp_model
    if _nlp_model is None:
        _nlp_model = load_model()  # 2-5 seconds, once
    return _nlp_model
```

**B. Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def parse_claim_cached(text: str):
    return parse_claim_with_nlp(text)
```

**C. Async Loading (Future):**
- Load models on server startup
- No per-request penalty

**Impact Assessment:**
- Single-threaded: +200ms per claim (acceptable)
- High throughput: May need async workers
- Memory: +1-2GB for loaded models

### 4. MEMORY RISK: 🟡 **MODERATE** (manageable)

**Current Memory:** ~500MB-1GB (pipeline + dependencies)

**NLP Memory Requirements:**
- spaCy model: ~500MB (en_core_web_sm)
- BART model: ~1.5GB (facebook/bart-large-mnli)
- Total NLP: ~2GB loaded

**Total After NLP:** ~3-3.5GB

**Replit Limits:**
- Free tier: 1GB (insufficient)
- Hacker tier: 4GB ✅ (sufficient)
- Pro tier: 8GB (comfortable)

**Mitigation:**
- Use smaller models initially (en_core_web_sm, not en_core_web_trf)
- Consider distilbart instead of bart-large
- Lazy load models (only when needed)

### 5. DEPENDENCY RISK: 🟢 **LOW**

**New Dependencies:**
- `transformers` (140MB package, mature)
- `torch` (2GB package, industry standard)
- `spacy` (50MB package, mature)

**Risk Factors:**
- ✅ All packages are stable, mature, widely used
- ✅ Version locking prevents unexpected updates
- ✅ Fallback to deterministic if imports fail

**Mitigation:**
```python
try:
    from transformers import pipeline
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False
    # Log warning, use deterministic only
```

### 6. IFCN COMPLIANCE RISK: 🟢 **LOW**

**IFCN Requirements:**
1. Transparency ✅ (log method used, confidence scores)
2. Reproducibility ✅ (version lock models)
3. Human oversight ✅ (confidence thresholds, review triggers)
4. Corrections ✅ (fallback to deterministic)
5. Methodology disclosure ✅ (document in public docs)

**Strategy:**
- Always log enrichment method used
- Store model versions in metadata
- Trigger human review if confidence < 0.7
- Maintain deterministic fallback for explainability

### 7. ERROR HANDLING RISK: 🟢 **LOW**

**Potential Failures:**
1. Model loading failure
2. OOM during inference
3. NLP timeout (slow claims)
4. Unexpected input format

**Mitigation:**
```python
def parse_claim_safe(text: str) -> Dict[str, Any]:
    try:
        return parse_claim_with_nlp(text)
    except ImportError:
        logger.warning("NLP unavailable, using deterministic")
        return parse_claim_deterministic(text)
    except MemoryError:
        logger.error("OOM in NLP, using deterministic")
        return parse_claim_deterministic(text)
    except Exception as e:
        logger.error(f"NLP failed: {e}, using deterministic")
        return parse_claim_deterministic(text)
```

**Guarantee:** System NEVER fails due to NLP (always falls back)

---

## IMPLEMENTATION STRATEGY

### Phase 1: Create NLP Module (Isolated)

**File:** `intelligence/claims/nlp_interpret.py`

**Strategy:** Build completely separately, no integration yet

```python
def extract_concept_nlp(text: str) -> Dict[str, Any]:
    """NLP-based concept extraction (isolated implementation)"""
    # Domain classification
    # Entity recognition
    # Relationship extraction
    # Returns same schema as deterministic
```

**Risk:** 🟢 **ZERO** (no changes to existing code)

### Phase 2: Add Fallback Wrapper

**File:** `intelligence/claims/interpret.py`

**Strategy:** Create hybrid function, keep old function

```python
def parse_claim(text: str) -> Dict[str, Any]:
    """Current deterministic implementation (unchanged)"""
    # ... existing code ...

def parse_claim_hybrid(text: str) -> Dict[str, Any]:
    """New hybrid implementation with fallback"""
    deterministic = parse_claim(text)  # Call existing

    if deterministic["concept"]:
        return deterministic  # Use proven path

    # Only try NLP if deterministic failed
    return try_nlp_with_fallback(text, deterministic)
```

**Risk:** 🟢 **MINIMAL** (old function untouched)

### Phase 3: Update Entry Point

**File:** `intelligence/analyze/enrich.py`

**Change:**
```python
# OLD:
enrich = parse_claim(base.get("text",""))

# NEW:
enrich = parse_claim_hybrid(base.get("text",""))
```

**Risk:** 🟢 **LOW** (single line change, fallback ensures safety)

### Phase 4: Testing & Validation

**Test Battery:**
1. Regression tests (working claims still work)
2. Issue 7 tests (broken claims now work)
3. Performance tests (acceptable latency)
4. Memory tests (within limits)
5. Error injection (fallback works)

**Rollback Plan:** Change one line back to `parse_claim()`

---

## TESTING STRATEGY

### Test Suite Design

**1. Regression Tests (MUST PASS):**
```python
test_water_boiling()           # Current working case
test_ice_melting()             # Current working case
test_scientific_measurements() # All current patterns
```

**2. Issue 7 Tests (TARGET):**
```python
test_covid_vaccines()          # Issue 7 case
test_climate_change()          # Common claim type
test_election_claims()         # Political claims
test_medical_claims()          # Medical domain
```

**3. Performance Tests:**
```python
test_enrichment_latency()      # <200ms per claim
test_model_loading()           # <5s first call
test_memory_usage()            # <3.5GB total
```

**4. Fallback Tests:**
```python
test_nlp_unavailable()         # Falls back gracefully
test_low_confidence()          # Uses deterministic
test_nlp_error()               # Catches exceptions
```

### Success Criteria

**Required (Must Pass):**
- ✅ All regression tests pass (no working claims break)
- ✅ Issue 7 claim returns non-empty enrichment
- ✅ Latency increase <300ms
- ✅ Memory usage <4GB
- ✅ Fallback works when NLP fails

**Desired (Goals):**
- 🎯 Coverage increases from 10% → 80%+
- 🎯 Latency increase <200ms
- 🎯 NLP confidence >0.7 on 85% of claims

---

## ROLLBACK PLAN

### If Issues Arise

**Severity: CRITICAL (pipeline broken)**
```bash
# Immediate rollback (30 seconds)
cd rogrv2-backend
git revert HEAD  # Undo last commit
git push origin refactor_6_nlp_enrichment
# Redeploy
```

**Severity: HIGH (performance unacceptable)**
```python
# Code change only (5 minutes)
# In intelligence/analyze/enrich.py:
enrich = parse_claim(base.get("text",""))  # Use old function
# Commit and deploy
```

**Severity: MEDIUM (some claims fail)**
```python
# Adjust confidence threshold
NLP_CONFIDENCE_THRESHOLD = 0.8  # Increase from 0.7
# Falls back more often
```

**Severity: LOW (coverage not meeting goals)**
- Not a rollback scenario
- Iterate on NLP implementation
- Deterministic still works

---

## MONITORING PLAN

### Metrics to Track

**1. Enrichment Success Rate:**
```python
log.info(f"Enrichment: method={method}, concept={bool(concept)}, entities={len(entities)}")
```

**2. Performance:**
```python
log.info(f"Enrichment latency: {duration_ms}ms")
```

**3. Fallback Rate:**
```python
log.info(f"NLP fallback: reason={reason}")
```

**4. Confidence Distribution:**
```python
log.info(f"NLP confidence: {confidence}")
```

### Alerts

**Set up alerts for:**
- Enrichment failure rate >5%
- Average latency >500ms
- Fallback rate >50% (NLP not helping)
- Memory usage >3.5GB

---

## CONCLUSION

### Risk Summary

| Category | Risk Level | Mitigation | Rollback Time |
|----------|-----------|------------|---------------|
| Breaking Changes | 🟢 LOW | Schema preserved | N/A |
| Regressions | 🟢 NONE | Deterministic fallback | 30 seconds |
| Performance | 🟡 MODERATE | Lazy loading, caching | 5 minutes |
| Memory | 🟡 MODERATE | Smaller models, Replit tier | 30 seconds |
| Dependencies | 🟢 LOW | Version locking | 30 seconds |
| IFCN Compliance | 🟢 LOW | Full logging, fallback | N/A |
| Error Handling | 🟢 LOW | Try-except with fallback | N/A |

### Recommendation

**✅ PROCEED** with NLP implementation using phased approach:

1. **Week 1:** Build isolated NLP module + unit tests
2. **Week 1:** Add fallback wrapper + integration tests
3. **Week 2:** Deploy to staging + monitor performance
4. **Week 2:** Deploy to production with gradual rollout
5. **Week 3:** IFCN compliance documentation + auditing

### Key Success Factors

1. ✅ **Deterministic fallback ensures zero regressions**
2. ✅ **Isolated implementation reduces risk**
3. ✅ **Single-line integration enables instant rollback**
4. ✅ **Comprehensive testing catches issues early**
5. ✅ **Monitoring ensures production health**

### Final Assessment

**The implementation is LOW RISK with HIGH REWARD.**

The fallback pattern guarantees that:
- Working claims continue working
- Broken claims get fixed
- System never fails due to NLP
- Instant rollback available

**No fundamental architectural changes required. This is a DROP-IN enhancement with safety guarantees.**

---

**Status:** ✅ **APPROVED FOR IMPLEMENTATION**

**Next Step:** Begin Phase 1 (Create NLP module)
