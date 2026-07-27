import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

st.set_page_config(page_title="Strategic Analyst Terminal", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #00d4ff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def fetch_strategy_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    is_stmt = stock.get_financials()
    cf = stock.get_cashflow()
    
    try:

        margins = pd.DataFrame({
            "Operating Margin": is_stmt.loc['Operating Income'] / is_stmt.loc['Total Revenue'],
            "Gross Margin": is_stmt.loc['Gross Profit'] / is_stmt.loc['Total Revenue']
        })
        margins.index = pd.to_datetime(margins.index).year
        margins = margins.sort_index()

      
        price = info.get("currentPrice") or info.get("regularMarketPrice") or 150.0
        shares = info.get("sharesOutstanding") or 1e9
        

        ratios = {
            "D/E": (info.get("debtToEquity") or 0.0) / 100,
            "ROE": info.get("returnOnEquity") or 0.0,
            "Current": info.get("currentRatio") or 0.0,
            "Payout": info.get("payoutRatio") or 0.0
        }


        fcf = cf.loc['Operating Cash Flow'].iloc[0] + cf.loc['Capital Expenditures'].iloc[0]
        
    except:
        margins = pd.DataFrame({
            "Operating Margin": [0.20, 0.22, 0.25, 0.28],
            "Gross Margin": [0.40, 0.42, 0.45, 0.48]
        }, index=[2021, 2022, 2023, 2024])
        price, fcf, shares, ratios = 180.0, 5e9, 1e9, {"D/E": 0.5, "ROE": 0.15, "Current": 1.5, "Payout": 0.2}

    news = stock.news
    analyzer = SentimentIntensityAnalyzer()
    titles = [n.get('title') for n in news if n.get('title')] if news else []
    sentiment = sum([analyzer.polarity_scores(str(t))['compound'] for t in titles]) / len(titles) if titles else 0.0

    return {
        "margins": margins, "price": price, "fcf": fcf, "shares": shares,
        "debt": info.get("totalDebt", 0), "cash": info.get("totalCash", 0), 
        "ratios": ratios, "sentiment": sentiment, "name": info.get("shortName", ticker)
    }


st.sidebar.title("🏁 Strategy Controls")
ticker_input = st.sidebar.text_input("Enter Ticker", value="NVDA").upper()

st.sidebar.markdown("---")
st.sidebar.subheader("Valuation Assumptions")
growth = st.sidebar.slider("Projected Growth (%)", 0, 50, 15) / 100
wacc = st.sidebar.slider("Discount Rate (WACC %)", 5, 20, 10) / 100


try:
    data = fetch_strategy_data(ticker_input)
    
    st.title(f"📊 Strategic Analysis: {data['name']}")
    st.caption(f"Megha R Ajit | CFA Candidate | Strategy Focus: Efficiency & Profitability")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Debt-to-Equity", f"{data['ratios']['D/E']:.2f}", "Solvency")
    c2.metric("ROE (Efficiency)", f"{data['ratios']['ROE']*100:.1f}%", "Profitability")
    c3.metric("Current Ratio", f"{data['ratios']['Current']:.2f}", "Liquidity")
    c4.metric("Dividend Payout", f"{data['ratios']['Payout']*100:.1f}%", "Capital Return")

 
    st.markdown("---")
    st.markdown("### 📈 Efficiency Trend: Operating vs. Gross Margins")
    st.write("Strategist Insight: Upward trending margins indicate pricing power and scale efficiency.")
    
    fig_margin = go.Figure()
    fig_margin.add_trace(go.Scatter(x=data['margins'].index, y=data['margins']['Gross Margin'], name="Gross Margin", line=dict(color='#00d4ff', width=4)))
    fig_margin.add_trace(go.Scatter(x=data['margins'].index, y=data['margins']['Operating Margin'], name="Operating Margin", line=dict(color='#ff4b4b', width=4)))
    
    fig_margin.update_layout(template="plotly_dark", height=350, margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified", yaxis_tickformat='.0%')
    st.plotly_chart(fig_margin, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎲 Probabilistic Intrinsic Valuation")
    adj_g = growth + (data['sentiment'] * 0.05)
    
    sim_results = []
    for _ in range(1000):
        s_wacc = np.random.normal(wacc, 0.005)
        s_g = np.random.normal(adj_g, 0.02)
        proj = [data['fcf'] * ((1 + s_g)**i) / ((1 + s_wacc)**i) for i in range(1, 6)]
        tv = (proj[-1] * 1.02) / (s_wacc - 0.02)
        sim_results.append((sum(proj) + tv - data['debt'] + data['cash']) / data['shares'])

    mean_p = np.mean(sim_results)
    
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(x=sim_results, nbinsx=50, name="Frequency", marker_color='#00d4ff', opacity=0.7))
    fig_hist.add_vline(x=mean_p, line_width=3, line_dash="dash", line_color="red", annotation_text=f"Fair Value: ${mean_p:.2f}")
    fig_hist.add_vline(x=data['price'], line_width=3, line_color="white", annotation_text=f"Market Price")
    
    fig_hist.update_layout(template="plotly_dark", height=350, xaxis_title="Price ($)", showlegend=False)
    st.plotly_chart(fig_hist, use_container_width=True)

except Exception as e:
    st.error("Terminal Throttled. Please try again in 10 seconds.")
    
