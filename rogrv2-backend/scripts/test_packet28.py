#!/usr/bin/env python3
import os, subprocess, json, pathlib, sys

BASE = os.environ.get("BASE","http://localhost:8000")

def main():
    env = dict(os.environ); env["BASE"] = BASE
    # Ensure API is up (idempotent)
    subprocess.run(["bash","scripts/dev_init.sh"], check=True, env=env, text=True)
    # Two quick claims
    cmd = ["bash","scripts/dev_csv_preview.sh","--claims","Austin increased its 2024 city budget by 8%.,The earth has two moons."]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True)
    print(p.stdout)
    if p.returncode != 0:
        raise SystemExit("CSV preview failed")
    # Verify outputs exist
    outs = sorted(pathlib.Path("outputs").glob("batch_*/claim_*.json"))
    assert outs, "No outputs written"
    d = json.loads(outs[-1].read_text(encoding="utf-8"))
    assert isinstance(d, dict) and "overall" in d and "claims" in d, "Bad output shape"
    print("PASS")

if __name__ == "__main__":
    main()