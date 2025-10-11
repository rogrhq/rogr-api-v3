# P20 Stance Detection Redesign

## Current Issue
Keyword-based stance detection fails for scientific claims.

## Root Cause
- Uses increase/decrease keywords designed for policy claims
- No numeric/unit comparison
- No condition awareness (sea level vs altitude)
- Sequential if statements caused overwrites (FIXED 2025-10-11)

## Minimal Fix Applied (2025-10-11)
- Changed if→elif to prevent overwrites
- Documented known issue in code
- Continuing testing with known broken stance

## Full Redesign Required
See SAGPT architectural plan:
1. Frame-based reasoning (not keywords)
2. Numeric/unit comparison with normalization
3. Condition-aware logic (baseline vs variations)
4. Windowed evidence parsing
5. Claim-type domain adapters
6. Decision tree with rationale output

## Testing Approach
1. Fix other bugs in P21-P25 first (with broken P20)
2. Get clean baseline
3. THEN implement P20 redesign
4. Any new bugs = isolated to P20 change

## When to Circle Back
After completing:
- P21-P25 bug fixes
- P26-P29 validation
- IFCN compliance
- Full execution plan

Estimated effort: 2-3 days for full redesign

## Example Failures (Documented for Future Fix)

### Scientific Claim
```
Claim: "Water boils at 100°C"
Evidence: "Water boils at lower temperatures at high altitude"
Current: stance="challenge" (detects "lower")
Should be: stance="support" (explains variation)
```

### Budget Claim (Working)
```
Claim: "Austin budget increased 8%"
Evidence: "Budget increased by 8.2% according to official records"
Current: stance="support" ✓
```

## Progress Tracking
- [x] Minimal fix (if→elif)
- [x] Documentation added
- [ ] P21-P25 bug isolation
- [ ] Full redesign implementation
- [ ] Integration testing
