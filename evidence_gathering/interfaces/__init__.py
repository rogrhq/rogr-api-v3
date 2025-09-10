"""
Interfaces Module - Clean Integration Points

Provides stable interfaces for existing systems to interact with 
the Enhanced Evidence Gathering system without breaking changes.

Interface Design Principles:
- Backward compatible with existing Evidence Shepherd integration
- Version-controlled interface evolution
- Clean separation between implementation and integration
- Feature flag support for A/B testing
"""

from .search_strategy_interface import SearchStrategyInterface

__all__ = ['SearchStrategyInterface']