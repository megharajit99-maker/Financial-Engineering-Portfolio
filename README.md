# Financial-Engineering-Portfolio
Automated financial & strategy tools: NLP-driven Equity Valuation, Strategic M&A Industry Screening, and Macro-Economic Sensitivity Engines


**Financial Engineering & Strategic Analytics Portfolio**

Developed by **Megha R Ajit **

This repository contains a suite of proprietary Python-based tools designed to automate high-level financial analysis and strategic decision-making. These projects bridge the gap between traditional corporate finance and modern data science.

**🚀 Project 1: Algorithmic Equity Valuation & Risk Engine**

File: **valuation_engine.py**

**Overview**

A dynamic Discounted Cash Flow (DCF) model that moves beyond static assumptions. It utilizes Natural Language Processing (NLP) to "read" live market news and objectively adjust the Equity Risk Premium (ERP) and growth projections based on market sentiment.

**Key Features:**

NLP Sentiment Scoring: Quantifies market mood from live news headlines via the VADER sentiment engine.
Monte Carlo Simulation: Executes 1,000+ iterations to generate a probability distribution of the share price, establishing a 95% confidence interval for fair value.

**Stochastic Risk Modeling**: Replaces deterministic inputs with random normal distributions to simulate real-world market volatility.

**🔍 Project 2: Strategic M&A Target Identification Engine**

Files: **ma_scout.py, ma_scout_report.csv**

**Overview**

An industry-scale screening tool designed for Corporate Strategy and Private Equity workflows. It automates the identification of acquisition targets by analyzing an entire sector universe simultaneously.

**Key Features:**

Multi-Criteria Decision Analysis (MCDA): Ranks targets using a weighted algorithm: Valuation (40%), Profitability (40%), and Solvency/Risk (20%).

**Industry Benchmarking**: Compares key multiples (EV/EBITDA) and margins across 10+ global peers instantly.

**Automated Reporting**: Generates a strategic "shortlist" in CSV format, reducing preliminary research time by ~90%.

**📊 Project 3: Macro-Economic Sensitivity & Stress Testing Engine**

File: **macro_engine.py**

**Overview**

A predictive analytics tool that quantifies the Macro-to-Micro transmission of global economic forces onto specific equity valuations.

**Key Features**:

Correlation Matrix: Analyzes historical relationships between stock performance and variables like the 10Y Treasury Yield and USD Index.

**Macro Stress Test**: Projects the impact of a 100bps interest rate "shock" on stock prices using statistical beta-regression.
**Visualization**: Generates professional heatmaps and normalized performance charts to identify external risk drivers.


**🛠 Tech Stack**

Language: Python 3.x

Data Science: Pandas, NumPy, Scipy

Finance API: yfinance

AI/NLP: vaderSentiment

Visualization: Matplotlib, Seaborn

Methodologies: DCF, Monte Carlo, MCDA, Beta-Regression

**📬 Contact**

Megha R Ajit

megharajit99@gmail.com
