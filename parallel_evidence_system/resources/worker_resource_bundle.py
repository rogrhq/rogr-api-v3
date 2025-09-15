"""
WorkerResourceBundle data structure with L2 validation traceability

TRACEABILITY:
- COMPLETE_COMPONENT_SPECIFICATIONS.md lines 378-442: Full specification
- COMPLETE_COMPONENT_SPECIFICATIONS.md lines 388-406: Field definitions
- COMPLETE_COMPONENT_SPECIFICATIONS.md line 401: evidence_validator field corrected to EvidenceRelevanceValidator
"""

from typing import Any
from dataclasses import dataclass  # COMPLETE_COMPONENT_SPECIFICATIONS.md line 385


@dataclass
class WorkerResourceBundle:
    """
    Thread-isolated resource bundle for parallel evidence workers.

    TRACEABILITY: COMPLETE_COMPONENT_SPECIFICATIONS.md lines 388-406
    Updated to align with authoritative ES component specifications.
    """

    # Core Evidence Processing Services - COMPLETE_COMPONENT_SPECIFICATIONS.md lines 395-402
    web_search: 'WebSearchService'
    """Thread-local web search service with isolated HTTP session"""

    content_extractor: 'WebContentExtractor'
    """Thread-local content extractor with isolated HTTP session"""

    evidence_validator: 'EvidenceRelevanceValidator'
    """Thread-local evidence relevance validator per ES_ACI_PLAN.md specification"""
    # TRACEABILITY: COMPLETE_COMPONENT_SPECIFICATIONS.md line 401 - corrected from EvidenceScorer

    # Resource Management - COMPLETE_COMPONENT_SPECIFICATIONS.md lines 405-406
    rate_limiter: Any
    """API rate limiter for managing request throttling across services"""