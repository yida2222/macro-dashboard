import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os
from anthropic import Anthropic
from dotenv import load_dotenv

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
    "Hang Seng (HK)": "^HSI",
    "CSI 300 (CN)": "000300.SS",
    "Gold": "GC=F",
    "Crude Oil": "CL=F",
    "Bitcoin": "BTC-USD",
    "Dollar Index": "DX-Y.NYB"
}

# ===== 🆕 缓存数据,加载速度提升 10 倍 =====
@st.cache_data(ttl=300)  # 缓存 5 分钟
def load_data(ticker, period):
    """拉取数据并缓存,避免重复请求"""
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
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=2
    )
    
    normalize = st.checkbox(
        "Normalize to 100 for comparison",
        value=True
    )
    
    st.divider()
    
    # 🆕 添加产品介绍
    with st.expander("ℹ️ About this dashboard"):
        st.markdown("""
        **Cross-Market Macro Dashboard** tracks 8 global assets across:
        - 🇺🇸 US Equities
        - 🇨🇳 Chinese Markets
        - 🇭🇰 Hong Kong
        - 🥇 Commodities
        - ₿ Cryptocurrency
        
        Built with Python, Streamlit, and yfinance.
        """)
    
    st.caption("Made by Yida Tong | UIUC Finance '26")

# 检查
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

if len(all_data.columns) == 0:
    st.error("No data loaded. Please try again.")
    st.stop()

# ===== 🆕 顶部 KPI 卡片 =====
st.subheader("📊 Quick Stats")

# 算每个资产的阶段收益率
returns_summary = {}
for col in all_data.columns:
    # 取第一个非 NaN 的值作为起点
    series = all_data[col].dropna()
    if len(series) < 2:
        continue  # 数据不够,跳过这个资产
    start_val = series.iloc[0]
    end_val = series.iloc[-1]
    if pd.isna(start_val) or pd.isna(end_val) or start_val == 0:
        continue
    pct = (end_val - start_val) / start_val * 100
    returns_summary[col] = pct

# 显示在卡片里 (最多 4 个)
cols = st.columns(min(4, len(returns_summary)))
top_assets = list(returns_summary.items())[:4]
for i, (asset, pct) in enumerate(top_assets):
    with cols[i]:
        # 取最新非 NaN 的值
        latest_value = all_data[asset].dropna().iloc[-1] if len(all_data[asset].dropna()) > 0 else 0
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

# 🆕 给不同资产分配专业配色
colors = ["#00D4FF", "#FF6B6B", "#FFD93D", "#6BCF7F", "#A78BFA", "#FB7185", "#34D399", "#F472B6"]

for i, asset_name in enumerate(all_data.columns):
    close_series = all_data[asset_name]
    
    if normalize:
        plot_series = (close_series / close_series.iloc[0]) * 100
    else:
        plot_series = close_series
    
    fig.add_trace(go.Scatter(
        x=all_data.index,
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
fig.update_xaxes(showgrid=False)
fig.update_yaxes(showgrid=True, gridcolor="#2a2a3a")

st.plotly_chart(fig, width="stretch")

# ===== 双栏布局:左边表格,右边热力图 =====
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📈 Performance Ranking")
    if len(all_data.columns) > 0:
        performance = pd.DataFrame({
            "Asset": all_data.columns,
            "Return %": [(all_data[col].iloc[-1] / all_data[col].iloc[0] - 1) * 100 for col in all_data.columns]
        })
        performance = performance.sort_values("Return %", ascending=False).reset_index(drop=True)
        performance["Return %"] = performance["Return %"].apply(lambda x: f"{x:+.2f}%")
        
        st.dataframe(
            performance,
            width="stretch",
            hide_index=True,
            height=300
        )

with col_right:
    st.subheader("🔥 Correlation")
    if len(all_data.columns) >= 2:
        returns = all_data.pct_change().dropna()
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
        st.info("Select 2+ assets")

# ===== 智能解读 =====
if len(all_data.columns) >= 2:
    st.divider()
    st.subheader("💡 Quick Insights")
    
    returns = all_data.pct_change().dropna()
    corr_matrix = returns.corr()
    
    # 找出最高和最低相关性
    corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            corr_pairs.append({
                "pair": f"{corr_matrix.columns[i]} ↔ {corr_matrix.columns[j]}",
                "value": corr_matrix.iloc[i, j]
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

# ===== 原始数据 =====
with st.expander("📋 View Raw Data"):
    st.dataframe(all_data, width="stretch")

# ===== 底部签名 =====
st.divider()
st.caption("⚠️ This dashboard is for educational purposes only. Not investment advice. Data via Yahoo Finance.")
# ===== 🤖 AI Market Commentary =====
st.divider()
st.subheader("🤖 AI Market Commentary")
st.caption("Click below to get AI-generated insights on the current market state")

# 初始化 Anthropic 客户端
api_key = os.getenv("ANTHROPIC_API_KEY")



if not api_key:
    st.error("⚠️ ANTHROPIC_API_KEY not found in .env file")
else:
    if st.button("✨ Generate AI Analysis", type="primary"):
        with st.spinner("AI is analyzing the markets..."):
            try:
                # 准备给 AI 看的数据摘要
                returns = all_data.pct_change().dropna()
                corr_matrix = returns.corr()
                
                # 算每个资产的总收益率
                summary_lines = []
                for col in all_data.columns:
                    pct = (all_data[col].iloc[-1] / all_data[col].iloc[0] - 1) * 100
                    summary_lines.append(f"- {col}: {pct:+.2f}%")
                
                performance_summary = "\n".join(summary_lines)
                
                # 找出最高 / 最低相关性
                corr_insights = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i + 1, len(corr_matrix.columns)):
                        pair = f"{corr_matrix.columns[i]} / {corr_matrix.columns[j]}"
                        value = corr_matrix.iloc[i, j]
                        corr_insights.append(f"- {pair}: {value:.2f}")
                
                correlation_summary = "\n".join(corr_insights)
                
                # 组装 prompt
                prompt = f"""You are a senior macro analyst. Based on the following cross-market data over the {period} period, write a concise market commentary (200-300 words).

PERFORMANCE BY ASSET:
{performance_summary}

CROSS-ASSET CORRELATIONS:
{correlation_summary}

Please write a market commentary that:
1. Identifies the dominant market narrative (e.g., "risk-on rally", "flight to safety", "regional decoupling")
2. Highlights which assets are leading and lagging
3. Notes any interesting correlations or divergences
4. Offers 1-2 thoughtful observations a portfolio manager would care about

Use a professional tone. Be specific about numbers. Avoid generic language."""

                # 调用 Claude API
                client = Anthropic(api_key=api_key)
                
                message = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # 显示 AI 的回复
                ai_response = message.content[0].text
                
                st.markdown("### 📝 AI Analysis")
                st.markdown(ai_response)
                
                # 显示一下用了多少 token (方便监控花费)
                with st.expander("📊 API Usage"):
                    st.caption(f"Input tokens: {message.usage.input_tokens} | Output tokens: {message.usage.output_tokens}")
                    cost = (message.usage.input_tokens * 3 + message.usage.output_tokens * 15) / 1_000_000
                    st.caption(f"Estimated cost: ${cost:.4f}")
                
            except Exception as e:
                st.error(f"Error calling Claude API: {e}")
                st.info("Common issues: API key invalid, no credit, or network problem.")