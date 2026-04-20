import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

LOG_FILE = Path("data/logs.jsonl")

st.set_page_config(page_title="AI System Observability Dashboard", layout="wide")
st.markdown(
    "<h1 style='text-align: center;'>AI System Observability Dashboard</h1>",
    unsafe_allow_html=True
)

# auto refresh mỗi 15s
st_autorefresh(interval=15_000, key="dashboard_refresh")
st.caption("Auto refresh mỗi 15s | Default time range: 1 hour")


def load_logs() -> pd.DataFrame:
    if not LOG_FILE.exists():
        return pd.DataFrame()

    rows = []
    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    defaults = {
        "latency_ms": 0.0,
        "status_code": 200,
        "cost_usd": 0.0,
        "tokens_in": 0,
        "tokens_out": 0,
        "quality_score": 0.0,
        "route": "unknown",
    }

    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    if "ts" not in df.columns:
        st.error("Log thiếu field `ts`, dashboard không thể vẽ theo thời gian.")
        st.stop()

    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts")

    df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce").fillna(0)
    df["status_code"] = pd.to_numeric(df["status_code"], errors="coerce").fillna(200).astype(int)
    df["cost_usd"] = pd.to_numeric(df["cost_usd"], errors="coerce").fillna(0.0)
    df["tokens_in"] = pd.to_numeric(df["tokens_in"], errors="coerce").fillna(0).astype(int)
    df["tokens_out"] = pd.to_numeric(df["tokens_out"], errors="coerce").fillna(0).astype(int)
    df["quality_score"] = pd.to_numeric(df["quality_score"], errors="coerce").fillna(0.0)

    return df


def safe_percentile(series: pd.Series, q: float) -> float:
    if series.empty:
        return 0.0
    return float(np.percentile(series, q))


df = load_logs()

if df.empty:
    st.warning("Chưa có dữ liệu trong data/logs.jsonl")
    st.stop()

df = ensure_columns(df)

if df.empty:
    st.warning("Không có log hợp lệ để hiển thị.")
    st.stop()

latest_ts = df["ts"].max()
window_start = latest_ts - pd.Timedelta(hours=1)
last_1h = df[df["ts"] >= window_start].copy()

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown(
        f"""
        <div style='text-align:center; padding:10px; border-radius:10px; background-color:#f5f5f5;'>
            <div style='font-size:12px; color:gray;'>Last log time</div>
            <div style='font-size:14px; font-weight:600;'>{latest_ts}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_b:
    st.markdown(
        f"""
        <div style='text-align:center; padding:10px; border-radius:10px; background-color:#f5f5f5;'>
            <div style='font-size:12px; color:gray;'>Total logs</div>
            <div style='font-size:18px; font-weight:600;'>{len(df)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_c:
    st.markdown(
        f"""
        <div style='text-align:center; padding:10px; border-radius:10px; background-color:#f5f5f5;'>
            <div style='font-size:12px; color:gray;'>Logs (last 1h)</div>
            <div style='font-size:18px; font-weight:600;'>{len(last_1h)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

if last_1h.empty:
    st.warning("Không có dữ liệu trong 1 giờ gần nhất.")
    st.stop()

# SLO tham khảo
LATENCY_SLO_MS = 2000
ERROR_SLO_PERCENT = 5

# ===== Hàng 1 =====
col1, col2 = st.columns(2)

with col1:
    st.subheader("Latency P50 / P95 / P99")

    p50 = safe_percentile(last_1h["latency_ms"], 50)
    p95 = safe_percentile(last_1h["latency_ms"], 95)
    p99 = safe_percentile(last_1h["latency_ms"], 99)

    m1, m2, m3 = st.columns(3)
    m1.metric("P50", f"{p50:.1f} ms")
    m2.metric("P95", f"{p95:.1f} ms", delta=f"{p95 - LATENCY_SLO_MS:.1f} ms vs SLO")
    m3.metric("P99", f"{p99:.1f} ms")

    latency_ts = last_1h.set_index("ts")["latency_ms"].resample("1min").mean().fillna(0)
    st.line_chart(latency_ts)

    if p95 > LATENCY_SLO_MS:
        st.error(f"P95 latency vượt SLO {LATENCY_SLO_MS} ms")
    else:
        st.success(f"P95 latency đang trong SLO {LATENCY_SLO_MS} ms")

with col2:
    st.subheader("Traffic (requests/min)")

    traffic = last_1h.set_index("ts").resample("1min").size()
    st.metric("Total Requests (1h)", int(len(last_1h)))
    st.line_chart(traffic)

# ===== Hàng 2 =====
col3, col4 = st.columns(2)

with col3:
    st.subheader("Error Rate with Breakdown")

    errors = last_1h[last_1h["status_code"] >= 400]
    error_rate = (len(errors) / len(last_1h) * 100) if len(last_1h) else 0.0

    st.metric("Error Rate", f"{error_rate:.2f}%")

    status_counts = last_1h["status_code"].value_counts().sort_index()
    st.bar_chart(status_counts)

    if error_rate > ERROR_SLO_PERCENT:
        st.error(f"Error rate vượt SLO {ERROR_SLO_PERCENT}%")
    else:
        st.success(f"Error rate đang trong SLO {ERROR_SLO_PERCENT}%")

with col4:
    st.subheader("Cost over Time")

    total_cost = float(last_1h["cost_usd"].sum())
    st.metric("Total Cost (1h)", f"${total_cost:.4f}")

    cost_ts = last_1h.set_index("ts")["cost_usd"].resample("1min").sum().fillna(0)
    st.line_chart(cost_ts)

# ===== Hàng 3 =====
col5, col6 = st.columns(2)

with col5:
    st.subheader("Tokens In / Out")

    tokens_in_total = int(last_1h["tokens_in"].sum())
    tokens_out_total = int(last_1h["tokens_out"].sum())

    m1, m2 = st.columns(2)
    m1.metric("Tokens In", tokens_in_total)
    m2.metric("Tokens Out", tokens_out_total)

    tokens_ts = (
        last_1h.set_index("ts")[["tokens_in", "tokens_out"]]
        .resample("1min")
        .sum()
        .fillna(0)
    )
    st.line_chart(tokens_ts)

with col6:
    st.subheader("Quality Proxy")

    avg_quality = float(last_1h["quality_score"].mean()) if len(last_1h) else 0.0
    bad_quality_rate = float((last_1h["quality_score"] <= 0).mean() * 100) if len(last_1h) else 0.0

    m1, m2 = st.columns(2)
    m1.metric("Avg Quality", f"{avg_quality:.2f}")
    m2.metric("Bad Quality Rate", f"{bad_quality_rate:.2f}%")

    quality_ts = last_1h.set_index("ts")["quality_score"].resample("1min").mean().fillna(0)
    st.line_chart(quality_ts)

# ===== Breakdown thêm =====
st.subheader("Route Breakdown")
route_counts = last_1h["route"].value_counts()
st.bar_chart(route_counts)

# ===== Raw logs =====
st.subheader("Raw Logs (last 50 rows)")
display_df = (
    last_1h.sort_values("ts", ascending=False)
    .head(50)
    .copy()
)
st.dataframe(display_df, use_container_width=True)