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

    # Clean numeric columns (same as your table_and_plot.py)
    exclude_cols = ['nepali_date', 'english_date', 'np_date',
                    'fiscal_year', 'day_of_year', 'name_of_the_day']
    cols_to_clean = [c for c in df.columns if c not in exclude_cols]
    df[cols_to_clean] = (
        df[cols_to_clean]
        .astype(str)
        .replace({',': '', ' ': '', '%': ''}, regex=True)
    )
    df[cols_to_clean] = df[cols_to_clean].apply(pd.to_numeric, errors='coerce')

    # Filter current fiscal year
    df = df[df['fiscal_year'] == "2082_83"]
    df = df.iloc[4:].reset_index(drop=True)

    # Forward fill zeros (same as your table_and_plot.py)
    cols = ['total_revenue_percentage', 'total_expenditure_percentage']
    df[cols] = df[cols].replace(0, np.nan)
    df[cols] = df[cols].ffill()

    return df

df = load_data()

# ── Build summary table (exactly your logic from table_and_plot.py) ───────────
last = df.iloc[-1]

summary_table = pd.DataFrame(
    {
        'Target Amount':      [last['total_revenue_target'],     last['total_expenditure_target']],
        'Collection to Date': [last['total_revenue_upto_today'], last['total_expenditure_upto_today']],
        'Percentage':         [last['total_revenue_percentage'], last['total_expenditure_percentage']],
    },
    index=['Revenue', 'Expenditure']
)

# Surplus / Deficit row
surplus_deficit = summary_table.loc['Revenue'] - summary_table.loc['Expenditure']
summary_table.loc['Surplus/Deficit'] = surplus_deficit

# Format numbers
def fmt_num(val):
    try:
        return f"{float(val):,.2f}"
    except:
        return val

display_table = summary_table.copy()
display_table['Target Amount']      = display_table['Target Amount'].apply(fmt_num)
display_table['Collection to Date'] = display_table['Collection to Date'].apply(fmt_num)
display_table['Percentage']         = display_table['Percentage'].apply(
    lambda x: f"{float(x):.2f}%" if pd.notna(x) else x
)

# ── Date context ───────────────────────────────────────────────────────────────
st.caption(
    f"📅 Data as of: **{last['nepali_date']}** (Nepali) | "
    f"**{last['english_date']}** (English) | "
    f"Day **{int(last['day_of_year'])}** of fiscal year"
)

# ── Table ──────────────────────────────────────────────────────────────────────
st.subheader("📋 Revenue & Expenditure Summary")
st.dataframe(display_table, use_container_width=True)

st.markdown("---")

# ── Line Chart (exactly your logic from table_and_plot.py) ────────────────────
st.subheader("📈 Revenue vs Expenditure Percentage Over Time")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df['day_of_year'],
    y=df['total_revenue_percentage'],
    name='Revenue %',
    mode='lines+markers',
    line=dict(color='#2ecc71', width=2),
    marker=dict(size=4),
    hovertemplate='Day %{x}<br>Revenue: %{y:.2f}%<extra></extra>',
))

fig.add_trace(go.Scatter(
    x=df['day_of_year'],
    y=df['total_expenditure_percentage'],
    name='Expenditure %',
    mode='lines+markers',
    line=dict(color='#e74c3c', width=2),
    marker=dict(size=4),
    hovertemplate='Day %{x}<br>Expenditure: %{y:.2f}%<extra></extra>',
))

fig.update_layout(
    xaxis_title='Day of Fiscal Year',
    yaxis_title='Percentage (%)',
    hovermode='x unified',
    legend=dict(orientation='h', y=1.08),
    height=450,
    margin=dict(l=40, r=20, t=40, b=40),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=True, gridcolor='#eee'),
    yaxis=dict(showgrid=True, gridcolor='#eee'),
)

st.plotly_chart(fig, use_container_width=True)

st.caption("Data source: FCGO (fcgo.gov.np) | Fiscal Year 2082/83")
