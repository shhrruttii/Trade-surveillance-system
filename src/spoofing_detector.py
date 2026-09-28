import pandas as pd
from datetime import timedelta
from src.config import SPOOFING


def detect_spoofing(orders_df: pd.DataFrame) -> pd.DataFrame:
    alerts = []

    cancelled = orders_df[orders_df["status"] == "CANCELLED"].copy()
    if cancelled.empty:
        return pd.DataFrame()

    cancelled["cancel_time"] = pd.to_datetime(cancelled["cancel_time"])
    cancelled["submit_time"] = pd.to_datetime(cancelled["submit_time"])
    cancelled["lifetime_seconds"] = (
        cancelled["cancel_time"] - cancelled["submit_time"]
    ).dt.total_seconds()

    fast_cancels = cancelled[
        cancelled["lifetime_seconds"] <= SPOOFING["max_order_lifetime_seconds"]
    ]

    if fast_cancels.empty:
        return pd.DataFrame()

    for _, cancel_order in fast_cancels.iterrows():
        if cancel_order["volume"] < SPOOFING["min_cancelled_volume"]:
            continue

        account = cancel_order["account"]
        symbol = cancel_order["symbol"]
        cancel_side = cancel_order["side"]
        opposite_side = "SELL" if cancel_side == "BUY" else "BUY"
        cancel_time = cancel_order["cancel_time"]

        opposite_execs = orders_df[
            (orders_df["account"] == account)
            & (orders_df["symbol"] == symbol)
            & (orders_df["side"] == opposite_side)
            & (orders_df["status"] == "FILLED")
        ].copy()

        if opposite_execs.empty:
            continue

        opposite_execs["submit_time"] = pd.to_datetime(opposite_execs["submit_time"])

        window = timedelta(seconds=SPOOFING["opposite_side_window_seconds"])
        matched_execs = opposite_execs[
            (opposite_execs["submit_time"] >= cancel_time)
            & (opposite_execs["submit_time"] <= cancel_time + window)
        ]

        if matched_execs.empty:
            continue

        executed_volume = matched_execs["volume"].sum()
        size_ratio = cancel_order["volume"] / max(executed_volume, 1)

        if size_ratio < SPOOFING["min_size_ratio_cancel_to_exec"]:
            continue

                # Normalize components (0-1 each), then weight
        size_component = min(1.0, size_ratio / (SPOOFING["min_size_ratio_cancel_to_exec"] * 3))
        speed_component = max(0.0, 1 - cancel_order["lifetime_seconds"] / SPOOFING["max_order_lifetime_seconds"])
        score = round((size_component * 50) + (speed_component * 30) + 20, 2)

        alerts.append({
            "alert_id": f"SPF_{cancel_order['order_id']}",
            "typology": "SPOOFING",
            "account": account,
            "symbol": symbol,
            "order_id": cancel_order["order_id"],
            "side": cancel_side,
            "cancelled_volume": cancel_order["volume"],
            "executed_volume": executed_volume,
            "size_ratio": round(size_ratio, 2),
            "order_lifetime_seconds": round(cancel_order["lifetime_seconds"], 2),
            "cancel_time": cancel_time,
            "matched_execution_ids": ",".join(matched_execs["order_id"].tolist()),
            "risk_score": round(score, 2),
            "ground_truth": cancel_order.get("abuse_type", "UNKNOWN"),
        })

    return pd.DataFrame(alerts)