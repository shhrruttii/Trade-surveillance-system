import pandas as pd
from datetime import timedelta
from src.config import WASH_TRADING


def detect_wash_trades(orders_df: pd.DataFrame) -> pd.DataFrame:
    alerts = []

    filled = orders_df[orders_df["status"] == "FILLED"].copy()
    if filled.empty:
        return pd.DataFrame()

    filled["submit_time"] = pd.to_datetime(filled["submit_time"])
    filled["counterparty"] = filled["counterparty"].fillna("").astype(str)
    filled = filled.sort_values("submit_time").reset_index(drop=True)

    for symbol in filled["symbol"].unique():
        symbol_trades = filled[filled["symbol"] == symbol].reset_index(drop=True)

        for _, trade1 in symbol_trades.iterrows():
            if trade1["volume"] < WASH_TRADING["min_volume_for_flag"]:
                continue

            account_a = trade1["account"]
            side_1 = trade1["side"]
            opposite_side = "SELL" if side_1 == "BUY" else "BUY"
            time_1 = trade1["submit_time"]
            cp_1 = str(trade1.get("counterparty", "")).strip()

            if not cp_1:
                continue

            window = timedelta(seconds=WASH_TRADING["max_round_trip_seconds"])

            candidates = symbol_trades[
                (symbol_trades["submit_time"] > time_1)
                & (symbol_trades["submit_time"] <= time_1 + window)
                & (symbol_trades["side"] == opposite_side)
                & (symbol_trades["account"] == cp_1)
            ]

            for _, trade2 in candidates.iterrows():
                time_2 = trade2["submit_time"]
                cp_2 = str(trade2.get("counterparty", "")).strip()

                if cp_2 != account_a:
                    continue

                reverse_candidates = symbol_trades[
                    (symbol_trades["submit_time"] > time_2)
                    & (symbol_trades["submit_time"] <= time_2 + window)
                    & (symbol_trades["side"] == opposite_side)
                    & (symbol_trades["account"] == account_a)
                ]

                if reverse_candidates.empty:
                    continue

                trade3 = reverse_candidates.iloc[0]

                price_1 = trade1["price"]
                price_3 = trade3["price"]
                price_diff_pct = abs(price_1 - price_3) / price_1

                if price_diff_pct > WASH_TRADING["price_similarity_tolerance"]:
                    continue

                round_trip_seconds = (trade3["submit_time"] - time_1).total_seconds()
                speed_component = max(0.0, 1 - round_trip_seconds / WASH_TRADING["max_round_trip_seconds"])
                price_component = max(0.0, 1 - price_diff_pct / WASH_TRADING["price_similarity_tolerance"])
                volume_component = min(1.0, trade1["volume"] / 300)
                score = round((speed_component * 35) + (price_component * 30) + (volume_component * 15) + 20, 2)

                alerts.append({
                    "alert_id": f"WSH_{trade1['order_id']}_{trade3['order_id']}",
                    "typology": "WASH_TRADING",
                    "account": account_a,
                    "account_a": account_a,
                    "account_b": cp_1,
                    "symbol": symbol,
                    "trade_1_id": trade1["order_id"],
                    "trade_2_id": trade2["order_id"],
                    "trade_3_id": trade3["order_id"],
                    "volume": int(trade1["volume"]),
                    "price_similarity_pct": round((1 - price_diff_pct) * 100, 4),
                    "round_trip_seconds": round(round_trip_seconds, 2),
                    "risk_score": score,
                    "ground_truth": trade1.get("abuse_type", "UNKNOWN"),
                })

                break

    result = pd.DataFrame(alerts)
    if not result.empty:
        result = result.drop_duplicates(subset=["alert_id"])

    return result