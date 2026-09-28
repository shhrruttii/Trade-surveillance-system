import streamlit as st
import pandas as pd
import plotly.express as px
import os

THEMES = {
    "Corporate Blue": {
        "bg": "#F8F9FB", "sidebar_bg": "#1F4E79", "sidebar_text": "#FFFFFF",
        "accent": "#1F4E79", "text": "#1A1A1A", "card_bg": "#FFFFFF",
        "card_border": "#D8DEE6",
        "chart_sequence": px.colors.qualitative.Set2,
        "priority_map": {"HIGH": "#d9534f", "MEDIUM": "#f0ad4e", "LOW": "#5bc0de"},
    },
    "Dark Mode": {
        "bg": "#0E1117", "sidebar_bg": "#000000", "sidebar_text": "#E0E0E0",
        "accent": "#00C8B4", "text": "#E8E8E8", "card_bg": "#1A1F2C",
        "card_border": "#2A3140",
        "chart_sequence": px.colors.qualitative.Bold,
        "priority_map": {"HIGH": "#FF5252", "MEDIUM": "#FFB74D", "LOW": "#4FC3F7"},
    },
    "Trading Terminal": {
        "bg": "#000000", "sidebar_bg": "#111111", "sidebar_text": "#00FF88",
        "accent": "#00FF88", "text": "#D0D0D0", "card_bg": "#0F0F0F",
        "card_border": "#1F3F2F",
        "chart_sequence": ["#00FF88", "#00CCFF", "#FFB800", "#FF4D4D"],
        "priority_map": {"HIGH": "#FF4D4D", "MEDIUM": "#FFB800", "LOW": "#00CCFF"},
    },
    "Warm Analyst": {
        "bg": "#FFFBF5", "sidebar_bg": "#8B5A3C", "sidebar_text": "#FFF5E9",
        "accent": "#C4704D", "text": "#3A2A1F", "card_bg": "#FFFFFF",
        "card_border": "#E8D5C0",
        "chart_sequence": px.colors.qualitative.Pastel,
        "priority_map": {"HIGH": "#C62828", "MEDIUM": "#EF6C00", "LOW": "#558B2F"},
    },
    "Regulatory Clean": {
        "bg": "#FAFAFA", "sidebar_bg": "#F0F0F0", "sidebar_text": "#333333",
        "accent": "#444444", "text": "#222222", "card_bg": "#FFFFFF",
        "card_border": "#CCCCCC",
        "chart_sequence": ["#333333", "#666666", "#999999", "#BBBBBB"],
        "priority_map": {"HIGH": "#B71C1C", "MEDIUM": "#E65100", "LOW": "#33691E"},
    },
}


@st.cache_data
def load_alerts():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "..", "outputs", "alerts.csv")
    df = pd.read_csv(path)
    for col in ["cancel_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def render():
    st.sidebar.divider()
    st.sidebar.header("Appearance")
    theme_name = st.sidebar.selectbox("Theme", options=list(THEMES.keys()), index=0)
    theme = THEMES[theme_name]

    st.markdown(f"""
    <style>
        .stApp {{ background-color: {theme["bg"]}; color: {theme["text"]}; }}
        section[data-testid="stSidebar"] {{ background-color: {theme["sidebar_bg"]}; }}
        section[data-testid="stSidebar"] * {{ color: {theme["sidebar_text"]} !important; }}
        h1, h2, h3 {{ color: {theme["text"]} !important; }}
        div[data-testid="stMetric"] {{
            background-color: {theme["card_bg"]};
            border: 1px solid {theme["card_border"]};
            border-radius: 10px; padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        div[data-testid="stMetric"] label {{ color: {theme["text"]} !important; }}
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
            color: {theme["accent"]} !important; font-weight: 700;
        }}
        .stButton > button, .stDownloadButton > button {{
            background-color: {theme["accent"]};
            color: {theme["card_bg"]};
            border: none; border-radius: 6px; font-weight: 600;
        }}
        div[data-testid="stDataFrame"] {{
            background-color: {theme["card_bg"]};
            border: 1px solid {theme["card_border"]};
            border-radius: 8px;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.title("Trade Surveillance Alert Console")
    st.caption("Market Abuse Typology Detection | Spoofing · Layering · Wash Trading")

    try:
        alerts = load_alerts()
    except FileNotFoundError:
        st.error("No alert data found. Run `python run.py` first.")
        st.stop()

    st.sidebar.divider()
    st.sidebar.header("Filters")

    typology_filter = st.sidebar.multiselect(
        "Typology",
        options=sorted(alerts["typology"].unique()),
        default=sorted(alerts["typology"].unique()),
    )
    priority_filter = st.sidebar.multiselect(
        "Priority",
        options=["HIGH", "MEDIUM", "LOW"],
        default=["HIGH", "MEDIUM", "LOW"],
    )
    if "account" in alerts.columns:
        account_filter = st.sidebar.multiselect(
            "Account",
            options=sorted(alerts["account"].dropna().unique()),
            default=sorted(alerts["account"].dropna().unique()),
        )
    else:
        account_filter = None

    score_range = st.sidebar.slider("Risk Score Range", 0, 100, (0, 100), 5)

    filtered = alerts[
        (alerts["typology"].isin(typology_filter))
        & (alerts["priority"].isin(priority_filter))
        & (alerts["risk_score"] >= score_range[0])
        & (alerts["risk_score"] <= score_range[1])
    ]
    if account_filter is not None:
        filtered = filtered[filtered["account"].isin(account_filter)]

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Alerts", len(filtered))
    with col2:
        st.metric("High Priority", (filtered["priority"] == "HIGH").sum())
    with col3:
        st.metric("Spoofing", (filtered["typology"] == "SPOOFING").sum())
    with col4:
        st.metric("Layering", (filtered["typology"] == "LAYERING").sum())
    with col5:
        st.metric("Wash Trading", (filtered["typology"] == "WASH_TRADING").sum())

    st.divider()

    if not filtered.empty:
        st.subheader("Drill-Down: Typology → Priority → Alert")
        sunburst_df = filtered.copy()
        sunburst_df["alert_label"] = sunburst_df["alert_id"].astype(str)
        fig = px.sunburst(
            sunburst_df,
            path=["typology", "priority", "alert_label"],
            color="risk_score",
            color_continuous_scale="RdYlGn_r",
        )
        fig.update_layout(
            paper_bgcolor=theme["card_bg"],
            plot_bgcolor=theme["card_bg"],
            font_color=theme["text"],
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if not filtered.empty:
            fig = px.pie(
                filtered, names="typology", title="Alerts by Typology",
                color_discrete_sequence=theme["chart_sequence"], hole=0.4,
            )
            fig.update_layout(
                paper_bgcolor=theme["card_bg"],
                plot_bgcolor=theme["card_bg"],
                font_color=theme["text"],
            )
            st.plotly_chart(fig, use_container_width=True)
    with col_c2:
        if not filtered.empty:
            fig = px.bar(
                filtered.groupby(["typology", "priority"]).size().reset_index(name="count"),
                x="typology", y="count", color="priority",
                title="Alerts by Typology and Priority",
                color_discrete_map=theme["priority_map"],
                barmode="stack",
            )
            fig.update_layout(
                paper_bgcolor=theme["card_bg"],
                plot_bgcolor=theme["card_bg"],
                font_color=theme["text"],
            )
            st.plotly_chart(fig, use_container_width=True)

    if "cancel_time" in filtered.columns and filtered["cancel_time"].notna().any():
        st.divider()
        st.subheader("Alert Trend Over Time")
        trend_df = filtered.dropna(subset=["cancel_time"]).copy()
        trend_df["bucket"] = trend_df["cancel_time"].dt.floor("5min")
        trend = trend_df.groupby(["bucket", "typology"]).size().reset_index(name="count")
        if not trend.empty:
            fig = px.line(
                trend, x="bucket", y="count", color="typology",
                markers=True, color_discrete_sequence=theme["chart_sequence"],
            )
            fig.update_layout(
                paper_bgcolor=theme["card_bg"],
                plot_bgcolor=theme["card_bg"],
                font_color=theme["text"],
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader(f"Alert Queue ({len(filtered)} alerts)")
    st.dataframe(
        filtered.sort_values("risk_score", ascending=False),
        use_container_width=True, height=400,
    )

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Filtered Alerts as CSV", csv,
        file_name="filtered_alerts.csv", mime="text/csv",
    )