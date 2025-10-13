# Semantic Logic Inventory - Phase 2 Pre-Analysis

## Executive Summary

**Audit Date:** 2025-10-12
**Last Updated:** 2025-10-12 (Added P27-P29 orchestration modules)

**Modules Audited:** 8
- **Content Modules (5):** P20, P21, P23, P24, + extract_facts shared utility
- **Orchestration Modules (3):** P27 (consensus), P28 (diversification), P29 (telemetry)

**Total Features Found:** 56 semantic + orchestration features across 11 categories
**Reusable Components:** 36 (64%)
**Gaps to Fill:** 20 (36%)

**Key Finding:** Most semantic logic already exists but is scattered across modules. High reuse potential! The biggest gaps are in paraphrase/synonym systems and unit normalization.

**Orchestration Finding:** P27-P29 are mostly infrastructure (not semantic logic). They coordinate research but don't do semantic analysis. Main gaps are configuration enhancements (variable formulas, knobs, parity checking).

**Opportunity:** Extract shared logic into centralized utilities (`intelligence/content/shared/`) to avoid duplication and enable cross-module improvements. Orchestration modules need configuration enhancements, not semantic logic.

---

## Feature-by-Feature Analysis

### 1. Paraphrase/Synonym Systems

#### Found in P20 (grade.py):
- [X] **No explicit paraphrase system**
- Details: Uses keyword matching only
- Missing: Verb ↔ Noun mappings, synonym expansion

#### Found in P21 (fullread.py):
- [X] **No explicit paraphrase system**
- Details: Relies on trigram similarity for lexical matching
- Missing: Semantic equivalences

#### Found in P23 (semantic_read.py):
- [X] **No explicit paraphrase system**
- Details: Token-based matching with stop word filtering
- Missing: Synonym dictionaries

#### Found in P24 (semantic_frames.py):
- [✓] **Partial**: Action verb families
- **Lines:** 74-75
- **Code:**
  ```python
  INC_VERBS = {"increase","increased","raise","raised","boost","boosted","grow","grew",...}
  DEC_VERBS = {"decrease","decreased","reduce","reduced","cut","cuts","lower",...}
  ```
- **Completeness:** Budget/policy domain only, missing scientific domain

#### Found in extract_facts.py:
- [✓] **Partial**: Predicate families
- **Lines:** 27-28
- **Code:**
  ```python
  PRED_INCREASE = ("increase","increased","rising","rise","grew","growth","up","higher")
  PRED_DECREASE = ("decrease","decreased","decline","down","lower","reduced","reduction")
  ```
- **Completeness:** Similar to P24, policy-oriented

#### Reusability Assessment:
- **Can reuse?** Yes - P24's INC_VERBS/DEC_VERBS and extract_facts PRED_* are similar
- **Where to use?** Centralize in shared module for P20, P21, P23, P24
- **What's missing?**
  - Scientific domain verbs (boil → boiling point, freeze → freezing point)
  - Synonym expansion (unemployment → jobless → without work)
  - Verb ↔ Noun mappings (increase → growth, decrease → decline)
  - Domain-specific vocabularies (temperature, pressure, altitude)

---

### 2. Unit Normalization/Conversion

#### Found in P20 (grade.py):
- [X] **No unit normalization**
- Details: Basic number extraction via extract_facts.claim_numbers()
- Missing: Unit parsing, conversion, standardization

#### Found in P21 (fullread.py):
- [✓] **Partial**: Percentage extraction with tolerance
- **Lines:** 22, 80-105
- **Code:**
  ```python
  _PERCENT = re.compile(r"(?:(\d{1,3})(?:\.\d+)?)\s?%|\b(\d{1,2})\s?(?:percent|per\s?cent)\b", re.I)

  def _percent_hits(claim: str, text: str) -> Tuple[bool, bool]:
      # ... extracts percentages ...
      # close if within 0.5 absolute or within 10% relative tolerance
      close = any(
          abs(t - c) <= 0.5 or (abs(t - c) / max(0.5, c)) <= 0.10
          for c in claim_nums for t in tnums
      )
  ```
- **Completeness:** Percentages only, with tolerance matching!
- **Missing:** Temperature, distance, money, other units

#### Found in P23 (semantic_read.py):
- [✓] **Basic**: Percentage extraction
- **Lines:** 63-70
- **Code:**
  ```python
  def _percent_numbers(text: str) -> List[str]:
      # 8% or 8 percent
      for m in re.finditer(r"\b(\d{1,3})\s*%\b", text):
          hits.append(m.group(1) + "%")
      for m in re.finditer(r"\b(\d{1,3})\s+percent\b", text):
          hits.append(m.group(1) + "%")
  ```
- **Completeness:** String format only, no numeric comparison

#### Found in P24 (semantic_frames.py):
- [✓] **Numeric**: Percentage extraction with numeric tolerance
- **Lines:** 89-97, 146-157
- **Code:**
  ```python
  def _percent_numbers(text: str) -> List[float]:  # Returns floats!
      # ... extracts as numbers ...

  def _quantity_compatible(cq: List[float], wq: List[float], tol_pp: float = 1.0):
      # Tolerance matching: ±1.0 percentage point
      if abs(c - w) <= tol_pp:
          return (True, "within_tolerance")
  ```
- **Completeness:** Percentages with tolerance (±1.0 pp), numeric comparison logic

#### Found in extract_facts.py:
- [✓] **Basic**: Percentage forms with word variants
- **Lines:** 21, 41-46, 64-80
- **Code:**
  ```python
  _PERCENT = re.compile(r"\b(\d{1,3})\s?%\b")

  def percent_forms(n: str) -> List[str]:
      forms = [f"{n}%"]
      w = NUMBER_WORDS.get(n)  # "eight"
      if w:
          forms.append(f"{w} percent")
      return forms
  ```
- **Completeness:** String variants ("8%" vs "eight percent")

#### Reusability Assessment:
- **Can reuse?** YES - P21's tolerance logic and P24's numeric comparison are excellent
- **Where to use?** Create shared `intelligence/content/shared/units.py`
- **Merge strategy:**
  - P21's `_percent_hits()` tolerance logic → foundation
  - P24's `_quantity_compatible()` → extend with P21's dual tolerance (absolute + relative)
  - extract_facts `percent_forms()` → word variant handling
- **What's missing?**
  - Temperature conversion (°C ↔ °F ↔ K)
  - Distance conversion (km ↔ miles ↔ meters)
  - Money normalization ($1M vs $1,000,000)
  - Unit detection and standardization

---

### 3. Condition Recognition/Equivalence

#### Found in P20 (grade.py):
- [X] **No condition recognition**

#### Found in P21 (fullread.py):
- [X] **No condition recognition**

#### Found in P23 (semantic_read.py):
- [X] **No condition recognition**

#### Found in P24 (semantic_frames.py):
- [✓] **Partial**: Scope detection (budget context)
- **Lines:** 73, 78-79, 129, 141, 172-175
- **Code:**
  ```python
  BUDGET_CONTEXT = {"budget","general fund","operating budget","fy","fiscal",...}

  def _has_budget_context(toks: List[str]) -> bool:
      return any(w in BUDGET_CONTEXT for w in toks)

  def _scope_ok(cs: str, ws: str) -> Tuple[bool, str]:
      # Checks if scopes match
  ```
- **Completeness:** Budget/fiscal scope only
- **Missing:** Scientific conditions (pressure, altitude), temporal conditions (time periods), location conditions

#### Found in extract_facts.py:
- [✓] **Basic**: Scope words
- **Lines:** 26, 137-142
- **Code:**
  ```python
  SCOPE_WORDS = ("general fund","all funds","enterprise fund","capital","operating","city budget","budget")

  def scope_hint(text: str) -> str:
      for s in SCOPE_WORDS:
          if s in T:
              return s
  ```
- **Completeness:** Budget scope only

#### Reusability Assessment:
- **Can reuse?** Partially - budget scope logic exists
- **Where to use?** Extend to multi-domain condition system
- **What's missing?**
  - Pressure conditions ("at sea level", "at altitude", "1 atm")
  - Temporal conditions ("in FY2024", "by 2022", "during Q3")
  - Location conditions ("in California", "nationwide")
  - Condition equivalence mappings (sea level = standard pressure = 1 atm)
  - Condition compatibility checks (sea level ≠ altitude, but explains variation)

---

### 4. Numeric Tolerance/Comparison

#### Found in P20 (grade.py):
- [X] **No numeric tolerance**
- Details: Uses has_any() for exact matching only

#### Found in P21 (fullread.py):
- [✓] **YES! Excellent implementation**
- **Lines:** 80-105
- **Code:**
  ```python
  def _percent_hits(claim: str, text: str) -> Tuple[bool, bool]:
      # close if within 0.5 absolute or within 10% relative tolerance
      close = any(
          abs(t - c) <= 0.5 or (abs(t - c) / max(0.5, c)) <= 0.10
          for c in claim_nums for t in tnums
      )
      return (True, close)
  ```
- **Completeness:** Dual tolerance (absolute ±0.5 AND relative ±10%) ✓
- **Quality:** Production-ready, handles edge cases

#### Found in P23 (semantic_read.py):
- [X] **No numeric tolerance**
- Details: String matching only

#### Found in P24 (semantic_frames.py):
- [✓] **YES! Simpler implementation**
- **Lines:** 146-157
- **Code:**
  ```python
  def _quantity_compatible(cq: List[float], wq: List[float], tol_pp: float = 1.0):
      if abs(c - w) <= tol_pp:
          return (True, "within_tolerance")
      return (False, "mismatch_quantity")
  ```
- **Completeness:** Absolute tolerance only (±1.0 pp)
- **Quality:** Simpler but less robust than P21

#### Found in extract_facts.py:
- [X] **No numeric tolerance**

#### Reusability Assessment:
- **Can reuse?** YES - P21's implementation is the gold standard
- **Where to use?** Centralize in `shared/units.py` for all modules
- **Upgrade strategy:**
  - P21's dual tolerance → default for percentages
  - Extend to other numeric types (temperature, currency)
  - P24 should import from shared instead of duplicating
- **What's missing?**
  - Temperature tolerance (±0.5°C)
  - Year tolerance (usually exact match)
  - Currency tolerance (±$100 or ±5%)
  - Configurable tolerance per domain

---

### 5. Entity Extraction/Matching

#### Found in P20 (grade.py):
- [✓] **Via extract_facts import**
- **Lines:** 32-34, 82-88
- **Code:**
  ```python
  from intelligence.content.extract_facts import claim_entities, ...

  ents = claim_entities(claim_text)
  has_ent = has_any(window, ents)
  ```
- **Completeness:** Uses shared utility

#### Found in P21 (fullread.py):
- [✓] **Token-based overlap**
- **Lines:** 112-118
- **Code:**
  ```python
  def _entity_overlap(claim: str, text: str) -> float:
      ct = set(_tokens(claim))
      tt = set(_tokens(text))
      inter = len(ct & tt)
      return inter / float(len(ct))
  ```
- **Completeness:** Simple overlap percentage

#### Found in P23 (semantic_read.py):
- [✓] **Length-based filtering**
- **Lines:** 119
- **Code:**
  ```python
  entities = [t for t in c_toks if len(t) > 2][:8]
  ```
- **Completeness:** Crude (length > 2), no identity checking

#### Found in P24 (semantic_frames.py):
- [✓] **Domain-aware filtering**
- **Lines:** 106-118, 166-170
- **Code:**
  ```python
  def _entities_from_claim_tokens(toks: List[str]) -> List[str]:
      # Excludes budget/action words
      for t in toks:
          if len(t) > 2 and t not in BUDGET_CONTEXT and t not in INC_VERBS and t not in DEC_VERBS:
              out.append(t)

  def _entity_overlap(ce: List[str], we: List[str]) -> Tuple[bool, str]:
      inter = set(ce) & set(we)
      return (bool(inter), "entity_overlap" if inter else "entity_mismatch")
  ```
- **Completeness:** Best implementation - domain-aware, overlap checking

#### Found in extract_facts.py:
- [✓] **Capitalization-based**
- **Lines:** 51-62
- **Code:**
  ```python
  def claim_entities(claim: str) -> List[str]:
      for t in tokenize(claim):
          if len(t) > 2 and t[0].isupper():
              ents.extend([t, f"City of {t}", f"{t} City Council"])
  ```
- **Completeness:** Capitalization + city aliases

#### Reusability Assessment:
- **Can reuse?** YES - but implementations vary in quality
- **Where to use?** Consolidate best practices
- **Best approach:**
  - extract_facts capitalization logic → base extraction
  - P24 domain-aware filtering → enhancement
  - P21 overlap percentage → scoring
- **What's missing?**
  - Entity type classification (location vs organization)
  - Entity identity verification (California ≠ Texas)
  - Entity normalization (CA = California)
  - Named entity recognition (proper NER)

---

### 6. Frame-Based Reasoning

#### Found in P20 (grade.py):
- [X] **No frame structure**
- Details: Flat keyword matching

#### Found in P21 (fullread.py):
- [X] **No frame structure**
- Details: Signal-based scoring

#### Found in P23 (semantic_read.py):
- [X] **No frame structure**
- Details: Signal-based scoring similar to P21

#### Found in P24 (semantic_frames.py):
- [✓] **YES! Full frame implementation**
- **Lines:** 121-144, 177-206
- **Code:**
  ```python
  def extract_claim_frame(claim_text: str) -> Dict[str, Any]:
      frame = {
          "entity": _entities_from_claim_tokens(ctoks),
          "action": _detect_action(ctoks),
          "quantity": _percent_numbers(c_norm)[:1],
          "year": _years(c_norm)[:1],
          "scope": "budget" if ... else "unknown",
      }

  def _entail_contradict(claim: Dict, win: Dict, sim: float) -> Tuple[str, List[str]]:
      # Slot-by-slot comparison
      # Returns: entail/contradict/mixed/unrelated + rules
  ```
- **Completeness:** Full frame structure with entailment/contradiction logic ✓
- **Quality:** Production-ready for budget/policy domain

#### Found in extract_facts.py:
- [✓] **Partial**: Fact view structure
- **Lines:** 144-157
- **Code:**
  ```python
  def extract_fact_view(claim: str, text: str) -> Dict[str, Any]:
      return {
          "entities": ents,
          "numbers": nums,
          "years": yrs,
          "scope": scope,
          "predicate": pred,
      }
  ```
- **Completeness:** Similar to frame but less structured

#### Reusability Assessment:
- **Can reuse?** YES - P24's frame logic is excellent
- **Where to use?** Extend to other modules (P20, P21, P23)
- **Integration strategy:**
  - P24 frames → foundation
  - Add scientific domain frames (phenomenon, temperature, pressure, condition)
  - P20 should use frames instead of keyword matching
- **What's missing?**
  - Scientific domain frames (temperature claims, physical phenomena)
  - Multi-domain frame adapters
  - Frame-based stance detection for P20
  - Contextual reasoning (condition-aware entailment)

---

### 7. Relationship Detection

#### Found in P20 (grade.py):
- [X] **No relationship detection**

#### Found in P21 (fullread.py):
- [X] **No explicit relationship detection**
- Details: Negation detection (_NEG) but no causal/temporal

#### Found in P23 (semantic_read.py):
- [X] **No relationship detection**

#### Found in P24 (semantic_frames.py):
- [X] **No explicit relationship detection**
- Details: Has negation but no causal/temporal/conditional

#### Found in extract_facts.py:
- [X] **No relationship detection**

#### Reusability Assessment:
- **Can reuse?** N/A - doesn't exist
- **What's missing?**
  - Causal relationships (because, due to, caused by)
  - Temporal relationships (before, after, during, since)
  - Conditional relationships (if, when, unless)
  - Contrastive relationships (but, however, although)

---

### 8. Action/Directional Logic

#### Found in P20 (grade.py):
- [✓] **Basic**: Keyword-based
- **Lines:** 54-55
- **Code:**
  ```python
  is_inc = any(w in t for w in ("increase","increased","up","rise","grew","growth","higher"))
  is_dec = any(w in t for w in ("decrease","decreased","down","lower","reduced","reduction"))
  ```
- **Completeness:** Policy-oriented keywords
- **Issue:** Used in stance detection, causes scientific claim failures

#### Found in P21 (fullread.py):
- [✓] **Stance verbs**: Support/challenge keywords
- **Lines:** 25-26, 69-78
- **Code:**
  ```python
  _SUPPORT = re.compile(r"\b(confirms?|supports?|corroborates?|shows|finds|indicates)\b", re.I)
  _CHALLENGE = re.compile(r"\b(disputes?|contradicts?|refutes?|debunks?|casts\s+doubt|challenges?)\b", re.I)

  def _stance_for_chunk(txt: str) -> str:
      sup = bool(_SUPPORT.search(txt))
      ch = bool(_CHALLENGE.search(txt))
  ```
- **Completeness:** Meta-stance verbs (verbs ABOUT stances)

#### Found in P23 (semantic_read.py):
- [✓] **Stance verbs**: Similar to P21
- **Lines:** 14, 75-85
- **Code:**
  ```python
  _SUPPORT_VERBS = {"confirm","shows","reports","states","announced","increased","approved",...}

  def _stance_for_window(win_norm: str) -> str:
      sup = bool(toks & _SUPPORT_VERBS)
  ```
- **Completeness:** Mix of meta-stance and action verbs

#### Found in P24 (semantic_frames.py):
- [✓] **YES! Best implementation**
- **Lines:** 74-75, 81-87
- **Code:**
  ```python
  INC_VERBS = {"increase","increased","raise","raised","boost","boosted","grow","grew",...}
  DEC_VERBS = {"decrease","decreased","reduce","reduced","cut","cuts","lower",...}

  def _detect_action(toks: List[str]) -> str:
      if any(w in INC_VERBS for w in toks):
          return "increase"
      if any(w in DEC_VERBS for w in toks):
          return "decrease"
      return "unknown"
  ```
- **Completeness:** Comprehensive action detection

#### Found in extract_facts.py:
- [✓] **Similar to P24**
- **Lines:** 27-28, 96-102, 104-115
- **Code:**
  ```python
  PRED_INCREASE = ("increase","increased","rising","rise","grew","growth","up","higher")
  PRED_DECREASE = ("decrease","decreased","decline","down","lower","reduced","reduction")

  def predicate_hint(text: str) -> str:
      if any(w in T for w in PRED_INCREASE):
          return "increase"

  def stance_hint(text: str) -> str:
      # Combines predicate with negation
  ```
- **Completeness:** Similar to P24, includes stance hint

#### Reusability Assessment:
- **Can reuse?** YES - P24/extract_facts have good implementations
- **Where to use?** Consolidate into shared module
- **Merge strategy:**
  - P24 INC_VERBS/DEC_VERBS → foundation
  - P21/P23 meta-stance verbs → separate category
  - extract_facts stance_hint → combine action + negation
- **What's missing?**
  - Scientific domain actions (boil, freeze, melt, evaporate)
  - Action alignment checking (claim action vs evidence action)
  - Directional contradiction detection (increased vs decreased)

---

## 9. Negation Handling

#### Found across all modules:
- **P20 (grade.py):** Line 56
- **P21 (fullread.py):** Lines 24, 168, 189-193
- **P23 (semantic_read.py):** Lines 10-13, 77
- **P24 (semantic_frames.py):** Lines 76, 142, 185, 191-192
- **extract_facts.py:** Lines 29, 106, 109

#### Implementations:

**P20:**
```python
neg = any(w in t for w in ("not ","no ","false","incorrect","deny","dispute","refute","contradict","debunk"))
```

**P21:**
```python
_NEG = re.compile(r"\b(no|not|never|without|lacks|declined|denied|false|incorrect|inaccurate|misleading)\b", re.I)
neg = bool(_NEG.search(txt))
# Stance adjustment based on negation
```

**P23:**
```python
_NEG_TOKENS = {"not","no","never","none","without","fails","didn't","didnt","doesn't","doesnt",...}
neg = bool(toks & _NEG_TOKENS)
```

**P24:**
```python
NEG_WORDS = {"not","no","never","without","deny","denied","false","untrue","incorrect",...}
neg = bool(set(wtoks) & NEG_WORDS)
# Used in entailment logic
```

**extract_facts.py:**
```python
NEGATORS = ("not","no","false","incorrect","deny","denied","dispute","disputed","refute","refuted","contradict","contradicted","debunk")
neg = any(w in T for w in NEGATORS)
# Used in stance_hint()
```

#### Reusability Assessment:
- **Can reuse?** YES - multiple implementations, should consolidate
- **Best implementation:** P21's regex (handles word boundaries)
- **Merge strategy:**
  - P21 _NEG regex → foundation (best)
  - Expand with P23/P24 additional terms
  - Standardize across all modules
- **What's missing?**
  - Negation scope detection (what is being negated?)
  - Double negation handling
  - Implicit negation (lack of, absence of)

---

## 10. Consensus Logic (P27)

**Module Type:** Orchestration / Coordination (not semantic analysis)

#### Found in P27 (consensus/dual_lane.py):
- [✓] **YES**: Agreement/disagreement detection
- **Lines:** 52-118
- **Code:**
  ```python
  def compute_consensus(r1_verdict, r2_verdict):
      # Agreement case
      if r1_label == r2_label:
          base_conf = max(r1_conf, r2_conf)
          bonus = 0.10  # FIXED
          final_conf = min(base_conf + bonus, 0.95)

      # Disagreement case
      if delta >= 0.20:  # Clear gap
          penalty = -0.05  # FIXED
      else:  # Too close
          penalty = -0.10  # FIXED
  ```
- **Completeness:** Fixed adjustments (+0.10, -0.05, -0.10)
- **Quality:** Works correctly but simplified

#### Archived Wrapper Has (TO BE RESTORED):
- [✓] **Variable bonus/penalty formulas**
- **Lines:** MONKEY_PATCH_ARCHIVE/wrappers/content/p27_consensus.py:52-92
- **Code:**
  ```python
  # Wrapper's variable formulas:
  bonus = min(0.20, 0.10 + 0.50 * abs(c1 - c2))  # Adapts to confidence gap
  penalty = min(0.30, 0.15 + 0.50 * abs(c1 - c2))  # Increases with disagreement
  base_conf = (c1 + c2) / 2.0  # Uses average, not max
  ```
- **Benefit:** More conservative when researchers have different confidences

#### Reusability Assessment:
- **Can reuse?** N/A - This is orchestration, not reusable semantic logic
- **Needs enhancement?** YES - Restore wrapper's variable formulas
- **What's missing?**
  - Variable bonus formula (currently fixed +0.10)
  - Variable penalty formula (currently fixed -0.05/-0.10)
  - Average-based confidence (currently uses max)
- **Dependencies:** None - self-contained
- **Used by:** P26 orchestration (run.py:152-156)

#### Cross-Module Impact:
- **Does P27 use any semantic logic from P20-P24?** NO
- **Could P20-P24 use P27 logic?** NO (orchestration only)
- **Does P27 need shared utilities?** NO (pure math/logic)

---

## 11. Diversification Logic (P28)

**Module Type:** Configuration / Setup (not semantic analysis)

#### Found in P28 (planning/diversify.py):
- [✓] **YES**: Seed generation
- **Lines:** 19-23
- **Code:**
  ```python
  def _generate_seed(lane_id: str, claim_text: str) -> int:
      combined = f"{lane_id}:{claim_text}"
      hash_obj = hashlib.md5(combined.encode())
      return int(hash_obj.hexdigest(), 16) % (2**31)
  ```
- **Completeness:** Deterministic, reproducible ✓
- **Different from wrapper:** Wrapper uses `f"{lane}::{claim}"` and first 8 hex chars

#### Found in P28: Provider Detection
- [✓] **Basic**: Single env var per provider
- **Lines:** 7-16
- **Code:**
  ```python
  def get_available_providers() -> List[str]:
      providers = []
      if os.getenv('GOOGLE_CSE_API_KEY'):
          providers.append('google')
      if os.getenv('BRAVE_API_KEY'):
          providers.append('brave')
      if os.getenv('BING_API_KEY'):
          providers.append('bing')
  ```
- **Completeness:** Works but simplified

#### Archived Wrapper Has (TO BE RESTORED):
- [✓] **Multi-env-var detection**
- **Code:**
  ```python
  # Wrapper checks multiple env var names per provider:
  # BING_API_KEY or BING_SUBSCRIPTION_KEY or AZURE_BING_KEY
  ```
- **Benefit:** More robust environment detection

#### Found in P28: Query Shuffling
- [✓] **YES**: Deterministic shuffling
- **Lines:** 36-40
- **Code:**
  ```python
  def _shuffle_queries_deterministic(queries: List[str], seed: int) -> List[str]:
      shuffled = queries.copy()
      random.Random(seed).shuffle(shuffled)
      return shuffled
  ```
- **Completeness:** Working ✓

#### Found in P28: Provider Ordering
- [✓] **YES**: R1 Google-first, R2 Brave-first
- **Lines:** 26-33
- **Code:**
  ```python
  def _ordered_providers_for_lane(lane_id: str, available: List[str]) -> List[str]:
      if lane_id == "R1":
          return sorted(available, key=lambda p: (p != 'google', p))
      else:  # R2
          return sorted(available, key=lambda p: (p != 'brave', p))
  ```
- **Completeness:** Achieves diversification goal ✓

#### Reusability Assessment:
- **Can reuse?** N/A - This is configuration, not semantic logic
- **Needs enhancement?** Minor - Multi-env-var provider detection
- **What's missing?**
  - Multiple env var names per provider (wrapper feature)
  - Arm name mapping flexibility ("A_SUPPORT" → "A")
- **Dependencies:** None - self-contained
- **Used by:** P26 orchestration (run.py:33-35)

#### Cross-Module Impact:
- **Does P28 use any semantic logic from P20-P24?** NO
- **Could P20-P24 use P28 logic?** NO (configuration only)
- **Does P28 need shared utilities?** NO (pure config)

---

## 12. Reproducibility Features (P29)

**Module Type:** Telemetry / Tracking (not semantic analysis)

#### Found in P29 (telemetry/collect.py):
- [✓] **YES**: LaneTelemetry class
- **Lines:** 6-24
- **Code:**
  ```python
  class LaneTelemetry:
      def __init__(self, lane_id: str):
          self.lane_id = lane_id
          self.start_time = time.time()
          self.provider_calls = {}

      def record_provider_call(self, provider: str) -> None:
          self.provider_calls[provider] = self.provider_calls.get(provider, 0) + 1

      def finalize(self) -> Dict[str, Any]:
          duration = (time.time() - self.start_time) * 1000
          return {"providers": self.provider_calls, "duration_ms": int(duration)}
  ```
- **Completeness:** Core features working ✓
- **Quality:** Manual telemetry (requires explicit record_provider_call())

#### Found in P29: Replay ID Generation
- [✓] **YES**: Deterministic replay IDs
- **Lines:** 26-52
- **Code:**
  ```python
  def generate_manifest(claim_text, r1_config, r2_config):
      combined = f"{claim_text}:{r1_config.get('seed')}:{r2_config.get('seed')}"
      replay_id = hashlib.md5(combined.encode()).hexdigest()
      return {
          "replay_id": replay_id,
          "lanes": {"R1": {...}, "R2": {...}},
          "created_at": datetime.utcnow().isoformat() + "Z"
      }
  ```
- **Completeness:** Basic manifest working ✓

#### Archived Wrapper Has (TO BE RESTORED):
- [✓] **Enhanced manifest fields**
  - `providers_available` - Environment snapshot at runtime
  - `knobs` per lane - Configuration controls:
    - `query_shuffle` (bool)
    - `timeout_jitter_ms` (int)
    - `max_per_provider` (int)
  - `diversified` flag - Top-level indicator
  - `parity.providers_equal` - Provider set equality check

- [✓] **Automatic telemetry collection**
  - Wrapper: Uses ContextVar and wrappers for auto-collection
  - Clean: Requires manual record_provider_call()

#### Reusability Assessment:
- **Can reuse?** Partially - telemetry tracking could be used elsewhere
- **Needs enhancement?** YES - Restore enhanced manifest features
- **What's missing?**
  - Knobs configuration in manifest
  - providers_available environment snapshot
  - Parity checking (R1 vs R2 provider equality)
  - Auto-telemetry via ContextVar (vs manual tracking)
- **Dependencies:** None - self-contained
- **Used by:** P26 orchestration (run.py:38-45, 160-165)

#### Cross-Module Impact:
- **Does P29 use any semantic logic from P20-P24?** NO
- **Could P20-P24 use P29 logic?** Potentially - telemetry tracking could be useful
- **Does P29 need shared utilities?** NO (pure tracking/logging)

---

## Reuse Strategy

### Shared Utilities to Create:

#### 1. `intelligence/content/shared/vocabulary.py`
**Purpose:** Centralize all word lists and action families

**Extract from:**
- P24 INC_VERBS, DEC_VERBS, BUDGET_CONTEXT, NEG_WORDS → foundation
- P21 _SUPPORT, _CHALLENGE regexes
- P23 _SUPPORT_VERBS, _NEG_TOKENS, _STOP
- extract_facts PRED_INCREASE, PRED_DECREASE, NEGATORS, SCOPE_WORDS

**New additions:**
- Scientific domain vocabularies (temperature, pressure, physics phenomena)
- Paraphrase families (verb ↔ noun mappings)
- Domain-specific synonym lists

**API:**
```python
# Action families
INC_VERBS: Set[str]
DEC_VERBS: Set[str]
ACTION_SYNONYMS: Dict[str, Set[str]]  # "boil" → {"boils", "boiling", "boiling point"}

# Stance/meta verbs
SUPPORT_VERBS: Set[str]
CHALLENGE_VERBS: Set[str]

# Negation
NEGATION_WORDS: Set[str]
NEGATION_PATTERN: re.Pattern

# Stop words
STOP_WORDS: Set[str]

# Domain contexts
BUDGET_CONTEXT: Set[str]
SCIENTIFIC_CONTEXT: Set[str]

# Helper functions
def is_action_verb(word: str) -> Optional[str]:  # Returns "increase"/"decrease"/None
def expand_synonyms(word: str) -> Set[str]:
def is_negation(text: str) -> bool:
```

#### 2. `intelligence/content/shared/units.py`
**Purpose:** Unit detection, normalization, and comparison

**Extract from:**
- P21 `_percent_hits()` tolerance logic → **GOLD STANDARD**
- P24 `_quantity_compatible()` → simpler version
- extract_facts `percent_forms()` → word variants

**New additions:**
- Temperature conversion (°C ↔ °F ↔ K)
- Distance conversion (km ↔ miles ↔ meters)
- Money normalization
- Generic numeric extraction and parsing

**API:**
```python
# Extraction
def extract_temperature(text: str) -> List[Tuple[float, str]]:  # [(100.0, "celsius")]
def extract_percentage(text: str) -> List[float]:
def extract_currency(text: str) -> List[Tuple[float, str]]:  # [(1000000, "USD")]

# Normalization
def normalize_temperature(value: float, unit: str) -> float:  # To Celsius
def normalize_distance(value: float, unit: str) -> float:  # To meters

# Comparison (with tolerance)
def values_match(
    claim_value: float,
    evidence_value: float,
    tolerance_abs: float,
    tolerance_rel: float
) -> Tuple[bool, str]:  # (match, reason)

# Percentage comparison (from P21)
def percent_match(claim: str, text: str) -> Tuple[bool, bool]:
```

#### 3. `intelligence/content/shared/entities.py`
**Purpose:** Entity extraction and matching

**Extract from:**
- extract_facts `claim_entities()` → capitalization logic
- P24 `_entities_from_claim_tokens()` → domain filtering
- P21 `_entity_overlap()` → overlap percentage

**New additions:**
- Entity type classification
- Entity normalization (CA → California)
- Entity identity checking

**API:**
```python
def extract_entities(text: str, domain: Optional[str] = None) -> List[str]:
def entity_overlap_score(claim_entities: List[str], text_entities: List[str]) -> float:
def normalize_entity(entity: str) -> str:  # CA → California
def entities_match(e1: str, e2: str) -> bool:  # Identity check
```

#### 4. `intelligence/content/shared/frames.py`
**Purpose:** Frame structures and reasoning

**Extract from:**
- P24 `extract_claim_frame()`, `extract_window_frame()` → **FOUNDATION**
- P24 `_entail_contradict()` → reasoning logic
- extract_facts `extract_fact_view()` → simpler structure

**New additions:**
- Scientific domain frames
- Multi-domain frame adapters
- Condition-aware reasoning

**API:**
```python
# Frame structures
@dataclass
class Frame:
    entity: List[str]
    action: str
    quantity: List[float]
    year: List[int]
    scope: str
    condition: Optional[str] = None  # NEW
    domain: str = "unknown"  # NEW

# Extraction
def extract_frame(text: str, domain: str = "auto") -> Frame:

# Comparison
def compare_frames(claim: Frame, evidence: Frame) -> Tuple[str, List[str]]:
    # Returns: ("entail"/"contradict"/"mixed"/"unrelated", rules)

# Slot matching
def slot_coverage(claim: Frame, evidence: Frame) -> float:
```

#### 5. `intelligence/content/shared/conditions.py`
**Purpose:** Condition extraction and equivalence (NEW - mostly gaps)

**Extract from:**
- P24 BUDGET_CONTEXT → scope logic (partial)

**New additions:**
- Pressure conditions (sea level, altitude, atm)
- Temporal conditions (FY, time periods)
- Location conditions
- Condition equivalence mappings

**API:**
```python
@dataclass
class Condition:
    type: str  # "pressure", "time", "location"
    value: str
    normalized: str  # "sea level" → "1 atm"

def extract_conditions(text: str) -> List[Condition]:
def conditions_compatible(c1: Condition, c2: Condition) -> str:
    # Returns: "equivalent", "compatible", "incompatible"
```

#### 6. `intelligence/content/shared/text_utils.py`
**Purpose:** Common text processing utilities

**Extract from:**
- All modules have similar `_norm()`, `_tokens()`, `_trigrams()`, `_jaccard()` functions
- **Consolidate to avoid duplication**

**API:**
```python
def normalize_text(text: str) -> str:
def tokenize(text: str, remove_stop: bool = False) -> List[str]:
def trigrams(tokens: List[str]) -> List[Tuple[str, str, str]]:
def jaccard_similarity(a: List[Tuple], b: List[Tuple]) -> float:
def split_sentences(text: str, min_length: int = 40) -> List[str]:
def sliding_windows(sentences: List[str], window_size: int) -> List[List[str]]:
```

---

## Module-Specific Needs (After Shared Utilities)

### P20 (grade.py) Enhancement Needs:
**Current:** Keyword-based stance detection
**Needs:**
1. ✅ Import from `shared/vocabulary` (action families, negation)
2. ✅ Import from `shared/units` (numeric tolerance, temperature)
3. ✅ Import from `shared/conditions` (pressure, altitude)
4. ✅ Import from `shared/frames` (frame-based reasoning)
5. **NEW:** Frame-based decision tree (phenomenon → numeric → directional)
6. **NEW:** Domain-aware adapters (scientific vs policy)

**Integration points:**
- Replace `_stance_for_window()` with frame-based logic
- Add condition awareness for scientific claims
- Use unit normalization for numeric comparison

### P21 (fullread.py) Enhancement Needs:
**Current:** Signal-based scoring with good tolerance logic
**Needs:**
1. ✅ Export `_percent_hits()` to `shared/units` (GOLD STANDARD)
2. ✅ Import from `shared/vocabulary` (meta-stance verbs)
3. ✅ Import from `shared/text_utils` (consolidate utils)
4. **Enhance:** Add paraphrase matching to trigram similarity
5. **Enhance:** Add condition awareness

**Integration points:**
- Keep scoring system (works well)
- Add paraphrase expansion before trigram matching
- Add condition extraction to signals

### P23 (semantic_read.py) Enhancement Needs:
**Current:** Token-based matching with window sliding
**Needs:**
1. ✅ Import from `shared/vocabulary` (stance verbs, negation)
2. ✅ Import from `shared/text_utils` (consolidate utils)
3. ✅ Import from `shared/entities` (better entity extraction)
4. **Enhance:** Add paraphrase matching
5. **Enhance:** Add unit normalization for numbers

**Integration points:**
- Keep window sliding and scoring system
- Enhance entity matching with shared utilities
- Add paraphrase expansion to similarity

### P24 (semantic_frames.py) Enhancement Needs:
**Current:** Best semantic logic - frame-based reasoning
**Needs:**
1. ✅ Export frames to `shared/frames` (FOUNDATION)
2. ✅ Export action detection to `shared/vocabulary`
3. ✅ Export quantity tolerance to `shared/units` (merge with P21)
4. **Enhance:** Add scientific domain frames
5. **Enhance:** Add condition-aware entailment
6. **Fix:** Action alignment bug (lines 189-190) - doesn't compare claim action

**Integration points:**
- Frame structure → foundation for all modules
- Extend to multi-domain (not just budget/policy)
- Fix action alignment logic

### P27 (consensus/dual_lane.py) Enhancement Needs:
**Current:** Fixed bonus/penalty adjustments
**Needs:**
1. **Restore:** Variable bonus formula from wrapper: `min(0.20, 0.10 + 0.50 * abs(c1 - c2))`
2. **Restore:** Variable penalty formula from wrapper: `min(0.30, 0.15 + 0.50 * abs(c1 - c2))`
3. **Change:** Use average confidence instead of max: `(c1 + c2) / 2.0`

**Integration points:**
- No integration with semantic modules
- Pure orchestration logic
- Used by P26 (run.py:152-156)

**Priority:** MEDIUM (1-2 days)

### P28 (planning/diversify.py) Enhancement Needs:
**Current:** Single env var per provider, basic shuffling
**Needs:**
1. **Enhance:** Multi-env-var provider detection (BING_API_KEY | BING_SUBSCRIPTION_KEY | AZURE_BING_KEY)
2. **Enhance:** Arm name mapping ("A_SUPPORT" → "A", "ARM_A" → "A")
3. **Consider:** Align seed generation with wrapper if shuffle compatibility needed

**Integration points:**
- No integration with semantic modules
- Pure configuration logic
- Used by P26 (run.py:33-35)

**Priority:** LOW (0.5-1 day, optional)

### P29 (telemetry/collect.py) Enhancement Needs:
**Current:** Basic telemetry and manifest
**Needs:**
1. **Add:** `providers_available` field to manifest (environment snapshot)
2. **Add:** `knobs` configuration per lane:
   - `query_shuffle` (bool)
   - `timeout_jitter_ms` (int)
   - `max_per_provider` (int)
3. **Add:** `diversified` flag (top-level indicator)
4. **Add:** `parity.providers_equal` (R1 vs R2 provider equality check)
5. **Consider:** Auto-telemetry via ContextVar (vs manual record_provider_call())

**Integration points:**
- No integration with semantic modules
- Pure tracking/telemetry logic
- Used by P26 (run.py:38-45, 160-165)

**Priority:** MEDIUM (1-2 days)

---

## Dependencies Identified

### Cross-Module Dependencies:
```
P20 depends on:
  - shared/vocabulary (action families)
  - shared/units (temperature, tolerance)
  - shared/conditions (pressure, altitude)
  - shared/frames (frame-based reasoning)

P21 depends on:
  - shared/vocabulary (meta-stance verbs)
  - shared/text_utils (consolidate utils)

P23 depends on:
  - shared/vocabulary (stance verbs, negation)
  - shared/entities (better extraction)
  - shared/text_utils (consolidate utils)

P24 depends on:
  - shared/units (merge tolerance logic with P21)
  - shared/text_utils (consolidate utils)

P27 depends on:
  - Nothing (pure math/orchestration logic)

P28 depends on:
  - Nothing (pure configuration logic)

P29 depends on:
  - Nothing (pure telemetry/tracking logic)

All content modules (P20-P24) depend on:
  - shared/text_utils (common functions)

Orchestration modules (P27-P29) are independent:
  - No semantic logic dependencies
  - No shared utilities needed
```

### Shared Utility Dependencies:
```
shared/frames depends on:
  - shared/vocabulary (action detection)
  - shared/entities (entity extraction)
  - shared/units (quantity comparison)
  - shared/conditions (condition matching)

shared/units depends on:
  - Nothing (standalone)

shared/vocabulary depends on:
  - Nothing (standalone)

shared/entities depends on:
  - shared/vocabulary (domain filtering)

shared/conditions depends on:
  - Nothing (standalone)
```

---

## Implementation Recommendations

### Phase 2A: Extract & Centralize Existing Logic (Week 1: Days 1-2)

**Priority 1: Create shared utilities from existing code**

1. **Day 1 Morning**: `shared/text_utils.py`
   - Consolidate `_norm()`, `_tokens()`, `_trigrams()`, `_jaccard()` from all modules
   - Single source of truth for text processing
   - **Impact:** Eliminates duplication across 4+ modules

2. **Day 1 Afternoon**: `shared/vocabulary.py`
   - Merge P24 INC_VERBS/DEC_VERBS + extract_facts PRED_*
   - Merge negation words from all modules (use P21 regex as base)
   - Add P21/P23 meta-stance verbs
   - **Impact:** Consistent action/stance detection

3. **Day 2 Morning**: `shared/units.py`
   - Extract P21 `_percent_hits()` as foundation (GOLD STANDARD)
   - Merge P24 `_quantity_compatible()` logic
   - Add extract_facts `percent_forms()` word variants
   - **Impact:** Robust numeric comparison for all modules

4. **Day 2 Afternoon**: `shared/entities.py`
   - Extract extract_facts `claim_entities()` capitalization logic
   - Add P24 domain filtering
   - Add P21 overlap scoring
   - **Impact:** Better entity matching

### Phase 2B: Build Missing Components (Week 1: Days 3-5)

**Priority 2: Fill gaps that don't exist anywhere**

5. **Day 3**: `shared/conditions.py` (NEW)
   - Pressure condition patterns (sea level, altitude, atm)
   - Temporal condition patterns (FY, time periods)
   - Location condition patterns
   - Condition equivalence mappings
   - **Impact:** Enables scientific claim handling

6. **Day 4**: `shared/frames.py` (from P24)
   - Extract P24 frame structure as foundation
   - Add Frame dataclass with condition field
   - Add multi-domain support (scientific + policy)
   - Preserve P24 entailment logic
   - **Impact:** Foundation for frame-based reasoning

7. **Day 5**: Enhance `shared/vocabulary.py` (paraphrases)
   - Add scientific domain vocabularies
   - Add verb ↔ noun mappings (boil → boiling point)
   - Add synonym families
   - **Impact:** Semantic matching beyond keywords

### Phase 2C: Module Integration (Week 2: Days 1-5)

**Priority 3: Update modules to use shared utilities**

8. **Day 1**: Update P24 (easiest - most logic already good)
   - Import from shared modules
   - Fix action alignment bug (compare claim vs evidence action)
   - Add condition awareness to entailment
   - **Validation:** P24 tests still pass + improvements

9. **Day 2**: Update P23 (medium difficulty)
   - Replace local utilities with shared imports
   - Add paraphrase matching
   - Add unit normalization
   - **Validation:** P23 tests still pass + semantic improvements

10. **Day 3**: Update P21 (medium difficulty)
    - Replace local utilities with shared imports
    - Add paraphrase expansion before trigram matching
    - Add condition extraction to signals
    - **Validation:** P21 tests still pass + improvements

11. **Day 4-5**: Update P20 (hardest - major redesign)
    - Replace keyword stance detection with frame-based logic
    - Add phenomenon matching
    - Add numeric comparison with unit normalization
    - Add condition awareness
    - Implement decision tree (phenomenon → numeric → directional)
    - **Validation:** P20 tests pass + scientific claims work

### Phase 2D: Testing & Documentation (Week 3: Days 1-2)

12. **Day 1**: Comprehensive testing
    - Run all P20-P24 tests
    - Test cross-module consistency
    - Validate scientific claim handling (water boiling example)
    - Validate policy claim handling (budget examples)

13. **Day 2**: Documentation
    - Update docs/SEMANTIC_GAPS.md with completion status
    - Document shared utility APIs
    - Create migration guide for future enhancements
    - Update Phase 2 execution plan with actual progress

### Phase 2E: Orchestration Module Enhancements (Week 3: Days 3-5)

**Priority 4: Configuration and coordination improvements (optional)**

14. **Day 3**: Update P27 (consensus) - MEDIUM priority
    - Replace fixed bonus (+0.10) with variable: `min(0.20, 0.10 + 0.50 * abs(c1 - c2))`
    - Replace fixed penalties (-0.05/-0.10) with variable: `min(0.30, 0.15 + 0.50 * abs(c1 - c2))`
    - Change base confidence from max to average: `(c1 + c2) / 2.0`
    - **Impact:** More conservative consensus in edge cases
    - **Validation:** Consensus tests still pass + improved behavior

15. **Day 4 Morning**: Update P28 (diversification) - LOW priority
    - Add multi-env-var provider detection (BING_API_KEY | BING_SUBSCRIPTION_KEY | AZURE_BING_KEY)
    - Add arm name mapping ("A_SUPPORT" → "A")
    - **Impact:** More robust environment detection
    - **Validation:** Diversification tests still pass

16. **Day 4 Afternoon - Day 5**: Update P29 (telemetry) - MEDIUM priority
    - Add `providers_available` field to manifest (environment snapshot)
    - Add `knobs` configuration per lane (query_shuffle, timeout_jitter_ms, max_per_provider)
    - Add `diversified` flag to manifest
    - Add `parity.providers_equal` check
    - Consider auto-telemetry via ContextVar
    - **Impact:** Enhanced reproducibility and debugging
    - **Validation:** Telemetry tests still pass + richer manifest

**Note:** Phase 2E is optional and lower priority than Phase 2A-D. Orchestration enhancements improve configuration and observability but don't affect semantic analysis quality.

---

## Risk Assessment

### Low Risk (Already Exists, Just Reuse):

✅ **Text utilities consolidation** (All modules have similar functions)
- Risk: None - just moving code
- Benefit: Eliminates duplication

✅ **Action/negation vocabulary consolidation** (P24 + extract_facts)
- Risk: None - merge existing sets
- Benefit: Consistent detection

✅ **Numeric tolerance logic** (P21 is gold standard)
- Risk: None - already working
- Benefit: All modules get robust tolerance

✅ **Entity extraction** (extract_facts + P24)
- Risk: None - combine best parts
- Benefit: Better entity matching

### Medium Risk (Exists But Needs Enhancement):

⚠️ **Frame structures** (P24 has good foundation)
- Risk: Adding conditions/domains may break existing logic
- Mitigation: Preserve P24 API, add optional fields
- Testing: Comprehensive P24 regression tests

⚠️ **Paraphrase systems** (Partial in P24, needs expansion)
- Risk: Synonym expansion may increase false positives
- Mitigation: Start conservative, validate scientifically
- Testing: Precision/recall metrics on test set

⚠️ **Unit normalization beyond percentages** (P21 has %, need temp/distance/money)
- Risk: Conversion bugs, edge cases
- Mitigation: Unit tests for each conversion
- Testing: Known examples (212°F = 100°C, etc.)

### High Risk (Doesn't Exist, Build From Scratch):

🔴 **Condition recognition and equivalence** (Completely new)
- Risk: Complex logic, many edge cases
- Mitigation: Start with simple patterns, iterate
- Testing: Scientific claim test suite

🔴 **P20 frame-based redesign** (Major architecture change)
- Risk: May break existing functionality
- Mitigation: Feature flag, parallel comparison
- Testing: Side-by-side old vs new

🔴 **Multi-domain frame adapters** (Scientific + policy)
- Risk: Domain detection may be ambiguous
- Mitigation: Explicit domain hints when possible
- Testing: Cross-domain test cases

---

## Next Steps

### Immediate Actions:

1. **Create shared module structure:**
   ```
   intelligence/content/shared/
   ├── __init__.py
   ├── text_utils.py      (Day 1 AM)
   ├── vocabulary.py      (Day 1 PM)
   ├── units.py           (Day 2 AM)
   ├── entities.py        (Day 2 PM)
   ├── conditions.py      (Day 3)
   ├── frames.py          (Day 4)
   └── README.md          (API documentation)
   ```

2. **Start with lowest-risk extractions:**
   - text_utils (pure consolidation)
   - vocabulary (merge existing sets)
   - units (extract P21 gold standard)

3. **Build test suites for shared utilities:**
   - Each shared module gets tests/test_shared_*.py
   - Validate before integrating into modules

4. **Update Phase 2 execution plan:**
   - Incorporate reuse strategy
   - Adjust timeline based on shared utilities
   - Document dependencies

### Success Criteria

**Completion Definition:**
- ✅ All shared utilities created and tested
- ✅ All 4 modules (P20-P24) updated to use shared code
- ✅ All existing tests still pass
- ✅ Scientific claim test suite passes (water boiling example)
- ✅ Policy claim test suite passes (budget examples)
- ✅ No code duplication across modules
- ✅ docs/SEMANTIC_GAPS.md updated with P20-P24 → COMPLETE

**Quality Metrics:**
- Stance accuracy on test set: > 85%
- Scientific claim accuracy: > 90%
- Policy claim accuracy: > 85%
- Code reuse: > 60% (measured by shared utility usage)

---

*This inventory provides a complete map of existing semantic logic and a clear path for Phase 2 implementation. The high reuse potential (65%) means we can move faster than originally estimated!*
