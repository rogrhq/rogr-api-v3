# path: sitecustomize.py
"""
Auto-load hooks: imported by Python at startup when repo root is on sys.path.
Ensures P19 & P20 wrappers are installed without editing existing modules.
Safe and idempotent.
"""
try:
    from intelligence.gather import p19_wrapper  # noqa: F401
except Exception:
    pass

try:
    from intelligence.content import p20_wrapper  # noqa: F401
except Exception:
    pass
