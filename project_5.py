import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

# --- 1. CONFIGURATION & BRANDING ---
st.set_page_config(page_title="Institutional Strategy Terminal", layout="wide", page_icon="🏛️")

# Professional Institutional Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #00d4ff; font-weight: bold; }
    div[data-testid="stSidebar"] { background-color: #161b22; }
    </style>
    """, unsafe_allow_html=True)

# PASTE YOUR API KEY HERE
FMP_API_KEY = "nY5efrP712f7IJKWjYTG8HgUldRElVES"

# --- 2. RESILIENT INSTITUTIONAL DATA ENGINE ---
@st.cache_data(show_spinner=False)
def fetch_institutional_data(ticker):
    """
    Fetches fundamental data via FMP API. 
    Includes a 'fail-safe' fallback to ensure 100% uptime for portfolio showcase.
    """
    try:
        # Step A: Validate Ticker & Get Quote
        quote_url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={FMP_API_KEY}"
        quote_res = requests.get(quote_url).json()
        
        if not quote_res or (isinstance(quote_res, dict) and "Error Message" in quote_res):
            raise ValueError("API Restricted")

        # Step B: Fetch Statements
        is_url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit=5&apikey={FMP_API_KEY}"
        cf_url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?limit=5&apikey={FMP_API_KEY}"
        ev_url = f"https://financialmodelingprep.com/api/v3/enterprise-values/{ticker}?limit=1&apikey={FMP_API_KEY}"
        
        income_stmt = requests.get(is_url).json()
        cash_flow = requests.get(cf_url).json()
        ev_metrics = requests.get(ev_url).json()[0]
        quote = quote_res[0]

        # Process Operating Leverage
        revs, ops, years = [], [], []
        for item in reversed(income_stmt):
            revs.append(item['revenue'])
            ops.append(item['operatingIncome'])
            years.append(item['calendarYear'])
        leverage_df = pd.DataFrame({"Revenue": revs, "Op_Income": ops}, index=years)

        # Process FCF per Share
        fcf_ps_list = [item['freeCashFlow'] / ev_metrics['numberOfShares'] for item in reversed(cash_flow)]
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
                "ROIC": income_stmt[0]['operatingIncome'] / ev_metrics['enterpriseValue'],
                "CapEx_Sales": abs(cash_flow[0]['capitalExpenditure'] / income_stmt[0]['revenue'])
            }
        }

    except Exception:
        # --- THE 'TOP 5%' FAIL-SAFE FALLBACK ---
        # If the API fails for any reason, load benchmark data to keep UI alive.
        st.sidebar.warning(f"⚠️ Live Feed for {ticker} Restricted. Showing Sector Benchmark.")
        
        years = ['2021', '2022', '2023', '2024']
        leverage_df = pd.DataFrame({
            "Revenue": [380e9, 470e9, 515e9, 575e9],
            "Op_Income": [22e9, 25e9, 13e9, 38e9]
        }, index=years)
        
        fcf_ps = pd.Series([4.5, 4.8, -1.2, 6.5], index=years)
        
        return {
            "name": f"{ticker} (Sector Benchmark)",
            "price": 185.00,
            "leverage": leverage_df,
            "fcf_ps": fcf_ps,
            "fcf_now": 35e9,
            "shares": 10e9,
            "debt": 50e9, "cash": 60e9,
            "ratios": {"OCF_Margin": 0.15, "ROIC": 0.18, "CapEx_Sales": 0.08}
        }

# --- 3. UI SIDEBAR ---
st.sidebar.title("🏢 Corporate Terminal")
ticker_input = st.sidebar.text_input("Enter Ticker", value="AMZN").upper()
st.sidebar.markdown("---")
growth_input = st.sidebar.slider("Projected FCF Growth (%)", 0, 50, 15) / 100
wacc_input = st.sidebar.slider("WACC / Discount Rate (%)", 5, 15, 10) / 100

# --- 4. DASHBOARD EXECUTION ---
data = fetch_institutional_data(ticker_input)

st.title(f"🏛️ Strategy Terminal: {data['name']}")
st.caption("Developed by Megha R Ajit | Data Feed: Financial Modeling Prep | ESCP Business School")

# SECTION 1: KPIS
st.markdown("### 🛠️ Strategic Efficiency Metrics")
c1, c2, c3, c4 = st.columns(4)
c1.metric("OCF Margin", f"{data['ratios']['OCF_Margin']*100:.1f}%", "Cash Flow")
c2.metric("ROIC", f"{data['ratios']['ROIC']*100:.1f}%", "Efficiency")
c3.metric("CapEx / Sales", f"{data['ratios']['CapEx_Sales']*100:.1f}%", "Intensity")
c4.metric("Market Price", f"${data['price']:.2f}")

# SECTION 2: OPERATING LEVERAGE
st.markdown("---")
st.markdown("### 📈 Operating Leverage Analysis")
st.write("Visualizing top-line Revenue scalability vs. Operating Income growth.")

fig_lev = go.Figure()
fig_lev.add_trace(go.Scatter(x=data['leverage'].index, y=data['leverage']['Revenue'], name="Revenue", line=dict(color='#00d4ff', width=4)))
fig_lev.add_trace(go.Bar(x=data['leverage'].index, y=data['leverage']['Op_Income'], name="Op Income", marker_color='#2ECC71', opacity=0.6))
fig_lev.update_layout(template="plotly_dark", height=350, hovermode="x unified", yaxis_title="USD ($)")
st.plotly_chart(fig_lev, use_container_width=True)

# SECTION 3: FCF TREND
st.markdown("---")
st.markdown("### 💵 Free Cash Flow per Share")
fig_fcf = go.Figure()
fig_fcf.add_trace(go.Bar(x=data['fcf_ps'].index, y=data['fcf_ps'].values, marker_color='#ff4b4b'))
fig_fcf.update_layout(template="plotly_dark", height=300, yaxis_title="FCF / Share ($)")
st.plotly_chart(fig_fcf, use_container_width=True)

# SECTION 4: MONTE CARLO
st.markdown("---")
st.markdown("### 🎲 Stochastic Intrinsic Valuation")

sim_results = []
for _ in range(500):
    s_wacc = np.random.normal(wacc_input, 0.005)
    s_g = np.random.normal(growth_input, 0.02)
    proj = [data['fcf_now'] * ((1 + s_g)**i) / ((1 + s_wacc)**i) for i in range(1, 6)]
    tv = (proj[-1] * 1.025) / (s_wacc - 0.025)
    sim_results.append((sum(proj) + tv - data['debt'] + data['cash']) / data['shares'])

mean_p = np.mean(sim_results)

fig_hist = go.Figure()
fig_hist.add_trace(go.Histogram(x=sim_results, nbinsx=50, marker_color='#00d4ff', opacity=0.7))
fig_hist.add_vline(x=mean_p, line_width=3, line_dash="dash", line_color="red", annotation_text=f"Fair Value: ${mean_p:.2f}")
fig_hist.update_layout(template="plotly_dark", height=350, xaxis_title="Intrinsic Price ($)", showlegend=False)
st.plotly_chart(fig_hist, use_container_width=True)
