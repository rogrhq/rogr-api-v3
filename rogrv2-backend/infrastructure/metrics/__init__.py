from __future__ import annotations
import time, threading, platform
from typing import Dict, Any

# Thread-safe registry (works in async handlers; lock guards updates)
_lock = threading.Lock()
_counters: Dict[str, int] = {
    "requests_total": 0,
    "status_2xx": 0,
    "status_4xx": 0,
    "status_5xx": 0,
}
_gauges: Dict[str, int] = {
    "in_flight": 0,
}
_latency: Dict[str, float] = {
    "count": 0.0,
    "sum_ms": 0.0,
}

def _bucket_status(status: int) -> str:
    if 200 <= status < 300: return "status_2xx"
    if 400 <= status < 500: return "status_4xx"
    if 500 <= status < 600: return "status_5xx"
    return "status_other"

def inc(k: str, n: int = 1) -> None:
    with _lock:
        _counters[k] = _counters.get(k, 0) + n

def gauge_add(k: str, n: int) -> None:
    with _lock:
        _gauges[k] = _gauges.get(k, 0) + n

def observe_latency_ms(ms: float) -> None:
    with _lock:
        _latency["count"] += 1.0
        _latency["sum_ms"] += float(ms)

def snapshot(additional: Dict[str, Any] | None = None) -> Dict[str, Any]:
    with _lock:
        avg = (_latency["sum_ms"] / _latency["count"]) if _latency["count"] > 0 else 0.0
        out = {
            "requests_total": _counters.get("requests_total", 0),
            "status_2xx": _counters.get("status_2xx", 0),
            "status_4xx": _counters.get("status_4xx", 0),
            "status_5xx": _counters.get("status_5xx", 0),
            "in_flight": _gauges.get("in_flight", 0),
            "request_latency_ms": {
                "count": int(_latency["count"]),
                "sum_ms": round(_latency["sum_ms"], 3),
                "avg_ms": round(avg, 3),
            },
        }
        if additional:
            out.update(additional)
        return out

def install_http_middleware(app) -> None:
    """
    Idempotently install an HTTP middleware that records:
    - requests_total
    - in_flight
    - latency
    - status buckets (2xx/4xx/5xx)
    """
    if getattr(app.state, "_metrics_installed", False):
        return
    app.state._metrics_installed = True

    @app.middleware("http")
    async def _metrics_mw(request, call_next):
        start = time.perf_counter()
        gauge_add("in_flight", +1)
        inc("requests_total", 1)
        try:
            response = await call_next(request)
            return response
        finally:
            dur_ms = (time.perf_counter() - start) * 1000.0
            observe_latency_ms(dur_ms)
            # response may not exist on exceptions; guard
            try:
                status = int(getattr(locals().get("response", None), "status_code", 500))
            except Exception:
                status = 500
            inc(_bucket_status(status), 1)
            gauge_add("in_flight", -1)

def diagnostics() -> Dict[str, Any]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
    }