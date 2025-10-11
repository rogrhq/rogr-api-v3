import asyncio, sys
sys.path.insert(0, '.')

# Test wrappers can't be imported
wrapper_modules = [
    "intelligence.gather.p19_wrapper",
    "intelligence.content.p22_ingest",
    "intelligence.content.p26_dual_researchers"
]

for mod in wrapper_modules:
    try:
        __import__(mod)
        print(f"✗ ERROR: {mod} still importable!")
        sys.exit(1)
    except (ImportError, ModuleNotFoundError):
        pass

print("✓ Wrappers not importable")

# Test pipeline works
from intelligence.pipeline.run import run_preview

async def test():
    result = await run_preview("Test")
    assert len(result['claims'][0]['researchers']) == 2
    print("✓ Pipeline works without wrappers")

asyncio.run(test())
print("✓ ALL TESTS PASSED")
