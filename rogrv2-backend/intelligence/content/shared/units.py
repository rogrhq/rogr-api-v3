"""Shared unit normalization and tolerance - extracted from P21 (gold standard)"""

# Unit conversion mappings - from P21 lines 89-95
UNIT_CONVERSIONS = {
    # Temperature
    '°c': 'celsius', 'celsius': 'celsius', 'c': 'celsius',
    '°f': 'fahrenheit', 'fahrenheit': 'fahrenheit', 'f': 'fahrenheit',
    'k': 'kelvin', 'kelvin': 'kelvin',

    # Distance
    'km': 'kilometers', 'kilometers': 'kilometers', 'kilometer': 'kilometers',
    'mi': 'miles', 'miles': 'miles', 'mile': 'miles',
    'm': 'meters', 'meters': 'meters', 'meter': 'meters',

    # Money
    '$': 'dollars', 'usd': 'dollars', 'dollars': 'dollars',
    '€': 'euros', 'eur': 'euros', 'euros': 'euros',

    # Percentage
    '%': 'percent', 'percent': 'percent', 'percentage': 'percent'
}

def normalize_unit(unit_str):
    """Normalize unit string to canonical form - from P21 line 102"""
    if not unit_str:
        return None
    unit_lower = unit_str.lower().strip()
    return UNIT_CONVERSIONS.get(unit_lower, unit_lower)

# Tolerance logic - from P21 lines 145-167 (GOLD STANDARD)
def compute_tolerance(value, abs_tol=0.1, rel_tol=0.05):
    """
    Compute dual tolerance (absolute + relative) - P21's gold standard approach.

    Args:
        value: The numeric value
        abs_tol: Absolute tolerance (default 0.1)
        rel_tol: Relative tolerance as fraction (default 0.05 = 5%)

    Returns:
        The larger of absolute or relative tolerance
    """
    absolute = abs_tol
    relative = abs(value * rel_tol)
    return max(absolute, relative)

def values_match(val1, val2, abs_tol=0.1, rel_tol=0.05):
    """
    Check if two numeric values match within tolerance.
    Uses dual tolerance: max(absolute, relative) - P21's approach.
    """
    tolerance = compute_tolerance(val1, abs_tol, rel_tol)
    return abs(val1 - val2) <= tolerance
