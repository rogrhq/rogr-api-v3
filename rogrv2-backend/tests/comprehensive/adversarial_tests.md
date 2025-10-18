# Adversarial Test Suite

Deliberately tricky claims to stress-test the system.

## Category 1: Misleading Context

**Test 1.1:** Implied context
- Claim: "Water boils at 100°C"
- Trick: Missing "at sea level"
- Evidence: Mix of sea-level and altitude data
- Expected: System should recognize implied context or mark mixed

**Test 1.2:** Time-sensitive facts
- Claim: "US President is Joe Biden"
- Trick: True when written, may be false later
- Evidence: Historical data
- Expected: System should weight recent evidence

## Category 2: Subtle Negation

**Test 2.1:** Double negatives
- Claim: "Vaccines don't not work"
- Trick: Double negative = positive
- Evidence: "Vaccines work"
- Expected: System should parse correctly

**Test 2.2:** Negation detection
- Claim: "Vaccines cause autism"
- Trick: Commonly believed myth
- Evidence: "Studies show vaccines do NOT cause autism"
- Expected: System should identify challenge

## Category 3: Numeric Precision Traps

**Test 3.1:** Rounding differences
- Claim: "Pi is 3.14"
- Evidence: "Pi is 3.14159..."
- Expected: System should recognize as close match (appropriate precision)

**Test 3.2:** Unit confusion
- Claim: "Speed limit is 65"
- Evidence: Mix of mph and km/h
- Expected: System should check unit consistency

## Category 4: Temporal Confusion

**Test 4.1:** Past vs present
- Claim: "Unemployment is 10%"
- Evidence: 2020 data (10%) vs 2024 data (4%)
- Expected: System should weight recent data

**Test 4.2:** Historical revision
- Claim: "Pluto is a planet"
- Evidence: Pre-2006 (yes) vs post-2006 (no, dwarf planet)
- Expected: System should recognize definition changed

## Category 5: Geographic Confusion

**Test 5.1:** Local vs national
- Claim: "Minimum wage is $15"
- Evidence: Mix of federal ($7.25) and California ($15)
- Expected: System should recognize geographic scope issue

**Test 5.2:** Country-specific
- Claim: "Healthcare is free"
- Evidence: Mix of US and UK data
- Expected: System should check geographic match

## Category 6: Cherry-Picked Evidence

**Test 6.1:** Single low-quality study
- Claim: "Coffee cures cancer"
- Evidence: One low-quality blog post
- Expected: System should reject based on authority/lack of consensus

**Test 6.2:** Outlier data
- Claim: "Vaccines are dangerous"
- Evidence: 1 anti-vax blog + 10 medical journals
- Expected: System should weight by authority

## Category 7: Correlation vs Causation

**Test 7.1:** Spurious correlation
- Claim: "Ice cream causes drowning"
- Evidence: "Ice cream sales and drowning both peak in summer"
- Expected: System should recognize correlation ≠ causation

## Category 8: False Equivalence

**Test 8.1:** Semantic differences
- Claim: "Evolution is just a theory"
- Evidence: Scientific definition of "theory"
- Expected: System should recognize colloquial vs scientific meaning

## Success Criteria

- Pass rate: 95%+ on adversarial tests
- System recognizes tricks
- Confident when should be, cautious when shouldn't
