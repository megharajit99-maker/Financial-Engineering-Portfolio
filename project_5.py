import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- 1. CONFIGURATION & AMAZON BRANDING ---
st.set_page_config(page_title="Corporate FP&A Terminal", layout="wide", page_icon="📦")

# Amazon-style Color Palette (#ff9900)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #ff9900; font-weight: bold; }
    div[data-testid="stSidebar"] { background-color: #161b22; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. RESILIENT DATA ENGINE ---
@st.cache_data(show_spinner=False)
def fetch_corporate_data(ticker):
    stock = yf.Ticker(ticker)
    try:
        # Attempt to pull live data
        info = stock.info
        is_stmt = stock.get_financials()
        cf = stock.get_cashflow()
        shares = info.get("sharesOutstanding") or 1e9
        
        if is_stmt.empty: raise ValueError("Throttled")

        # Operating Leverage Calculation
        leverage_df = pd.DataFrame({
            "Revenue": is_stmt.loc['Total Revenue'],
            "Op_Income": is_stmt.loc['Operating Income']
        })
        leverage_df.index = pd.to_datetime(leverage_df.index).year
        leverage_df = leverage_df.sort_index()

        # FCF per Share Trend
        fcf_series = cf.loc['Operating Cash Flow'] + cf.loc['Capital Expenditures']
        fcf_per_share = fcf_series / shares
        fcf_per_share.index = pd.to_datetime(fcf_per_share.index).year
        fcf_per_share = fcf_per_share.sort_index()

        # Efficiency Metrics
        ratios = {
            "OCF_Margin": (cf.loc['Operating Cash Flow'].iloc[0] / is_stmt.loc['Total Revenue'].iloc[0]),
            "ROIC": info.get("returnOnAssets", 0.05) * 2.5,
            "CapEx_Sales": abs(cf.loc['Capital Expenditures'].iloc[0] / is_stmt.loc['Total Revenue'].iloc[0])
        }
        
        price = info.get("currentPrice", 150.0)
        fcf_now = fcf_series.iloc[0]
        name = info.get("shortName", ticker)
        debt = info.get("totalDebt", 50e9)
        cash = info.get("totalCash", 60e9)

    except:
        # --- PROFESSIONAL FALLBACK (Industry Benchmarks) ---
        years = [2021, 2022, 2023, 2024]
        leverage_df = pd.DataFrame({
            "Revenue": [386e9, 469e9, 513e9, 574e9],
            "Op_Income": [22e9, 24e9, 12e9, 36e9]
        }, index=years)
        
        fcf_per_share = pd.Series({2021: 4.5, 2022: -1.2, 2023: 2.1, 2024: 6.8})
        ratios = {"OCF_Margin": 0.14, "ROIC": 0.18, "CapEx_Sales": 0.09}
        price, fcf_now, shares, name, debt, cash = 185.0, 32e9, 10e9, f"{ticker} (Benchmark)", 50e9, 60e9

    return {
        "leverage": leverage_df, "fcf_ps": fcf_per_share, "ratios": ratios,
        "price": price, "fcf_now": fcf_now, "shares": shares,
        "debt": debt, "cash": cash, "name": name
    }

# --- 3. UI SIDEBAR ---
st.sidebar.title("📦 FP&A Terminal")
ticker_input = st.sidebar.text_input("Company Ticker", value="AMZN").upper()
st.sidebar.markdown("---")
growth_input = st.sidebar.slider("Projected FCF Growth (%)", 0, 50, 20) / 100
wacc_input = st.sidebar.slider("Discount Rate (WACC %)", 5, 15, 9) / 100
sim_input = st.sidebar.select_slider("Simulations", options=[500, 1000], value=500)

# --- 4. DASHBOARD EXECUTION ---
data = fetch_corporate_data(ticker_input)

st.title(f"📊 Corporate FP&A Terminal: {data['name']}")
st.caption("Megha R Ajit | Strategy & Financial Planning Analysis | ESCP Business School")

# SECTION 1: KPIS
st.markdown("### 🛠️ Corporate Efficiency Metrics")
c1, c2, c3, c4 = st.columns(4)
c1.metric("OCF Margin", f"{data['ratios']['OCF_Margin']*100:.1f}%", "Cash Gen")
c2.metric("ROIC", f"{data['ratios']['ROIC']*100:.1f}%", "Cap Return")
c3.metric("CapEx / Sales", f"{data['ratios']['CapEx_Sales']*100:.1f}%", "Intensity")
c4.metric("Market Price", f"${data['price']:.2f}")

# SECTION 2: OPERATING LEVERAGE
st.markdown("---")
st.markdown("### 📈 Operating Leverage Analysis")
st.write("Metric: Scaling efficiency (Revenue Growth vs. Operating Income Growth)")

fig_lev = go.Figure()
fig_lev.add_trace(go.Scatter(x=data['leverage'].index, y=data['leverage']['Revenue'], name="Revenue", line=dict(color='#ff9900', width=4)))
fig_lev.add_trace(go.Bar(x=data['leverage'].index, y=data['leverage']['Op_Income'], name="Op Income", marker_color='#00d4ff', opacity=0.6))
fig_lev.update_layout(template="plotly_dark", height=350, hovermode="x unified", yaxis_title="USD ($)")
st.plotly_chart(fig_lev, use_container_width=True)

# SECTION 3: FCF TREND
st.markdown("---")
st.markdown("### 💵 Free Cash Flow per Share (Amazon 'North Star' Metric)")
fig_fcf = go.Figure()
fig_fcf.add_trace(go.Bar(x=data['fcf_ps'].index, y=data['fcf_ps'].values, marker_color='#2ECC71'))
fig_fcf.update_layout(template="plotly_dark", height=300, yaxis_title="FCF / Share ($)", xaxis=dict(tickmode='linear'))
st.plotly_chart(fig_fcf, use_container_width=True)

# SECTION 4: MONTE CARLO
st.markdown("---")
st.markdown("### 🎲 Stochastic FCF Valuation")

sim_results = []
for _ in range(sim_input):
    s_wacc = np.random.normal(wacc_input, 0.005)
    s_g = np.random.normal(growth_input, 0.02)
    # 5-Year Projection
    proj = [data['fcf_now'] * ((1 + s_g)**i) / ((1 + s_wacc)**i) for i in range(1, 6)]
    tv = (proj[-1] * 1.025) / (s_wacc - 0.025)
    sim_results.append((sum(proj) + tv - data['debt'] + data['cash']) / data['shares'])

mean_p = np.mean(sim_results)

fig_hist = go.Figure()
fig_hist.add_trace(go.Histogram(x=sim_results, nbinsx=50, marker_color='#ff9900', opacity=0.7))
fig_hist.add_vline(x=mean_p, line_width=3, line_dash="dash", line_color="red", annotation_text=f"Fair Value: ${mean_p:.2f}")
fig_hist.update_layout(template="plotly_dark", height=350, xaxis_title="Intrinsic Price ($)", showlegend=False)
st.plotly_chart(fig_hist, use_container_width=True)
