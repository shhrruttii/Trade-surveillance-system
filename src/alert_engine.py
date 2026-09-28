import pandas as pd
from src.spoofing_detector import detect_spoofing
from src.layering_detector import detect_layering
from src.wash_trade_detector import detect_wash_trades
from src.config import PRIORITY


def assign_priority(score: float) -> str:
    if score >= PRIORITY["HIGH"]["min_score"]:
        return "HIGH"
    elif score >= PRIORITY["MEDIUM"]["min_score"]:
        return "MEDIUM"
    else:
        return "LOW"


def run_all_detectors(orders_df: pd.DataFrame) -> pd.DataFrame:
    print("Running Spoofing detector...")
    spoofing_alerts = detect_spoofing(orders_df)
    print(f"  Found {len(spoofing_alerts)} spoofing alerts")

    print("Running Layering detector...")
    layering_alerts = detect_layering(orders_df)
    print(f"  Found {len(layering_alerts)} layering alerts")

    print("Running Wash Trading detector...")
    wash_alerts = detect_wash_trades(orders_df)
    print(f"  Found {len(wash_alerts)} wash trading alerts")

    all_alerts = pd.concat(
        [spoofing_alerts, layering_alerts, wash_alerts],
        ignore_index=True
    )

    if all_alerts.empty:
        return all_alerts

    all_alerts["priority"] = all_alerts["risk_score"].apply(assign_priority)
    all_alerts = all_alerts.sort_values(
        "risk_score", ascending=False
    ).reset_index(drop=True)
    all_alerts.insert(0, "alert_seq", range(1, len(all_alerts) + 1))

    return all_alerts


def print_summary(alerts_df: pd.DataFrame):
    if alerts_df.empty:
        print("\nNo alerts generated.")
        return

    print("\n" + "=" * 60)
    print("ALERT SUMMARY")
    print("=" * 60)
    print(f"\nTotal alerts: {len(alerts_df)}")
    print(f"\nBy typology:")
    print(alerts_df["typology"].value_counts().to_string())
    print(f"\nBy priority:")
    print(alerts_df["priority"].value_counts().to_string())

    if "ground_truth" in alerts_df.columns:
        print(f"\nDetection vs Ground Truth:")
        for typology in alerts_df["typology"].unique():
            subset = alerts_df[alerts_df["typology"] == typology]
            true_positives = (subset["ground_truth"] == typology).sum()
            total = len(subset)
            print(f"  {typology}: {true_positives}/{total} true positives "
                  f"({100*true_positives/total:.1f}%)")