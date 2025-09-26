#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://localhost:8000}"
mkdir -p exports
curl -fsS "$BASE/openapi.json" > exports/openapi-mvp.json
python3 - <<PY
import json,glob,os
os.makedirs("exports/contracts-v2", exist_ok=True)
for p in glob.glob("frontend_contracts/v2/*.json"):
    out = os.path.join("exports/contracts-v2", os.path.basename(p))
    open(out,"w",encoding="utf-8").write(open(p,"r",encoding="utf-8").read())
PY
curl -fsS "$BASE/contracts/v2/postman" > exports/rogr_v2.postman_collection.json
ls -la exports