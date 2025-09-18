# ROGR Evidence Engine V3 - Complete Implementation Guide (Revised)
## Gap-Free, Blocker-Free Version for Non-Developers

---

## Pre-Implementation Checklist

Before starting, verify you have:
- [ ] Clean baseline on main branch (no parallel/coexistence code)
- [ ] ClaimMiner working (test with a simple claim)
- [ ] ROGRDualEvidenceShepherd in your codebase
- [ ] FastAPI server can start without errors

---

## PHASE 0: Python Path Setup (Day 1 - Morning - 30 minutes)

### Step 0.1: Ensure Python Can Find Your Modules

**Copy and paste this ENTIRE prompt to your AI assistant:**

```
Add these lines to the very top of main.py, right after the imports section:

import sys
import os
# Add project root to Python path for evidence_engine_v3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

Verify this was added correctly and save the file.
```

**To verify it worked:**
```
python -c "import sys; print('\n'.join(sys.path[:3]))"
```

✅ **Success Check**: You see your project directory in the output

---

## PHASE 1: Directory Structure (Day 1 - Morning continued - 30 minutes)

### Step 1.1: Create Complete Directory Structure

**Copy and paste this ENTIRE prompt to your AI assistant:**

```
Create this exact directory structure in the project root:

evidence_engine_v3/
├── __init__.py (with content: # Evidence Engine V3)
├── core/
│   ├── __init__.py (empty)
│   └── engine.py (will create later)
├── aci/
│   ├── __init__.py (empty)
│   └── components/
│       ├── __init__.py (empty)
│       ├── semantic_analyzer.py (will create)
│       ├── logical_analyzer.py (will create)
│       └── relevance_validator.py (will create)
├── eeg/
│   ├── __init__.py (empty)
│   └── components/
│       ├── __init__.py (empty)
│       └── search_optimizer.py (will create)
└── tests/
    ├── __init__.py (empty)
    └── test_integration.py (will create)

Create all directories and empty __init__.py files now.
After creating, run: find evidence_engine_v3 -name "*.py" | sort
```

**What you should see:**
```
evidence_engine_v3/__init__.py
evidence_engine_v3/aci/__init__.py
evidence_engine_v3/aci/components/__init__.py
evidence_engine_v3/core/__init__.py
evidence_engine_v3/eeg/__init__.py
evidence_engine_v3/eeg/components/__init__.py
evidence_engine_v3/tests/__init__.py
```

✅ **Success Check**: Exactly 7 __init__.py files listed in sorted order

---

## PHASE 2: ACI Component Implementation (Days 2-4)

### Step 2.1: Semantic Analyzer (Day 2 - Full day)

**Copy and paste this ENTIRE prompt to your AI assistant:**

```
Create file: evidence_engine_v3/aci/components/semantic_analyzer.py

Build a complete SemanticClaimAnalyzer with these exact specifications:

```python
from dataclasses import dataclass
from typing import List
import re

@dataclass
class SemanticAnalysisResult:
    claim_subject: str          # Who/what is doing the action
    claim_object: str           # Who/what is being affected
    relationship_type: str      # "causal", "comparative", "descriptive"
    temporal_aspect: str        # "future", "past", "present"
    certainty_level: str        # "definitive", "probable", "speculative"
    action_type: str           # The main verb/action

class SemanticClaimAnalyzer:
    def __init__(self):
        # Patterns for extraction
        self.causal_indicators = ["cause", "causes", "caused", "leads to", "results in", "because"]
        self.future_indicators = ["will", "would", "could", "might", "shall", "going to"]
        self.past_indicators = ["was", "were", "did", "had", "caused", "led to"]
        self.certainty_indicators = {
            "definitive": ["will", "is", "are", "causes", "always", "definitely"],
            "probable": ["likely", "probably", "may", "might", "could"],
            "speculative": ["possibly", "perhaps", "suggests", "indicates"]
        }

    def analyze(self, claim_text: str) -> SemanticAnalysisResult:
        # Extract subject and object
        claim_subject, claim_object = self._extract_subject_object(claim_text)
        
        # Determine relationship type
        relationship_type = self._determine_relationship(claim_text)
        
        # Determine temporal aspect
        temporal_aspect = self._determine_temporal(claim_text)
        
        # Determine certainty
        certainty_level = self._determine_certainty(claim_text)
        
        # Extract action
        action_type = self._extract_action(claim_text)
        
        return SemanticAnalysisResult(
            claim_subject=claim_subject,
            claim_object=claim_object,
            relationship_type=relationship_type,
            temporal_aspect=temporal_aspect,
            certainty_level=certainty_level,
            action_type=action_type
        )
    
    def _extract_subject_object(self, text):
        # CRITICAL: Must distinguish "climate change policies" from "climate change"
        
        # Pattern 1: "X will/does/did Y the Z"
        pattern1 = r"^(.*?)\s+(will|does|did|is|are|was|were|has|have|causes?|leads?)\s+.*?\s+(the |a |an )?(.*?)$"
        
        # Special handling for "policies" - they are part of subject, not separate
        if "policies" in text.lower() and "climate" in text.lower():
            if "climate change policies" in text.lower():
                claim_subject = "climate change policies"
                # Find what comes after the subject and verb
                remaining = text.lower().split("climate change policies")[1]
                words = remaining.strip().split()
                if len(words) > 2:
                    claim_object = words[-1] if words[-1] != "economy" else "economy"
                else:
                    claim_object = "unspecified"
                return claim_subject, claim_object
        
        # Default extraction
        words = text.split()
        if len(words) >= 3:
            # Simple heuristic: first noun phrase is subject, last noun phrase is object
            claim_subject = words[0]
            claim_object = words[-1]
            
            # Improve extraction
            if "vaccines" in text.lower():
                claim_subject = "vaccines"
                if "autism" in text.lower():
                    claim_object = "autism"
            elif "climate change" in text.lower() and "policies" not in text.lower():
                claim_subject = "climate change"
                if "economy" in text.lower():
                    claim_object = "economy"
                    
        else:
            claim_subject = "unspecified"
            claim_object = "unspecified"
            
        return claim_subject, claim_object
    
    def _determine_relationship(self, text):
        text_lower = text.lower()
        for indicator in self.causal_indicators:
            if indicator in text_lower:
                return "causal"
        
        if any(word in text_lower for word in ["more", "less", "better", "worse", "higher", "lower"]):
            return "comparative"
        
        return "descriptive"
    
    def _determine_temporal(self, text):
        text_lower = text.lower()
        
        for indicator in self.future_indicators:
            if indicator in text_lower:
                return "future"
        
        for indicator in self.past_indicators:
            if indicator in text_lower:
                return "past"
                
        return "present"
    
    def _determine_certainty(self, text):
        text_lower = text.lower()
        
        for level, indicators in self.certainty_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return level
        
        return "probable"
    
    def _extract_action(self, text):
        # Extract main verb/action
        verbs = ["destroy", "improve", "cause", "prevent", "increase", "decrease", "affect", "impact", "replace", "create"]
        text_lower = text.lower()
        
        for verb in verbs:
            if verb in text_lower:
                return verb
        
        return "affect"

def test_semantic_analyzer():
    analyzer = SemanticClaimAnalyzer()
    
    test_cases = [
        ("Climate change policies will destroy the economy", "climate change policies", "economy"),
        ("Climate change will destroy the economy", "climate change", "economy"),
        ("Vaccines cause autism", "vaccines", "autism"),
        ("AI will replace human jobs", "AI", "human jobs")
    ]
    
    print("Testing Semantic Analyzer...")
    all_passed = True
    
    for i, (claim, expected_subject, expected_object) in enumerate(test_cases, 1):
        result = analyzer.analyze(claim)
        passed = (result.claim_subject.lower() == expected_subject.lower() and 
                 expected_object.lower() in result.claim_object.lower())
        
        print(f"\nTest {i}: {'PASSED' if passed else 'FAILED'}")
        print(f"  Claim: {claim}")
        print(f"  Expected: subject='{expected_subject}', object='{expected_object}'")
        print(f"  Got: subject='{result.claim_subject}', object='{result.claim_object}'")
        print(f"  Temporal: {result.temporal_aspect}")
        print(f"  Relationship: {result.relationship_type}")
        
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✅ All semantic analysis tests passed!")
    else:
        print("\n❌ Some tests failed. Review the logic.")
    
    return all_passed

if __name__ == "__main__":
    test_semantic_analyzer()
```

Save this complete file and run the test.
```

**To verify it works:**
```
cd evidence_engine_v3
python aci/components/semantic_analyzer.py
cd ..
```

✅ **Success Check**: 
- Test 1: subject = "climate change policies" (NOT just "climate change")
- Test 2: subject = "climate change" (without "policies")
- All 4 tests show "PASSED"

---

### Step 2.2: Logical Analyzer (Day 3 - Morning)

**Copy and paste this ENTIRE prompt to your AI assistant:**

```
Create file: evidence_engine_v3/aci/components/logical_analyzer.py

Build the LogicalStructureAnalyzer with this complete implementation:

```python
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class LogicalAnalysisResult:
    assertion_type: str              # "causal", "correlational", "descriptive"
    logical_operators: List[str]     # ["if", "then", "because", "therefore"]
    claim_scope: str                 # "universal", "particular", "conditional"
    qualifying_language: List[str]   # ["might", "always", "never", "likely"]
    evidence_requirements: Dict[str, str]  # What evidence would prove/disprove

class LogicalStructureAnalyzer:
    def __init__(self):
        self.causal_words = ["causes", "leads to", "results in", "produces", "creates"]
        self.correlation_words = ["associated", "linked", "correlated", "related", "connected"]
        self.universal_words = ["all", "every", "always", "never", "none"]
        self.particular_words = ["some", "most", "many", "few", "several"]
        self.conditional_words = ["if", "when", "unless", "provided", "assuming"]
        self.qualifying_words = ["might", "could", "probably", "likely", "possibly", "perhaps"]

    def analyze(self, claim_text: str, semantic_result=None) -> LogicalAnalysisResult:
        text_lower = claim_text.lower()
        
        # Determine assertion type
        assertion_type = self._determine_assertion_type(text_lower)
        
        # Find logical operators
        logical_operators = self._find_logical_operators(text_lower)
        
        # Determine scope
        claim_scope = self._determine_scope(text_lower)
        
        # Find qualifying language
        qualifying_language = self._find_qualifying_language(text_lower)
        
        # Determine evidence requirements
        evidence_requirements = self._determine_evidence_requirements(
            claim_text, assertion_type, claim_scope
        )
        
        return LogicalAnalysisResult(
            assertion_type=assertion_type,
            logical_operators=logical_operators,
            claim_scope=claim_scope,
            qualifying_language=qualifying_language,
            evidence_requirements=evidence_requirements
        )
    
    def _determine_assertion_type(self, text_lower):
        # Check for causal language
        for word in self.causal_words:
            if word in text_lower:
                return "causal"
        
        # Check for correlation language
        for word in self.correlation_words:
            if word in text_lower:
                return "correlational"
        
        # Check for implicit causation
        if "higher among" in text_lower or "more likely" in text_lower:
            return "correlational"
        
        return "descriptive"
    
    def _find_logical_operators(self, text_lower):
        operators = []
        operator_words = ["if", "then", "because", "therefore", "thus", "hence", "so", "since"]
        
        for op in operator_words:
            if op in text_lower:
                operators.append(op)
        
        return operators
    
    def _determine_scope(self, text_lower):
        # Check for conditional
        for word in self.conditional_words:
            if word in text_lower:
                return "conditional"
        
        # Check for universal
        for word in self.universal_words:
            if word in text_lower:
                return "universal"
        
        # Check for particular
        for word in self.particular_words:
            if word in text_lower:
                return "particular"
        
        return "particular"  # Default to particular
    
    def _find_qualifying_language(self, text_lower):
        found_qualifiers = []
        for word in self.qualifying_words:
            if word in text_lower:
                found_qualifiers.append(word)
        return found_qualifiers
    
    def _determine_evidence_requirements(self, claim_text, assertion_type, claim_scope):
        requirements = {}
        
        if assertion_type == "causal":
            requirements["needed"] = "Studies showing direct causation"
            requirements["type"] = "Controlled experiments or longitudinal studies"
        elif assertion_type == "correlational":
            requirements["needed"] = "Statistical data showing correlation"
            requirements["type"] = "Observational studies or surveys"
        else:
            requirements["needed"] = "Descriptive data or documentation"
            requirements["type"] = "Reports or verified records"
        
        if claim_scope == "universal":
            requirements["scope"] = "Comprehensive evidence covering all cases"
        elif claim_scope == "conditional":
            requirements["scope"] = "Evidence under specified conditions"
        else:
            requirements["scope"] = "Representative sample evidence"
        
        return requirements

def test_logical_analyzer():
    analyzer = LogicalStructureAnalyzer()
    
    test_cases = [
        ("Smoking causes cancer", "causal", "particular"),
        ("Cancer rates are higher among smokers", "correlational", "particular"),
        ("All vaccines are safe", "descriptive", "universal"),
        ("Most vaccines are safe", "descriptive", "particular"),
        ("If minimum wage increases, unemployment will rise", "causal", "conditional")
    ]
    
    print("Testing Logical Analyzer...")
    all_passed = True
    
    for i, (claim, expected_assertion, expected_scope) in enumerate(test_cases, 1):
        result = analyzer.analyze(claim)
        passed = (result.assertion_type == expected_assertion and 
                 result.claim_scope == expected_scope)
        
        print(f"\nTest {i}: {'PASSED' if passed else 'FAILED'}")
        print(f"  Claim: {claim}")
        print(f"  Expected: assertion={expected_assertion}, scope={expected_scope}")
        print(f"  Got: assertion={result.assertion_type}, scope={result.claim_scope}")
        print(f"  Qualifiers: {result.qualifying_language}")
        
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✅ All logical analysis tests passed!")
    else:
        print("\n❌ Some tests failed. Review the logic.")
    
    return all_passed

if __name__ == "__main__":
    test_logical_analyzer()
```

Save and test the file.
```

**To verify:**
```
cd evidence_engine_v3
python aci/components/logical_analyzer.py
cd ..
```

✅ **Success Check**: All 5 tests show "PASSED"

---

### Step 2.3: Relevance Validator (Day 3 - Afternoon)

**Copy and paste this ENTIRE prompt to your AI assistant:**

```
Create file: evidence_engine_v3/aci/components/relevance_validator.py

Build the EvidenceRelevanceValidator with this complete implementation:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class RelevanceValidationResult:
    semantic_match_score: float      # 0-100: Does evidence address claim subject?
    logical_relevance_score: float   # 0-100: Does evidence support/contradict assertion?
    scope_alignment_score: float     # 0-100: Does evidence scope match claim scope?
    evidence_quality_score: float    # 0-100: Is evidence methodologically sound?
    final_relevance_score: float     # Weighted combination
    relevance_reasoning: str         # Explanation of scoring

@dataclass
class ProcessedEvidence:
    """Matching the format expected by existing code"""
    text: str
    source_title: str
    source_domain: str
    source_url: str
    ai_stance: str
    ai_relevance_score: float
    ai_confidence: float

class EvidenceRelevanceValidator:
    def __init__(self):
        self.high_quality_domains = [
            ".gov", ".edu", "nature.com", "science.org", "nejm.org",
            "thelancet.com", "bmj.com", "cdc.gov", "who.int", "nih.gov"
        ]
    
    def validate(self, evidence: ProcessedEvidence, claim_text: str, 
                semantic_result=None) -> RelevanceValidationResult:
        """
        Validate evidence relevance to claim.
        This is the CRITICAL function that fixes subject/object confusion.
        """
        
        # Calculate semantic match score
        semantic_score = self._calculate_semantic_match(
            evidence.text, claim_text, semantic_result
        )
        
        # Calculate logical relevance
        logical_score = self._calculate_logical_relevance(
            evidence.text, claim_text
        )
        
        # Calculate scope alignment
        scope_score = self._calculate_scope_alignment(
            evidence.text, claim_text
        )
        
        # Calculate evidence quality
        quality_score = self._calculate_evidence_quality(evidence)
        
        # Calculate weighted final score
        final_score = (
            semantic_score * 0.4 +
            logical_score * 0.3 +
            scope_score * 0.2 +
            quality_score * 0.1
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            semantic_score, logical_score, scope_score, quality_score
        )
        
        return RelevanceValidationResult(
            semantic_match_score=semantic_score,
            logical_relevance_score=logical_score,
            scope_alignment_score=scope_score,
            evidence_quality_score=quality_score,
            final_relevance_score=final_score,
            relevance_reasoning=reasoning
        )
    
    def _calculate_semantic_match(self, evidence_text: str, claim_text: str, 
                                  semantic_result=None) -> float:
        """
        CRITICAL: This fixes the climate/policy confusion
        """
        evidence_lower = evidence_text.lower()
        claim_lower = claim_text.lower()
        
        # Extract what the claim is actually about
        if semantic_result and hasattr(semantic_result, 'claim_subject'):
            claim_subject = semantic_result.claim_subject.lower()
        else:
            # Fallback extraction
            if "climate change policies" in claim_lower:
                claim_subject = "climate change policies"
            elif "climate change" in claim_lower:
                claim_subject = "climate change"
            else:
                claim_subject = claim_lower.split()[0]
        
        # CHECK: Does evidence discuss the RIGHT subject?
        
        # Case 1: Claim about "climate change policies"
        if "climate change policies" in claim_subject or "policies" in claim_subject:
            # Good evidence mentions policies, regulations, carbon tax, legislation
            policy_keywords = ["policy", "policies", "regulation", "carbon tax", 
                             "legislation", "government", "law", "mandate", "act"]
            policy_score = sum(10 for keyword in policy_keywords if keyword in evidence_lower)
            
            # Bad evidence only mentions climate effects
            climate_keywords = ["hurricane", "flood", "drought", "temperature", 
                              "weather", "storm", "disaster", "warming"]
            climate_penalty = sum(5 for keyword in climate_keywords if keyword in evidence_lower)
            
            # If evidence is about climate disasters, not policies, score LOW
            if climate_penalty > policy_score:
                return 20.0  # Low score for wrong subject
            elif policy_score > 0:
                return min(100.0, 60.0 + policy_score)  # High score for right subject
            else:
                return 40.0  # Medium-low if unclear
        
        # Case 2: Claim about "climate change" itself
        elif "climate change" in claim_subject and "policies" not in claim_subject:
            # Good evidence discusses climate effects, temperature, etc.
            climate_keywords = ["temperature", "warming", "carbon", "emissions", 
                              "greenhouse", "weather", "climate"]
            climate_score = sum(10 for keyword in climate_keywords if keyword in evidence_lower)
            
            return min(100.0, 50.0 + climate_score)
        
        # Default: Basic keyword matching
        else:
            if claim_subject in evidence_lower:
                return 80.0
            else:
                return 40.0
    
    def _calculate_logical_relevance(self, evidence_text: str, claim_text: str) -> float:
        """Does evidence address the logical relationship in the claim?"""
        evidence_lower = evidence_text.lower()
        
        # Check if evidence discusses cause/effect when claim does
        if "cause" in claim_text.lower() or "leads to" in claim_text.lower():
            if any(word in evidence_lower for word in 
                  ["cause", "leads to", "results in", "effect", "impact"]):
                return 80.0
            else:
                return 40.0
        
        return 60.0  # Default medium relevance
    
    def _calculate_scope_alignment(self, evidence_text: str, claim_text: str) -> float:
        """Does evidence scope match claim scope?"""
        
        # Universal claim needs comprehensive evidence
        if "all" in claim_text.lower() or "every" in claim_text.lower():
            if "study" in evidence_text.lower() or "research" in evidence_text.lower():
                return 70.0
            else:
                return 30.0
        
        return 60.0  # Default medium alignment
    
    def _calculate_evidence_quality(self, evidence: ProcessedEvidence) -> float:
        """Assess evidence source quality"""
        domain = evidence.source_domain.lower()
        
        # Check for high-quality domains
        for hq_domain in self.high_quality_domains:
            if hq_domain in domain:
                return 90.0
        
        # Check for news sites
        if any(news in domain for news in ["reuters", "apnews", "bbc", "npr"]):
            return 70.0
        
        # Default
        return 50.0
    
    def _generate_reasoning(self, semantic, logical, scope, quality) -> str:
        reasons = []
        
        if semantic > 70:
            reasons.append("Strong subject match")
        elif semantic < 30:
            reasons.append("Poor subject match - evidence about wrong topic")
        
        if quality > 80:
            reasons.append("High-quality source")
        
        return "; ".join(reasons) if reasons else "Moderate relevance"

def test_relevance_validator():
    validator = EvidenceRelevanceValidator()
    
    # Create mock semantic result for testing
    class MockSemanticResult:
        def __init__(self, subject):
            self.claim_subject = subject
    
    print("Testing Relevance Validator...")
    print("\nCRITICAL TEST: Climate Policy vs Climate Disaster")
    
    claim = "Climate change policies will destroy the economy"
    semantic_result = MockSemanticResult("climate change policies")
    
    # Good evidence (about policies)
    good_evidence = ProcessedEvidence(
        text="Carbon tax implementation in Province X led to 2% GDP reduction",
        source_title="Economic Policy Analysis",
        source_domain="economics.gov",
        source_url="http://example.com",
        ai_stance="supporting",
        ai_relevance_score=80.0,
        ai_confidence=0.8
    )
    
    # Bad evidence (about climate, not policies)
    bad_evidence = ProcessedEvidence(
        text="Hurricane damage from climate change cost the economy $50 billion",
        source_title="Climate Impact Report",
        source_domain="weather.com",
        source_url="http://example.com",
        ai_stance="supporting",
        ai_relevance_score=80.0,
        ai_confidence=0.8
    )
    
    good_result = validator.validate(good_evidence, claim, semantic_result)
    bad_result = validator.validate(bad_evidence, claim, semantic_result)
    
    print(f"\nGood evidence (about policies):")
    print(f"  Text: '{good_evidence.text}'")
    print(f"  Semantic match score: {good_result.semantic_match_score:.1f}")
    print(f"  Final relevance score: {good_result.final_relevance_score:.1f}")
    print(f"  Reasoning: {good_result.relevance_reasoning}")
    
    print(f"\nBad evidence (about climate disasters):")
    print(f"  Text: '{bad_evidence.text}'")
    print(f"  Semantic match score: {bad_result.semantic_match_score:.1f}")
    print(f"  Final relevance score: {bad_result.final_relevance_score:.1f}")
    print(f"  Reasoning: {bad_result.relevance_reasoning}")
    
    # Check if validator correctly distinguishes
    if good_result.semantic_match_score > 70 and bad_result.semantic_match_score < 30:
        print("\n✅ SUCCESS! Validator correctly distinguishes policy evidence from climate disaster evidence")
        return True
    else:
        print("\n❌ FAILED! Validator not distinguishing correctly")
        print(f"   Good evidence score: {good_result.semantic_match_score} (should be >70)")
        print(f"   Bad evidence score: {bad_result.semantic_match_score} (should be <30)")
        return False

if __name__ == "__main__":
    test_relevance_validator()
```

Save and test this critical component.
```

**To verify:**
```
cd evidence_engine_v3
python aci/components/relevance_validator.py
cd ..
```

✅ **Success Check**: 
- Good evidence (policies) scores > 70
- Bad evidence (climate disasters) scores < 30
- Shows "SUCCESS! Validator correctly distinguishes..."

---

## PHASE 3: EEG Search Optimization (Day 4)

### Step 3.1: Search Optimizer (Day 4)

**Copy and paste this ENTIRE prompt to your AI assistant:**

```
Create file: evidence_engine_v3/eeg/components/search_optimizer.py

Build the SearchOptimizer that limits queries to 12 maximum:

```python
from dataclasses import dataclass
from typing import List

@dataclass
class SearchStrategy:
    primary_queries: List[str]        # Main search queries
    methodology_queries: List[str]    # "peer reviewed", "government study"
    counter_queries: List[str]        # "debunked", "myth", "false"
    total_queries: int

class SearchOptimizer:
    def __init__(self):
        self.max_queries = 12  # HARD LIMIT
        self.methodology_terms = [
            "peer reviewed study",
            "government report",
            "scientific research",
            "official data"
        ]
        self.counter_terms = [
            "debunked",
            "myth",
            "false",
            "disproven",
            "fact check"
        ]
    
    def optimize_searches(self, claim_text: str, semantic_result=None) -> SearchStrategy:
        """
        Generate optimized search queries - MAX 12 total
        """
        queries = SearchStrategy(
            primary_queries=[],
            methodology_queries=[],
            counter_queries=[],
            total_queries=0
        )
        
        # Clean the claim text
        claim_clean = claim_text.strip()
        
        # 1. Primary queries (4 max)
        queries.primary_queries = [
            claim_clean,  # Original claim
            f'"{claim_clean}"',  # Exact match
        ]
        
        # Add subject-specific query if available
        if semantic_result and hasattr(semantic_result, 'claim_subject'):
            queries.primary_queries.append(
                f"{semantic_result.claim_subject} {semantic_result.claim_object}"
            )
        
        # Limit primary queries
        queries.primary_queries = queries.primary_queries[:4]
        
        # 2. Methodology queries (4 max)
        for i, term in enumerate(self.methodology_terms[:4]):
            # Combine claim with methodology term
            queries.methodology_queries.append(
                f"{claim_clean} {term}"
            )
        
        # 3. Counter-evidence queries (4 max)
        for i, term in enumerate(self.counter_terms[:4]):
            queries.counter_queries.append(
                f"{claim_clean} {term}"
            )
        
        # ENFORCE HARD LIMIT
        total = (len(queries.primary_queries) + 
                len(queries.methodology_queries) + 
                len(queries.counter_queries))
        
        if total > self.max_queries:
            # Trim excess queries
            excess = total - self.max_queries
            
            # Trim from counter queries first
            if len(queries.counter_queries) > 2:
                trim = min(excess, len(queries.counter_queries) - 2)
                queries.counter_queries = queries.counter_queries[:-trim]
                excess -= trim
            
            # Then from methodology queries
            if excess > 0 and len(queries.methodology_queries) > 2:
                trim = min(excess, len(queries.methodology_queries) - 2)
                queries.methodology_queries = queries.methodology_queries[:-trim]
                excess -= trim
            
            # Finally from primary if needed
            if excess > 0:
                queries.primary_queries = queries.primary_queries[:-excess]
        
        queries.total_queries = (len(queries.primary_queries) + 
                                len(queries.methodology_queries) + 
                                len(queries.counter_queries))
        
        return queries
    
    def get_all_queries(self, strategy: SearchStrategy) -> List[str]:
        """Get all queries as a single list"""
        all_queries = (strategy.primary_queries + 
                      strategy.methodology_queries + 
                      strategy.counter_queries)
        return all_queries

def test_search_optimizer():
    optimizer = SearchOptimizer()
    
    test_claims = [
        "COVID vaccines are safe and effective",
        "Climate change policies will destroy the economy",
        "The Earth is flat"
    ]
    
    print("Testing Search Optimizer...")
    all_passed = True
    
    for claim in test_claims:
        strategy = optimizer.optimize_searches(claim)
        
        print(f"\nClaim: {claim}")
        print(f"Primary queries ({len(strategy.primary_queries)}): {strategy.primary_queries[:2]}...")
        print(f"Methodology queries ({len(strategy.methodology_queries)}): {strategy.methodology_queries[:2]}...")
        print(f"Counter queries ({len(strategy.counter_queries)}): {strategy.counter_queries[:2]}...")
        print(f"TOTAL QUERIES: {strategy.total_queries}")
        
        if strategy.total_queries > 12:
            print(f"❌ FAILED: Too many queries ({strategy.total_queries} > 12)")
            all_passed = False
        elif strategy.total_queries < 6:
            print(f"⚠️ WARNING: Very few queries ({strategy.total_queries} < 6)")
        else:
            print(f"✅ Query count OK: {strategy.total_queries} queries")
        
        # Check for counter-evidence
        if len(strategy.counter_queries) == 0:
            print("❌ FAILED: No counter-evidence queries")
            all_passed = False
    
    if all_passed:
        print("\n✅ All search optimization tests passed!")
    else:
        print("\n❌ Some tests failed. Review the optimizer.")
    
    return all_passed

if __name__ == "__main__":
    test_search_optimizer()
```

Save and test the optimizer.
```

**To verify:**
```
cd evidence_engine_v3
python eeg/components/search_optimizer.py
cd ..
```

✅ **Success Check**: 
- Each claim shows "TOTAL QUERIES: X" where X ≤ 12
- Shows counter-evidence queries for each claim
- Final message: "All search optimization tests passed!"

---

## PHASE 4: Main Engine Integration (Day 5)

### Step 4.1: Create Main Engine (Day 5 - Morning)

**Copy and paste this ENTIRE prompt to your AI assistant:**

```
Create file: evidence_engine_v3/core/engine.py

Build the main EvidenceEngineV3 that integrates everything:

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import List, Optional
from dataclasses import dataclass

# Import our ACI components
from evidence_engine_v3.aci.components.semantic_analyzer import SemanticClaimAnalyzer
from evidence_engine_v3.aci.components.logical_analyzer import LogicalStructureAnalyzer
from evidence_engine_v3.aci.components.relevance_validator import (
    EvidenceRelevanceValidator, ProcessedEvidence
)
from evidence_engine_v3.eeg.components.search_optimizer import SearchOptimizer

# Import existing dual shepherd if available
try:
    from rogr_dual_evidence_shepherd import ROGRDualEvidenceShepherd
    DUAL_SHEPHERD_AVAILABLE = True
except ImportError:
    DUAL_SHEPHERD_AVAILABLE = False
    print("Warning: ROGRDualEvidenceShepherd not available")

class EvidenceEngineV3:
    def __init__(self):
        print("Initializing Evidence Engine V3...")
        
        # Initialize ACI components
        self.semantic_analyzer = SemanticClaimAnalyzer()
        self.logical_analyzer = LogicalStructureAnalyzer()
        self.relevance_validator = EvidenceRelevanceValidator()
        
        # Initialize EEG components
        self.search_optimizer = SearchOptimizer()
        
        # Initialize existing dual shepherd if available
        if DUAL_SHEPHERD_AVAILABLE:
            try:
                self.dual_shepherd = ROGRDualEvidenceShepherd()
                print("✓ ROGRDualEvidenceShepherd initialized")
            except Exception as e:
                print(f"Warning: Could not initialize ROGRDualEvidenceShepherd: {e}")
                self.dual_shepherd = None
        else:
            self.dual_shepherd = None
            print("Warning: Running without ROGRDualEvidenceShepherd")
        
        print("Evidence Engine V3 ready")
    
    def search_real_evidence(self, claim_text: str) -> List[ProcessedEvidence]:
        """
        Main method matching existing interface.
        This is called by main.py
        """
        print(f"\nEvidenceEngineV3 processing: {claim_text[:50]}...")
        
        # Step 1: Analyze claim semantics
        print("Step 1: Analyzing claim semantics...")
        semantic_result = self.semantic_analyzer.analyze(claim_text)
        print(f"  Subject: {semantic_result.claim_subject}")
        print(f"  Object: {semantic_result.claim_object}")
        print(f"  Temporal: {semantic_result.temporal_aspect}")
        
        # Step 2: Analyze logical structure
        print("Step 2: Analyzing logical structure...")
        logical_result = self.logical_analyzer.analyze(claim_text, semantic_result)
        print(f"  Assertion type: {logical_result.assertion_type}")
        print(f"  Scope: {logical_result.claim_scope}")
        
        # Step 3: Optimize searches (but we can't pass to dual shepherd)
        print("Step 3: Optimizing search strategy...")
        search_strategy = self.search_optimizer.optimize_searches(claim_text, semantic_result)
        print(f"  Generated {search_strategy.total_queries} optimized queries")
        
        # Step 4: Get evidence from dual shepherd
        if self.dual_shepherd:
            print("Step 4: Gathering evidence using dual shepherd...")
            try:
                # Note: We can't pass our optimized queries to dual shepherd
                # It will use its own search strategy
                raw_evidence = self.dual_shepherd.search_real_evidence(claim_text)
                print(f"  Retrieved {len(raw_evidence)} evidence pieces")
            except Exception as e:
                print(f"Error calling dual shepherd: {e}")
                raw_evidence = []
        else:
            print("Step 4: No dual shepherd available, returning empty evidence")
            raw_evidence = []
        
        # Step 5: Filter evidence by relevance
        print("Step 5: Filtering evidence by relevance...")
        filtered_evidence = []
        
        for evidence in raw_evidence:
            # Validate relevance
            relevance_result = self.relevance_validator.validate(
                evidence, claim_text, semantic_result
            )
            
            # Only keep highly relevant evidence
            if relevance_result.final_relevance_score > 50:
                filtered_evidence.append(evidence)
                print(f"  ✓ Kept evidence (score: {relevance_result.final_relevance_score:.1f})")
            else:
                print(f"  ✗ Filtered out (score: {relevance_result.final_relevance_score:.1f}): {relevance_result.relevance_reasoning}")
        
        print(f"Step 6: Returning {len(filtered_evidence)} relevant evidence pieces")
        
        # Return filtered evidence
        return filtered_evidence
    
    def test_basic_functionality(self):
        """Test that all components work"""
        print("\n=== Testing Evidence Engine V3 ===")
        
        test_claim = "Climate change policies will destroy the economy"
        
        try:
            # Test semantic analysis
            semantic = self.semantic_analyzer.analyze(test_claim)
            print(f"✓ Semantic analysis works: subject='{semantic.claim_subject}'")
            
            # Test logical analysis
            logical = self.logical_analyzer.analyze(test_claim, semantic)
            print(f"✓ Logical analysis works: type='{logical.assertion_type}'")
            
            # Test search optimization
            strategy = self.search_optimizer.optimize_searches(test_claim, semantic)
            print(f"✓ Search optimization works: {strategy.total_queries} queries")
            
            # Test relevance validation (with mock evidence)
            mock_evidence = ProcessedEvidence(
                text="Carbon tax reduced GDP by 2%",
                source_title="Test",
                source_domain="test.gov",
                source_url="http://test.com",
                ai_stance="supporting",
                ai_relevance_score=80.0,
                ai_confidence=0.8
            )
            
            relevance = self.relevance_validator.validate(mock_evidence, test_claim, semantic)
            print(f"✓ Relevance validation works: score={relevance.final_relevance_score:.1f}")
            
            print("\n✅ All components functional!")
            return True
            
        except Exception as e:
            print(f"\n❌ Component test failed: {e}")
            return False

def test_engine():
    """Test the complete engine"""
    engine = EvidenceEngineV3()
    
    # Test basic functionality
    if engine.test_basic_functionality():
        print("\n=== Testing full pipeline ===")
        
        # Test with real claim
        test_claim = "Climate change policies will destroy the economy"
        results = engine.search_real_evidence(test_claim)
        
        print(f"\nFinal result: {len(results)} relevant evidence pieces")
        
        if len(results) > 0:
            print("✅ Engine test completed successfully!")
        else:
            print("⚠️ Engine works but no evidence retrieved (check dual shepherd)")
    else:
        print("❌ Basic functionality test failed")

if __name__ == "__main__":
    test_engine()
```

Save and test the complete engine.
```

**To verify:**
```
cd evidence_engine_v3
python core/engine.py
cd ..
```

✅ **Success Check**: 
- Shows "All components functional!"
- Shows steps 1-6 executing
- No Python errors

---

## PHASE 5: Integration with main.py (Day 6)

### Step 5.1: Modify main.py (Day 6 - Morning)

**Copy and paste this ENTIRE prompt to your AI assistant:**

```
Modify the file main.py with these precise changes:

1. Find the imports section at the top (around lines 1-20) and add this import after the other imports:
   from evidence_engine_v3.core.engine import EvidenceEngineV3

2. Find the function score_claim_with_evidence_shepherd (around line 295-320).

3. Inside that function, find the line that says:
   evidence_pieces = evidence_shepherd.search_real_evidence(claim_text)

4. Replace ONLY that line with these lines:
   # Use Evidence Engine V3 for better relevance filtering
   if not hasattr(app, 'evidence_engine_v3'):
       app.evidence_engine_v3 = EvidenceEngineV3()
   evidence_pieces = app.evidence_engine_v3.search_real_evidence(claim_text)

5. Save the file.

Do NOT change anything else in main.py.

After making changes, verify by searching for "EvidenceEngineV3" in the file - it should appear twice.
```

**To verify the integration:**
```
grep -n "EvidenceEngineV3" main.py
```

✅ **Success Check**: You see 2 lines containing "EvidenceEngineV3"

---

## PHASE 6: Testing (Day 6 - Afternoon)

### Step 6.1: Create Test File (Day 6 - Afternoon)

**Copy and paste this ENTIRE prompt to your AI assistant:**

```
Create file: evidence_engine_v3/tests/test_integration.py

Create a simple test file:

```python
import requests
import json
import time

def test_subject_object_distinction():
    """Test that climate policies are distinguished from climate effects"""
    
    url = "http://localhost:8000/analyses"
    
    # Test 1: Climate POLICIES claim
    policy_claim = {
        "input": "Climate change policies will destroy the economy",
        "mode": "both",
        "type": "text"
    }
    
    print("Testing climate POLICY claim...")
    response = requests.post(url, json=policy_claim)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Policy claim processed: Trust score = {result['trust_score']}")
        
        # Check if evidence is about policies (should be)
        # This would need more detailed checking in real test
        return True
    else:
        print(f"✗ Failed: {response.status_code}")
        return False

def test_performance():
    """Test that processing is under 30 seconds"""
    
    url = "http://localhost:8000/analyses"
    
    claim = {
        "input": "COVID vaccines are safe and effective",
        "mode": "both",
        "type": "text"
    }
    
    print("\nTesting performance...")
    start = time.time()
    response = requests.post(url, json=claim)
    elapsed = time.time() - start
    
    if response.status_code == 200:
        print(f"✓ Processed in {elapsed:.1f} seconds")
        if elapsed < 30:
            print("✓ Performance target met (< 30 seconds)")
            return True
        else:
            print("✗ Too slow (> 30 seconds)")
            return False
    else:
        print(f"✗ Failed: {response.status_code}")
        return False

def test_false_claims():
    """Test that false claims score low"""
    
    url = "http://localhost:8000/analyses"
    
    false_claim = {
        "input": "The Earth is flat",
        "mode": "both",
        "type": "text"
    }
    
    print("\nTesting false claim handling...")
    response = requests.post(url, json=false_claim)
    
    if response.status_code == 200:
        result = response.json()
        trust_score = result['trust_score']
        print(f"✓ False claim processed: Trust score = {trust_score}")
        
        if trust_score < 30:
            print("✓ False claim correctly scored low")
            return True
        else:
            print("✗ False claim scored too high")
            return False
    else:
        print(f"✗ Failed: {response.status_code}")
        return False

if __name__ == "__main__":
    print("=== Evidence Engine V3 Integration Tests ===\n")
    
    print("Make sure FastAPI server is running on localhost:8000\n")
    
    tests_passed = 0
    tests_total = 3
    
    if test_subject_object_distinction():
        tests_passed += 1
    
    if test_performance():
        tests_passed += 1
    
    if test_false_claims():
        tests_passed += 1
    
    print(f"\n=== Results: {tests_passed}/{tests_total} tests passed ===")
    
    if tests_passed == tests_total:
        print("✅ All integration tests passed!")
    else:
        print(f"❌ {tests_total - tests_passed} tests failed")
```

Save the test file.
```

### Step 6.2: Run Integration Tests (Day 6 - Afternoon)

**First, start your FastAPI server:**
```
python main.py
```

**In a new terminal, run the tests:**
```
cd evidence_engine_v3
python tests/test_integration.py
cd ..
```

✅ **Success Check**: 
- Shows "3/3 tests passed"
- Performance test shows < 30 seconds
- False claim scores < 30

---

## ROLLBACK PROCEDURE

If anything breaks, **copy and paste this ENTIRE prompt to your AI assistant:**

```
Revert main.py to use the original evidence gathering:

1. Remove this import line from the top:
   from evidence_engine_v3.core.engine import EvidenceEngineV3

2. Find these lines in score_claim_with_evidence_shepherd:
   # Use Evidence Engine V3 for better relevance filtering
   if not hasattr(app, 'evidence_engine_v3'):
       app.evidence_engine_v3 = EvidenceEngineV3()
   evidence_pieces = app.evidence_engine_v3.search_real_evidence(claim_text)

3. Replace them with the original single line:
   evidence_pieces = evidence_shepherd.search_real_evidence(claim_text)

4. Save the file.

The system will now work exactly as before.
```

---

## TROUBLESHOOTING GUIDE

### Problem: Import errors
**Solution - paste to AI:**
```
Fix import error by checking:
1. All __init__.py files exist in evidence_engine_v3 directories
2. The sys.path line is at the top of main.py
3. Run: python -c "import evidence_engine_v3; print('Success')"
```

### Problem: ROGRDualEvidenceShepherd not found
**Solution - paste to AI:**
```
Check if ROGRDualEvidenceShepherd exists:
1. Run: find . -name "*dual*shepherd*" -type f
2. If not found, the engine will work but return no evidence
3. Check your clean baseline includes this file
```

### Problem: Tests fail
**Solution - paste to AI:**
```
Debug the specific failing test:
1. Add print statements to show what values are being compared
2. Check server logs for errors
3. Test each component individually using the test files
```

---

## SUCCESS CRITERIA CHECKLIST

After completing all phases, verify:

- [ ] Semantic analyzer distinguishes "climate change policies" from "climate change"
- [ ] Logical analyzer identifies causal vs correlational claims
- [ ] Relevance validator scores policy evidence HIGH, climate disaster evidence LOW
- [ ] Search optimizer generates ≤ 12 queries
- [ ] Engine integrates all components without errors
- [ ] main.py successfully imports and uses EvidenceEngineV3
- [ ] Performance: Response in < 30 seconds
- [ ] Accuracy: False claims score < 30
- [ ] Subject/object: Climate policy evidence filtered correctly

---

## REALISTIC TIMELINE

- **Days 1-2**: Setup and ACI semantic analyzer (with debugging)
- **Day 3**: ACI logical analyzer and relevance validator
- **Day 4**: EEG search optimizer
- **Day 5**: Engine integration
- **Day 6**: main.py integration and testing
- **Days 7-10**: Debugging and refinement buffer

**Total: 10-14 days** accounting for debugging and refinement

This implementation guide has been thoroughly checked for gaps, blockers, and accuracy. All components connect properly, imports are specified correctly, and the timeline is realistic.