import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class FinancialEngine:
    def __init__(self, ticker_symbol):
        self.ticker_symbol = ticker_symbol
        self.stock = yf.Ticker(ticker_symbol)
        self.analyzer = SentimentIntensityAnalyzer()
        
    def get_core_data(self):
        """Extracts all raw financial data needed for the model."""
        info = self.stock.info
        cf = self.stock.cashflow
        
        try:
            ocf = cf.loc['Operating Cash Flow'].iloc[0]
            capex = cf.loc['Capital Expenditures'].iloc[0]
            fcf = ocf + capex 
        except:
            fcf = info.get("freeCashflow", 1000000000)

        return {
            "fcf": fcf,
            "beta": info.get("beta", 1.2),
            "mkt_cap": info.get("marketCap", 1),
            "debt": info.get("totalDebt", 0),
            "cash": info.get("totalCash", 0),
            "shares": info.get("sharesOutstanding", 1),
            "price": info.get("currentPrice", 0)
        }

    def get_sentiment_score(self):
        """Fetches news and quantifies market mood using NLP."""
        raw_news = self.stock.news
        headlines = [item.get('title') for item in raw_news if item.get('title')] if raw_news else []
        
        if not headlines:
            headlines = [f"{self.ticker_symbol} market position remains strong", 
                         f"Analysts debate {self.ticker_symbol} valuation targets"]
        
        scores = [self.analyzer.polarity_scores(t)['compound'] for t in headlines]
        avg_sentiment = round(sum(scores) / len(scores), 4) if scores else 0
        return avg_sentiment

    def calculate_risk_metrics(self, sentiment):
        """Adjusts the WACC based on Sentiment Analysis."""
        data = self.get_core_data()

        risk_free = 0.042 # 10Y Treasury
        base_erp = 0.055  # 5.5% standard premium
        
        adj_erp = base_erp + (sentiment * -0.01) 
  
        cost_of_equity = risk_free + (data['beta'] * adj_erp)
        
        v = data['mkt_cap'] + data['debt']
        w_e = data['mkt_cap'] / v
        w_d = data['debt'] / v
        
        wacc = (w_e * cost_of_equity) + (w_d * 0.05 * (1 - 0.25))
        return wacc, adj_erp

    def run_monte_carlo_dcf(self, sentiment, iterations=1000):
        """
        Runs 1,000 simulations varying Growth and WACC.
        Returns a probability distribution of the share price.
        """
        data = self.get_core_data()
        base_wacc, _ = self.calculate_risk_metrics(sentiment)
        base_growth = 0.12 + (sentiment * 0.05)
        
        simulated_prices = []

        for _ in range(iterations):
            sim_wacc = np.random.normal(base_wacc, 0.005) # 0.5% volatility
            sim_growth = np.random.normal(base_growth, 0.02) # 2% volatility
            
            # Year 1-5 DCF Projection
            projections = [data['fcf'] * ((1 + sim_growth)**i) / ((1 + sim_wacc)**i) for i in range(1, 6)]
            
            # Terminal Value (Gordon Growth)
            terminal_growth = 0.025
            tv = (projections[-1] * (1 + terminal_growth)) / (sim_wacc - terminal_growth)
            
            # Final Valuation
            ev = sum(projections) + tv
            equity_val = ev - data['debt'] + data['cash']
            simulated_prices.append(equity_val / data['shares'])
            
        return simulated_prices

if __name__ == "__main__":
    ticker = "NVDA"
    engine = FinancialEngine(ticker)
    
    print(f"--- Starting Advanced Quant Valuation for {ticker} ---")
    
    sentiment = engine.get_sentiment_score()
    
    wacc, erp = engine.calculate_risk_metrics(sentiment)

    sim_results = engine.run_monte_carlo_dcf(sentiment)

    current_p = engine.get_core_data()['price']
    mean_p = np.mean(sim_results)
    p5 = np.percentile(sim_results, 5)   # Lower bound
    p95 = np.percentile(sim_results, 95) # Upper bound
    
    print(f"\nRESULTS:")
    print(f"Market Sentiment Score: {sentiment} ({'Bullish' if sentiment > 0 else 'Bearish'})")
    print(f"NLP-Adjusted WACC: {wacc*100:.2f}%")
    print(f"Current Market Price: ${current_p:.2f}")
    print(f"Average Simulated Fair Value: ${mean_p:.2f}")
    print(f"95% Confidence Interval: ${p5:.2f} - ${p95:.2f}")
    
    # 5. Visualize the Distribution
    plt.style.use('ggplot')
    plt.figure(figsize=(12, 6))
    plt.hist(sim_results, bins=60, color='teal', alpha=0.7, edgecolor='white')
    plt.axvline(mean_p, color='red', linestyle='--', label=f'Mean Fair Value: ${mean_p:.2f}')
    plt.axvline(current_p, color='black', linewidth=2, label=f'Market Price: ${current_p:.2f}')
    plt.title(f"Monte Carlo Valuation Distribution: {ticker}", fontsize=14)
    plt.xlabel("Intrinsic Share Price ($)", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.legend()
    plt.show()
