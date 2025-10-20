#!/usr/bin/env python3
"""Count and categorize silent error handlers in intelligence/"""
import re
import os

results = {
    "critical": [],  # In pipeline/run.py (main execution path)
    "high": [],      # In content/ (grading, stance, authority)
    "medium": [],    # In gather/ (search, fetch)
    "low": []        # In utility/helper files
}

# Scan each Python file
for root, dirs, files in os.walk('intelligence'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)

            try:
                with open(filepath, 'r') as f:
                    lines = f.readlines()
            except:
                continue

            for i, line in enumerate(lines, 1):
                if re.search(r'except.*:', line):
                    # Check if next line is pass or return None
                    if i < len(lines):
                        next_line = lines[i].strip()
                        if next_line == 'pass' or next_line == 'return None' or next_line == 'continue':
                            location = f"{filepath}:{i}"

                            # Categorize
                            if 'pipeline/run.py' in filepath:
                                results['critical'].append(location)
                            elif 'content/' in filepath:
                                results['high'].append(location)
                            elif 'gather/' in filepath:
                                results['medium'].append(location)
                            else:
                                results['low'].append(location)

# Print summary
print("\nSILENT ERROR HANDLER SUMMARY")
print("=" * 60)
print(f"CRITICAL (pipeline/run.py): {len(results['critical'])}")
for loc in results['critical']:
    print(f"  - {loc}")

print(f"\nHIGH (content/ - grading/stance): {len(results['high'])}")
for loc in results['high'][:20]:  # Limit to first 20
    print(f"  - {loc}")
if len(results['high']) > 20:
    print(f"  ... and {len(results['high']) - 20} more")

print(f"\nMEDIUM (gather/ - search/fetch): {len(results['medium'])}")
for loc in results['medium'][:20]:
    print(f"  - {loc}")
if len(results['medium']) > 20:
    print(f"  ... and {len(results['medium']) - 20} more")

print(f"\nLOW (utilities): {len(results['low'])}")
for loc in results['low'][:20]:
    print(f"  - {loc}")
if len(results['low']) > 20:
    print(f"  ... and {len(results['low']) - 20} more")

total = sum(len(v) for v in results.values())
print(f"\nTOTAL SILENT ERROR HANDLERS: {total}")
