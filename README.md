# 📊 Cross-Market Macro Dashboard

> An AI-powered analytics platform tracking 8 global markets in real time, with cross-asset correlation analysis and Claude-generated market commentary.

[![Streamlit](https://img.shields.io/badge/Streamlit-Live%20Demo-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://yidatong-macro-dashboard.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Claude API](https://img.shields.io/badge/Claude-Sonnet%204.6-D97757?style=flat-square)](https://docs.claude.com)

🔗 **Live Demo**: [yidatong-macro-dashboard.streamlit.app](https://yidatong-macro-dashboard.streamlit.app)

![Dashboard Preview](https://github.com/yida2222/macro-dashboard/raw/main/screenshot-main.png)

---

## 💡 What it does

Modern financial markets are deeply interconnected, but most retail tools force you to look at one asset at a time. This dashboard solves that problem:

- **Compare up to 8 assets** across US equities, Chinese stocks, Hong Kong markets, commodities, and cryptocurrency — on a single normalized chart
- **Identify cross-asset correlations** with a daily-return heatmap that reveals hedging opportunities and regime shifts
- **Get AI-powered market commentary** from Claude Sonnet 4.6 that synthesizes the data into a 200-300 word professional narrative
- **Switch between linear and log scale** to compare assets with vastly different growth rates (e.g., Bitcoin vs Gold over 12 years)

Built for someone trying to understand *why* markets move together — not just *that* they do.

---

## ✨ Key Features

| Feature | What it shows |
|---------|---------------|
| 📊 **Quick Stats** | Real-time prices + period returns across selected assets |
| 📈 **Performance Comparison** | Normalized multi-asset chart with linear/log scale toggle |
| 📋 **Performance Ranking** | Sorted return table with NaN-safe formatting |
| 🔥 **Correlation Matrix** | Daily-return heatmap (-1 to +1, red/blue) |
| 💡 **Quick Insights** | Auto-detected best/worst performers and most/least correlated pairs |
| 🤖 **AI Market Commentary** | Claude-generated 200-300 word professional analysis |

---

## 🛠️ Tech Stack

- **Language**: Python 3.14
- **Frontend**: Streamlit · Plotly
- **Data**: yfinance (Yahoo Finance API)
- **AI**: Anthropic Claude API (claude-sonnet-4-6)
- **Deployment**: Streamlit Community Cloud
- **Version Control**: Git · GitHub

---

## 🎯 Supported Assets

| Region | Asset | Ticker |
|--------|-------|--------|
| 🇺🇸 US | S&P 500 ETF | SPY |
| 🇺🇸 US | Nasdaq 100 ETF | QQQ |
| 🇭🇰 HK | Hang Seng (via Tracker Fund) | 2800.HK |
| 🇨🇳 CN | CSI 300 | 000300.SS |
| 🥇 Commodity | Gold Futures | GC=F |
| 🛢️ Commodity | Crude Oil Futures | CL=F |
| ₿ Crypto | Bitcoin | BTC-USD |
| 💵 FX | US Dollar Index | DX-Y.NYB |

---

## 🚀 Run Locally

```bash
# Clone the repo
git clone https://github.com/yida2222/macro-dashboard.git
cd macro-dashboard

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your Anthropic API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Run the app
streamlit run app.py
```

Get your API key at [console.anthropic.com](https://console.anthropic.com).

---

## 📚 What I Learned Building This

This was my first end-to-end software project, built over 11 days from zero programming experience. Key takeaways:

1. **Working with messy real-world data is most of the job.** Half of my code is NaN handling — different assets have different trading hours, weekends, holidays, and inception dates. Production-grade financial code assumes data will be broken.

2. **Prompt engineering matters as much as code.** The AI commentary feature went from generic to genuinely insightful when I restructured the prompt — explicitly defining the analyst's role, the output format, and what observations a portfolio manager would care about.

3. **Visualization choices encode judgment.** Switching Bitcoin vs Gold from linear to log scale doesn't just change the look — it reframes the entire story. The same data tells different stories depending on the axis.

4. **Deploying is half the value.** A local script no one can access is a hobby; a deployed URL is a product. The 80% effort to build → 20% to deploy ratio is real, and the 20% is what makes the work matter.

---

## 👤 Author

**Yida Tong** — UIUC Consumer Economics & Finance, Class of 2026 (December)

Five internships across China's financial sector — including the People's Bank of China (stablecoin policy research), CITIC Securities (equity research), and Industrial Bank Hong Kong (corporate banking & AML). Currently seeking US-based Summer 2026 internships and January 2027 full-time Analyst roles.

📧 yidatong11@gmail.com  
🔗 [LinkedIn](https://www.linkedin.com/in/tongyida/)

---

## ⚠️ Disclaimer

This dashboard is for **educational and portfolio purposes only**. It is not investment advice, and the author is not a licensed financial advisor. Market data is provided by Yahoo Finance via the `yfinance` library and may be delayed or inaccurate. AI-generated commentary reflects the model's statistical pattern matching and should not be used to make investment decisions.

---

## 📄 License

MIT License — feel free to fork, modify, and learn from this project.
