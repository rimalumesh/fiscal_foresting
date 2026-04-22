import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from io import BytesIO

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FCGO Fiscal Dashboard",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 FCGO Fiscal Revenue Dashboard")

# ── Load data from private GitHub repo ────────────────────────────────────────
GITHUB_USER   = "rimalumesh"
GITHUB_REPO   = "fiscal_foresting"
GITHUB_BRANCH = "main"
EXCEL_FILE    = "fiscal_dashboard_data.xlsx"
GITHUB_TOKEN  = st.secrets["GITHUB_TOKEN"]

@st.cache_data(ttl=3600)
def load_data():
    url = (
        f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}"
        f"/contents/{EXCEL_FILE}?ref={GITHUB_BRANCH}"
    )
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw",
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    df = pd.read_excel(BytesIO(resp.content))

    # ── Clean numeric columns ──────────────────────────────────────────────────
    exclude = ["nepali_date", "english_date", "np_date",
               "fiscal_year", "day_of_year", "name_of_the_day"]
    num_cols = [c for c in df.columns if c not in exclude]
    df[num_cols] = (
        df[num_cols]
        .astype(str)
        .replace({",": "", " ": "", "%": ""}, regex=True)
    )
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")

    # ── Filter current fiscal year ─────────────────────────────────────────────
    df = df[df["fiscal_year"] == "2082_83"].copy()
    df = df.iloc[4:].reset_index(drop=True)

    # ── Forward-fill zeros for percentage columns ──────────────────────────────
    pct_cols = ["total_revenue_percentage", "total_expenditure_percentage",
                "tax_percentage"]
    df[pct_cols] = df[pct_cols].replace(0, np.nan)
    df[pct_cols] = df[pct_cols].ffill()

    return df

df = load_data()

# ── Identify latest two rows ───────────────────────────────────────────────────
latest      = df.iloc[-1]
day_before  = df.iloc[-2]

latest_label     = str(latest["nepali_date"])
day_before_label = str(day_before["nepali_date"])

# ── Summary Table ──────────────────────────────────────────────────────────────
st.subheader("📋 Revenue Summary")

def fmt(val):
    """Format large numbers with commas."""
    try:
        return f"{float(val):,.2f}"
    except:
        return val

table_data = {
    ("", "Metric"): ["Tax Revenue", "Total Revenue"],

    (day_before_label, "Actual"): [
        fmt(day_before["tax_upto_today"]),
        fmt(day_before["total_revenue_upto_today"]),
    ],
    (day_before_label, "Target"): [
        fmt(day_before["tax_target"]),
        fmt(day_before["total_revenue_target"]),
    ],

    (latest_label, "Actual"): [
        fmt(latest["tax_upto_today"]),
        fmt(latest["total_revenue_upto_today"]),
    ],
    (latest_label, "Target"): [
        fmt(latest["tax_target"]),
        fmt(latest["total_revenue_target"]),
    ],
}

summary_df = pd.DataFrame(table_data)
summary_df.columns = pd.MultiIndex.from_tuples(summary_df.columns)
summary_df = summary_df.set_index(("", "Metric"))
summary_df.index.name = None

st.dataframe(summary_df, use_container_width=True)

# ── Achievement % cards ────────────────────────────────────────────────────────
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
col1.metric(
    label=f"Tax Achievement ({latest_label})",
    value=f"{latest['tax_percentage']:.1f}%",
)
col2.metric(
    label=f"Total Revenue Achievement ({latest_label})",
    value=f"{latest['total_revenue_percentage']:.1f}%",
)
col3.metric(
    label=f"Tax Achievement ({day_before_label})",
    value=f"{day_before['tax_percentage']:.1f}%",
)
col4.metric(
    label=f"Total Revenue Achievement ({day_before_label})",
    value=f"{day_before['total_revenue_percentage']:.1f}%",
)

# ── Line Chart ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📈 Actual vs Target Total Revenue (% of Annual Target)")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["day_of_year"],
    y=df["total_revenue_percentage"],
    name="Actual Revenue %",
    mode="lines+markers",
    line=dict(color="#2ecc71", width=2),
    marker=dict(size=4),
    hovertemplate="Day %{x}<br>Actual: %{y:.2f}%<extra></extra>",
))

fig.add_trace(go.Scatter(
    x=df["day_of_year"],
    y=[100] * len(df),           # straight 100% target line
    name="Target (100%)",
    mode="lines",
    line=dict(color="#e74c3c", width=2, dash="dash"),
    hovertemplate="Day %{x}<br>Target: 100%<extra></extra>",
))

fig.update_layout(
    xaxis_title="Day of Fiscal Year",
    yaxis_title="% of Annual Target",
    hovermode="x unified",
    legend=dict(orientation="h", y=1.08),
    height=450,
    margin=dict(l=40, r=20, t=40, b=40),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=True, gridcolor="#eee"),
    yaxis=dict(showgrid=True, gridcolor="#eee"),
)

st.plotly_chart(fig, use_container_width=True)

st.caption("Data source: FCGO (fcgo.gov.np) | Fiscal Year 2082/83")
