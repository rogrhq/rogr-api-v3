"""Condition recognition and equivalence - NEW module (gap identified in inventory)"""

# Scientific condition equivalents
CONDITION_EQUIVALENTS = {
    'sea level': ['standard pressure', '1 atm', '101.325 kpa', 'at sea level'],
    'room temperature': ['20°c', '68°f', '293k', 'ambient temperature'],
    'standard conditions': ['stp', '0°c and 1 atm', '273k and 101.325 kpa'],
    'normal pressure': ['1 atm', 'atmospheric pressure', '101.325 kpa'],
    'high altitude': ['low pressure', 'reduced pressure', 'above sea level'],
}

# Fiscal year patterns
FISCAL_PATTERNS = {
    'fy2024': ['fiscal year 2024', 'fy 2024', '2024 fiscal year'],
    'fy2023': ['fiscal year 2023', 'fy 2023', '2023 fiscal year'],
    'q1': ['first quarter', 'quarter 1', 'q1'],
    'q2': ['second quarter', 'quarter 2', 'q2'],
    'q3': ['third quarter', 'quarter 3', 'q3'],
    'q4': ['fourth quarter', 'quarter 4', 'q4'],
}

def normalize_condition(condition_text):
    """Normalize condition to canonical form"""
    cond_lower = condition_text.lower().strip()

    # Check scientific conditions
    for canonical, equivalents in CONDITION_EQUIVALENTS.items():
        if cond_lower == canonical or cond_lower in [e.lower() for e in equivalents]:
            return canonical

    # Check fiscal patterns
    for canonical, equivalents in FISCAL_PATTERNS.items():
        if cond_lower == canonical or cond_lower in [e.lower() for e in equivalents]:
            return canonical

    return cond_lower

def conditions_equivalent(cond1, cond2):
    """Check if two conditions are equivalent"""
    norm1 = normalize_condition(cond1)
    norm2 = normalize_condition(cond2)
    return norm1 == norm2

def extract_conditions(text):
    """Extract condition phrases from text"""
    conditions = []
    text_lower = text.lower()

    # Look for scientific conditions
    for canonical, equivalents in CONDITION_EQUIVALENTS.items():
        for equiv in [canonical] + equivalents:
            if equiv.lower() in text_lower:
                conditions.append(canonical)
                break

    # Look for fiscal patterns
    for canonical, equivalents in FISCAL_PATTERNS.items():
        for equiv in [canonical] + equivalents:
            if equiv.lower() in text_lower:
                conditions.append(canonical)
                break

    return list(set(conditions))  # deduplicate
