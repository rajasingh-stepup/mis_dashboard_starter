import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from dateutil import parser
from datetime import datetime, date
from typing import Dict, List, Tuple

st.set_page_config(page_title="MIS Dashboard", page_icon="📊", layout="wide")

# -----------------------------
# Helpers & State
# -----------------------------

DEFAULT_MAPPING = {
    "date": ["date", "Date", "txn_date"],
    "segment": ["segment", "customer_segment"],
    "region": ["region", "state", "zone"],
    "channel": ["channel", "sales_channel"],
    "product": ["product", "sku", "item_name"],
    "orders": ["orders", "order_count"],
    "units": ["units", "qty", "quantity"],
    "gmv": ["gmv", "gross_sales", "sales_value"],
    "revenue": ["revenue", "net_sales"],
    "cost": ["cost", "cogs", "expenses"],
    "customers": ["customers", "unique_customers", "active_users"],
}

if "mapping" not in st.session_state:
    st.session_state["mapping"] = DEFAULT_MAPPING.copy()

if "df" not in st.session_state:
    st.session_state["df"] = None

# -----------------------------
# Loaders
# -----------------------------

@st.cache_data(show_spinner=False)
def load_data(file) -> pd.DataFrame:
    if file.name.lower().endswith(".csv"):
        df = pd.read_csv(file)
    else:
        # Excel: pick first sheet by default
        df = pd.read_excel(file, sheet_name=0)
    return df

def normalize_columns(df: pd.DataFrame, mapping: Dict[str, List[str]]) -> Tuple[pd.DataFrame, Dict[str,str]]:
    # Build reverse lookup by lower-case
    lower_cols = {c.lower(): c for c in df.columns}
    chosen = {}
    for std_col, candidates in mapping.items():
        found = None
        for cand in candidates:
            key = cand.lower()
            if key in lower_cols:
                found = lower_cols[key]
                break
        chosen[std_col] = found
    # Rename
    rename_map = {v: k for k, v in chosen.items() if v is not None}
    ndf = df.rename(columns=rename_map).copy()
    return ndf, chosen

def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"])
        except Exception:
            # Attempt generic parse
            df["date"] = pd.to_datetime(df["date"].apply(lambda x: parser.parse(str(x), dayfirst=False)), errors="coerce")
    for num_col in ["orders","units","gmv","revenue","cost","customers"]:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")
    return df

def validate_data(df: pd.DataFrame) -> List[str]:
    issues = []
    if "date" not in df.columns:
        issues.append("Missing required column: date")
    if "revenue" not in df.columns and "gmv" not in df.columns:
        issues.append("Need at least one of: revenue or gmv")
    for col in df.columns:
        if df[col].isna().mean() > 0.5:
            issues.append(f"Column '{col}' has >50% missing values")
    return issues

# -----------------------------
# Metrics & Charts
# -----------------------------

def build_kpis(df: pd.DataFrame) -> Dict[str, float]:
    kpis = {}
    kpis["Revenue"] = float(df.get("revenue", pd.Series(dtype=float)).sum()) if "revenue" in df else float(df.get("gmv", pd.Series(dtype=float)).sum())
    kpis["Orders"] = float(df.get("orders", pd.Series(dtype=float)).sum())
    kpis["Units"] = float(df.get("units", pd.Series(dtype=float)).sum())
    kpis["Customers"] = float(df.get("customers", pd.Series(dtype=float)).nunique()) if "customers" in df else np.nan
    if "cost" in df and ("revenue" in df or "gmv" in df):
        sales = df["revenue"] if "revenue" in df else df["gmv"]
        kpis["Gross Margin"] = float((sales - df["cost"]).sum())
        kpis["GM %"] = float(np.round(100 * (1 - (df["cost"].sum() / (sales.sum() or 1))), 2))
    return kpis

def build_charts(df: pd.DataFrame):
    # Timeseries
    c1, c2 = st.columns((2,1))
    with c1:
        if "date" in df and ("revenue" in df or "gmv" in df):
            metric = "revenue" if "revenue" in df else "gmv"
            ts = df.groupby("date", as_index=False)[metric].sum().sort_values("date")
            fig = px.line(ts, x="date", y=metric, markers=True, title="Revenue over time")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        if "orders" in df and "date" in df:
            ts2 = df.groupby("date", as_index=False)["orders"].sum().sort_values("date")
            fig2 = px.bar(ts2, x="date", y="orders", title="Orders per day")
            st.plotly_chart(fig2, use_container_width=True)

    # Breakdown charts
    b1, b2, b3 = st.columns(3)
    metric = "revenue" if "revenue" in df else ("gmv" if "gmv" in df else None)
    if metric:
        if "segment" in df:
            seg = df.groupby("segment", as_index=False)[metric].sum().sort_values(metric, ascending=False)
            b1.plotly_chart(px.pie(seg, names="segment", values=metric, title="Revenue by Segment"), use_container_width=True)
        if "region" in df:
            reg = df.groupby("region", as_index=False)[metric].sum().sort_values(metric, ascending=False)
            b2.plotly_chart(px.bar(reg, x="region", y=metric, title="Revenue by Region"), use_container_width=True)
        if "channel" in df:
            ch = df.groupby("channel", as_index=False)[metric].sum().sort_values(metric, ascending=False)
            b3.plotly_chart(px.bar(ch, x="channel", y=metric, title="Revenue by Channel"), use_container_width=True)

# -----------------------------
# Sidebar - Upload & Filters
# -----------------------------

st.sidebar.header("Upload MIS")
file = st.sidebar.file_uploader("Upload CSV or Excel", type=["csv","xlsx","xls"])

if file:
    raw = load_data(file)
else:
    st.sidebar.info("No file uploaded. Using sample data from assets/sample_mis.csv")
    raw = pd.read_csv("assets/sample_mis.csv")

# Column mapping
with st.expander("🔧 Column Mapping", expanded=False):
    st.caption("Map your MIS columns to standard names. Unmapped columns will be ignored for metrics.")
    mapping = {}
    for std_col, candidates in DEFAULT_MAPPING.items():
        options = ["-- None --"] + list(raw.columns)
        # try auto-detect
        preselect = "-- None --"
        for cand in candidates:
            for real in raw.columns:
                if real.lower() == cand.lower():
                    preselect = real
                    break
            if preselect != "-- None --":
                break
        mapping[std_col] = st.selectbox(f"{std_col} →", options, index=options.index(preselect) if preselect in options else 0, key=f"map_{std_col}")
    # apply
    rename_map = {v: k for k, v in mapping.items() if v and v != "-- None --"}
    df = raw.rename(columns=rename_map).copy()
    df = coerce_types(df)
    st.session_state["df"] = df

# Filters
st.sidebar.header("Filters")
df = st.session_state["df"]
if df is None or df.empty:
    st.error("No data available after mapping.")
    st.stop()

if "date" in df:
    min_d, max_d = pd.to_datetime(df["date"]).min(), pd.to_datetime(df["date"]).max()
    drange = st.sidebar.date_input("Date range", value=(min_d.date(), max_d.date()))
    if isinstance(drange, tuple) and len(drange) == 2:
        df = df[(df["date"] >= pd.to_datetime(drange[0])) & (df["date"] <= pd.to_datetime(drange[1]))]

def multi_filter(col):
    vals = sorted([v for v in df[col].dropna().unique()]) if col in df else []
    picked = st.sidebar.multiselect(col.capitalize(), vals)
    return df[df[col].isin(picked)] if picked else df

for c in ["segment","region","channel","product"]:
    df = multi_filter(c) if c in df else df

# -----------------------------
# Main layout
# -----------------------------
st.title("📊 MIS Dashboard")
issues = validate_data(df)
if issues:
    st.warning("Data quality notes:\n- " + "\n- ".join(issues))

kpis = build_kpis(df)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Revenue", f"{kpis.get('Revenue', 0):,.0f}")
k2.metric("Orders", f"{kpis.get('Orders', 0):,.0f}")
k3.metric("Units", f"{kpis.get('Units', 0):,.0f}")
k4.metric("Customers", f"{kpis.get('Customers', 0):,.0f}" if not np.isnan(kpis.get('Customers', np.nan)) else "—")
gm_pct = kpis.get("GM %", None)
k5.metric("GM %", f"{gm_pct:.1f}%" if gm_pct is not None else "—")

build_charts(df)

st.subheader("Detailed Table")
st.dataframe(df.reset_index(drop=True), use_container_width=True)
st.download_button("⬇️ Download filtered data (CSV)", df.to_csv(index=False), file_name="filtered_mis.csv", mime="text/csv")

st.info("Go to **Report (PPT)** in the left sidebar to export a slide deck of the current filtered view.")