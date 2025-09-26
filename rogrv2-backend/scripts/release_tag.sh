#!/usr/bin/env bash
set -euo pipefail
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Not a git repo"; exit 1; }
git checkout -B release/mvp-v0.1.0
git add -A
git commit -m "Freeze MVP contracts and docs" || true
git tag -f v0.1.0
git log -1 --oneline
git tag -n1 --list "v0.1.0"