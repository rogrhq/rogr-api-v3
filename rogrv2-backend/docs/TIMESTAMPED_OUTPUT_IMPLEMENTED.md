# Timestamped Output Implementation

**Date:** 2025-10-21
**Status:** ✅ Complete

## Changes Made

### 1. Created Directory
```bash
mkdir -p docs/pipeline_diagnostics/
```

All future diagnostic outputs will be saved here with timestamps.

### 2. Modified Test Script

**File:** `tests/complete_pipeline_diagnostic.py`
**Lines:** 10-26

**Before:**
```python
import asyncio
import json
import sys
from typing import Dict, Any

# Redirect output to file
output_file = open('docs/PIPELINE_EXECUTION_TRACE.md', 'w')
sys.stdout = output_file
```

**After:**
```python
import asyncio
import json
import sys
from typing import Dict, Any
from datetime import datetime

# Create timestamped output file
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_filename = f'docs/pipeline_diagnostics/diagnostic_{timestamp}.md'
output_file = open(output_filename, 'w')
sys.stdout = output_file

# Print header with timestamp
print(f"# Pipeline Diagnostic Report")
print(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"**Output File:** {output_filename}")
print("")
```

## How It Works

### Filename Format
```
docs/pipeline_diagnostics/diagnostic_YYYYMMDD_HHMMSS.md
```

**Examples:**
- `diagnostic_20251021_142730.md` - Run on Oct 21, 2025 at 2:27:30 PM
- `diagnostic_20251021_143015.md` - Run on Oct 21, 2025 at 2:30:15 PM
- `diagnostic_20251021_150045.md` - Run on Oct 21, 2025 at 3:00:45 PM

### Output Header

Each file starts with:
```markdown
# Pipeline Diagnostic Report
**Timestamp:** 2025-10-21 14:27:30
**Output File:** docs/pipeline_diagnostics/diagnostic_20251021_142730.md
```

## Benefits

### 1. No Overwrites
- Each run creates a new file
- Historical diagnostics preserved
- Can compare runs over time

### 2. Easy Sorting
- Files sort chronologically by name
- `ls -t` shows newest first
- `ls` shows oldest first

### 3. Quick Access to Latest
```bash
# Get latest diagnostic
latest=$(ls -t docs/pipeline_diagnostics/diagnostic_*.md | head -1)
cat "$latest"
```

### 4. Historical Analysis
```bash
# Compare two runs
diff docs/pipeline_diagnostics/diagnostic_20251021_142730.md \
     docs/pipeline_diagnostics/diagnostic_20251021_143015.md

# Count files (track how many runs)
ls docs/pipeline_diagnostics/ | wc -l

# Show all run timestamps
ls docs/pipeline_diagnostics/
```

## Usage

### Run Diagnostic
```bash
cd /Users/txtk/Documents/ROGR/github/rogrv2-backend
PYTHONPATH=/Users/txtk/Documents/ROGR/github/rogrv2-backend python3 tests/complete_pipeline_diagnostic.py
```

### Find Output
```bash
# List all diagnostics (newest first)
ls -lht docs/pipeline_diagnostics/

# Open latest
open $(ls -t docs/pipeline_diagnostics/diagnostic_*.md | head -1)

# View latest in terminal
cat $(ls -t docs/pipeline_diagnostics/diagnostic_*.md | head -1)
```

### Compare Runs
```bash
# Get two most recent
latest=$(ls -t docs/pipeline_diagnostics/diagnostic_*.md | head -1)
previous=$(ls -t docs/pipeline_diagnostics/diagnostic_*.md | head -2 | tail -1)

# Show differences
diff "$previous" "$latest"
```

## Maintenance

### Cleanup Old Files
```bash
# Keep only last 10 diagnostics
cd docs/pipeline_diagnostics/
ls -t diagnostic_*.md | tail -n +11 | xargs rm

# Or keep only from last 7 days
find . -name "diagnostic_*.md" -mtime +7 -delete
```

### Archive
```bash
# Archive diagnostics older than 30 days
mkdir -p archive/
find . -name "diagnostic_*.md" -mtime +30 -exec mv {} archive/ \;
```

## Backward Compatibility

**Old location still works for reference:**
- `docs/PIPELINE_EXECUTION_TRACE.md` - Last run before timestamping

**New runs use:**
- `docs/pipeline_diagnostics/diagnostic_YYYYMMDD_HHMMSS.md`

## File Size Tracking

Expected size per diagnostic: ~20-25 KB

With 100 runs: ~2-2.5 MB
With 1000 runs: ~20-25 MB

**Recommended:** Keep last 50-100 runs, archive older ones

## Example Workflow

### Before Code Change
```bash
# Run baseline diagnostic
PYTHONPATH=. python3 tests/complete_pipeline_diagnostic.py
baseline=$(ls -t docs/pipeline_diagnostics/diagnostic_*.md | head -1)
echo "Baseline: $baseline"
```

### Make Code Changes
```bash
# Edit code...
```

### After Code Change
```bash
# Run new diagnostic
PYTHONPATH=. python3 tests/complete_pipeline_diagnostic.py
latest=$(ls -t docs/pipeline_diagnostics/diagnostic_*.md | head -1)
echo "Latest: $latest"

# Compare
diff "$baseline" "$latest" | head -100
```

### Track Progress
```bash
# Show all diagnostics from today
ls -lh docs/pipeline_diagnostics/diagnostic_$(date +%Y%m%d)*.md
```

## Integration with Git

### .gitignore Recommendation
```gitignore
# Keep diagnostic directory structure
docs/pipeline_diagnostics/

# But ignore diagnostic files (they're large and transient)
docs/pipeline_diagnostics/diagnostic_*.md

# Optionally keep one for reference
!docs/pipeline_diagnostics/diagnostic_baseline.md
```

**Or** commit them if you want historical tracking:
```bash
git add docs/pipeline_diagnostics/diagnostic_*.md
git commit -m "Add diagnostic snapshots"
```

## Troubleshooting

### File Not Created
**Issue:** Directory doesn't exist
**Fix:**
```bash
mkdir -p docs/pipeline_diagnostics/
```

### Permission Denied
**Issue:** Can't write to directory
**Fix:**
```bash
chmod 755 docs/pipeline_diagnostics/
```

### Too Many Files
**Issue:** Directory getting large
**Fix:**
```bash
# Keep only last 20
cd docs/pipeline_diagnostics/
ls -t diagnostic_*.md | tail -n +21 | xargs rm
```

---

**Implementation Status: COMPLETE ✅**

Next diagnostic run will automatically create a timestamped file in `docs/pipeline_diagnostics/`.
