from streamlit_autorefresh import st_autorefresh
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os
from anthropic import Anthropic
from dotenv import load_dotenv
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# 加载 .env 文件里的密钥
load_dotenv()

# ===== 页面配置 =====
st.set_page_config(
    page_title="Cross-Market Macro Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== 自定义 CSS =====
st.markdown("""
<style>
    .main {padding-top: 1rem;}
    .stMetric {
        background-color: #1a1a2e;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #00D4FF;
    }
    h1 {color: #FAFAFA; margin-bottom: 0;}
    .stCaption {color: #888;}
</style>
""", unsafe_allow_html=True)

# ===== 标题区 =====
col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("📊 Cross-Market Macro Dashboard")
    # ===== 实时刷新机制 =====
# 每 5 分钟自动重新运行整个页面
st_autorefresh(interval=5 * 60 * 1000, key="auto_refresh")

# 显示数据更新时间
et_tz = pytz.timezone('America/New_York')
now_et = datetime.now(et_tz)
col_time, col_btn = st.columns([3, 1])
with col_time:
    st.caption(f"🕐 Last refreshed: **{now_et.strftime('%Y-%m-%d %H:%M:%S ET')}** · Market data delayed ~15-20 min · Auto-refresh every 5 min")
with col_btn:
    if st.button("🔄 Refresh now", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Real-time analytics across US equities, Chinese stocks, commodities, and crypto")
with col_status:
    st.markdown(
        "<div style='text-align:right; padding-top:25px; color:#00FF7F;'>● Live Data</div>",
        unsafe_allow_html=True
    )

st.divider()

# ===== 跨市场资产清单 =====
ASSETS = {
    "S&P 500 (US)": "SPY",
    "Nasdaq 100 (US)": "QQQ",
    "Hang Seng (HK)": "2800.HK",
    "CSI 300 (CN)": "000300.SS",
    "Gold": "GC=F",
    "Crude Oil": "CL=F",
    "Bitcoin": "BTC-USD",
    "Dollar Index": "DX-Y.NYB"
}

# ===== 缓存数据,加载速度提升 10 倍 =====
@st.cache_data(ttl=60)
def load_data(ticker, period):
    """拉取数据并缓存"""
    data = yf.download(ticker, period=period, auto_adjust=True, multi_level_index=False, progress=False)
    return data

# ===== 侧边栏 =====
with st.sidebar:
    st.header("⚙️ Settings")
    
    selected_assets = st.multiselect(
        "Select assets to compare",
        options=list(ASSETS.keys()),
        default=["S&P 500 (US)", "Hang Seng (HK)", "Gold", "Bitcoin"],
        help="Pick 2-8 assets to compare"
    )
    
    period = st.selectbox(
        "Time Period",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"],
        index=2,
        help="'max' shows the longest available history"
    )
    
    normalize = st.checkbox(
        "Normalize to 100 for comparison",
        value=True
    )
    
    log_scale = st.checkbox(
        "Log scale (recommended for long periods)",
        value=False,
        help="Use logarithmic Y-axis when growth rates differ greatly"
    )
    
    st.divider()
    
    with st.expander("ℹ️ About this dashboard"):
        st.markdown("""
        **Cross-Market Macro Dashboard** tracks 8 global assets:
        - 🇺🇸 US Equities
        - 🇨🇳 Chinese Markets
        - 🇭🇰 Hong Kong
        - 🥇 Commodities
        - ₿ Cryptocurrency
        
        Built with Python, Streamlit, and Claude API.
        """)
    
    st.caption("Made by Yida Tong | UIUC Finance '26")

# ===== 检查 =====
if len(selected_assets) == 0:
    st.warning("👈 Please select at least one asset from the sidebar.")
    st.stop()

# ===== 拉数据 =====
all_data = pd.DataFrame()

with st.spinner(f"Loading {len(selected_assets)} assets..."):
    for asset_name in selected_assets:
        ticker = ASSETS[asset_name]
        try:
            data = load_data(ticker, period)
            if len(data) > 0:
                all_data[asset_name] = data["Close"]
        except Exception as e:
            st.error(f"Error loading {asset_name}: {e}")

# ===== 对齐时间范围(关键:避免不同资产历史长度不同的 NaN 问题) =====
if normalize and len(all_data.columns) > 1:
    all_data = all_data.dropna()
    if len(all_data) == 0:
        st.error("⚠️ No overlapping date range. Try shorter period or fewer assets.")
        st.stop()

if len(all_data.columns) == 0:
    st.error("No data loaded. Please try again.")
    st.stop()

# ===== Quick Stats KPI =====
st.subheader("📊 Quick Stats")

returns_summary = {}
for col in all_data.columns:
    series = all_data[col].dropna()
    if len(series) < 2:
        continue
    start_val = series.iloc[0]
    end_val = series.iloc[-1]
    if pd.isna(start_val) or pd.isna(end_val) or start_val == 0:
        continue
    pct = (end_val - start_val) / start_val * 100
    returns_summary[col] = pct

if len(returns_summary) > 0:
    cols = st.columns(min(4, len(returns_summary)))
    top_assets = list(returns_summary.items())[:4]
    for i, (asset, pct) in enumerate(top_assets):
        with cols[i]:
            clean_series = all_data[asset].dropna()
            latest_value = clean_series.iloc[-1] if len(clean_series) > 0 else 0
            st.metric(
                label=asset,
                value=f"${latest_value:,.2f}",
                delta=f"{pct:+.2f}%",
                delta_color="normal"
            )

st.divider()

# ===== 走势图 =====
st.subheader(f"📈 Performance Comparison ({period})")

fig = go.Figure()
colors = ["#00D4FF", "#FF6B6B", "#FFD93D", "#6BCF7F", "#A78BFA", "#FB7185", "#34D399", "#F472B6"]

for i, asset_name in enumerate(all_data.columns):
    close_series = all_data[asset_name].dropna()
    if len(close_series) == 0:
        continue
    
    if normalize:
        plot_series = (close_series / close_series.iloc[0]) * 100
    else:
        plot_series = close_series
    
    fig.add_trace(go.Scatter(
        x=close_series.index,
        y=plot_series,
        mode="lines",
        name=asset_name,
        line=dict(width=2.5, color=colors[i % len(colors)])
    ))

y_axis_label = "Normalized (Start = 100)" if normalize else "Price"
fig.update_layout(
    xaxis_title="",
    yaxis_title=y_axis_label,
    template="plotly_dark",
    height=500,
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(0,0,0,0)"
    ),
    margin=dict(l=0, r=0, t=30, b=0),
    plot_bgcolor="#0e1117",
    paper_bgcolor="#0e1117"
)

# 对数刻度
if log_scale:
    fig.update_yaxes(type="log")

fig.update_xaxes(showgrid=False)
fig.update_yaxes(showgrid=True, gridcolor="#2a2a3a")

st.plotly_chart(fig, width="stretch")

# ===== 双栏:Performance Ranking + Correlation =====
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📈 Performance Ranking")
    if len(all_data.columns) > 0:
        performance_data = []
        for col in all_data.columns:
            series = all_data[col].dropna()
            if len(series) < 2:
                continue
            start_val = series.iloc[0]
            end_val = series.iloc[-1]
            if pd.isna(start_val) or pd.isna(end_val) or start_val == 0:
                continue
            pct = (end_val / start_val - 1) * 100
            if pd.isna(pct):
                continue
            performance_data.append({"Asset": col, "Return %": pct})
        
        if len(performance_data) > 0:
            performance = pd.DataFrame(performance_data)
            performance = performance.sort_values("Return %", ascending=False).reset_index(drop=True)
            performance["Return %"] = performance["Return %"].apply(
                lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A"
            )
            st.dataframe(
                performance,
                width="stretch",
                hide_index=True,
                height=300
            )
        else:
            st.info("No valid performance data.")

with col_right:
    st.subheader("🔥 Correlation")
    if len(all_data.columns) >= 2:
        returns = all_data.pct_change().dropna()
        if len(returns) > 0:
            corr_matrix = returns.corr()
            fig_corr = px.imshow(
                corr_matrix,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1
            )
            fig_corr.update_layout(
                template="plotly_dark",
                height=300,
                margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_corr, width="stretch")
        else:
            st.info("Not enough data for correlation.")
    else:
        st.info("Select 2+ assets")

# ===== Quick Insights =====
if len(all_data.columns) >= 2 and len(returns_summary) >= 2:
    st.divider()
    st.subheader("💡 Quick Insights")
    
    returns = all_data.pct_change().dropna()
    if len(returns) > 0:
        corr_matrix = returns.corr()
        
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                value = corr_matrix.iloc[i, j]
                if pd.notna(value):
                    corr_pairs.append({
                        "pair": f"{corr_matrix.columns[i]} ↔ {corr_matrix.columns[j]}",
                        "value": value
                    })
        
        if corr_pairs:
            corr_pairs_sorted = sorted(corr_pairs, key=lambda x: x["value"], reverse=True)
            highest = corr_pairs_sorted[0]
            lowest = corr_pairs_sorted[-1]
            
            best_performer = max(returns_summary.items(), key=lambda x: x[1])
            worst_performer = min(returns_summary.items(), key=lambda x: x[1])
            
            insight_col1, insight_col2 = st.columns(2)
            with insight_col1:
                st.success(f"🚀 **Best performer**: {best_performer[0]} ({best_performer[1]:+.2f}%)")
                st.info(f"🔗 **Most synced**: {highest['pair']} (corr {highest['value']:.2f})")
            with insight_col2:
                st.error(f"📉 **Worst performer**: {worst_performer[0]} ({worst_performer[1]:+.2f}%)")
                st.info(f"⚖️ **Most diverging**: {lowest['pair']} (corr {lowest['value']:.2f})")

# ===== 🎯 Pairs Trading Analysis =====
if len(all_data.columns) >= 2:
    st.divider()
    st.subheader("🎯 Pairs Trading Analysis")
    st.caption("Statistical analysis for mean-reversion strategies. Identifies cointegrated pairs with tradable z-score divergence.")

    from statsmodels.tsa.stattools import coint
    from statsmodels.regression.linear_model import OLS
    from statsmodels.tools import add_constant
    import numpy as np

    def calculate_half_life(spread):
        """用 OLS 估计 OU 过程的半衰期"""
        spread_lag = spread.shift(1).dropna()
        spread_diff = spread.diff().dropna()
        common_idx = spread_lag.index.intersection(spread_diff.index)
        if len(common_idx) < 30:
            return None
        spread_lag = spread_lag.loc[common_idx]
        spread_diff = spread_diff.loc[common_idx]
        try:
            model = OLS(spread_diff.values, add_constant(spread_lag.values)).fit()
            beta = model.params[1]
            if beta >= 0:
                return None
            half_life = -np.log(2) / beta
            return half_life if 0 < half_life < 1000 else None
        except Exception:
            return None

    pairs_data = []

    for i in range(len(all_data.columns)):
        for j in range(i + 1, len(all_data.columns)):
            col_a = all_data.columns[i]
            col_b = all_data.columns[j]

            series_a = all_data[col_a].dropna()
            series_b = all_data[col_b].dropna()

            common_idx = series_a.index.intersection(series_b.index)
            if len(common_idx) < 60:
                continue

            series_a = series_a.loc[common_idx]
            series_b = series_b.loc[common_idx]

            try:
                log_a = np.log(series_a.values)
                log_b = np.log(series_b.values)

                model = OLS(log_a, add_constant(log_b)).fit()
                alpha = model.params[0]
                beta = model.params[1]

                spread = pd.Series(log_a - beta * log_b - alpha, index=series_a.index)

                _, coint_pvalue, _ = coint(series_a.values, series_b.values)

                spread_mean = spread.mean()
                spread_std = spread.std()
                if spread_std == 0:
                    continue
                current_z = (spread.iloc[-1] - spread_mean) / spread_std

                returns_a = series_a.pct_change().dropna()
                returns_b = series_b.pct_change().dropna()
                common_ret = returns_a.index.intersection(returns_b.index)
                correlation = returns_a.loc[common_ret].corr(returns_b.loc[common_ret]) if len(common_ret) > 10 else np.nan

                hl = calculate_half_life(spread)

                if coint_pvalue < 0.05 and abs(current_z) > 2:
                    signal = "🔴 Strong tradable"
                elif coint_pvalue < 0.05 and abs(current_z) > 1:
                    signal = "🟡 Mild (cointegrated)"
                elif coint_pvalue < 0.1:
                    signal = "🟢 At equilibrium"
                else:
                    signal = "⚪ Not cointegrated"

                pairs_data.append({
                    "Pair": f"{col_a} ↔ {col_b}",
                    "Correlation": correlation,
                    "Coint p-value": coint_pvalue,
                    "Hedge β": beta,
                    "Z-Score": current_z,
                    "Half-life (days)": hl,
                    "Signal": signal
                })
            except Exception:
                continue

    if len(pairs_data) > 0:
        pairs_df = pd.DataFrame(pairs_data)
        pairs_df["abs_z"] = pairs_df["Z-Score"].abs()
        pairs_df = pairs_df.sort_values("abs_z", ascending=False).drop(columns=["abs_z"]).reset_index(drop=True)

        display_df = pairs_df.copy()
        display_df["Correlation"] = display_df["Correlation"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
        display_df["Coint p-value"] = display_df["Coint p-value"].apply(lambda x: f"{x:.3f}")
        display_df["Hedge β"] = display_df["Hedge β"].apply(lambda x: f"{x:.2f}")
        display_df["Z-Score"] = display_df["Z-Score"].apply(lambda x: f"{x:+.2f}")
        display_df["Half-life (days)"] = display_df["Half-life (days)"].apply(
            lambda x: f"{x:.1f}" if x is not None and pd.notna(x) else "N/A"
        )

        st.dataframe(display_df, width="stretch", hide_index=True)

        tradable = pairs_df[(pairs_df["Coint p-value"] < 0.05) & (pairs_df["Z-Score"].abs() > 2)]

        if len(tradable) > 0:
            top = tradable.iloc[0]
            asset_a, asset_b = top["Pair"].split(" ↔ ")
            direction = "above" if top["Z-Score"] > 0 else "below"
            trade_idea = f"Short {asset_a}, Long {asset_b}" if top["Z-Score"] > 0 else f"Long {asset_a}, Short {asset_b}"
            hl_text = f"~{top['Half-life (days)']:.0f} days" if top['Half-life (days)'] is not None and pd.notna(top['Half-life (days)']) else "unknown"

            st.warning(
                f"⚠️ **Strongest tradable signal**: `{top['Pair']}` — "
                f"cointegrated (p={top['Coint p-value']:.3f}), "
                f"current spread is **{abs(top['Z-Score']):.2f}σ {direction}** historical mean.\n\n"
                f"**Mean-reversion play**: {trade_idea} with hedge ratio β = {top['Hedge β']:.2f}. "
                f"Estimated half-life: {hl_text}.\n\n"
                f"*Educational only — not investment advice.*"
            )
        elif len(pairs_df[pairs_df["Coint p-value"] < 0.05]) == 0:
            st.info("ℹ️ No pairs are statistically cointegrated in this time window. Try a longer period (1y+) or different assets.")

        with st.expander("ℹ️ How to read this table"):
            st.markdown("""
            **Cointegration p-value**:
            - `< 0.05` → ✅ Statistically cointegrated, pair is tradable
            - `0.05 - 0.10` → ⚠️ Weakly cointegrated
            - `> 0.10` → ❌ Not cointegrated; do not trade as a pair

            **Hedge Ratio (β)**: OLS coefficient from `log(A) = α + β·log(B) + ε`.
            For every $1 long in A, hold $β short in B to neutralize systematic risk.

            **Z-Score**: How many standard deviations the current spread is from its historical mean.
            Trade signal requires **both** cointegrated AND |Z| > 2.

            **Half-life**: Estimated days for the spread to revert halfway to the mean.
            - `< 10 days` → ✅ Excellent
            - `10-30 days` → 🟡 Tradable but slow
            - `> 30 days` → ❌ Capital cost likely exceeds expected return

            **Why this is better than simple correlation**:
            Two assets can have high correlation but diverge long-term (not cointegrated).
            Pairs trading on correlation alone loses money when the "pair" is actually drifting apart.
            """)
    else:
        st.info("Need at least 60 days of overlapping data across assets to compute cointegration.")
# ===== Raw Data =====
with st.expander("📋 View Raw Data"):
    st.dataframe(all_data, width="stretch")

# ===== AI Market Commentary =====
st.divider()
st.subheader("🤖 AI Market Commentary")
st.caption("Click below to get AI-generated insights on the current market state")

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("⚠️ ANTHROPIC_API_KEY not found")
else:
    if st.button("✨ Generate AI Analysis", type="primary"):
        with st.spinner("AI is analyzing the markets..."):
            try:
                returns = all_data.pct_change().dropna()
                corr_matrix = returns.corr()
                
                summary_lines = []
                for col in all_data.columns:
                    series = all_data[col].dropna()
                    if len(series) < 2:
                        continue
                    pct = (series.iloc[-1] / series.iloc[0] - 1) * 100
                    if pd.notna(pct):
                        summary_lines.append(f"- {col}: {pct:+.2f}%")
                performance_summary = "\n".join(summary_lines)
                
                corr_insights = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i + 1, len(corr_matrix.columns)):
                        pair = f"{corr_matrix.columns[i]} / {corr_matrix.columns[j]}"
                        value = corr_matrix.iloc[i, j]
                        if pd.notna(value):
                            corr_insights.append(f"- {pair}: {value:.2f}")
                correlation_summary = "\n".join(corr_insights)
                
                prompt = f"""You are a senior macro analyst. Based on the following cross-market data over the {period} period, write a concise market commentary (200-300 words).

PERFORMANCE BY ASSET:
{performance_summary}

CROSS-ASSET CORRELATIONS:
{correlation_summary}

Please write a market commentary that:
1. Identifies the dominant market narrative
2. Highlights which assets are leading and lagging
3. Notes any interesting correlations or divergences
4. Offers 1-2 thoughtful observations a portfolio manager would care about

Use a professional tone. Be specific about numbers."""

                client = Anthropic(api_key=api_key)
                message = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                ai_response = message.content[0].text
                st.markdown("### 📝 AI Analysis")
                st.markdown(ai_response)
                
                with st.expander("📊 API Usage"):
                    st.caption(f"Input: {message.usage.input_tokens} | Output: {message.usage.output_tokens}")
                    cost = (message.usage.input_tokens * 3 + message.usage.output_tokens * 15) / 1_000_000
                    st.caption(f"Cost: ${cost:.4f}")
                
            except Exception as e:
                st.error(f"Error calling Claude API: {e}")

# ===== 底部 =====
st.divider()
st.caption("⚠️ For educational purposes only. Not investment advice. Data via Yahoo Finance.")