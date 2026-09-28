import pandas as pd


def generate_excel_report(alerts_df: pd.DataFrame, output_path: str):
    if alerts_df.empty:
        print("No alerts to report.")
        return

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        workbook = writer.book

        alert_sheet = alerts_df.copy()
        alert_sheet.to_excel(writer, sheet_name="Alert Queue", index=False)

        worksheet = writer.sheets["Alert Queue"]
        header_format = workbook.add_format({
            "bold": True, "bg_color": "#1F4E79", "font_color": "white",
            "border": 1, "text_wrap": True
        })

        for col_num, col_name in enumerate(alert_sheet.columns):
            worksheet.write(0, col_num, col_name, header_format)
            worksheet.set_column(col_num, col_num, max(12, len(str(col_name)) + 2))

        if "risk_score" in alert_sheet.columns:
            score_col = alert_sheet.columns.get_loc("risk_score")
            worksheet.conditional_format(
                1, score_col, len(alert_sheet), score_col,
                {
                    "type": "3_color_scale",
                    "min_color": "#63BE7B",
                    "mid_color": "#FFEB84",
                    "max_color": "#F8696B",
                }
            )

        if "priority" in alert_sheet.columns:
            priority_col = alert_sheet.columns.get_loc("priority")
            worksheet.conditional_format(
                1, priority_col, len(alert_sheet), priority_col,
                {
                    "type": "text",
                    "criteria": "containing",
                    "value": "HIGH",
                    "format": workbook.add_format({"bg_color": "#F8696B", "bold": True}),
                }
            )
            worksheet.conditional_format(
                1, priority_col, len(alert_sheet), priority_col,
                {
                    "type": "text",
                    "criteria": "containing",
                    "value": "MEDIUM",
                    "format": workbook.add_format({"bg_color": "#FFEB84"}),
                }
            )

        pivot_typology = alerts_df.groupby("typology").agg(
            alert_count=("alert_id", "count"),
            avg_risk_score=("risk_score", "mean"),
            max_risk_score=("risk_score", "max"),
        ).round(2).reset_index()
        pivot_typology.to_excel(writer, sheet_name="Pivot - Typology", index=False)

        pivot_account = alerts_df.groupby("account").agg(
            alert_count=("alert_id", "count"),
            avg_risk_score=("risk_score", "mean"),
            high_priority_count=("priority", lambda x: (x == "HIGH").sum()),
        ).round(2).reset_index().sort_values("alert_count", ascending=False)
        pivot_account.to_excel(writer, sheet_name="Pivot - Account", index=False)

        pivot_priority = alerts_df.groupby("priority").agg(
            alert_count=("alert_id", "count"),
            avg_risk_score=("risk_score", "mean"),
        ).round(2).reset_index()
        pivot_priority.to_excel(writer, sheet_name="Pivot - Priority", index=False)

        summary_data = {
            "Metric": [
                "Total Alerts", "High Priority", "Medium Priority", "Low Priority",
                "Spoofing Alerts", "Layering Alerts", "Wash Trading Alerts",
                "Avg Risk Score", "Max Risk Score",
            ],
            "Value": [
                len(alerts_df),
                (alerts_df["priority"] == "HIGH").sum(),
                (alerts_df["priority"] == "MEDIUM").sum(),
                (alerts_df["priority"] == "LOW").sum(),
                (alerts_df["typology"] == "SPOOFING").sum(),
                (alerts_df["typology"] == "LAYERING").sum(),
                (alerts_df["typology"] == "WASH_TRADING").sum(),
                round(alerts_df["risk_score"].mean(), 2),
                round(alerts_df["risk_score"].max(), 2),
            ],
        }
        pd.DataFrame(summary_data).to_excel(
            writer, sheet_name="Summary", index=False
        )

    print(f"Excel report saved to: {output_path}")