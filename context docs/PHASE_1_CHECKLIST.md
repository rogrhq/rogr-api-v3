# Phase 1 Implementation Checklist

## IMMEDIATE NEXT SESSION ACTIONS

### Step 1: Legacy System Preservation (20 minutes)
```bash
# Create legacy directory
mkdir legacy_evidence_system

# Move all shepherd files (EXACT COMMANDS):
git mv rogr_evidence_shepherd.py legacy_evidence_system/
git mv dual_ai_evidence_shepherd.py legacy_evidence_system/
git mv claude_evidence_shepherd.py legacy_evidence_system/
git mv rogr_dual_evidence_shepherd.py legacy_evidence_system/
git mv ai_evidence_shepherd.py legacy_evidence_system/
git mv evidence_shepherd_v2.py legacy_evidence_system/
git mv rogr_evidence_shepherd_original.py legacy_evidence_system/
git mv multi_ai_evidence_shepherd.py legacy_evidence_system/
git mv multi_ai_evidence_shepherd_v2.py legacy_evidence_system/
git mv test_evidence_shepherd_v2.py legacy_evidence_system/
git mv evidence_quality_assessor.py legacy_evidence_system/
git mv evidence_shepherd.py legacy_evidence_system/

# Update main.py imports (find and replace):
# FROM: from rogr_dual_evidence_shepherd import ROGRDualEvidenceShepherd
# TO: from legacy_evidence_system.rogr_dual_evidence_shepherd import ROGRDualEvidenceShepherd

# Test legacy system works:
curl -X POST "BACKEND_URL/analyses" -H "Content-Type: application/json" -d '{"input": "test claim", "type": "text"}'

# Commit:
git commit -m "Phase 1: Preserve legacy evidence system - all 12 files migrated"
```

### Step 2: Parallel System Foundation (25 minutes)
```bash
# Create parallel system structure
mkdir -p parallel_evidence_system/{orchestrator,workers,resources,tests}
touch parallel_evidence_system/__init__.py
touch parallel_evidence_system/orchestrator/__init__.py
touch parallel_evidence_system/workers/__init__.py
touch parallel_evidence_system/resources/__init__.py
touch parallel_evidence_system/tests/__init__.py
```

**Then implement ThreadSafeResourcePool:**

```python
# parallel_evidence_system/resources/worker_resource_pool.py
import threading
import requests
from typing import Dict, Any
from dataclasses import dataclass

@dataclass  
class WorkerResourceBundle:
    """Isolated resource bundle for single worker thread"""
    web_search: Any
    content_extractor: Any  
    ai_scorer: Any
    session_id: str

class ThreadSafeResourcePool:
    """Thread-safe resource pool providing isolated resources per worker"""
    
    def __init__(self):
        self._local = threading.local()
        self._session_counter = 0
        self._lock = threading.Lock()
    
    def get_worker_resources(self) -> WorkerResourceBundle:
        """Get thread-local isolated resources"""
        if not hasattr(self._local, 'resources'):
            with self._lock:
                self._session_counter += 1
                session_id = f"worker_{self._session_counter}"
            
            # Create thread-local resources
            self._local.resources = WorkerResourceBundle(
                web_search=self._create_web_search_service(),
                content_extractor=self._create_content_extractor(), 
                ai_scorer=self._create_ai_scorer(),
                session_id=session_id
            )
        
        return self._local.resources
    
    def _create_web_search_service(self):
        # Create isolated WebSearchService with own session
        from web_search_service import WebSearchService
        return WebSearchService()
    
    def _create_content_extractor(self):
        # Create isolated WebContentExtractor with own session  
        from web_content_extractor import WebContentExtractor
        return WebContentExtractor()
        
    def _create_ai_scorer(self):
        # Create isolated AI scorer (placeholder for now)
        return None  # Will implement in Phase 2
```

**Test thread safety:**
```python
# parallel_evidence_system/tests/test_resource_pool.py
import threading
import time
from parallel_evidence_system.resources.worker_resource_pool import ThreadSafeResourcePool

def test_thread_isolation():
    """Test that each thread gets isolated resources"""
    pool = ThreadSafeResourcePool()
    results = {}
    
    def worker(thread_id):
        resources = pool.get_worker_resources()
        results[thread_id] = resources.session_id
        time.sleep(0.1)  # Simulate work
        # Verify resources haven't changed
        assert resources.session_id == pool.get_worker_resources().session_id
    
    # Run multiple threads
    threads = []
    for i in range(3):
        t = threading.Thread(target=worker, args=(f"thread_{i}",))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Verify each thread got different session IDs
    session_ids = list(results.values())
    assert len(set(session_ids)) == 3, "Each thread should have unique session"
    print("✅ Thread isolation test passed")

if __name__ == "__main__":
    test_thread_isolation()
```

### Step 3: Feature Flag Integration (15 minutes)
```python
# Add to main.py (near imports):
import os

class EvidenceSystemFactory:
    @staticmethod  
    def create_evidence_system(use_parallel: bool = None):
        if use_parallel is None:
            use_parallel = os.getenv('USE_PARALLEL_EVIDENCE', 'false').lower() == 'true'
            
        if use_parallel:
            # Will implement in Phase 2
            raise NotImplementedError("Parallel system not yet implemented")  
        else:
            from legacy_evidence_system.rogr_dual_evidence_shepherd import ROGRDualEvidenceShepherd
            return ROGRDualEvidenceShepherd()

# Update evidence processing endpoint to use factory:
# Find where ROGRDualEvidenceShepherd is instantiated
# Replace with: evidence_system = EvidenceSystemFactory.create_evidence_system()
```

### Step 4: Validation & Commit (10 minutes)
```bash
# Test resource pool
cd parallel_evidence_system/tests && python test_resource_pool.py

# Test legacy system still works
curl -X POST "BACKEND_URL/analyses" -H "Content-Type: application/json" -d '{"input": "test claim", "type": "text"}'

# Commit parallel foundation
git add parallel_evidence_system/
git commit -m "Phase 1: Parallel system foundation - ThreadSafeResourcePool with thread isolation"

# Final commit
git add main.py  
git commit -m "Phase 1: Feature flag integration - EvidenceSystemFactory with USE_PARALLEL_EVIDENCE"
```

## SUCCESS CRITERIA
- [ ] Legacy system functional in `legacy_evidence_system/`
- [ ] Parallel system structure created
- [ ] ThreadSafeResourcePool implemented with thread isolation test passing
- [ ] Feature flag integration working (defaults to legacy)
- [ ] All changes committed with clear messages

## ESTIMATED TIME: 70 minutes
**If session is shorter, prioritize Steps 1-2 (legacy preservation + basic resource pool)**

## UPDATE CONTEXT DOCUMENTS AT SESSION END
- Update `CURRENT_SESSION_STATE.md` with progress
- Update `NEXT_SESSION_OBJECTIVES.md` with Phase 2 priorities
- Update `IMPLEMENTATION_PROGRESS.md` completion checkboxes