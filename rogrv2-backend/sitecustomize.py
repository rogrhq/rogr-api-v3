"""
Auto-load hook: imported by Python at startup when repo root is on sys.path.
This ensures the P19 wrapper is installed without editing existing modules.
"""
try:
    # Importing this module installs the run_plan wrapper (idempotent).
    from intelligence.gather import p19_wrapper  # noqa: F401
except Exception:
    # Never block startup if the wrapper cannot load.
    pass
