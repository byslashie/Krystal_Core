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
    page_title="景氣循環",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme(st)

# ============================================================================
# 標題與介紹
# ============================================================================

st.markdown(create_header(
    "🌍 景氣循環 & 美林時鐘",
    "宏觀經濟狀況分析與策略適配"
), unsafe_allow_html=True)

st.markdown("""
美林時鐘（Minsky Clock）根據經濟周期的不同階段（擴張/過熱/衰退/復甦），
提供當前市場環境評估和最優策略建議。
""")

# ============================================================================
# 側邊欄配置
# ============================================================================

with st.sidebar:
    st.markdown("### ⚙️ 景氣循環設置")

    economic_indicators = st.multiselect(
        "📊 選擇監控指標",
        ["利率", "通膨", "GDP增長", "失業率", "消費", "企業獲利"],
        default=["利率", "通膨", "GDP增長"]
    )

    update_frequency = st.selectbox(
        "🔄 更新頻率",
        ["每日", "每週", "每月"],
        index=2
    )

    data_source = st.selectbox(
        "📡 數據來源",
        ["FRED (聯準會)", "Yahoo Finance", "自定義API"],
        index=0
    )

# ============================================================================
# 美林時鐘 - 當前狀態
# ============================================================================

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("### 📍 當前位置")

    # 假數據：當前景氣狀態
    current_phase = "擴張期"
    phase_emoji = "🟢"
    confidence = 0.78

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
        border: 2px solid #10B981;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    ">
        <div style="font-size: 48px; margin: 10px 0;">{phase_emoji}</div>
        <div style="font-size: 24px; font-weight: bold; color: #10B981;">{current_phase}</div>
        <div style="font-size: 14px; color: #6B7280; margin-top: 10px;">
            信心度: <strong>{confidence:.0%}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # 美林時鐘圖表
    fig = go.Figure()

    # 四個象限對應的經濟階段
    phases_data = {
        '復甦期': {'x': 0.25, 'y': 0.75, 'color': '#3B82F6', 'emoji': '🔵'},
        '擴張期': {'x': 0.75, 'y': 0.75, 'color': '#10B981', 'emoji': '🟢'},
        '過熱期': {'x': 0.75, 'y': 0.25, 'color': '#F59E0B', 'emoji': '🟠'},
        '衰退期': {'x': 0.25, 'y': 0.25, 'color': '#EF4444', 'emoji': '🔴'},
    }

    # 添加背景象限
    fig.add_shape(type="rect", x0=0, y0=0.5, x1=0.5, y1=1,
                  fillcolor="rgba(59, 130, 246, 0.1)", line=dict(color="rgba(59, 130, 246, 0.3)"))
    fig.add_shape(type="rect", x0=0.5, y0=0.5, x1=1, y1=1,
                  fillcolor="rgba(16, 185, 129, 0.1)", line=dict(color="rgba(16, 185, 129, 0.3)"))
    fig.add_shape(type="rect", x0=0.5, y0=0, x1=1, y1=0.5,
                  fillcolor="rgba(245, 158, 11, 0.1)", line=dict(color="rgba(245, 158, 11, 0.3)"))
    fig.add_shape(type="rect", x0=0, y0=0, x1=0.5, y1=0.5,
                  fillcolor="rgba(239, 68, 68, 0.1)", line=dict(color="rgba(239, 68, 68, 0.3)"))

    # 添加階段標籤
    fig.add_annotation(text="復甦", x=0.25, y=0.85, font=dict(size=12, color="#3B82F6"), showarrow=False)
    fig.add_annotation(text="擴張", x=0.75, y=0.85, font=dict(size=12, color="#10B981"), showarrow=False)
    fig.add_annotation(text="過熱", x=0.75, y=0.15, font=dict(size=12, color="#F59E0B"), showarrow=False)
    fig.add_annotation(text="衰退", x=0.25, y=0.15, font=dict(size=12, color="#EF4444"), showarrow=False)

    # 添加當前位置指示
    fig.add_trace(go.Scatter(
        x=[0.75], y=[0.75],
        mode='markers+text',
        marker=dict(size=20, color='#10B981', symbol='star'),
        text=['當前'],
        textposition='top center',
        showlegend=False
    ))

    # 軸線
    fig.add_shape(type="line", x0=0.5, y0=0, x1=0.5, y1=1, line=dict(color="gray", width=1, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=0.5, x1=1, y1=0.5, line=dict(color="gray", width=1, dash="dash"))

    fig.update_xaxes(title="通膨水平 →", range=[0, 1], showticklabels=False)
    fig.update_yaxes(title="經濟增長 →", range=[0, 1], showticklabels=False)
    fig.update_layout(
        title="美林時鐘",
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        showlegend=False,
        hovermode=False
    )

    st.plotly_chart(fig, use_container_width=True)

with col3:
    st.markdown("### 💡 策略建議")

    strategies = {
        "資產配置": ["股票: 70%", "債券: 20%", "現金: 10%"],
        "股票風格": ["成長股優先"],
        "部門配置": ["科技: ↑ 超配", "能源: ↓ 低配"],
        "固定收益": ["長期債券"],
        "風險管理": ["中等杠桿"]
    }

    for strategy_type, items in strategies.items():
        st.markdown(f"**{strategy_type}**")
        for item in items:
            st.markdown(f"- {item}")
        st.markdown("")

# ============================================================================
# 經濟指標面板
# ============================================================================

st.markdown("---")
st.markdown("### 📊 關鍵經濟指標")

# 假數據：各項經濟指標
indicators_data = pd.DataFrame({
    '指標': ['利率 (Fed Funds)', '通膨率 (CPI)', 'GDP增長', '失業率', '消費信心'],
    '當前值': ['5.33%', '3.28%', '2.5%', '3.8%', '104.7'],
    '上月值': ['5.25%', '3.24%', '2.3%', '3.9%', '103.5'],
    '變化': ['↑ +0.08%', '↑ +0.04%', '↑ +0.20%', '↓ -0.10%', '↑ +1.2'],
    '趨勢': ['🔴 上升', '🟠 偏高', '🟢 加速', '🟢 下降', '🟢 改善']
})

st.dataframe(
    indicators_data,
    use_container_width=True,
    hide_index=True,
    column_config={
        '指標': st.column_config.TextColumn(width='medium'),
        '當前值': st.column_config.TextColumn(width='small'),
        '上月值': st.column_config.TextColumn(width='small'),
        '變化': st.column_config.TextColumn(width='small'),
        '趨勢': st.column_config.TextColumn(width='small'),
    }
)

# ============================================================================
# 景氣循環歷史圖表
# ============================================================================

st.markdown("---")
st.markdown("### 📈 12個月景氣循環追蹤")

# 假數據：12 個月的景氣狀態追蹤
dates = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='M')
phases_numeric = [1, 1, 1.5, 2, 2.5, 2.8, 3, 3.5, 3.2, 2.5, 1.8, 1.5]  # 1=復甦, 2=擴張, 3=過熱, 4=衰退

phase_names = {1: '復甦', 2: '擴張', 3: '過熱', 4: '衰退'}

fig_history = go.Figure()

fig_history.add_trace(go.Scatter(
    x=dates,
    y=phases_numeric,
    mode='lines+markers',
    name='景氣階段',
    line=dict(color='#6B21A8', width=3),
    marker=dict(size=8),
    fill='tozeroy',
    fillcolor='rgba(107, 33, 168, 0.1)'
))

fig_history.update_layout(
    title="景氣循環 12 個月追蹤",
    xaxis_title="時間",
    yaxis_title="階段 (1=復甦, 2=擴張, 3=過熱, 4=衰退)",
    height=300,
    hovermode='x unified'
)

st.plotly_chart(fig_history, use_container_width=True)

# ============================================================================
# 景氣循環與投資績效相關性
# ============================================================================

st.markdown("---")
st.markdown("### 🔗 景氣循環與策略績效相關性")

col1, col2 = st.columns(2)

with col1:
    # 不同景氣階段的策略績效
    phase_performance = pd.DataFrame({
        '景氣階段': ['復甦期', '擴張期', '過熱期', '衰退期'],
        '策略A績效': [8.5, 15.2, 5.3, -2.1],
        '策略B績效': [2.3, 8.5, 12.4, 6.7],
        '策略C績效': [-1.2, 3.5, -8.5, 9.2],
    })

    fig_phase = px.bar(
        phase_performance,
        x='景氣階段',
        y=['策略A績效', '策略B績效', '策略C績效'],
        barmode='group',
        title='各策略在不同景氣階段的績效',
        height=300
    )

    st.plotly_chart(fig_phase, use_container_width=True)

with col2:
    # 當前環境下的推薦配置
    current_allocation = pd.DataFrame({
        '策略': ['策略A\n(成長導向)', '策略B\n(均衡)', '策略C\n(防御)'],
        '建議配置': [40, 45, 15]
    })

    fig_allocation = px.pie(
        current_allocation,
        values='建議配置',
        names='策略',
        title='當前景氣環境推薦配置',
        height=300
    )

    st.plotly_chart(fig_allocation, use_container_width=True)

# ============================================================================
# 底部說明
# ============================================================================

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🟢 擴張期
    - 經濟增長加速，企業獲利提升
    - 適合：成長股、小型股
    - 策略A 表現最佳
    """)

with col2:
    st.markdown("""
    ### 🟠 過熱期
    - 經濟過度擴張，通膨上升
    - 適合：防御股、必需消費
    - 策略B 表現最佳
    """)

with col3:
    st.markdown("""
    ### 🔴 衰退期
    - 經濟放緩，企業獲利下滑
    - 適合：債券、黃金、避險
    - 策略C 表現最佳
    """)

st.info("""
💡 **提示**: 本頁面的經濟數據目前為示例假資料。
實際應用時應連接到 FRED API、Yahoo Finance 等實時數據源，
並根據 econ_classifier.py 的 M1 判斷自動更新。
""")
