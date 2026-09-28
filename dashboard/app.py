import streamlit as st

st.set_page_config(
    page_title="Trade Surveillance Console",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar page navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["📊 Alert Console", "⚙️ Rule Calibration"],
)

if page == "📊 Alert Console":
    from pages_alert_console import render
    render()
elif page == "⚙️ Rule Calibration":
    from pages_rule_calibration import render
    render()