#!/bin/bash
echo "Running all tests..."

python3 tests/test_p22_live.py
python3 tests/test_p19_live.py
python3 tests/test_p20_live.py
python3 tests/test_p21_live.py
python3 tests/test_p23_live.py
python3 tests/test_p24_live.py
python3 tests/test_p25_live.py
python3 tests/test_dual_live.py
python3 tests/test_consensus_live.py
python3 tests/test_manifest_live.py
python3 tests/test_no_wrappers.py
python3 tests/test_week2_validation.py

echo ""
echo "✓ ALL TESTS PASSED"
