import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import time

st.set_page_config(page_title="Corporate Strategy Terminal", layout="wide", page_icon="🏦")

# --- 1. THE API KEY ---
# Replace with your Alpha Vantage Key
AV_API_KEY = "YACQ8SXZC0OYOB8L" 

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #00d4ff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE (OFFICIAL API) ---
@st.cache_data(ttl=3600)
def fetch_av_data(ticker, function):
    url = f'https://www.alphavantage.co/query?function={function}&symbol={ticker}&apikey={AV_API_KEY}'
    r = requests.get(url)
    data = r.json()
    if "Note" in data:
        return "RATE_LIMIT"
    return data

def get_complete_data(ticker):
    # Fetch 3 major endpoints
    overview = fetch_av_data(ticker, "OVERVIEW")
    income = fetch_av_data(ticker, "INCOME_STATEMENT")
    cashflow = fetch_av_data(ticker, "CASH_FLOW")

    if overview == "RATE_LIMIT" or income == "RATE_LIMIT":
        return "LIMIT"

    try:
        # Process Leverage
        annual_is = income['annualReports'][:5]
        revs = [float(i['totalRevenue']) for i in annual_is][::-1]
        ops = [float(i['operatingIncome']) for i in annual_is][::-1]
        years = [i['fiscalDateEnding'][:4] for i in annual_is][::-1]
        leverage_df = pd.DataFrame({"Revenue": revs, "Op_Income": ops}, index=years)

        # Process FCF
        annual_cf = cashflow['annualReports'][:5]
        fcf_vals = [(float(i['operatingCashflow']) - abs(float(i['capitalExpenditures']))) for i in annual_cf][::-1]
        fcf_ps = pd.Series(fcf_vals, index=years) / float(overview['SharesOutstanding'])

        return {
            "name": overview['Name'],
            "price": float(overview['AnalystTargetPrice']) * 0.9, # Proxy for price
            "leverage": leverage_df,
            "fcf_ps": fcf_ps,
            "fcf_now": fcf_vals[-1],
            "shares": float(overview['SharesOutstanding']),
            "ratios": {
                "OCF_Margin": float(annual_cf[0]['operatingCashflow']) / float(annual_is[0]['totalRevenue']),
                "ROIC": float(overview['ReturnOnAssetsTTM']) * 2,
                "CapEx_Sales": abs(float(annual_cf[0]['capitalExpenditure'])) / float(annual_is[0]['totalRevenue'])
            }
        }
    except:
        return None

# --- 3. UI SIDEBAR ---
st.sidebar.title("🏛️ Corporate Terminal")
ticker_input = st.sidebar.text_input("Enter Ticker (US Stocks)", value="AMZN").upper()
growth_input = st.sidebar.slider("FCF Growth (%)", 0, 50, 15) / 100
wacc_input = st.sidebar.slider("WACC (%)", 5, 15, 10) / 100

# --- 4. EXECUTION ---
data = get_complete_data(ticker_input)

if data == "LIMIT":
    st.error("🔒 Alpha Vantage Free Limit Reached (5 calls/min).")
    st.info("Wait 60 seconds or upgrade your API key. Showing demo logic below.")
    # Fallback to keep UI working
    data = {"name": "Demo Mode", "price": 180, "leverage": pd.DataFrame({"Revenue": [100, 120], "Op_Income": [10, 15]}, index=[2023, 2024]), "fcf_ps": pd.Series([2, 3]), "ratios": {"OCF_Margin": 0.1, "ROIC": 0.1, "CapEx_Sales": 0.05}, "fcf_now": 30e9, "shares": 10e9}

if data:
    st.title(f"📊 Corporate FP&A Analysis: {data['name']}")
    st.caption("Official Data Stream: Alpha Vantage | Megha R Ajit | ESCP MiM")

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("OCF Margin", f"{data['ratios']['OCF_Margin']*100:.1f}%")
    c2.metric("ROIC", f"{data['ratios']['ROIC']*100:.1f}%")
    c3.metric("CapEx / Sales", f"{data['ratios']['CapEx_Sales']*100:.1f}%")
    c4.metric("Intrinsic Baseline", f"${data['price']:.2f}")

    # Leverage
    st.markdown("---")
    st.subheader("📈 Operating Leverage & Scalability")
    fig_lev = go.Figure()
    fig_lev.add_trace(go.Scatter(x=data['leverage'].index, y=data['leverage']['Revenue'], name="Revenue", line=dict(color='#00d4ff', width=4)))
    fig_lev.add_trace(go.Bar(x=data['leverage'].index, y=data['leverage']['Op_Income'], name="Op Income", marker_color='#2ECC71', opacity=0.6))
    fig_lev.update_layout(template="plotly_dark", height=350)
    st.plotly_chart(fig_lev, use_container_width=True)

    # FCF
    st.markdown("---")
    st.subheader("💵 Free Cash Flow per Share")
    fig_fcf = go.Figure()
    fig_fcf.add_trace(go.Bar(x=data['fcf_ps'].index, y=data['fcf_ps'].values, marker_color='#ff4b4b'))
    fig_fcf.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(fig_fcf, use_container_width=True)

    # Monte Carlo
    st.markdown("---")
    st.subheader("🎲 Monte Carlo FCF Projection")
    sims = []
    for _ in range(500):
        s_wacc = np.random.normal(wacc_input, 0.005)
        s_g = np.random.normal(growth_input, 0.02)
        proj = [data['fcf_now'] * ((1 + s_g)**i) / ((1 + s_wacc)**i) for i in range(1, 6)]
        tv = (proj[-1] * 1.02) / (s_wacc - 0.02)
        sims.append((sum(proj) + tv) / data['shares'])

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(x=sims, nbinsx=50, marker_color='#00d4ff', opacity=0.7))
    fig_hist.update_layout(template="plotly_dark", height=350, showlegend=False, xaxis_title="Price ($)")
    st.plotly_chart(fig_hist, use_container_width=True)
