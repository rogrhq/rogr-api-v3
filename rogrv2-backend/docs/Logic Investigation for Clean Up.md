# ROGRv2 Complete Investigation List
**Logic Flaws Analysis: SHOULD BE vs CURRENTLY DOING**

**Date:** 2025-10-14  
**Branch:** post-mp-cleanup  
**Purpose:** Map all identified logic flaws and intended design for systematic investigation

---

## Table of Contents

1. [Stage 1: Search Query Generation (P19)](#stage-1-search-query-generation-p19)
2. [Stage 2: Evidence Curation Filter (P19 - Missing/Broken)](#stage-2-evidence-curation-filter-p19---missingbroken)
3. [Stage 3: Read Stage 1 - Stance Detection & Quality Filter (P20 - Misused)](#stage-3-read-stage-1---stance-detection--quality-filter-p20---misused)
4. [Stage 4: Read Stage 2 - Full Semantic Read (P21-P24)](#stage-4-read-stage-2---full-semantic-read-p21-p24)
5. [Stage 5: Individual Evidence Grading](#stage-5-individual-evidence-grading)
6. [Stage 6: Arm Aggregation & Verdict (P25)](#stage-6-arm-aggregation--verdict-p25)
7. [Stage 7: Dual Researchers (R1 & R2)](#stage-7-dual-researchers-r1--r2)
8. [Stage 8: Consensus Building (P27)](#stage-8-consensus-building-p27)
9. [Cross-Cutting Issues](#cross-cutting-issues)
10. [Priority Order](#priority-order)

---

## STAGE 1: Search Query Generation (P19)

### SHOULD BE DOING:
- Generate targeted support queries that find confirming evidence
- Generate targeted challenge queries that find contradicting evidence
- Support queries: Focus on claim as stated (exact facts, established consensus)
- Challenge queries: Focus on exceptions, variations, contradictions, debunking
- Diversify query strategy between R1 and R2 (not just order)

### CURRENTLY DOING:
- Generates base queries from claim
- Adds counter-frame keywords (numeric_dispute, denominator_shift, timing_change, authority_conflict, methodology)
- R1 and R2 only differ by seed (query order) and provider

### Issues Identified:
- Support queries may be returning challenge articles
- Challenge queries too broad/generic
- Counter-frame templates might be weak
- Query diversification between R1/R2 only changes order, not strategy

### Need to Investigate:
- [ ] What queries are actually generated for each claim type?
- [ ] What search results do these queries return?
- [ ] Are counter-frame keywords polluting support queries?
- [ ] Do queries align with arm objectives?
- [ ] Are support queries specific enough to avoid contradictory results?
- [ ] Are challenge queries finding actual counterpoints or just related topics?

---

## STAGE 2: Evidence Curation Filter (P19 - Missing/Broken)

### SHOULD BE DOING:
- Search returns 10-20 results per arm
- Run lightweight stance detection on ALL results
- Filter: Keep only on-mission evidence
  - Arm A: Keep "support" stance only
  - Arm B: Keep "challenge" stance only
  - Discard: "unrelated" or off-mission stances
- Apply quality gate: Minimum credibility/relevance threshold
- Rank filtered results by strength/relevance
- Select top 3-5 as curated evidence packet per arm

### CURRENTLY DOING:
- Search returns results
- Assign arm based on which query found it (query source = arm assignment)
- Rank by search engine relevance score
- Select top 3 per arm
- No stance filtering
- No quality gate

### Issues Identified:
- Stance detection NOT used as filter
- Arm assignment by query source, not evidence content
- No quality gate before ranking
- "Unrelated" items not filtered out
- Wrong evidence can end up in wrong arm

### Need to Investigate:
- [ ] Is stance detection being called during P19? (Answer: No)
- [ ] What criteria currently determines top 3 selection? (Answer: Search relevance only)
- [ ] What SHOULD the curation criteria be?
  - [ ] Stance alignment with arm objective?
  - [ ] Minimum relevance threshold?
  - [ ] Source credibility check?
  - [ ] Content completeness (not just snippets)?
- [ ] Should filtering happen before or after fetching full content?
- [ ] How to handle when one arm has <3 qualifying items?

---

## STAGE 3: Read Stage 1 - Stance Detection & Quality Filter (P20 - Misused)

### SHOULD BE DOING:
- Lightweight, fast stance classification
- Used as FILTER during evidence curation (Stage 2)
- Determines: Does this evidence support, challenge, or is it unrelated?
- Based on: Claim-evidence semantic alignment, entity/fact overlap, frame compatibility
- Output: Stance label only (not a grade yet)
- Purpose: Quality gate to ensure only on-mission evidence proceeds

### CURRENTLY DOING:
- Full analysis with scoring (not lightweight)
- Happens AFTER evidence selection (too late to filter)
- Produces: stance + item_grade (0-10 scale) + finding object
- Used as grading step, not filter
- Checks: Entity match, number match, similarity, frame comparison
- Output becomes part of evidence item but doesn't affect selection

### Issues Identified:
- Happens too late (after evidence already selected)
- Scale mismatch (0-10 vs 0-1)
- Not being used as filter, just as grade
- "Unrelated" stance doesn't remove items
- Too heavy/slow to use as filter

### Need to Investigate:
- [ ] What criteria does P20 use for stance determination?
  - [ ] Frame matching?
  - [ ] Semantic similarity?
  - [ ] Entity/number overlap?
  - [ ] Paraphrase detection?
- [ ] How accurate is stance detection? (Baseline: Wikipedia WWII marked "unrelated")
- [ ] What's the distribution of stance labels? (Too many "unrelated"?)
- [ ] Should P20 be lightweight filter or full analysis?
- [ ] Can we split P20 into: P19_filter (lightweight stance) + P20_grade (full analysis)?
- [ ] What's the minimum info needed for stance classification? (Snippet vs full content?)

---

## STAGE 4: Read Stage 2 - Full Semantic Read (P21-P24)

### SHOULD BE DOING:
- Deep analysis of curated evidence (3-5 items per arm)
- Extract key statements that support/challenge claim
- Identify most relevant sections of each article
- Understand paraphrases and equivalent statements
- Extract frames (entity-action-number-context)
- Determine: HOW STRONGLY does this evidence support the arm's position?
- Build evidence profile per item:
  - Relevant excerpts/quotes
  - Strength of support/challenge
  - Source credibility
  - Coverage (which aspects of claim it addresses)
  - Context and conditions
- Output: Rich evidence profile + individual evidence grade (0-1 scale)

### CURRENTLY DOING:
- P21 (full-read): Slides windows, finds best match, produces grade_full (0-10)
- P23 (semantic): Paraphrase matching, produces item_grade (0-1, overwrites P20)
- P24 (frames): Extracts and compares frames, produces best_frame_score (0-1)
- Multiple overlapping analyses
- Multiple grades per item (item_grade, grade_full, best_frame_score)
- Unclear what each module uniquely contributes
- P23 fixes P20's scale bug by overwriting

### Issues Identified:
- Multiple modules doing overlapping work (P21, P23, P24)
- Unclear what each contributes uniquely
- P23 overwrites P20's item_grade (fixes scale bug but creates dependency)
- Three different grades - which one represents evidence strength?

### Need to Investigate:
- [ ] What does P21 (full-read) actually extract?
  - [ ] Best matching window?
  - [ ] Credibility score?
  - [ ] How does grade_full differ from item_grade?
- [ ] What does P23 (semantic) actually extract?
  - [ ] Paraphrase matches?
  - [ ] Why does it overwrite item_grade?
  - [ ] What do findings[] contain?
- [ ] What does P24 (frames) actually extract?
  - [ ] Frame compatibility?
  - [ ] How does best_frame_score relate to item_grade?
- [ ] How should these modules work together to build arm position?
- [ ] What evidence should be extracted and presented per item?
- [ ] Should these be combined into one comprehensive read module?
- [ ] What's the final evidence representation per item?

---

## STAGE 5: Individual Evidence Grading

### SHOULD BE DOING:
- Produce ONE unified grade per evidence item
- Grade represents: How strongly does this item support the arm's position?
- Consider:
  - Relevance to claim
  - Strength of statements (definitive vs hedged)
  - Source authority (.gov, .edu, peer-reviewed vs blog, social media)
  - Coverage (full article vs snippet)
  - Directness (explicitly states vs implied)
  - Context alignment (conditions match claim)
- Scale: 0.0 to 1.0 (normalized)
- Output: Single evidence_strength score

### CURRENTLY DOING:
- Multiple grades per item:
  - P20: item_grade (0-10 scale) ❌
  - P21: grade_full (0-10 scale)
  - P23: item_grade (0-1 scale, overwrites P20) ✅
  - P24: best_frame_score (0-1 scale) ✅
- P25 uses: 0.55 * best_frame_score + 0.45 * item_grade
- Unclear which grade represents "evidence strength"
- Scale inconsistency causes bugs

### Issues Identified:
- Scale mismatch (P20: 0-10, P25 expects: 0-1)
- Multiple grades per item (item_grade, grade_full, best_frame_score)
- Unclear which grade represents "strength of evidence"
- P23 dependency to fix P20 bug

### Need to Investigate:
- [ ] What does item_grade represent? (Quality? Relevance? Strength?)
- [ ] What does grade_full represent?
- [ ] What does best_frame_score represent?
- [ ] How are these combined in P25?
- [ ] What SHOULD evidence grade represent?
  - [ ] How well it supports arm's position?
  - [ ] Quality of source?
  - [ ] Relevance to claim?
  - [ ] All of the above?
- [ ] Should there be ONE unified grade or multiple dimensions?
- [ ] What factors should contribute to evidence grade?
- [ ] How should source authority be weighted?

---

## STAGE 6: Arm Aggregation & Verdict (P25)

### SHOULD BE DOING:
- Aggregate 3-5 evidence items per arm into arm strength
- Consider multiple factors:
  - **Quantity**: How many pieces of evidence? (More = stronger case)
  - **Quality**: Average evidence grade (Higher = stronger case)
  - **Total strength**: Sum of evidence grades (Cumulative support)
  - **Source authority**: Weight .gov/.edu/peer-reviewed higher
  - **Source diversity**: Different domains = more robust (vs same source repeated)
  - **Internal consistency**: Do all items agree? (Conflicting evidence weakens arm)
  - **Coverage breadth**: Do items cover different aspects or repeat same point?
  - **Diminishing returns**: Additional evidence adds less value
- Compare Arm A vs Arm B across all factors
- Determine verdict:
  - If A significantly stronger → "supports"
  - If B significantly stronger → "challenges"
  - If close/balanced → "mixed"
  - If both weak → "insufficient"
- Calculate confidence based on:
  - Strength gap between arms (larger gap = higher confidence)
  - Quality of stronger arm (better evidence = higher confidence)
  - Quantity of evidence (more items = higher confidence)
  - Source authority (authoritative sources = higher confidence)
  - Internal consistency (agreement = higher confidence)

### CURRENTLY DOING:
- Arm strength: Top 4 items with diminishing returns [1.0, 0.7, 0.5, 0.35]
- Formula: strength = 0.55 * best_frame + 0.45 * item_grade (per item)
- Confidence: 0.4 * total + 0.4 * balance + 0.2 * count
- Verdict: Simple threshold (A-B > 0.15 → supports)
- Considers: Item grades, count, balance
- Missing: Source authority, source diversity, internal consistency, coverage breadth

### Issues Identified:
- Missing source authority weighting
- Missing source diversity consideration
- Missing internal consistency checks
- Missing coverage breadth analysis
- Simple threshold logic (A-B > 0.15 → supports)
- Doesn't account for conflicting evidence within arm

### Need to Investigate:
- [ ] How is arm_strength currently calculated?
  - [ ] Formula: Diminishing returns on top 4 items
  - [ ] Does it account for source authority? (No)
  - [ ] Does it account for source diversity? (No)
  - [ ] Does it account for internal consistency? (No)
- [ ] How is confidence currently calculated?
  - [ ] Formula: 0.4*total + 0.4*balance + 0.2*count
  - [ ] Why these weights?
  - [ ] What's missing?
- [ ] How is verdict label determined?
  - [ ] Threshold: 0.15 balance
  - [ ] Why 0.15?
  - [ ] Is this appropriate?
- [ ] What SHOULD arm comparison consider?
  - [ ] Quantity of evidence
  - [ ] Quality of evidence
  - [ ] Source authority
  - [ ] Source diversity
  - [ ] Internal consistency
  - [ ] Coverage breadth
  - [ ] Conflicting evidence handling
- [ ] How to weight these factors relative to each other?
- [ ] Should threshold be dynamic based on claim type?

---

## STAGE 7: Dual Researchers (R1 & R2)

### SHOULD BE DOING:
- Provide independent analysis from different perspectives
- Reduce bias by having two separate investigations
- Increase evidence coverage by searching different sources
- Cross-check findings for robustness
- Differences could include:
  - Different search providers (diversity of sources)
  - Different query strategies (different angles)
  - Different analysis weights/thresholds (different judgment)
  - Different risk tolerance (one conservative, one aggressive)
- Goal: If both agree → high confidence; If disagree → flag for deeper review

### CURRENTLY DOING:
- R1: Brave search, seed=0, original query order
- R2: Google search, seed=42, shuffled query order
- Both use identical processing pipeline (P20-P25)
- Both use same analysis logic, thresholds, weights
- Only difference: Which search results they get
- Run sequentially (R2 waits for R1)

### Issues Identified:
- Only difference: search provider (Brave vs Google) + seed (0 vs 42)
- Not truly independent analysis
- Same processing pipeline (P20-P25)
- 37.5% disagreement rate in baseline
- No differentiation in interpretation or judgment

### Need to Investigate:
- [ ] What is the PURPOSE of two researchers?
  - [ ] Search provider diversity?
  - [ ] Bias reduction?
  - [ ] Robustness?
- [ ] Should they differ in MORE than just search?
  - [ ] Different analysis approaches?
  - [ ] Different thresholds?
  - [ ] Different weighting?
- [ ] Why 37.5% disagreement in baseline?
  - [ ] Different evidence found?
  - [ ] Same evidence, different interpretation?
  - [ ] Processing inconsistencies?
- [ ] Is disagreement good or bad?
  - [ ] Good: Shows diversity of perspectives
  - [ ] Bad: Shows unreliable/inconsistent system
- [ ] Should researchers run in parallel or sequential?
- [ ] What's the value-add of R2 vs just running R1 twice?

---

## STAGE 8: Consensus Building (P27)

### SHOULD BE DOING:
- Compare both researchers' findings comprehensively
- Review evidence quality from both sides:
  - Did R1 find stronger evidence than R2?
  - Did R2 find evidence R1 missed?
  - Which researcher's evidence is more authoritative?
  - Do they contradict or complement?
- Resolve disagreements by:
  - Examining WHY they disagree (different evidence vs different interpretation)
  - Weighing evidence quality to determine which view is more supported
  - Identifying if one researcher missed key evidence
  - Determining if disagreement indicates genuine ambiguity (→ "mixed")
- Synthesize final verdict that:
  - Reflects best evidence from both researchers
  - Accounts for evidence quality differences
  - Adjusts confidence based on agreement/disagreement
  - Explains reasoning for final decision
- Output: Final verdict with clear rationale showing how R1 + R2 findings were integrated

### CURRENTLY DOING:
- Compare verdict labels (supports/challenges/mixed)
- Compare confidence scores
- Apply simple rules:
  - If labels match → Same label + 10% confidence bonus
  - If labels differ + arm balance > 0.20 → Pick stronger side - 5%
  - If labels differ + arm balance < 0.20 → Default "mixed" - 10%
- Output: Final label, confidence, rationale (rule name + arm means)
- Does NOT compare evidence quality
- Does NOT examine why disagreement occurred
- Does NOT synthesize evidence from both sides

### Issues Identified:
- Only compares verdicts (labels + confidence)
- Doesn't compare evidence quality
- Simple rules (agree → +10%, disagree → -5% or -10%)
- No actual "discussion" of evidence differences
- Doesn't explain WHY one researcher might be right vs wrong
- Mechanical rule application, not intelligent synthesis

### Need to Investigate:
- [ ] What SHOULD consensus compare?
  - [ ] Verdicts only?
  - [ ] Evidence quality?
  - [ ] Arm strengths?
  - [ ] Individual evidence grades?
  - [ ] Source authority differences?
- [ ] How should disagreements be resolved?
  - [ ] Current: Pick stronger arm or default to "mixed"
  - [ ] Should: Compare evidence quality to determine which researcher is right?
- [ ] What does "consensus" mean?
  - [ ] Agreement on verdict?
  - [ ] Agreement on evidence interpretation?
  - [ ] Synthesized view from both perspectives?
- [ ] When should final verdict differ from both researchers?
  - [ ] When R1 and R2 both partially correct?
  - [ ] When evidence quality suggests different conclusion?
- [ ] Should consensus re-examine original evidence or just work with verdicts?
- [ ] How to explain consensus reasoning to user?

---

## CROSS-CUTTING ISSUES

### Scale & Normalization

**SHOULD BE:**
- All grades on universal 0-1 scale
- Consistent meaning: 0.0 = no support, 1.0 = perfect support
- Normalization happens at source (each module produces 0-1)
- Clear documentation of what each grade represents

**CURRENTLY:**
- P20: 0-10 scale
- P21: 0-10 scale
- P23: 0-1 scale (overwrites P20)
- P24: 0-1 scale
- P25: Expects 0-1 but gets mixed scales
- Bug: P20's 0-10 treated as 0-1 if P23 fails

**Need to Investigate:**
- [ ] All grades on same scale? (Currently: No)
- [ ] What should the universal scale be? (0-1 recommended)
- [ ] Where should normalization happen?
- [ ] How to prevent scale bugs in future?

---

### "Unrelated" Evidence

**SHOULD BE:**
- "Unrelated" items discarded during curation (Stage 2)
- Never make it to full processing
- Clear threshold for what qualifies as "unrelated"
- Rare occurrence (most search results should be relevant)

**CURRENTLY:**
- "Unrelated" items not filtered out
- Marked "unrelated" but still processed and scored
- High frequency in baseline (Wikipedia WWII marked "unrelated")
- Dilutes signal and lowers confidence

**Need to Investigate:**
- [ ] Why so many items marked "unrelated"? (Baseline: frequent)
- [ ] Should "unrelated" items be discarded or scored?
- [ ] Is "unrelated" threshold too aggressive?
- [ ] What makes something "unrelated" vs "weak support/challenge"?

---

### Evidence vs Verdict Flow

**SHOULD BE:**
- Clear pipeline: Evidence quality → Arm strength → Verdict
- Better evidence = stronger arm = higher confidence verdict
- Transparent how evidence leads to conclusion
- Verdict always traceable back to specific evidence

**CURRENTLY:**
- Evidence grades → Arm strength (formula unclear)
- Arm strength → Verdict (threshold-based)
- Confidence calculation separate from verdict
- Not always clear why verdict reached

**Need to Investigate:**
- [ ] Clear separation between evidence quality and verdict?
- [ ] Does better evidence always lead to higher confidence?
- [ ] Can weak evidence still support correct verdict?
- [ ] Is the flow transparent enough for users to understand?

---

## PRIORITY ORDER

### CRITICAL (Blocks Accuracy):
1. **Scale mismatch** (P20 0-10 vs P25 0-1) - Fix immediately
2. **Stance detection not used as filter** (P19) - Fundamental design flaw
3. **Query generation returning wrong results** - Root cause investigation

### HIGH (Limits Quality):
4. **P25 arm comparison missing factors** (authority, diversity, consistency) - Incomplete logic
5. **"Unrelated" overuse** - Filtering problem
6. **Evidence grading criteria unclear** - Multiple conflicting grades

### MEDIUM (Improves Reliability):
7. **R1/R2 purpose and differentiation** - Not truly independent
8. **Consensus logic oversimplified** - Missing evidence comparison
9. **P21-P24 module overlap/redundancy** - Architectural cleanup

---

## Next Steps

1. **Prioritize investigations** - Start with CRITICAL issues
2. **Trace actual code execution** - Understand what's really happening vs documented
3. **Examine baseline test data** - See real examples of each issue
4. **Consult SAGPT** - Validate intended design vs current implementation
5. **Develop fix strategy** - Address root causes, not symptoms

---

**Document Complete**  
**Version:** 1.0  
**Status:** Ready for systematic investigation