import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import yaml
from streamlit_autorefresh import st_autorefresh

LOG_FILE = Path("data/logs.jsonl")
ALERT_RULES_FILE = Path("config/alert_rules.yaml")

st.set_page_config(page_title="AI System Observability Dashboard", layout="wide")
st.markdown(
    "<h1 style='text-align: center;'>AI System Observability Dashboard</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: gray;'>Default time range: 1 hour</p>",
    unsafe_allow_html=True,
)

st_autorefresh(interval=15_000, key="dashboard_refresh")


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

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def load_alert_rules() -> dict:
    default_rules = {
        "latency_p95_ms": {
            "threshold": 2000,
            "severity": "warning",
            "message": "High latency",
        },
        "error_rate_percent": {
            "threshold": 5.0,
            "severity": "critical",
            "message": "High error rate",
        },
        "bad_quality_rate_percent": {
            "threshold": 20.0,
            "severity": "warning",
            "message": "Quality degraded",
        },
    }

    if not ALERT_RULES_FILE.exists():
        return default_rules

    try:
        with ALERT_RULES_FILE.open("r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
    except Exception:
        return default_rules

    if "alerts" in loaded and isinstance(loaded["alerts"], dict):
        loaded = loaded["alerts"]

    merged = default_rules.copy()
    for key, default_value in default_rules.items():
        if key in loaded and isinstance(loaded[key], dict):
            merged[key] = {**default_value, **loaded[key]}

    return merged


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    if "ts" not in df.columns:
        st.error("Log thiếu field `ts`, dashboard không thể vẽ theo thời gian.")
        st.stop()

    df["ts"] = pd.to_datetime(df["ts"], errors="coerce", utc=True)
    df["ts"] = df["ts"].dt.tz_convert("Asia/Ho_Chi_Minh")
    df = df.dropna(subset=["ts"]).sort_values("ts").copy()

    numeric_defaults = {
        "latency_ms": 0.0,
        "status_code": 200,
        "cost_usd": 0.0,
        "tokens_in": 0,
        "tokens_out": 0,
        "quality_score": 0.0,
    }

    text_defaults = {
        "route": "unknown",
        "service": "-",
        "event": "-",
        "feature": "-",
        "method": "-",
        "model": "-",
        "session_id": "-",
        "trace_id": "-",
        "span_id": "-",
        "parent_span_id": "-",
        "correlation_id": "-",
        "level": "-",
    }

    for col, default in numeric_defaults.items():
        if col not in df.columns:
            df[col] = default

    for col, default in text_defaults.items():
        if col not in df.columns:
            df[col] = default

    df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce").fillna(0.0)
    df["status_code"] = pd.to_numeric(df["status_code"], errors="coerce").fillna(200).astype(int)
    df["cost_usd"] = pd.to_numeric(df["cost_usd"], errors="coerce").fillna(0.0)
    df["tokens_in"] = pd.to_numeric(df["tokens_in"], errors="coerce").fillna(0).astype(int)
    df["tokens_out"] = pd.to_numeric(df["tokens_out"], errors="coerce").fillna(0).astype(int)
    df["quality_score"] = pd.to_numeric(df["quality_score"], errors="coerce").fillna(0.0)

    for col, default in text_defaults.items():
        df[col] = df[col].fillna(default).astype(str).str.strip()
        df.loc[df[col] == "", col] = default

    df.loc[df["trace_id"] == "-", "trace_id"] = df.loc[df["trace_id"] == "-", "correlation_id"]

    return df


def safe_percentile(series: pd.Series, q: float) -> float:
    if series.empty:
        return 0.0
    return float(np.percentile(series, q))


def show_alert(metric_value: float, threshold: float, severity: str, ok_text: str, bad_text: str) -> None:
    if metric_value > threshold:
        if severity.lower() == "critical":
            st.error(bad_text)
        elif severity.lower() == "warning":
            st.warning(bad_text)
        else:
            st.info(bad_text)
    else:
        st.success(ok_text)


def build_trace_timeline(trace_df: pd.DataFrame) -> list[str]:
    lines = []
    for _, row in trace_df.iterrows():
        ts_text = row["ts"].strftime("%H:%M:%S") if pd.notna(row["ts"]) else "-"
        lines.append(
            f"{ts_text} | trace_id={row['trace_id']} | span={row['span_id']} | parent={row['parent_span_id']} | service={row['service']} | event={row['event']}"
        )
    return lines


df = load_logs()

if df.empty:
    st.warning("Chưa có dữ liệu trong data/logs.jsonl")
    st.stop()

df = ensure_columns(df)

if df.empty:
    st.warning("Không có log hợp lệ để hiển thị.")
    st.stop()

alert_rules = load_alert_rules()

latest_ts = df["ts"].max()
window_start = latest_ts - pd.Timedelta(hours=1)
last_1h = df[df["ts"] >= window_start].copy()

latest_ts_display = latest_ts.strftime("%Y-%m-%d %H:%M:%S")

if last_1h.empty:
    st.warning("Không có dữ liệu trong 1 giờ gần nhất.")
    st.stop()

LATENCY_SLO_MS = float(alert_rules["latency_p95_ms"]["threshold"])
ERROR_SLO_PERCENT = float(alert_rules["error_rate_percent"]["threshold"])
BAD_QUALITY_SLO_PERCENT = float(alert_rules["bad_quality_rate_percent"]["threshold"])

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown(
        f"""
        <div style='text-align:center; padding:10px; border-radius:10px; background-color:#f5f5f5;'>
            <div style='font-size:12px; color:gray;'>Last log time</div>
            <div style='font-size:14px; font-weight:600;'>{latest_ts_display}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_b:
    st.markdown(
        f"""
        <div style='text-align:center; padding:10px; border-radius:10px; background-color:#f5f5f5;'>
            <div style='font-size:12px; color:gray;'>Total logs</div>
            <div style='font-size:18px; font-weight:600;'>{len(df)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_c:
    st.markdown(
        f"""
        <div style='text-align:center; padding:10px; border-radius:10px; background-color:#f5f5f5;'>
            <div style='font-size:12px; color:gray;'>Logs (last 1h)</div>
            <div style='font-size:18px; font-weight:600;'>{len(last_1h)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

p50 = safe_percentile(last_1h["latency_ms"], 50)
p95 = safe_percentile(last_1h["latency_ms"], 95)
p99 = safe_percentile(last_1h["latency_ms"], 99)

errors = last_1h[last_1h["status_code"] >= 400]
error_rate = (len(errors) / len(last_1h) * 100) if len(last_1h) else 0.0
avg_quality = float(last_1h["quality_score"].mean()) if len(last_1h) else 0.0
bad_quality_rate = float((last_1h["quality_score"] <= 0).mean() * 100) if len(last_1h) else 0.0
total_cost = float(last_1h["cost_usd"].sum())

st.subheader("Alerts")
alert_cols = st.columns(3)

with alert_cols[0]:
    show_alert(
        metric_value=p95,
        threshold=LATENCY_SLO_MS,
        severity=alert_rules["latency_p95_ms"].get("severity", "warning"),
        ok_text=f"Latency healthy: P95 = {p95:.1f} ms",
        bad_text=f"{alert_rules['latency_p95_ms'].get('message', 'High latency')}: P95 = {p95:.1f} ms > {LATENCY_SLO_MS:.1f} ms",
    )

with alert_cols[1]:
    show_alert(
        metric_value=error_rate,
        threshold=ERROR_SLO_PERCENT,
        severity=alert_rules["error_rate_percent"].get("severity", "critical"),
        ok_text=f"Error rate healthy: {error_rate:.2f}%",
        bad_text=f"{alert_rules['error_rate_percent'].get('message', 'High error rate')}: {error_rate:.2f}% > {ERROR_SLO_PERCENT:.2f}%",
    )

with alert_cols[2]:
    show_alert(
        metric_value=bad_quality_rate,
        threshold=BAD_QUALITY_SLO_PERCENT,
        severity=alert_rules["bad_quality_rate_percent"].get("severity", "warning"),
        ok_text=f"Quality healthy: bad quality rate = {bad_quality_rate:.2f}%",
        bad_text=f"{alert_rules['bad_quality_rate_percent'].get('message', 'Quality degraded')}: bad quality rate = {bad_quality_rate:.2f}% > {BAD_QUALITY_SLO_PERCENT:.2f}%",
    )

col1, col2 = st.columns(2)

with col1:
    st.subheader("Latency P50 / P95 / P99")

    m1, m2, m3 = st.columns(3)
    m1.metric("P50", f"{p50:.1f} ms")
    m2.metric("P95", f"{p95:.1f} ms", delta=f"{p95 - LATENCY_SLO_MS:.1f} ms vs alert threshold")
    m3.metric("P99", f"{p99:.1f} ms")

    latency_ts = last_1h.set_index("ts")["latency_ms"].resample("1min").mean().fillna(0)
    st.line_chart(latency_ts)

with col2:
    st.subheader("Traffic (requests/min)")
    st.metric("Total Requests", int(len(df)))
    traffic = last_1h.set_index("ts").resample("1min").size().rename("requests")
    st.bar_chart(traffic)

col3, col4 = st.columns(2)

with col3:
    st.subheader("Error Rate with Breakdown")
    st.metric("Error Rate", f"{error_rate:.2f}%")
    status_counts = last_1h["status_code"].value_counts().sort_index()
    st.bar_chart(status_counts)

with col4:
    st.subheader("Cost over Time")
    cost_ts = last_1h.set_index("ts")["cost_usd"].resample("1min").sum().fillna(0)
    max_cost = float(cost_ts.max()) if not cost_ts.empty else 0.0

    m1, m2 = st.columns(2)
    m1.metric("Total Cost (1h)", f"${total_cost:.4f}")
    m2.metric("Max Cost / min", f"${max_cost:.4f}")

    st.line_chart(cost_ts)

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

    m1, m2 = st.columns(2)
    m1.metric("Avg Quality", f"{avg_quality:.2f}")
    m2.metric("Bad Quality Rate", f"{bad_quality_rate:.2f}%")

    quality_ts = last_1h.set_index("ts")["quality_score"].resample("1min").mean().fillna(0)
    st.line_chart(quality_ts)

st.subheader("Route Breakdown")
route_counts = (
    last_1h["route"]
    .value_counts()
    .rename_axis("route")
    .reset_index(name="count")
    .set_index("route")
)
st.bar_chart(route_counts)

st.subheader("Trace Logs")

trace_source = last_1h.copy()
trace_source = trace_source[trace_source["trace_id"] != "-"].copy()

if trace_source.empty:
    st.info("Chưa có trace log hợp lệ.")
else:
    trace_ids = sorted(trace_source["trace_id"].drop_duplicates().tolist(), reverse=True)

    selected_trace_id = st.selectbox(
        "Chọn trace_id để xem trace",
        options=trace_ids,
        index=0,
    )

    selected_trace = (
        trace_source[trace_source["trace_id"] == selected_trace_id]
        .sort_values(["ts", "service", "event"], ascending=True)
        .copy()
    )

    trace_first_ts = selected_trace["ts"].min()
    trace_last_ts = selected_trace["ts"].max()
    trace_duration_ms = (
        (trace_last_ts - trace_first_ts).total_seconds() * 1000
        if pd.notna(trace_first_ts) and pd.notna(trace_last_ts)
        else 0
    )

    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Trace ID", selected_trace_id)
    tc2.metric("Spans / Logs", len(selected_trace))
    tc3.metric("Trace Window", f"{trace_duration_ms:.1f} ms")

    st.markdown("**Trace Timeline**")
    st.code("\n".join(build_trace_timeline(selected_trace)), language="text")

    trace_columns = [
        col for col in [
            "ts",
            "trace_id",
            "span_id",
            "parent_span_id",
            "service",
            "event",
            "method",
            "route",
            "feature",
            "model",
            "session_id",
            "correlation_id",
            "status_code",
            "latency_ms",
            "tokens_in",
            "tokens_out",
            "cost_usd",
            "quality_score",
            "payload",
            "level",
        ]
        if col in selected_trace.columns
    ]

    st.markdown("**Trace Detail**")
    st.dataframe(selected_trace[trace_columns], use_container_width=True)

st.subheader("Raw Logs")
display_df = (
    last_1h.sort_values("ts", ascending=False)
    .head(200)
    .copy()
)
st.dataframe(display_df, use_container_width=True)