"""
WebSearchService placeholder with L2 validation traceability

TRACEABILITY:
- COMPLETE_COMPONENT_SPECIFICATIONS.md line 395: web_search field requirement
- ADR-002 line 36: WebSearchService with isolated session
- Phase 1 foundation - full implementation in Phase 2
"""

from typing import Any


class WebSearchService:
    """
    Thread-local web search service with isolated HTTP session

    TRACEABILITY: ADR-002 line 36, COMPLETE_COMPONENT_SPECIFICATIONS.md line 395
    """

    def __init__(self, session: Any):
        """
        Initialize with thread-local HTTP session

        TRACEABILITY: COMPLETE_COMPONENT_SPECIFICATIONS.md line 418 session parameter
        """
        self.session = session

    def search_web(self, query: str, max_results: int = 8):
        """
        Placeholder method for web search

        TRACEABILITY: Phase 1 foundation - implementation in Phase 2 per COMPLETE_ARCHITECTURE_PLAN.md
        """
        return []