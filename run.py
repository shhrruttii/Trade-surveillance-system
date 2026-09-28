import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.alert_engine import run_all_detectors, print_summary
from src.excel_report import generate_excel_report


def main():
    print("=" * 60)
    print("STEP 1: Generating simulated order data")
    print("=" * 60)

    if not os.path.exists("data/orders.csv"):
        from data.generate_data import (
            generate_normal_orders, generate_spoofing_orders,
            generate_layering_orders, generate_wash_trades,
        )

        all_orders = []
        all_orders.extend(generate_normal_orders(500))
        all_orders.extend(generate_spoofing_orders(15))
        all_orders.extend(generate_layering_orders(10))
        all_orders.extend(generate_wash_trades(8))

        df = pd.DataFrame(all_orders)
        if "counterparty" not in df.columns:
            df["counterparty"] = ""
        df["counterparty"] = df["counterparty"].fillna("")
        df = df.sort_values("submit_time").reset_index(drop=True)
        df.to_csv("data/orders.csv", index=False)
        print(f"Generated {len(df)} orders -> data/orders.csv")
    else:
        print("Using existing data/orders.csv")

    print("\n" + "=" * 60)
    print("STEP 2: Running detection engines")
    print("=" * 60)

    orders = pd.read_csv("data/orders.csv")
    alerts = run_all_detectors(orders)

    os.makedirs("outputs", exist_ok=True)
    alerts.to_csv("outputs/alerts.csv", index=False)
    print(f"\nSaved {len(alerts)} alerts -> outputs/alerts.csv")

    print_summary(alerts)

    print("\n" + "=" * 60)
    print("STEP 3: Generating Excel analyst report")
    print("=" * 60)

    generate_excel_report(alerts, "outputs/surveillance_report.xlsx")

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print("\nOutputs:")
    print("  - outputs/alerts.csv")
    print("  - outputs/surveillance_report.xlsx")
    print("\nTo run the dashboard:")
    print("  streamlit run dashboard/app.py")


if __name__ == "__main__":
    main()