from __future__ import annotations
import asyncio, time, uuid
from typing import Any, Dict, Optional, Callable, Awaitable

JobPayload = Dict[str, Any]
JobResult  = Dict[str, Any]

# States: queued -> running -> completed|failed
_JOBS: Dict[str, Dict[str, Any]] = {}
_Q: Optional[asyncio.Queue] = None
_WORKER_TASK: Optional[asyncio.Task] = None
_HANDLERS: Dict[str, Callable[[JobPayload], Awaitable[JobResult]]] = {}

def _now() -> int:
    return int(time.time())

def register_handler(kind: str, fn: Callable[[JobPayload], Awaitable[JobResult]]) -> None:
    _HANDLERS[kind] = fn

async def _worker_loop():
    global _Q
    assert _Q is not None
    while True:
        jid = await _Q.get()
        try:
            j = _JOBS.get(jid) or {}
            kind = j.get("kind")
            payload = j.get("payload") or {}
            j["status"] = "running"
            j["started_at"] = _now()
            _JOBS[jid] = j
            fn = _HANDLERS.get(kind)
            if not fn:
                raise RuntimeError(f"no handler for kind={kind}")
            res = await fn(payload)
            j["status"] = "completed"
            j["result"] = res
            j["completed_at"] = _now()
            _JOBS[jid] = j
        except Exception as e:
            j = _JOBS.get(jid, {"id": jid})
            j["status"] = "failed"
            j["error"] = str(e)
            j["completed_at"] = _now()
            _JOBS[jid] = j
        finally:
            _Q.task_done()

def start() -> None:
    """Idempotent: create queue + spawn worker task once."""
    global _Q, _WORKER_TASK
    if _Q is None:
        _Q = asyncio.Queue()
    if _WORKER_TASK is None or _WORKER_TASK.done():
        loop = asyncio.get_event_loop()
        _WORKER_TASK = loop.create_task(_worker_loop())

def stop() -> None:
    """Not used in tests; left for future expansion."""
    pass

def snapshot_job(job_id: str) -> Dict[str, Any]:
    return dict(_JOBS.get(job_id) or {})

async def enqueue(kind: str, payload: JobPayload) -> str:
    jid = str(uuid.uuid4())
    _JOBS[jid] = {"id": jid, "kind": kind, "status": "queued", "payload": payload, "created_at": _now()}
    assert _Q is not None, "queue not started"
    await _Q.put(jid)
    return jid