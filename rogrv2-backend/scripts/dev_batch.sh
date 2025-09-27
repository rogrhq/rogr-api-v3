#!/usr/bin/env bash
set -euo pipefail
# Usage: bash scripts/dev_batch.sh path/to/claims.txt
# claims.txt should contain one line per claim.
FILE="${1:-}"
if [ -z "${FILE}" ] || [ ! -f "${FILE}" ]; then
  echo "Usage: $0 path/to/claims.txt" >&2
  exit 1
fi
while IFS= read -r line; do
  [ -z "$line" ] && continue
  echo ">> Running: $line"
  bash scripts/dev_preview.sh --text "$line"
done < "$FILE"