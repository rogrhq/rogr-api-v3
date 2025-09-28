#!/usr/bin/env python3
import os, json, subprocess, pathlib, sys, time

BASE = os.environ.get("BASE","http://localhost:8000")

def run_preview():
    # Use the shell wrapper so PY is resolved
    env = dict(os.environ); env["BASE"] = BASE
    p = subprocess.run(["bash","scripts/dev_preview.sh","--text","Austin increased its 2024 city budget by 8%."],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True, timeout=120)
    print(p.stdout)
    if p.returncode != 0:
        raise SystemExit("dev_preview.sh failed")

def load_latest_output():
    outdir = pathlib.Path("outputs")
    cand = sorted(outdir.glob("preview_*.json"))
    assert cand, "no outputs generated"
    return json.loads(cand[-1].read_text(encoding="utf-8"))

def main():
    run_preview()
    data = load_latest_output()
    assert isinstance(data, dict), "result is not a JSON object"
    assert "overall" in data and "claims" in data, "missing keys in result"
    assert isinstance(data["claims"], list), "claims should be a list"
    print("PASS")

if __name__ == "__main__":
    main()