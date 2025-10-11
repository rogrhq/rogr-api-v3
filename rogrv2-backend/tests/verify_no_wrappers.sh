#!/bin/bash
echo "Checking for wrapper imports..."

WRAPPERS=(
    "p19_wrapper" "p20_wrapper" "p21_wrapper" "p22_ingest"
    "p23_semantic" "p24_semantic_frames" "p25_semantic_aggregate"
    "p26_dual_researchers" "p27_consensus" "p28_diversify"
    "p29_diversify_controls" "sitecustomize"
)

FOUND=0
for wrapper in "${WRAPPERS[@]}"; do
    results=$(grep -r "import.*$wrapper\|from.*$wrapper" . \
        --include="*.py" \
        --exclude-dir=".git" \
        --exclude-dir="__pycache__" \
        --exclude-dir="MONKEY_PATCH_ARCHIVE" 2>/dev/null)

    if [ -n "$results" ]; then
        echo "⚠ Found: $wrapper"
        echo "$results"
        FOUND=1
    fi
done

if [ $FOUND -eq 0 ]; then
    echo "✓ No wrapper imports found"
else
    echo "✗ Fix imports before archiving"
    exit 1
fi
