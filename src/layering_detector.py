import pandas as pd
from datetime import timedelta
from src.config import LAYERING


def detect_layering(orders_df: pd.DataFrame) -> pd.DataFrame:
    alerts = []

    cancelled = orders_df[orders_df["status"] == "CANCELLED"].copy()
    if cancelled.empty:
        return pd.DataFrame()

    cancelled["submit_time"] = pd.to_datetime(cancelled["submit_time"])
    cancelled["cancel_time"] = pd.to_datetime(cancelled["cancel_time"])

    grouped = cancelled.groupby(["account", "symbol", "side"])

    for (account, symbol, side), group in grouped:
        if len(group) < LAYERING["min_price_levels"]:
            continue

        group = group.sort_values("submit_time").reset_index(drop=True)

        for i in range(len(group)):
            cluster = group.iloc[i:].copy()
            base_submit = cluster.iloc[0]["submit_time"]
            cluster = cluster[
                cluster["submit_time"] <= base_submit + timedelta(seconds=1)
            ]

            if len(cluster) < LAYERING["min_price_levels"]:
                continue

            unique_prices = cluster["price"].nunique()
            if unique_prices < LAYERING["min_price_levels"]:
                continue

            price_span = cluster["price"].max() - cluster["price"].min()
            if price_span > LAYERING["max_level_span_ticks"] * 0.01:
                continue

            cancel_times = cluster["cancel_time"]
            cancel_span = (cancel_times.max() - cancel_times.min()).total_seconds()
            if cancel_span > LAYERING["max_cancellation_window_seconds"]:
                continue

            total_volume = cluster["volume"].sum()
            if total_volume < LAYERING["min_total_cancelled_volume"]:
                continue

            opposite_side = "SELL" if side == "BUY" else "BUY"
            last_cancel = cancel_times.max()

            opposite_execs = orders_df[
                (orders_df["account"] == account)
                & (orders_df["symbol"] == symbol)
                & (orders_df["side"] == opposite_side)
                & (orders_df["status"] == "FILLED")
            ].copy()

            if opposite_execs.empty:
                continue

            opposite_execs["submit_time"] = pd.to_datetime(opposite_execs["submit_time"])

            window = timedelta(seconds=LAYERING["opposite_side_window_seconds"])
            matched = opposite_execs[
                (opposite_execs["submit_time"] >= last_cancel)
                & (opposite_execs["submit_time"] <= last_cancel + window)
            ]

            if matched.empty:
                continue

            executed_volume = matched["volume"].sum()

            level_component = min(1.0, unique_prices / 5)
            speed_component = max(0.0, 1 - cancel_span / LAYERING["max_cancellation_window_seconds"])
            volume_component = min(1.0, total_volume / 1000)
            score = round((level_component * 35) + (speed_component * 30) + (volume_component * 15) + 20, 2)

            alerts.append({
                "alert_id": f"LAY_{account}_{symbol}_{side}_{i}",
                "typology": "LAYERING",
                "account": account,
                "symbol": symbol,
                "side": side,
                "num_price_levels": unique_prices,
                "total_cancelled_volume": total_volume,
                "executed_volume": executed_volume,
                "price_span": round(price_span, 4),
                "cancel_span_seconds": round(cancel_span, 2),
                "order_ids": ",".join(cluster["order_id"].tolist()),
                "matched_execution_ids": ",".join(matched["order_id"].tolist()),
                "risk_score": score,
                "ground_truth": cluster.iloc[0].get("abuse_type", "UNKNOWN"),
            })

            break

    return pd.DataFrame(alerts)