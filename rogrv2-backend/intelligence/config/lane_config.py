"""
Phase 5.2: Lane-specific configuration for R1 and R2

R1 (Precision): Strict thresholds, conservative
R2 (Recall): Lenient thresholds, exploratory
"""

LANE_CONFIGS = {
    'R1': {
        # Strict thresholds
        'stance_threshold': 0.70,      # Must be very clear stance
        'min_item_grade': 0.60,        # High bar for evidence quality
        'verdict_delta': 0.20,         # Wide gap required between arms
        'min_confidence': 0.65,        # Conservative confidence
        'min_items_per_arm': 2,        # Need at least 2 items

        # Query strategy
        'query_style': 'precision',    # Use quoted, exact queries
        'max_queries_per_arm': 5,
    },
    'R2': {
        # Lenient thresholds
        'stance_threshold': 0.50,      # More permissive stance
        'min_item_grade': 0.40,        # Lower bar for evidence
        'verdict_delta': 0.15,         # Narrower gap okay
        'min_confidence': 0.45,        # More exploratory
        'min_items_per_arm': 2,

        # Query strategy
        'query_style': 'recall',       # Use broad, paraphrased queries
        'max_queries_per_arm': 8,
    },
}

def get_lane_config(lane: str) -> dict:
    """Get configuration for specified lane (R1 or R2)"""
    return LANE_CONFIGS.get(lane, LANE_CONFIGS['R1'])  # Default to R1

