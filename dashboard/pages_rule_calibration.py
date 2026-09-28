import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.spoofing_detector import detect_spoofing
from src.layering_detector import detect_layering
from src.wash_trade_detector import detect_wash_trades
from src import config


@st.cache_data
def load_orders():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "..", "data", "orders.csv")
    return pd.read_csv(path)


def render():
    st.title("⚙️ Rule Calibration Console")
    st.caption(
        "Tune detection thresholds live. Alert counts recompute in real time. "
        "This mirrors the calibration work surveillance analysts perform daily."
    )

    orders = load_orders()

    st.sidebar.divider()
    st.sidebar.header("Spoofing Rules")
    sp_lifetime = st.sidebar.slider(
        "Max Order Lifetime (sec)", 0.1, 5.0,
        float(config.SPOOFING["max_order_lifetime_seconds"]), 0.1
    )
    sp_size_ratio = st.sidebar.slider(
        "Min Cancel/Exec Size Ratio", 1.0, 20.0,
        float(config.SPOOFING["min_size_ratio_cancel_to_exec"]), 0.5
    )
    sp_min_vol = st.sidebar.slider(
        "Min Cancelled Volume", 50, 2000,
        int(config.SPOOFING["min_cancelled_volume"]), 50
    )

    st.sidebar.header("Layering Rules")
    ly_levels = st.sidebar.slider(
        "Min Price Levels", 2, 8,
        int(config.LAYERING["min_price_levels"]), 1
    )
    ly_cancel_window = st.sidebar.slider(
        "Max Cancel Window (sec)", 0.5, 10.0,
        float(config.LAYERING["max_cancellation_window_seconds"]), 0.5
    )

    st.sidebar.header("Wash Trading Rules")
    wt_window = st.sidebar.slider(
        "Max Round-Trip (sec)", 10, 120,
        int(config.WASH_TRADING["max_round_trip_seconds"]), 5
    )
    wt_price_tol = st.sidebar.slider(
        "Price Tolerance", 0.0001, 0.05,
        float(config.WASH_TRADING["price_similarity_tolerance"]),
        0.0001, format="%.4f"
    )

    config.SPOOFING["max_order_lifetime_seconds"] = sp_lifetime
    config.SPOOFING["min_size_ratio_cancel_to_exec"] = sp_size_ratio
    config.SPOOFING["min_cancelled_volume"] = sp_min_vol
    config.LAYERING["min_price_levels"] = ly_levels
    config.LAYERING["max_cancellation_window_seconds"] = ly_cancel_window
    config.WASH_TRADING["max_round_trip_seconds"] = wt_window
    config.WASH_TRADING["price_similarity_tolerance"] = wt_price_tol

    sp = detect_spoofing(orders)
    ly = detect_layering(orders)
    wt = detect_wash_trades(orders)

    st.subheader("Live Alert Counts")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Spoofing", len(sp))
    c2.metric("Layering", len(ly))
    c3.metric("Wash Trading", len(wt))
    c4.metric("Total", len(sp) + len(ly) + len(wt))

    st.divider()
    st.subheader("Sensitivity Analysis")
    st.caption("How alert counts respond as you vary a single threshold.")

    tab1, tab2, tab3 = st.tabs(["Spoofing", "Layering", "Wash Trading"])

    with tab1:
        rows = []
        for lt in [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]:
            config.SPOOFING["max_order_lifetime_seconds"] = lt
            rows.append({"Lifetime (sec)": lt, "Alerts": len(detect_spoofing(orders))})
        config.SPOOFING["max_order_lifetime_seconds"] = sp_lifetime
        df = pd.DataFrame(rows)
        fig = px.line(df, x="Lifetime (sec)", y="Alerts", markers=True,
                      title="Spoofing Alerts vs Order Lifetime")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        rows = []
        for lv in [2, 3, 4, 5, 6]:
            config.LAYERING["min_price_levels"] = lv
            rows.append({"Min Levels": lv, "Alerts": len(detect_layering(orders))})
        config.LAYERING["min_price_levels"] = ly_levels
        df = pd.DataFrame(rows)
        fig = px.line(df, x="Min Levels", y="Alerts", markers=True,
                      title="Layering Alerts vs Minimum Price Levels")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        rows = []
        for w in [10, 20, 30, 45, 60, 90, 120]:
            config.WASH_TRADING["max_round_trip_seconds"] = w
            rows.append({"Round Trip (sec)": w, "Alerts": len(detect_wash_trades(orders))})
        config.WASH_TRADING["max_round_trip_seconds"] = wt_window
        df = pd.DataFrame(rows)
        fig = px.line(df, x="Round Trip (sec)", y="Alerts", markers=True,
                      title="Wash Trading Alerts vs Round-Trip Window")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Current Thresholds")
    st.json({
        "spoofing": config.SPOOFING,
        "layering": config.LAYERING,
        "wash_trading": config.WASH_TRADING,
    })