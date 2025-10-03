from __future__ import annotations
import json
import logging
import os
from typing import Any, Dict

_LOGGER = logging.getLogger("rogr.diag")

_TRUE = {"1","true","yes","on","y","t"}

def enabled() -> bool:
    v = os.getenv("ROGR_DIAG", "")
    return v.lower() in _TRUE


def log(event: str, **fields: Any) -> None:
    if not enabled():
        return
    try:
        payload: Dict[str, Any] = {"event": event, **fields}
        _LOGGER.info(json.dumps(payload, ensure_ascii=False))
    except Exception:
        # Never break runtime due to diagnostics
        pass
