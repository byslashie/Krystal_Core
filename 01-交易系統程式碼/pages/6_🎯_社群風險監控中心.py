import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 导入UI主题
sys.path.append(str(Path(__file__).parent.parent))
from utils.ui_theme import apply_theme, create_header, create_info_box

# ============================================================================
# 頁面配置
# ============================================================================

st.set_page_config(
    page_title="社群風險監控",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme(st)

# ============================================================================
# 標題與介紹
# ============================================================================

st.markdown(create_header(
    "🎯 社群風險監控中心",
    "實時追蹤社群信號，預防系統性風險"
), unsafe_allow_html=True)

st.markdown("""
通過社群輿情、異常交易行為、機構動向等多維度信號，
實時識別可能的市場系統性風險，提前預警。
""")

# ============================================================================
# 側邊欄配置
# ============================================================================

with st.sidebar:
    st.markdown("### ⚙️ 監控設置")

    monitoring_sources = st.multiselect(
        "📡 監控來源",
        ["Twitter/X", "Reddit", "金融新聞", "機構動向", "交易異常"],
        default=["Twitter/X", "金融新聞", "交易異常"]
    )

    risk_threshold = st.slider(
        "⚠️ 風險告警閾值",
        0, 100, 60,
        help="超過此分數時觸發高風險警告"
    )

    update_interval = st.selectbox(
        "🔄 檢查頻率",
        ["實時", "每 5 分鐘", "每 15 分鐘", "每小時"],
        index=1
    )

# ============================================================================
# 實時風險評分卡
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
        border: 2px solid #10B981;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    ">
        <div style="font-size: 14px; color: #6B7280; margin-bottom: 5px;">整體風險評分</div>
        <div style="font-size: 48px; font-weight: bold; color: #10B981;">28</div>
        <div style="font-size: 12px; color: #10B981; margin-top: 5px;">🟢 低風險</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(251, 146, 60, 0.1) 100%);
        border: 2px solid #F59E0B;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    ">
        <div style="font-size: 14px; color: #6B7280; margin-bottom: 5px;">社群情緒</div>
        <div style="font-size: 48px; font-weight: bold; color: #F59E0B;">+45</div>
        <div style="font-size: 12px; color: #F59E0B; margin-top: 5px;">⬆️ 樂觀情緒</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
        border: 2px solid #3B82F6;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    ">
        <div style="font-size: 14px; color: #6B7280; margin-bottom: 5px;">異常交易量</div>
        <div style="font-size: 48px; font-weight: bold; color: #3B82F6;">12</div>
        <div style="font-size: 12px; color: #3B82F6; margin-top: 5px;">⚠️ 個異常信號</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(107, 33, 168, 0.1) 0%, rgba(123, 58, 237, 0.1) 100%);
        border: 2px solid #6B21A8;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    ">
        <div style="font-size: 14px; color: #6B7280; margin-bottom: 5px;">機構動向</div>
        <div style="font-size: 48px; font-weight: bold; color: #6B21A8;">5</div>
        <div style="font-size: 12px; color: #6B21A8; margin-top: 5px;">📊 大宗交易</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# 實時風險告警
# ============================================================================

st.markdown("---")
st.markdown("### 🚨 實時風險告警 (過去 24 小時)")

alerts = [
    {
        'time': '今天 14:32',
        'severity': '🟢 低',
        'type': '社群情緒',
        'message': 'Tesla 相關推文正面情緒上升 15%，可能推高股價',
        'action': '觀察'
    },
    {
        'time': '今天 11:15',
        'severity': '🟡 中',
        'type': '交易異常',
        'message': '美國 10 年期公債成交量異常高，可能預示利率方向改變',
        'action': '注意'
    },
    {
        'time': '今天 09:45',
        'severity': '🟢 低',
        'type': '機構動向',
        'message': '高盛減持新興市場持倉 5%，可能影響 EM 資產',
        'action': '追蹤'
    },
    {
        'time': '昨天 16:20',
        'severity': '🟡 中',
        'type': '宏觀新聞',
        'message': 'IMF 下調全球經濟增長預測至 2.4%，波及風險資產',
        'action': '評估'
    },
]

for alert in alerts:
    col1, col2, col3 = st.columns([0.5, 3, 1])

    with col1:
        st.markdown(f"**{alert['severity']}**")

    with col2:
        st.markdown(f"""
        **{alert['type']}** · {alert['time']}

        {alert['message']}
        """)

    with col3:
        st.markdown(f"<div style='text-align: right; padding-top: 10px;'><span style='background: #F3F4F6; padding: 5px 10px; border-radius: 4px; font-size: 12px;'>{alert['action']}</span></div>", unsafe_allow_html=True)

    st.divider()

# ============================================================================
# 風險指標趨勢圖
# ============================================================================

st.markdown("---")
st.markdown("### 📈 風險指標 7 日趨勢")

col1, col2 = st.columns(2)

with col1:
    # 總體風險評分趨勢
    dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='D')
    risk_scores = [35, 38, 32, 28, 35, 30, 28]

    fig_risk = go.Figure()

    fig_risk.add_trace(go.Scatter(
        x=dates,
        y=risk_scores,
        mode='lines+markers',
        name='風險評分',
        line=dict(color='#6B21A8', width=3),
        marker=dict(size=10),
        fill='tozeroy',
        fillcolor='rgba(107, 33, 168, 0.1)'
    ))

    # 添加閾值線
    fig_risk.add_hline(y=risk_threshold, line_dash="dash", line_color="red",
                      annotation_text=f"警告閾值: {risk_threshold}", annotation_position="right")

    fig_risk.update_layout(
        title="整體風險評分趨勢",
        xaxis_title="日期",
        yaxis_title="風險評分 (0-100)",
        height=300,
        hovermode='x unified'
    )

    st.plotly_chart(fig_risk, use_container_width=True)

with col2:
    # 各維度風險指數
    dimensions = ['社群情緒', '交易異常', '機構動向', '新聞事件', '技術面']
    scores = [25, 35, 20, 40, 28]
    colors = ['#10B981' if s < 40 else '#F59E0B' if s < 60 else '#EF4444' for s in scores]

    fig_radar = go.Figure()

    fig_radar.add_trace(go.Bar(
        y=dimensions,
        x=scores,
        orientation='h',
        marker=dict(color=colors),
        text=scores,
        textposition='auto',
    ))

    fig_radar.update_layout(
        title="風險維度分析",
        xaxis_title="風險指數 (0-100)",
        height=300,
        showlegend=False,
        margin=dict(l=150)
    )

    st.plotly_chart(fig_radar, use_container_width=True)

# ============================================================================
# 社群信號詳細分析
# ============================================================================

st.markdown("---")
st.markdown("### 💬 社群信號詳細分析")

tab1, tab2, tab3, tab4 = st.tabs(["🐦 Twitter/X", "📱 Reddit", "📰 金融新聞", "🏦 機構動向"])

with tab1:
    st.markdown("#### Twitter/X 情緒分析")

    twitter_data = pd.DataFrame({
        '標籤': ['#Fed', '#Crypto', '#TechStock', '#ChinaEconomy', '#StockMarket'],
        '提及次數': [1250, 980, 1120, 650, 890],
        '正面比例': [35, 42, 55, 28, 48],
        '情緒趨勢': ['⬇️ 下降', '⬆️ 上升', '⬆️ 上升', '⬇️ 下降', '➡️ 平穩']
    })

    st.dataframe(twitter_data, use_container_width=True, hide_index=True)

    st.markdown("**熱門推文** (過去 24 小時)")
    for i in range(3):
        st.caption(f"推文 #{i+1}: '市場對 Fed 利率決議反應...' (❤️ 1.2K 💬 340 🔄 890)")

with tab2:
    st.markdown("#### Reddit 討論熱度")

    reddit_data = pd.DataFrame({
        '板塊': ['r/investing', 'r/stocks', 'r/cryptocurrency', 'r/trading'],
        '本週討論數': [2400, 2100, 1850, 1620],
        '熱門話題': ['Fed 決議', 'AI 股票', 'BTC 反彈', '日內交易策略'],
        '情緒': ['🟠 謹慎', '🟢 樂觀', '🟠 混合', '🟢 樂觀']
    })

    st.dataframe(reddit_data, use_container_width=True, hide_index=True)

with tab3:
    st.markdown("#### 金融新聞監控")

    news_data = pd.DataFrame({
        '時間': ['今天 10:30', '今天 08:45', '昨天 16:20', '昨天 14:15'],
        '來源': ['彭博社', '路透社', '路透社', '彭博社'],
        '標題': [
            'Fed 官員暗示 2024 年可能降息 3 次',
            'S&P 500 創新高，科技股領漲',
            'IMF 下調全球經濟增速預估',
            '美股波動率指數 VIX 跌至年低'
        ],
        '影響': ['🔴 高', '🟢 正面', '🔴 高', '🟢 正面']
    })

    st.dataframe(news_data, use_container_width=True, hide_index=True)

with tab4:
    st.markdown("#### 機構動向追蹤")

    institution_data = pd.DataFrame({
        '機構': ['高盛', '摩根士丹利', 'BlackRock', '貝萊德'],
        '最新動向': ['減持新興市場', '增持科技股', '平衡部署', '加碼債券'],
        '資金規模': ['$5.2B', '$3.8B', '$12.4B', '$8.6B'],
        '可能影響': ['⬇️ EM 資產', '⬆️ 科技股', '➡️ 平穩', '⬇️ 利率']
    })

    st.dataframe(institution_data, use_container_width=True, hide_index=True)

# ============================================================================
# 風險應對建議
# ============================================================================

st.markdown("---")
st.markdown("### 💡 當前環境風險應對建議")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    #### 🛡️ 降低風險敞口

    - 減少單一行業部位
    - 增加防御性資產
    - 提高現金比例至 15%
    - 考慮對沖策略
    """)

with col2:
    st.markdown("""
    #### ⚠️ 加強監控

    - 關注 Fed 政策動向
    - 追蹤波動率指數 VIX
    - 監控新興市場流動性
    - 觀察企業盈利預警
    """)

with col3:
    st.markdown("""
    #### 📊 優化配置

    - 考慮增加黃金配置
    - 適度配置長期債券
    - 評估國際多元化
    - 保持流動性緩衝
    """)

# ============================================================================
# 底部說明
# ============================================================================

st.markdown("---")

st.info("""
💡 **系統說明**:
- 本監控中心數據目前為示例假資料
- 實際應用時應連接到 Twitter API、Reddit API、新聞 API、Bloomberg 等真實數據源
- 風險評分算法應基於多因子模型，考慮社群情緒、交易異常、機構動向等多維度
- 告警應自動推送至 Telegram 或其他通知渠道
""")

st.markdown("""
### 📌 功能特性
- ✅ 實時社群信號追蹤
- ✅ 異常交易檢測
- ✅ 機構動向監控
- ✅ 自動風險告警
- ✅ 多維度風險評分
- ✅ 歷史趨勢分析
""")
