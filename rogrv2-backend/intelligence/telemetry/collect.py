from typing import Dict, Any
import time
import hashlib
from datetime import datetime

class LaneTelemetry:
    """Track execution metrics for one researcher lane."""

    def __init__(self, lane_id: str):
        self.lane_id = lane_id
        self.start_time = time.time()
        self.provider_calls = {}

    def record_provider_call(self, provider: str) -> None:
        """Record a provider call."""
        self.provider_calls[provider] = self.provider_calls.get(provider, 0) + 1

    def finalize(self) -> Dict[str, Any]:
        """Finalize and return metrics."""
        duration = (time.time() - self.start_time) * 1000
        return {
            "providers": self.provider_calls,
            "duration_ms": int(duration)
        }

def generate_manifest(
    claim_text: str,
    r1_config: Dict[str, Any],
    r2_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate reproducibility manifest."""

    # Generate replay_id
    combined = f"{claim_text}:{r1_config.get('seed')}:{r2_config.get('seed')}"
    replay_id = hashlib.md5(combined.encode()).hexdigest()

    return {
        "replay_id": replay_id,
        "claim_text": claim_text,
        "lanes": {
            "R1": {
                "providers": r1_config.get("providers", []),
                "seed": r1_config.get("seed", 0),
                "queries_first3": r1_config.get("queries_first3", {})
            },
            "R2": {
                "providers": r2_config.get("providers", []),
                "seed": r2_config.get("seed", 0),
                "queries_first3": r2_config.get("queries_first3", {})
            }
        },
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

# TEST
if __name__ == "__main__":
    import time

    t = LaneTelemetry("R1")
    t.record_provider_call("google")
    t.record_provider_call("google")
    t.record_provider_call("brave")
    time.sleep(0.1)

    result = t.finalize()
    print(f"Telemetry: {result}")
    assert result['providers']['google'] == 2
    assert result['duration_ms'] >= 100

    # Test manifest
    r1_cfg = {"providers": ["google"], "seed": 123}
    r2_cfg = {"providers": ["brave"], "seed": 456}
    manifest = generate_manifest("Test", r1_cfg, r2_cfg)

    print(f"Manifest: {manifest['replay_id'][:20]}...")
    assert 'replay_id' in manifest

    # Test determinism
    manifest2 = generate_manifest("Test", r1_cfg, r2_cfg)
    assert manifest['replay_id'] == manifest2['replay_id']

    print("✓ PASS")
