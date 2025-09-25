import os, stat, sys
REQ_DIRS = [
    "api","workers","intelligence/claims","intelligence/strategy","intelligence/gather",
    "intelligence/analyze","intelligence/consensus","intelligence/score",
    "ai_providers/claude","ai_providers/inhouse","search_providers/google_cse",
    "search_providers/bing","search_providers/inhouse","infrastructure/auth",
    "infrastructure/logging","infrastructure/http","infrastructure/storage",
    "infrastructure/heuristics","database","scripts","frontend_contracts"
]
REQ_FILES = [
    "scripts/run_api.sh","requirements.txt","infrastructure/logging/__init__.py",
    "infrastructure/http/__init__.py","infrastructure/storage/__init__.py",
    "infrastructure/auth/jwt.py","main.py","api/health.py",
]
missing = [d for d in REQ_DIRS if not os.path.isdir(d)] + [f for f in REQ_FILES if not os.path.isfile(f)]
errors = []
if not missing:
    st = os.stat("scripts/run_api.sh")
    if not (st.st_mode & stat.S_IXUSR):
        errors.append("scripts/run_api.sh not executable")
if missing or errors:
    print("FAIL")
    if missing:
        print("Missing:"); [print(" -", m) for m in missing]
    if errors:
        print("Errors:"); [print(" -", e) for e in errors]
    sys.exit(1)
print("PASS")