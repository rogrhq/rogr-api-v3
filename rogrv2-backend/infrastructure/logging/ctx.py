from __future__ import annotations
import contextvars
from typing import Optional

_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)

def set_request_id(value: Optional[str]) -> None:
    _request_id_var.set(value)

def get_request_id() -> Optional[str]:
    return _request_id_var.get()