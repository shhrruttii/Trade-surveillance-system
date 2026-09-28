"""
Configuration: thresholds and parameters for detection rules.
"""

SPOOFING = {
    "max_order_lifetime_seconds": 2,
    "min_size_ratio_cancel_to_exec": 5.0,
    "min_cancelled_volume": 100,
    "opposite_side_window_seconds": 10,
}

LAYERING = {
    "min_price_levels": 3,
    "max_level_span_ticks": 5,
    "max_cancellation_window_seconds": 3,
    "opposite_side_window_seconds": 10,
    "min_total_cancelled_volume": 200,
}

WASH_TRADING = {
    "max_round_trip_seconds": 60,
    "min_volume_for_flag": 100,
    "price_similarity_tolerance": 0.005,
    "min_circular_trades": 2,
}

PRIORITY = {
    "HIGH": {"min_score": 90, "color": "#d9534f"},
    "MEDIUM": {"min_score": 75, "color": "#f0ad4e"},
    "LOW": {"min_score": 0, "color": "#5bc0de"},
}