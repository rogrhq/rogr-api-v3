# Minimal import smoke to assert single production path (no wrappers/rebinds)
def test_core_path_no_wrappers():
    import importlib
    api = importlib.import_module("api.analyses")
    core = importlib.import_module("intelligence.pipeline.run")
    assert api.run_preview is core.run_preview, "api.run_preview must be core.run_preview"
