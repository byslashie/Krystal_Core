import streamlit as st
import sys
from pathlib import Path

# 导入UI主题
sys.path.append(str(Path(__file__).parent.parent))
from utils.ui_theme import apply_theme, create_header, create_info_box

# 页面配置
st.set_page_config(
    page_title="首頁",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 应用主题
apply_theme(st)

# 主标题
st.markdown(create_header(
    "🏠 Krystal AI × 總經 × 自動化交易系統",
    "專業級量化交易策略分析平台 V3.0"
), unsafe_allow_html=True)

# 核心功能介绍
st.markdown("### 📋 核心功能模組")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(91, 71, 217, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
        border: 1px solid rgba(91, 71, 217, 0.2);
        border-radius: 12px;
        padding: 20px;
        height: 100%;
    ">
        <h4 style="color: #5B47D9; margin-top: 0;">📤 策略績效上傳</h4>
        <p style="color: #4B5563; font-size: 14px; margin-bottom: 0;">
            上傳策略交易資料 CSV 檔案，系統自動驗證與解析
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
        border: 1px solid rgba(6, 182, 212, 0.2);
        border-radius: 12px;
        padding: 20px;
        height: 100%;
    ">
        <h4 style="color: #06B6D4; margin-top: 0;">📊 績效分析</h4>
        <p style="color: #4B5563; font-size: 14px; margin-bottom: 0;">
            計算年化報酬、Sharpe Ratio、最大回撤等專業量化指標
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(217, 70, 239, 0.1) 100%);
        border: 1px solid rgba(236, 72, 153, 0.2);
        border-radius: 12px;
        padding: 20px;
        height: 100%;
    ">
        <h4 style="color: #EC4899; margin-top: 0;">🤖 AI 建議</h4>
        <p style="color: #4B5563; font-size: 14px; margin-bottom: 0;">
            AI 模型根據數據回饋優化建議與風險提示
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 高级功能
st.markdown("### ⚡ 進階功能")

col1, col2 = st.columns(2)

with col1:
    st.markdown(create_info_box(
        "📈 視覺化圖表",
        "包含累積資金曲線、回撤分析、月度滾動報酬率、年月熱力圖等 7 類互動式圖表",
        icon="📊",
        color="#5B47D9"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(create_info_box(
        "☁️ Google Sheets 同步",
        "自動將績效資料寫入雲端 Google Sheets，支援多策略對比與歷史追蹤",
        icon="💾",
        color="#06B6D4"
    ), unsafe_allow_html=True)

st.markdown("---")

# 快速开始
st.markdown("### 🚀 快速開始")

st.markdown("""
**第 1 步：準備資料**
- 確保 CSV 檔案包含: `進場時間`、`出場時間`、`進場價格`、`出場價格`
- 支援 UTF-8 或 Big5 編碼

**第 2 步：上傳策略**
- 點選左側「策略上傳與績效」頁面
- 輸入初始資金與 Benchmark 代碼
- 上傳 CSV 檔案

**第 3 步：查看分析報告**
- 系統自動計算績效指標
- 生成視覺化圖表與統計表格
- 可選擇 AI 模型獲取優化建議

**第 4 步：多策略對比**
- 在「多策略績效比較」頁面對比不同策略
- 查看績效差異與相關性分析
""")

st.markdown("---")

# 技术栈信息
st.markdown("### 🛠️ 技術棧")

tech_info = """
| 層級 | 技術 |
|------|------|
| **前端框架** | Streamlit (Python Web App) |
| **數據處理** | Pandas, NumPy, Polars |
| **可視化** | Plotly, Matplotlib |
| **AI/LLM** | OpenRouter API (Gemini, DeepSeek, Llama) |
| **金融數據** | yfinance, IB API, Yuanta API |
| **雲端存儲** | Google Sheets API |

"""

st.markdown(tech_info)

# 底部提示
st.markdown("""
---
<div style="
    background: linear-gradient(135deg, rgba(91, 71, 217, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
    border-left: 4px solid #5B47D9;
    border-radius: 12px;
    padding: 16px;
    margin-top: 32px;
">
    <p style="color: #1F2937; margin: 0; font-size: 14px;">
        <strong>💡 提示：</strong> 本系統採用專業級設計與最新 AI 技術，為您提供全方位的量化交易解決方案
    </p>
</div>
""", unsafe_allow_html=True)
