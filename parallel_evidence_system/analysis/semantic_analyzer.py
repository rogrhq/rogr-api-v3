"""
SemanticClaimAnalyzer - ES_ACI_PLAN.md lines 47-55

Semantic claim analysis component for Advanced Claim Interpretation pipeline.
Analyzes claim meaning and relationships to identify subject, object, relationship type,
temporal aspects, and certainty levels for enhanced evidence search strategy generation.
"""

from dataclasses import dataclass
from typing import Optional
import re
import anthropic


@dataclass
class SemanticAnalysisResult:
    """
    Semantic analysis result structure per ES_ACI_PLAN.md specification.
    Complete semantic breakdown of claim for enhanced evidence targeting.
    """
    claim_subject: str          # "climate change policies"
    claim_object: str           # "economy"
    relationship_type: str      # "causal", "comparative", "descriptive"
    temporal_aspect: str        # "future", "past", "present"
    certainty_level: str        # "definitive", "probable", "speculative"
    action_type: str           # "destroy", "improve", "affect"


class SemanticClaimAnalyzer:
    """
    Semantic claim analysis component per ES_ACI_PLAN.md specification.

    Analyzes claim meaning and relationships to identify subject, object,
    relationship type, temporal aspects, and certainty levels for enhanced
    evidence search strategy generation.
    """

    def __init__(self, ai_client: Optional[anthropic.Anthropic] = None):
        """
        Initialize semantic analyzer with AI client for advanced analysis.

        Args:
            ai_client: Anthropic client for semantic processing (optional)
        """
        self.ai_client = ai_client or anthropic.Anthropic()

        # Temporal indicators for analysis
        self.temporal_patterns = {
            'future': ['will', 'going to', 'shall', 'expected to', 'projected to'],
            'past': ['was', 'were', 'had', 'did', 'has been', 'have been'],
            'present': ['is', 'are', 'being', 'currently', 'now', 'today']
        }

        # Certainty level indicators
        self.certainty_patterns = {
            'definitive': ['will definitely', 'certainly', 'absolutely', 'without doubt'],
            'probable': ['likely', 'probably', 'most likely', 'expected to'],
            'speculative': ['might', 'could', 'may', 'possibly', 'potentially']
        }

        # Relationship type patterns
        self.relationship_patterns = {
            'causal': ['cause', 'leads to', 'results in', 'destroys', 'creates'],
            'comparative': ['better than', 'worse than', 'more than', 'less than'],
            'descriptive': ['is', 'are', 'has', 'contains', 'includes']
        }

    def analyze(self, claim_text: str) -> SemanticAnalysisResult:
        """
        Analyze claim semantics to extract subject/object relationships.

        Per ES_ACI_PLAN.md specification - extracts semantic components for
        enhanced evidence search strategy generation.

        Args:
            claim_text: The claim text to analyze

        Returns:
            SemanticAnalysisResult: Complete semantic analysis with all fields
        """
        # Use AI for sophisticated semantic analysis
        analysis_prompt = self._create_analysis_prompt(claim_text)

        try:
            response = self.ai_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": analysis_prompt}]
            )

            # Parse AI response into structured result
            return self._parse_analysis_response(response.content[0].text, claim_text)

        except Exception as e:
            # Fallback to rule-based analysis if AI fails
            return self._fallback_analysis(claim_text)

    def _create_analysis_prompt(self, claim_text: str) -> str:
        """Create structured prompt for AI semantic analysis."""
        return f"""Analyze this claim's semantic structure for fact-checking purposes:

CLAIM: "{claim_text}"

Extract these semantic components:

1. CLAIM SUBJECT (what is being discussed): The main entity or concept
2. CLAIM OBJECT (what is being affected): The target or outcome
3. RELATIONSHIP TYPE: causal, comparative, or descriptive
4. TEMPORAL ASPECT: future, past, or present
5. CERTAINTY LEVEL: definitive, probable, or speculative
6. ACTION TYPE: destroy, improve, affect, or other specific action

Respond in this exact format:
SUBJECT: [subject]
OBJECT: [object]
RELATIONSHIP: [relationship_type]
TEMPORAL: [temporal_aspect]
CERTAINTY: [certainty_level]
ACTION: [action_type]

Focus on the logical structure for evidence targeting, not content evaluation."""

    def _parse_analysis_response(self, response_text: str, claim_text: str) -> SemanticAnalysisResult:
        """Parse AI response into SemanticAnalysisResult structure."""

        # Extract fields using regex patterns
        subject_match = re.search(r'SUBJECT:\s*(.+)', response_text, re.IGNORECASE)
        object_match = re.search(r'OBJECT:\s*(.+)', response_text, re.IGNORECASE)
        relationship_match = re.search(r'RELATIONSHIP:\s*(.+)', response_text, re.IGNORECASE)
        temporal_match = re.search(r'TEMPORAL:\s*(.+)', response_text, re.IGNORECASE)
        certainty_match = re.search(r'CERTAINTY:\s*(.+)', response_text, re.IGNORECASE)
        action_match = re.search(r'ACTION:\s*(.+)', response_text, re.IGNORECASE)

        return SemanticAnalysisResult(
            claim_subject=subject_match.group(1).strip() if subject_match else "unknown",
            claim_object=object_match.group(1).strip() if object_match else "unknown",
            relationship_type=relationship_match.group(1).strip().lower() if relationship_match else "descriptive",
            temporal_aspect=temporal_match.group(1).strip().lower() if temporal_match else "present",
            certainty_level=certainty_match.group(1).strip().lower() if certainty_match else "speculative",
            action_type=action_match.group(1).strip().lower() if action_match else "affect"
        )

    def _fallback_analysis(self, claim_text: str) -> SemanticAnalysisResult:
        """Rule-based fallback analysis if AI processing fails."""
        claim_lower = claim_text.lower()

        # Basic temporal analysis
        temporal_aspect = "present"
        for aspect, patterns in self.temporal_patterns.items():
            if any(pattern in claim_lower for pattern in patterns):
                temporal_aspect = aspect
                break

        # Basic certainty analysis
        certainty_level = "speculative"
        for level, patterns in self.certainty_patterns.items():
            if any(pattern in claim_lower for pattern in patterns):
                certainty_level = level
                break

        # Basic relationship analysis
        relationship_type = "descriptive"
        for rel_type, patterns in self.relationship_patterns.items():
            if any(pattern in claim_lower for pattern in patterns):
                relationship_type = rel_type
                break

        # Simple subject/object extraction (basic approach)
        words = claim_text.split()
        subject = words[0] if words else "unknown"
        obj = words[-1] if len(words) > 1 else "unknown"

        return SemanticAnalysisResult(
            claim_subject=subject,
            claim_object=obj,
            relationship_type=relationship_type,
            temporal_aspect=temporal_aspect,
            certainty_level=certainty_level,
            action_type="affect"
        )