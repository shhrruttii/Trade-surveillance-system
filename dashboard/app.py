import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Trade Surveillance Console", layout="wide")

st.title("Trade Surveillance Alert Console")
st.caption("Market Abuse Typology Detection | Spoofing - Layering - Wash Trading")


@st.cache_data
def load_alerts():
    return pd.read_csv("outputs/alerts.csv")


try:
    alerts = load_alerts()
except FileNotFoundError:
    st.error("No alert data found. Run `python run.py` first.")
    st.stop()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Alerts", len(alerts))
with col2:
    st.metric("High Priority", (alerts["priority"] == "HIGH").sum())
with col3:
    st.metric("Spoofing", (alerts["typology"] == "SPOOFING").sum())
with col4:
    st.metric("Layering", (alerts["typology"] == "LAYERING").sum())
with col5:
    st.metric("Wash Trading", (alerts["typology"] == "WASH_TRADING").sum())

st.divider()

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    typology_filter = st.multiselect(
        "Typology",
        options=alerts["typology"].unique(),
        default=alerts["typology"].unique(),
    )
with col_f2:
    priority_filter = st.multiselect(
        "Priority",
        options=["HIGH", "MEDIUM", "LOW"],
        default=["HIGH", "MEDIUM", "LOW"],
    )
with col_f3:
    min_score = st.slider("Minimum Risk Score", 0, 100, 0, 5)

filtered = alerts[
    (alerts["typology"].isin(typology_filter))
    & (alerts["priority"].isin(priority_filter))
    & (alerts["risk_score"] >= min_score)
]

st.divider()

col_c1, col_c2 = st.columns(2)

with col_c1:
    fig_typology = px.pie(
        filtered, names="typology", title="Alerts by Typology",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    st.plotly_chart(fig_typology, use_container_width=True)

with col_c2:
    fig_priority = px.bar(
        filtered.groupby(["typology", "priority"]).size().reset_index(name="count"),
        x="typology", y="count", color="priority",
        title="Alerts by Typology and Priority",
        color_discrete_map={"HIGH": "#d9534f", "MEDIUM": "#f0ad4e", "LOW": "#5bc0de"},
    )
    st.plotly_chart(fig_priority, use_container_width=True)

st.subheader("Alert Queue")
st.dataframe(
    filtered.sort_values("risk_score", ascending=False),
    use_container_width=True,
    height=400,
)