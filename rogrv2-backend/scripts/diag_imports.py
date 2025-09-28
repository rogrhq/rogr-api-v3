#!/usr/bin/env python3
from __future__ import annotations
import importlib, sys

targets = [
    "api.analyses",
    "intelligence.claims.interpret",
    "intelligence.strategy.plan",
    "intelligence.gather.normalize",
    "intelligence.gather.online",
    "intelligence.analyze.enrich",
    "intelligence.consensus.metrics",
    "intelligence.consensus.overall",
    "ai_assist.config",
    "ai_assist.planner",
    "ai_assist.nli",
    "ai_assist.explainer",
    "infrastructure.http.async_http",
    "infrastructure.storage.snapshots",
    "search_providers.google_cse",
    "search_providers.bing",
    "search_providers.brave",
]
ok, bad = [], []
for mod in targets:
    try:
        importlib.import_module(mod)
        ok.append(mod)
    except Exception as e:
        bad.append((mod, f"{type(e).__name__}: {e}"))
print("=== IMPORT OK ===")
for m in ok: print(" ", m)
print("=== IMPORT FAIL ===")
for m, err in bad: print(" ", m, "->", err)
if bad: sys.exit(1)