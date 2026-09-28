"""
Generate simulated order and trade data with embedded abuse patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

BASE_PRICE = 100.0
TICK_SIZE = 0.01
SYMBOLS = ["ES_FUT", "NQ_FUT", "CL_FUT"]
ACCOUNTS = [f"ACC_{i:03d}" for i in range(1, 21)]


def generate_normal_orders(n=500):
    orders = []
    start_time = datetime(2024, 1, 15, 9, 30, 0)

    for i in range(n):
        account = np.random.choice(ACCOUNTS)
        symbol = np.random.choice(SYMBOLS)
        side = np.random.choice(["BUY", "SELL"])
        price_offset = np.random.randint(-5, 6) * TICK_SIZE
        price = round(BASE_PRICE + price_offset, 2)
        volume = np.random.randint(10, 100)
        submit_time = start_time + timedelta(seconds=np.random.randint(0, 3600))

        if np.random.random() < 0.8:
            status = "FILLED"
            cancel_time = None
        else:
            status = "CANCELLED"
            cancel_time = submit_time + timedelta(seconds=np.random.randint(5, 60))

        orders.append({
            "order_id": f"ORD_{i:05d}",
            "account": account,
            "symbol": symbol,
            "side": side,
            "price": price,
            "volume": volume,
            "submit_time": submit_time,
            "cancel_time": cancel_time,
            "status": status,
            "abuse_type": "NORMAL",
        })

    return orders


def generate_spoofing_orders(n=15):
    orders = []
    start_time = datetime(2024, 1, 15, 10, 0, 0)

    for i in range(n):
        account = np.random.choice(ACCOUNTS)
        symbol = np.random.choice(SYMBOLS)
        spoof_side = np.random.choice(["BUY", "SELL"])
        opposite_side = "SELL" if spoof_side == "BUY" else "BUY"

        base_time = start_time + timedelta(seconds=i * 60)

        spoof_price = round(BASE_PRICE + (2 if spoof_side == "BUY" else -2) * TICK_SIZE, 2)
        orders.append({
            "order_id": f"SPOOF_{i:05d}_A",
            "account": account,
            "symbol": symbol,
            "side": spoof_side,
            "price": spoof_price,
            "volume": np.random.randint(500, 1500),
            "submit_time": base_time,
            "cancel_time": base_time + timedelta(seconds=np.random.uniform(0.5, 1.8)),
            "status": "CANCELLED",
            "abuse_type": "SPOOFING",
        })

        orders.append({
            "order_id": f"SPOOF_{i:05d}_B",
            "account": account,
            "symbol": symbol,
            "side": opposite_side,
            "price": round(BASE_PRICE, 2),
            "volume": np.random.randint(20, 80),
            "submit_time": base_time + timedelta(seconds=np.random.uniform(1, 3)),
            "cancel_time": None,
            "status": "FILLED",
            "abuse_type": "SPOOFING",
        })

    return orders


def generate_layering_orders(n=10):
    orders = []
    start_time = datetime(2024, 1, 15, 11, 0, 0)

    for i in range(n):
        account = np.random.choice(ACCOUNTS)
        symbol = np.random.choice(SYMBOLS)
        layer_side = np.random.choice(["BUY", "SELL"])
        opposite_side = "SELL" if layer_side == "BUY" else "BUY"

        base_time = start_time + timedelta(seconds=i * 90)

        num_levels = np.random.randint(3, 6)
        cancel_base = base_time + timedelta(seconds=np.random.uniform(1.5, 2.5))

        for level in range(num_levels):
            price_offset = (level + 1) * TICK_SIZE
            price = round(BASE_PRICE + (price_offset if layer_side == "BUY" else -price_offset), 2)

            orders.append({
                "order_id": f"LAYER_{i:05d}_L{level}",
                "account": account,
                "symbol": symbol,
                "side": layer_side,
                "price": price,
                "volume": np.random.randint(80, 200),
                "submit_time": base_time + timedelta(seconds=level * 0.1),
                "cancel_time": cancel_base + timedelta(seconds=level * 0.1),
                "status": "CANCELLED",
                "abuse_type": "LAYERING",
            })

        orders.append({
            "order_id": f"LAYER_{i:05d}_EXEC",
            "account": account,
            "symbol": symbol,
            "side": opposite_side,
            "price": round(BASE_PRICE, 2),
            "volume": np.random.randint(50, 150),
            "submit_time": base_time + timedelta(seconds=3),
            "cancel_time": None,
            "status": "FILLED",
            "abuse_type": "LAYERING",
        })

    return orders


def generate_wash_trades(n=8):
    orders = []
    start_time = datetime(2024, 1, 15, 13, 0, 0)

    for i in range(n):
        account_a = np.random.choice(ACCOUNTS)
        account_b = ACCOUNTS[(ACCOUNTS.index(account_a) + 1) % len(ACCOUNTS)]
        symbol = np.random.choice(SYMBOLS)

        base_time = start_time + timedelta(seconds=i * 120)

        orders.append({
            "order_id": f"WASH_{i:05d}_1A",
            "account": account_a,
            "symbol": symbol,
            "side": "BUY",
            "price": round(BASE_PRICE + np.random.uniform(-0.02, 0.02), 2),
            "volume": np.random.randint(100, 300),
            "submit_time": base_time,
            "cancel_time": None,
            "status": "FILLED",
            "abuse_type": "WASH_TRADING",
            "counterparty": account_b,
        })
        orders.append({
            "order_id": f"WASH_{i:05d}_1B",
            "account": account_b,
            "symbol": symbol,
            "side": "SELL",
            "price": round(BASE_PRICE + np.random.uniform(-0.02, 0.02), 2),
            "volume": np.random.randint(100, 300),
            "submit_time": base_time + timedelta(seconds=0.5),
            "cancel_time": None,
            "status": "FILLED",
            "abuse_type": "WASH_TRADING",
            "counterparty": account_a,
        })

        reverse_time = base_time + timedelta(seconds=np.random.randint(5, 25))
        orders.append({
            "order_id": f"WASH_{i:05d}_2A",
            "account": account_a,
            "symbol": symbol,
            "side": "SELL",
            "price": round(BASE_PRICE + np.random.uniform(-0.02, 0.02), 2),
            "volume": np.random.randint(100, 300),
            "submit_time": reverse_time,
            "cancel_time": None,
            "status": "FILLED",
            "abuse_type": "WASH_TRADING",
            "counterparty": account_b,
        })
        orders.append({
            "order_id": f"WASH_{i:05d}_2B",
            "account": account_b,
            "symbol": symbol,
            "side": "BUY",
            "price": round(BASE_PRICE + np.random.uniform(-0.02, 0.02), 2),
            "volume": np.random.randint(100, 300),
            "submit_time": reverse_time + timedelta(seconds=0.5),
            "cancel_time": None,
            "status": "FILLED",
            "abuse_type": "WASH_TRADING",
            "counterparty": account_a,
        })

    return orders


def main():
    print("Generating simulated order data...")

    all_orders = []
    all_orders.extend(generate_normal_orders(500))
    all_orders.extend(generate_spoofing_orders(15))
    all_orders.extend(generate_layering_orders(10))
    all_orders.extend(generate_wash_trades(8))

    df = pd.DataFrame(all_orders)
    df["counterparty"] = df.get("counterparty", pd.Series([""] * len(df), index=df.index))
    df["counterparty"] = df["counterparty"].fillna("")
    df = df.sort_values("submit_time").reset_index(drop=True)
    df.to_csv("data/orders.csv", index=False)

    print(f"Generated {len(df)} orders")
    print(f"  Normal: {(df['abuse_type'] == 'NORMAL').sum()}")
    print(f"  Spoofing: {(df['abuse_type'] == 'SPOOFING').sum()}")
    print(f"  Layering: {(df['abuse_type'] == 'LAYERING').sum()}")
    print(f"  Wash Trading: {(df['abuse_type'] == 'WASH_TRADING').sum()}")


if __name__ == "__main__":
    main()