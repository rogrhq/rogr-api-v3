"""
Evidence Gathering Module - Enhanced Evidence Gathering (EEG) System

This module implements the IFCN-compliant evidence gathering system with 
methodology-first search strategies, designed for scalable fact-checking operations.

Architecture:
- search_strategy/: Phase 1 - Multi-Angle Search Intelligence
- interfaces/: Clean integration points with existing systems
- tests/: Comprehensive test coverage for all components

Future Phases:
- Phase 2: Source Quality Assessment
- Phase 3: Deep Content Analysis  
- Phase 4: Evidence Triangulation
- Phase 5: Counter-Evidence Intelligence
- Phase 6: Quality Control & Ranking
"""

__version__ = "1.0.0"
__author__ = "ROGR Development Team"

from .interfaces.search_strategy_interface import SearchStrategyInterface
from .search_strategy.methodology_strategist import MethodologySearchStrategist

__all__ = [
    'SearchStrategyInterface',
    'MethodologySearchStrategist'
]