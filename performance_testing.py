"""
Performance Testing Framework for EEG Phase 1 A/B Testing

Tracks and compares performance metrics between current system and EEG Phase 1:
- Query count reduction (target: 75%)
- Processing time improvement (target: 54%)
- Quality score maintenance
- IFCN compliance validation
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class PerformanceMetrics:
    """Performance metrics for a single test run"""
    test_id: str
    timestamp: float
    claim_text: str
    use_eeg_phase_1: bool
    
    # Performance metrics
    total_processing_time: float
    query_count: int
    evidence_pieces_found: int
    
    # Quality metrics
    consensus_score: Optional[float]
    disagreement_level: Optional[float]
    quality_weighted_score: Optional[float]
    individual_scores: List[tuple]
    
    # EEG specific metrics
    eeg_strategy_time: Optional[float] = None
    methodology_types_used: Optional[List[str]] = None
    ifcn_compliance_score: Optional[float] = None
    
    # Error tracking
    errors: List[str] = None

class PerformanceTestingFramework:
    """A/B testing framework for EEG Phase 1 performance comparison"""
    
    def __init__(self):
        self.test_results: List[PerformanceMetrics] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def start_test(self, claim_text: str, use_eeg_phase_1: bool) -> str:
        """Start a new performance test"""
        test_id = f"{self.session_id}_{len(self.test_results):03d}"
        
        metrics = PerformanceMetrics(
            test_id=test_id,
            timestamp=time.time(),
            claim_text=claim_text,
            use_eeg_phase_1=use_eeg_phase_1,
            total_processing_time=0.0,
            query_count=0,
            evidence_pieces_found=0,
            consensus_score=None,
            disagreement_level=None,
            quality_weighted_score=None,
            individual_scores=[],
            errors=[]
        )
        
        self.test_results.append(metrics)
        print(f"🧪 Started performance test: {test_id} (EEG: {use_eeg_phase_1})")
        return test_id
    
    def record_eeg_strategy(self, test_id: str, strategy_time: float, 
                           query_count: int, methodology_types: List[str],
                           ifcn_compliance: bool):
        """Record EEG Phase 1 strategy generation metrics"""
        metrics = self._find_test(test_id)
        if metrics:
            metrics.eeg_strategy_time = strategy_time
            metrics.query_count = query_count
            metrics.methodology_types_used = methodology_types
            metrics.ifcn_compliance_score = 1.0 if ifcn_compliance else 0.0
            print(f"📊 EEG metrics recorded for {test_id}: {query_count} queries, {strategy_time:.2f}s")
    
    def record_evidence_results(self, test_id: str, evidence_count: int,
                               consensus_score: float, disagreement_level: float,
                               quality_weighted_score: float, individual_scores: List[tuple]):
        """Record evidence gathering and consensus results"""
        metrics = self._find_test(test_id)
        if metrics:
            metrics.evidence_pieces_found = evidence_count
            metrics.consensus_score = consensus_score
            metrics.disagreement_level = disagreement_level
            metrics.quality_weighted_score = quality_weighted_score
            metrics.individual_scores = individual_scores
            print(f"🎯 Consensus metrics recorded for {test_id}: {consensus_score:.1f} score")
    
    def finish_test(self, test_id: str, total_time: float, errors: List[str] = None):
        """Finish a performance test and record total time"""
        metrics = self._find_test(test_id)
        if metrics:
            metrics.total_processing_time = total_time
            metrics.errors = errors or []
            
            print(f"✅ Test {test_id} complete: {total_time:.1f}s total")
            if errors:
                print(f"⚠️ Errors encountered: {len(errors)}")
    
    def compare_performance(self, baseline_test_id: str, eeg_test_id: str) -> Dict[str, Any]:
        """Compare performance between baseline and EEG Phase 1"""
        baseline = self._find_test(baseline_test_id)
        eeg_test = self._find_test(eeg_test_id)
        
        if not baseline or not eeg_test:
            return {"error": "Test results not found"}
        
        # Calculate improvements
        time_improvement = ((baseline.total_processing_time - eeg_test.total_processing_time) 
                           / baseline.total_processing_time) * 100
        
        query_reduction = ((baseline.query_count - eeg_test.query_count) 
                          / baseline.query_count) * 100 if baseline.query_count > 0 else 0
        
        quality_change = ((eeg_test.quality_weighted_score or 0) - (baseline.quality_weighted_score or 0))
        
        comparison = {
            "baseline_test_id": baseline_test_id,
            "eeg_test_id": eeg_test_id,
            "performance_improvements": {
                "processing_time_improvement_percent": round(time_improvement, 1),
                "query_reduction_percent": round(query_reduction, 1),
                "quality_score_change": round(quality_change, 2)
            },
            "baseline_metrics": {
                "processing_time": baseline.total_processing_time,
                "query_count": baseline.query_count,
                "quality_score": baseline.quality_weighted_score
            },
            "eeg_metrics": {
                "processing_time": eeg_test.total_processing_time,
                "query_count": eeg_test.query_count,
                "quality_score": eeg_test.quality_weighted_score,
                "eeg_strategy_time": eeg_test.eeg_strategy_time,
                "methodology_types": eeg_test.methodology_types_used,
                "ifcn_compliance": eeg_test.ifcn_compliance_score
            },
            "targets_met": {
                "time_improvement_target_54_percent": time_improvement >= 54.0,
                "query_reduction_target_75_percent": query_reduction >= 75.0,
                "quality_maintained": quality_change >= -5.0  # Allow 5 point decrease
            }
        }
        
        return comparison
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of all tests in current session"""
        baseline_tests = [t for t in self.test_results if not t.use_eeg_phase_1]
        eeg_tests = [t for t in self.test_results if t.use_eeg_phase_1]
        
        return {
            "session_id": self.session_id,
            "total_tests": len(self.test_results),
            "baseline_tests": len(baseline_tests),
            "eeg_tests": len(eeg_tests),
            "average_baseline_time": sum(t.total_processing_time for t in baseline_tests) / len(baseline_tests) if baseline_tests else 0,
            "average_eeg_time": sum(t.total_processing_time for t in eeg_tests) / len(eeg_tests) if eeg_tests else 0,
            "test_results": [asdict(t) for t in self.test_results]
        }
    
    def save_results(self, filename: Optional[str] = None):
        """Save test results to JSON file"""
        if not filename:
            filename = f"performance_test_results_{self.session_id}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.get_session_summary(), f, indent=2)
        
        print(f"💾 Test results saved to: {filename}")
    
    def _find_test(self, test_id: str) -> Optional[PerformanceMetrics]:
        """Find test by ID"""
        for test in self.test_results:
            if test.test_id == test_id:
                return test
        return None

# Global instance for use across the application
performance_tester = PerformanceTestingFramework()