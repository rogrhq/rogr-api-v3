#!/usr/bin/env bash
set -euo pipefail

# Ensure the repository root is on Python's import path
export PYTHONPATH="${PYTHONPATH:-.}:."

# Enable diagnostics for visibility during the packet test
export ROGR_DIAG=1

# Run the P29 packet test
python3 scripts/test_packetP29.py
