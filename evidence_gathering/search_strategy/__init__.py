"""
Search Strategy Module - Phase 1 Implementation

Multi-Angle Search Intelligence with IFCN compliance:
- Methodology-first approach (no institutional bias)
- Progressive complexity implementation
- Performance safeguards and quality gates
- Auditable domain classification

Components:
- methodology_strategist: Core search strategy generation
- evidence_classifier: Domain-agnostic evidence type classification
- counter_research: Quality-based opposition research
- quality_validator: IFCN compliance and performance validation
"""

from .methodology_strategist import MethodologySearchStrategist
from .evidence_classifier import EvidenceTypeClassifier
from .counter_research import CounterEvidenceEngine
from .quality_validator import SearchQualityValidator

__all__ = [
    'MethodologySearchStrategist',
    'EvidenceTypeClassifier', 
    'CounterEvidenceEngine',
    'SearchQualityValidator'
]