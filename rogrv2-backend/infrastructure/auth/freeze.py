from __future__ import annotations
from typing import Set

_frozen: Set[str] = set()

def freeze(sub: str) -> None:
    if sub:
        _frozen.add(sub)

def unfreeze(sub: str) -> None:
    if sub:
        _frozen.discard(sub)

def is_frozen(sub: str) -> bool:
    return bool(sub and sub in _frozen)