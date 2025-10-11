"""
ROGRv2 bootstrap imports for runtime wrappers.
Loads P20 (if present) and P22 ingestion enrichment.
This file is auto-imported by Python when present on sys.path.
"""
from importlib import import_module
import os, json, traceback

def _try(mod: str):
    try:
        import_module(mod)
        if os.getenv("ROGR_DIAG"):
            print(json.dumps({"event": "sitecustomize.import_ok", "module": mod}))
    except Exception as e:
        if os.getenv("ROGR_DIAG"):
            print(json.dumps({"event": "sitecustomize.import_fail", "module": mod, "error": str(e)}))

# Keep earlier packet wrapper if installed
_try("intelligence.content.p20_wrapper")
# Install P22 ingestion enrichment
_try("intelligence.content.p22_ingest")
