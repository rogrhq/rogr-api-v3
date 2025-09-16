# Established Code Patterns for Parallel Architecture

## **CRITICAL: These patterns MUST be followed consistently across all implementation**

---

## **1. Thread-Safe Component Pattern**
**Usage**: All parallel system components must use this base pattern
```python
import threading
from abc import ABC, abstractmethod

class ThreadSafeComponent(ABC):
    """Base class ensuring thread-safe initialization and resource management"""
    
    def __init__(self):
        self._local = threading.local()
        self._lock = threading.Lock()
        self.component_id = self._generate_component_id()
        
    def _generate_component_id(self) -> str:
        """Generate unique component identifier for logging/debugging"""
        import uuid
        return f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
        
    @abstractmethod
    def _initialize_thread_resources(self):
        """Each subclass must implement thread-local resource initialization"""
        pass
        
    def get_thread_resources(self):
        """Get or create thread-local resources"""
        if not hasattr(self._local, 'initialized'):
            with self._lock:
                if not hasattr(self._local, 'initialized'):
                    self._initialize_thread_resources()
                    self._local.initialized = True
        return self._local
```

**Example Usage:**
```python
class ThreadSafeEvidenceWorker(ThreadSafeComponent):
    def _initialize_thread_resources(self):
        self._local.session = requests.Session()
        self._local.ai_client = self._create_ai_client()
        self._local.worker_id = f"worker_{threading.current_thread().ident}"
```

---

## **2. Evidence System Factory Pattern (Phase 1.3)**
**Usage**: Feature flag integration for toggling between evidence systems
```python
class EvidenceSystemFactory:
    """Factory for creating evidence systems with feature flag support per ADR-004"""

    @staticmethod
    def create_evidence_system(use_parallel: bool = None):
        """Create evidence system based on USE_PARALLEL_EVIDENCE environment variable"""
        if use_parallel is None:
            use_parallel = os.getenv('USE_PARALLEL_EVIDENCE', 'false').lower() == 'true'

        if use_parallel:
            try:
                from parallel_evidence_system.orchestrator.parallel_evidence_orchestrator import ParallelEvidenceOrchestrator
                print("✅ Creating Parallel Evidence System")
                return ParallelEvidenceOrchestrator()
            except ImportError as e:
                print(f"❌ Parallel Evidence System not available: {e}")
                return None
        else:
            # Legacy system path with preserved functionality
            try:
                use_eeg_phase_1 = os.getenv('USE_EEG_PHASE_1', 'false').lower() == 'true'
                system = ROGRDualEvidenceShepherd(use_eeg_phase_1=use_eeg_phase_1)
                if system.is_enabled():
                    return system
                return None
            except Exception as e:
                print(f"❌ Legacy Evidence System failed: {e}")
                return None
```

**Integration Pattern in main.py:**
```python
# Feature flag integration with graceful fallback
use_parallel_evidence = os.getenv('USE_PARALLEL_EVIDENCE', 'false').lower() == 'true'

if use_parallel_evidence:
    print("🔄 USE_PARALLEL_EVIDENCE=true - attempting parallel system")
    evidence_system = EvidenceSystemFactory.create_evidence_system(use_parallel=True)
    if evidence_system is None:
        print("⚠️ Parallel system failed, falling back to legacy system")
        use_parallel_evidence = False

if not use_parallel_evidence:
    # Original legacy initialization preserved exactly
    evidence_system = EvidenceSystemFactory.create_evidence_system(use_parallel=False)
```

---

## **3. Resource Cleanup Context Manager Pattern**
**Usage**: All resource-using operations must use context managers
```python
from contextlib import contextmanager
import logging

@contextmanager
def managed_resource(resource_factory, cleanup_func):
    """Generic resource management with guaranteed cleanup"""
    resource = None
    try:
        resource = resource_factory()
        logging.info(f"Resource acquired: {type(resource).__name__}")
        yield resource
    except Exception as e:
        logging.error(f"Resource operation failed: {e}")
        raise
    finally:
        if resource:
            try:
                cleanup_func(resource)
                logging.info(f"Resource cleaned up: {type(resource).__name__}")
            except Exception as cleanup_error:
                logging.error(f"Resource cleanup failed: {cleanup_error}")

# Specific implementations:
@contextmanager
def managed_http_session():
    """HTTP session with guaranteed cleanup"""
    session = requests.Session()
    try:
        yield session
    finally:
        session.close()

@contextmanager  
def managed_ai_client():
    """AI client with connection cleanup"""
    client = anthropic.Anthropic()
    try:
        yield client
    finally:
        # AI client cleanup if needed
        pass
```

**Example Usage:**
```python
def execute_web_search(self, query: str):
    with managed_http_session() as session:
        response = session.get(f"https://api.search.com/v1/search?q={query}")
        return response.json()
```

---

## **3. Error Handling with Session Context Pattern**
**Usage**: All operations must use consistent error handling with context
```python
import logging
from typing import Optional
from dataclasses import dataclass

@dataclass
class OperationContext:
    session_id: str
    component_name: str
    operation_name: str
    claim_text: Optional[str] = None
    
class ROGRException(Exception):
    """Base exception with context tracking"""
    def __init__(self, message: str, context: OperationContext, original_error: Exception = None):
        self.message = message
        self.context = context  
        self.original_error = original_error
        super().__init__(self._format_message())
        
    def _format_message(self) -> str:
        return f"{self.context.component_name}.{self.context.operation_name}: {self.message}"

def with_error_handling(context: OperationContext):
    """Decorator for consistent error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                logging.info(
                    f"Operation successful: {context.operation_name}",
                    extra={
                        'session_id': context.session_id,
                        'component': context.component_name,
                        'claim': context.claim_text[:50] if context.claim_text else None
                    }
                )
                return result
            except Exception as e:
                logging.error(
                    f"Operation failed: {context.operation_name} - {str(e)}",
                    extra={
                        'session_id': context.session_id,  
                        'component': context.component_name,
                        'error_type': type(e).__name__,
                        'claim': context.claim_text[:50] if context.claim_text else None
                    }
                )
                raise ROGRException(
                    f"Failed during {context.operation_name}: {str(e)}",
                    context,
                    e
                )
        return wrapper
    return decorator
```

**Example Usage:**
```python
class ThreadSafeEvidenceWorker:
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.context = OperationContext(
            session_id=worker_id,
            component_name="ThreadSafeEvidenceWorker"
        )
        
    @with_error_handling(OperationContext("worker_123", "ThreadSafeEvidenceWorker", "execute_strategy"))
    def execute_strategy(self, strategy: ParallelSearchStrategy) -> List[ProcessedEvidence]:
        # Implementation with automatic error handling and logging
        pass
```

---

## **4. Parallel Execution Safety Pattern**
**Usage**: All concurrent operations must use this pattern
```python
import concurrent.futures
import threading
from typing import List, Dict, Callable, Any

class ParallelExecutionManager:
    """Safe parallel execution with resource management and error handling"""
    
    def __init__(self, max_workers: int = 4, timeout_seconds: int = 60):
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        
    def execute_parallel(self, 
                        tasks: List[Callable], 
                        task_args: List[tuple] = None,
                        individual_timeout: int = 30) -> List[Any]:
        """Execute tasks in parallel with comprehensive error handling"""
        
        if task_args is None:
            task_args = [()] * len(tasks)
            
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(task, *args): (task, args)
                for task, args in zip(tasks, task_args)
            }
            
            # Collect results with timeout handling
            try:
                for future in concurrent.futures.as_completed(future_to_task, timeout=self.timeout_seconds):
                    task, args = future_to_task[future]
                    try:
                        result = future.result(timeout=individual_timeout)
                        results.append(result)
                        logging.info(f"Parallel task completed: {task.__name__}")
                    except concurrent.futures.TimeoutError:
                        error_result = self._create_timeout_result(task, args)
                        results.append(error_result)
                        logging.warning(f"Parallel task timeout: {task.__name__}")
                    except Exception as e:
                        error_result = self._create_error_result(task, args, e)
                        results.append(error_result)
                        logging.error(f"Parallel task failed: {task.__name__} - {str(e)}")
                        
            except concurrent.futures.TimeoutError:
                # Overall timeout - some tasks didn't complete
                logging.error(f"Parallel execution overall timeout: {self.timeout_seconds}s")
                # Add placeholder results for incomplete tasks
                while len(results) < len(tasks):
                    results.append(self._create_timeout_result(None, None))
                    
        return results
        
    def _create_timeout_result(self, task: Callable, args: tuple) -> Any:
        """Create standardized timeout result"""
        return {'success': False, 'error': 'timeout', 'task': task.__name__ if task else 'unknown'}
        
    def _create_error_result(self, task: Callable, args: tuple, error: Exception) -> Any:
        """Create standardized error result"""
        return {'success': False, 'error': str(error), 'task': task.__name__ if task else 'unknown'}
```

**Example Usage:**
```python
def process_claims_parallel(self, claims: List[str]) -> List[ConsensusResult]:
    parallel_manager = ParallelExecutionManager(max_workers=4, timeout_seconds=120)
    
    tasks = [self.process_single_claim for _ in claims]
    task_args = [(claim,) for claim in claims]
    
    results = parallel_manager.execute_parallel(tasks, task_args, individual_timeout=60)
    return results
```

---

## **5. Configuration and Feature Flag Pattern**
**Usage**: All configuration must use this centralized pattern
```python
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
import json

@dataclass
class ParallelSystemConfig:
    """Centralized configuration for parallel evidence system"""
    
    # Feature flags
    use_parallel_evidence: bool = False
    enable_eeg_phase_1: bool = True
    enable_aci_analysis: bool = True
    enable_counter_evidence: bool = False
    
    # Performance settings
    max_claim_workers: int = 4
    max_ai_workers: int = 2
    evidence_timeout_seconds: int = 30
    total_timeout_seconds: int = 120
    
    # Resource limits
    max_evidence_per_claim: int = 5
    max_queries_per_claim: int = 9
    thread_pool_size: int = 6
    
    # Quality settings
    min_evidence_relevance_score: float = 70.0
    min_consensus_confidence: float = 0.7
    
    @classmethod
    def from_environment(cls) -> 'ParallelSystemConfig':
        """Load configuration from environment variables"""
        return cls(
            use_parallel_evidence=os.getenv('USE_PARALLEL_EVIDENCE', 'false').lower() == 'true',
            enable_eeg_phase_1=os.getenv('ENABLE_EEG_PHASE_1', 'true').lower() == 'true',
            enable_aci_analysis=os.getenv('ENABLE_ACI_ANALYSIS', 'true').lower() == 'true',
            enable_counter_evidence=os.getenv('ENABLE_COUNTER_EVIDENCE', 'false').lower() == 'true',
            max_claim_workers=int(os.getenv('MAX_CLAIM_WORKERS', '4')),
            max_ai_workers=int(os.getenv('MAX_AI_WORKERS', '2')),
            evidence_timeout_seconds=int(os.getenv('EVIDENCE_TIMEOUT_SECONDS', '30')),
            total_timeout_seconds=int(os.getenv('TOTAL_TIMEOUT_SECONDS', '120'))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            'use_parallel_evidence': self.use_parallel_evidence,
            'enable_eeg_phase_1': self.enable_eeg_phase_1,
            'enable_aci_analysis': self.enable_aci_analysis,
            'performance_settings': {
                'max_claim_workers': self.max_claim_workers,
                'max_ai_workers': self.max_ai_workers,
                'evidence_timeout_seconds': self.evidence_timeout_seconds
            }
        }

# Global configuration instance
CONFIG = ParallelSystemConfig.from_environment()
```

**Example Usage:**
```python
from parallel_evidence_system.config import CONFIG

class ParallelConsensusEngine:
    def __init__(self):
        self.max_workers = CONFIG.max_claim_workers
        self.timeout = CONFIG.total_timeout_seconds
        
    def process_claims(self, claims: List[str]):
        if not CONFIG.use_parallel_evidence:
            return self._use_legacy_system(claims)
        
        # Parallel processing with configured limits
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Implementation using CONFIG settings
            pass
```

---

## **6. Logging and Monitoring Pattern**
**Usage**: All components must use structured logging with this pattern
```python
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

class ROGRLogger:
    """Structured logging for parallel evidence system"""
    
    def __init__(self, component_name: str, session_id: str):
        self.component_name = component_name
        self.session_id = session_id
        self.logger = logging.getLogger(f"rogr.{component_name}")
        
    def log_operation_start(self, operation: str, context: Dict[str, Any] = None):
        """Log operation start with context"""
        self._log('INFO', 'operation_start', operation, context)
        
    def log_operation_success(self, operation: str, duration_ms: float, context: Dict[str, Any] = None):
        """Log successful operation completion"""
        context = context or {}
        context['duration_ms'] = duration_ms
        self._log('INFO', 'operation_success', operation, context)
        
    def log_operation_error(self, operation: str, error: Exception, context: Dict[str, Any] = None):
        """Log operation error with full context"""
        context = context or {}
        context.update({
            'error_type': type(error).__name__,
            'error_message': str(error),
            'error_details': getattr(error, 'context', None)
        })
        self._log('ERROR', 'operation_error', operation, context)
        
    def log_performance_metric(self, metric_name: str, value: float, unit: str = 'seconds', context: Dict[str, Any] = None):
        """Log performance metrics"""
        context = context or {}
        context.update({
            'metric_name': metric_name,
            'metric_value': value,
            'metric_unit': unit
        })
        self._log('INFO', 'performance_metric', metric_name, context)
        
    def _log(self, level: str, event_type: str, operation: str, context: Dict[str, Any] = None):
        """Internal structured logging method"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'component': self.component_name,
            'session_id': self.session_id,
            'event_type': event_type,
            'operation': operation,
            'context': context or {}
        }
        
        message = f"{event_type}:{operation}"
        extra = {'structured_data': json.dumps(log_entry)}
        
        if level == 'INFO':
            self.logger.info(message, extra=extra)
        elif level == 'ERROR':
            self.logger.error(message, extra=extra)
        elif level == 'WARNING':
            self.logger.warning(message, extra=extra)
```

**Example Usage:**
```python
class ThreadSafeEvidenceWorker:
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.logger = ROGRLogger('ThreadSafeEvidenceWorker', worker_id)
        
    def execute_strategy(self, strategy: ParallelSearchStrategy) -> List[ProcessedEvidence]:
        import time
        start_time = time.time()
        
        self.logger.log_operation_start('execute_strategy', {
            'claim_text': strategy.claim_text[:50],
            'query_count': len(strategy.search_queries)
        })
        
        try:
            # Implementation
            evidence = self._process_evidence(strategy)
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_success('execute_strategy', duration_ms, {
                'evidence_count': len(evidence),
                'claim_text': strategy.claim_text[:50]
            })
            
            return evidence
            
        except Exception as e:
            self.logger.log_operation_error('execute_strategy', e, {
                'claim_text': strategy.claim_text[:50],
                'query_count': len(strategy.search_queries)
            })
            raise
```

---

## **Pattern Usage Guidelines**

### **Mandatory Patterns (MUST USE)**
1. **ThreadSafeComponent** - All parallel system components
2. **Resource Cleanup Context Manager** - All HTTP sessions, AI clients, file handles
3. **Error Handling with Context** - All operations that can fail  
4. **Structured Logging** - All components for monitoring and debugging

### **Recommended Patterns (SHOULD USE)**
5. **Parallel Execution Manager** - Any concurrent operations
6. **Configuration Pattern** - All configurable behavior

### **Pattern Validation**
Each AI session should verify new code follows these patterns:
- Thread-safe initialization ✅
- Resource cleanup guaranteed ✅  
- Error handling with context ✅
- Structured logging present ✅
- Configuration externalized ✅

**These patterns ensure consistency, reliability, and maintainability across the entire parallel architecture implementation.**