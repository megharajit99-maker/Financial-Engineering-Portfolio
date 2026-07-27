import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Institutional Strategy Terminal", layout="wide", page_icon="🏦")

# PASTE YOUR API KEY HERE FROM THE DASHBOARD
FMP_API_KEY = "nY5efrP712f7IJKWjYTG8HgUldRElVES" 

# Amazon-style Professional Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #00d4ff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INSTITUTIONAL DATA ENGINE (FMP API) ---
@st.cache_data(show_spinner=False)
def fetch_institutional_data(ticker):
    try:
        # A. Income Statement (Last 5 Years)
        is_url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit=5&apikey={FMP_API_KEY}"
        income_stmt = requests.get(is_url).json()
        
        # B. Cash Flow Statement (Last 5 Years)
        cf_url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?limit=5&apikey={FMP_API_KEY}"
        cash_flow = requests.get(cf_url).json()

        # C. Key Metrics (Price, Name, Shares)
        quote_url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={FMP_API_KEY}"
        quote = requests.get(quote_url).json()[0]

        # D. Enterprise Value (for Debt/Cash/Shares outstanding)
        ev_url = f"https://financialmodelingprep.com/api/v3/enterprise-values/{ticker}?limit=1&apikey={FMP_API_KEY}"
        ev_metrics = requests.get(ev_url).json()[0]

        # Process Operating Leverage Data
        revs, ops, years = [], [], []
        for item in reversed(income_stmt):
            revs.append(item['revenue'])
            ops.append(item['operatingIncome'])
            years.append(item['calendarYear'])
        
        leverage_df = pd.DataFrame({"Revenue": revs, "Op_Income": ops}, index=years)

        # Process FCF per Share
        fcf_ps_list = []
        for item in reversed(cash_flow):
            fcf_ps_list.append(item['freeCashFlow'] / ev_metrics['numberOfShares'])
        
        fcf_ps = pd.Series(fcf_ps_list, index=years)

        return {
            "name": quote['name'],
            "price": quote['price'],
            "leverage": leverage_df,
            "fcf_ps": fcf_ps,
            "fcf_now": cash_flow[0]['freeCashFlow'],
            "shares": ev_metrics['numberOfShares'],
            "debt": ev_metrics['enterpriseValue'] - ev_metrics['marketCapitalization'],
            "cash": ev_metrics['minusCashAndCashEquivalents'],
            "ratios": {
                "OCF_Margin": cash_flow[0]['operatingCashFlow'] / income_stmt[0]['revenue'],
                "ROIC": income_stmt[0]['operatingIncome'] / (ev_metrics['enterpriseValue']),
                "CapEx_Sales": abs(cash_flow[0]['capitalExpenditure'] / income_stmt[0]['revenue'])
            }
        }
    except Exception as e:
        st.error(f"API Connection Error: Ensure Ticker is valid and API Key is correct.")
        return None

# --- 3. UI SIDEBAR ---
st.sidebar.title("🏢 Corporate Terminal")
ticker_input = st.sidebar.text_input("Enter Ticker", value="AMZN").upper()
st.sidebar.markdown("---")
growth_input = st.sidebar.slider("Assumed FCF Growth (%)", 0, 50, 20) / 100
wacc_input = st.sidebar.slider("WACC / Discount Rate (%)", 5, 15, 9) / 100

# --- 4. DASHBOARD EXECUTION ---
data = fetch_institutional_data(ticker_input)

if data:
    st.title(f"🏛️ Strategy Terminal: {data['name']}")
    st.caption("Megha R Ajit | Data Feed: Financial Modeling Prep (Official) | ESCP Business School")

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("OCF Margin", f"{data['ratios']['OCF_Margin']*100:.1f}%", "Cash Flow")
    m2.metric("ROIC", f"{data['ratios']['ROIC']*100:.1f}%", "Efficiency")
    m3.metric("CapEx / Sales", f"{data['ratios']['CapEx_Sales']*100:.1f}%", "Intensity")
    m4.metric("Market Price", f"${data['price']:.2f}")

    # Leverage Chart
    st.markdown("---")
    st.subheader("📈 Operating Leverage (Revenue vs. Op Income)")
    fig_lev = go.Figure()
    fig_lev.add_trace(go.Scatter(x=data['leverage'].index, y=data['leverage']['Revenue'], name="Revenue", line=dict(color='#00d4ff', width=4)))
    fig_lev.add_trace(go.Bar(x=data['leverage'].index, y=data['leverage']['Op_Income'], name="Op Income", marker_color='#2ECC71', opacity=0.6))
    fig_lev.update_layout(template="plotly_dark", height=350, hovermode="x unified")
    st.plotly_chart(fig_lev, use_container_width=True)

    # FCF Trend
    st.markdown("---")
    st.subheader("💵 Free Cash Flow per Share History")
    fig_fcf = go.Figure()
    fig_fcf.add_trace(go.Bar(x=data['fcf_ps'].index, y=data['fcf_ps'].values, marker_color='#ff4b4b'))
    fig_fcf.update_layout(template="plotly_dark", height=300, yaxis_title="FCF / Share ($)")
    st.plotly_chart(fig_fcf, use_container_width=True)

    # Monte Carlo Valuation
    st.markdown("---")
    st.subheader("🎲 Monte Carlo FCF Projection (5-Year)")
    sims = []
    for _ in range(1000):
        s_wacc = np.random.normal(wacc_input, 0.005)
        s_g = np.random.normal(growth_input, 0.02)
        proj = [data['fcf_now'] * ((1 + s_g)**i) / ((1 + s_wacc)**i) for i in range(1, 6)]
        tv = (proj[-1] * 1.025) / (s_wacc - 0.025)
        sims.append((sum(proj) + tv - data['debt'] + data['cash']) / data['shares'])

    mean_p = np.mean(sims)
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(x=sims, nbinsx=60, marker_color='#00d4ff', opacity=0.7))
    fig_hist.add_vline(x=mean_p, line_width=3, line_dash="dash", line_color="red", annotation_text=f"Fair Value: ${mean_p:.2f}")
    fig_hist.update_layout(template="plotly_dark", height=350, xaxis_title="Intrinsic Price ($)", showlegend=False)
    st.plotly_chart(fig_hist, use_container_width=True)
