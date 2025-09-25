from __future__ import annotations
import time, os
from typing import Dict, Tuple
from fastapi import Depends, HTTPException, Request

# In-memory windowed counter: key=(token or ip), window=60s
_WINDOW = 60
_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
# state: { key: (window_start_epoch, count) }
_STATE: Dict[str, Tuple[int, int]] = {}

def rate_limit_dep(req: Request):
    # Prefer token; fallback to IP
    auth = req.headers.get("authorization", "")
    key = auth if auth else (req.client.host if req.client else "unknown")
    now = int(time.time())
    start, count = _STATE.get(key, (now, 0))
    # window rollover
    if now - start >= _WINDOW:
        start, count = now, 0
    count += 1
    _STATE[key] = (start, count)
    if count > _LIMIT:
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    return True