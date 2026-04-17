"""
🎨 激進的Figma風格CSS重寫 - 完全覆蓋Streamlit預設
使用最強力度的CSS選擇器和 !important 標記
"""

def get_aggressive_figma_css():
    """
    獲取激進的Figma風格CSS - 完全覆蓋Streamlit預設樣式
    包含所有可能的選擇器和!important標記
    """
    return """
    <style>
        /* ============ 全局重置 ============ */
        * {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif !important;
        }

        html, body {
            background: linear-gradient(180deg, #F5F0FF 0%, #FFFFFF 100%) !important;
            color: #1A1A2E !important;
        }

        /* ============ Streamlit容器 ============ */
        .main {
            background: linear-gradient(180deg, #F5F0FF 0%, #FFFFFF 100%) !important;
            color: #1A1A2E !important;
        }

        .stApp {
            background: linear-gradient(180deg, #F5F0FF 0%, #FFFFFF 100%) !important;
        }

        [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #F5F0FF 0%, #FFFFFF 100%) !important;
        }

        /* ============ 側邊欄 ============ */
        [data-testid="stSidebar"] {
            background: #FFFFFF !important;
            border-right: 1px solid #E8E0FF !important;
        }

        [data-testid="stSidebar"] > div:first-child {
            background: #FFFFFF !important;
        }

        .css-1d391kg {
            background: #FFFFFF !important;
        }

        /* ============ 標題樣式 ============ */
        h1, h2, h3, h4, h5, h6 {
            color: #1A1A2E !important;
            font-weight: 700 !important;
        }

        h1 {
            font-size: 32px !important;
            margin-bottom: 32px !important;
            letter-spacing: -0.5px !important;
        }

        h2 {
            font-size: 20px !important;
            margin-bottom: 16px !important;
            letter-spacing: -0.3px !important;
        }

        h3 {
            font-size: 18px !important;
            margin-bottom: 12px !important;
            color: #1A1A2E !important;
        }

        /* ============ 按鈕 ============ */
        .stButton > button {
            background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25) !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            height: auto !important;
            min-height: 44px !important;
        }

        .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 16px rgba(16, 185, 129, 0.35) !important;
        }

        .stButton > button:active {
            transform: translateY(0) !important;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25) !important;
        }

        /* ============ 輸入框 ============ */
        .stTextInput input,
        .stNumberInput input,
        .stSelectbox select,
        .stTextArea textarea,
        .stDateInput input,
        .stTimeInput input,
        .stMultiSelect div > div {
            background: white !important;
            border: 1px solid #E8E0FF !important;
            border-radius: 8px !important;
            color: #1A1A2E !important;
            padding: 10px 16px !important;
            font-size: 14px !important;
            transition: all 0.2s ease !important;
            font-family: inherit !important;
        }

        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stSelectbox select:focus,
        .stTextArea textarea:focus {
            border-color: #6B21A8 !important;
            box-shadow: 0 0 0 3px rgba(107, 33, 168, 0.1) !important;
            outline: none !important;
        }

        /* ============ 表格 ============ */
        .dataframe {
            background: white !important;
            border-collapse: collapse !important;
            border: 1px solid #E8E0FF !important;
            border-radius: 12px !important;
        }

        .dataframe thead {
            background: linear-gradient(90deg, #F9F7FF 0%, #F5F0FF 100%) !important;
        }

        .dataframe thead tr {
            border-bottom: 2px solid #E8E0FF !important;
        }

        .dataframe thead th {
            color: #6B7280 !important;
            font-weight: 600 !important;
            padding: 12px !important;
            text-align: left !important;
            font-size: 12px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            background: linear-gradient(90deg, #F9F7FF 0%, #F5F0FF 100%) !important;
            border: none !important;
        }

        .dataframe tbody {
            background: white !important;
        }

        .dataframe tbody tr {
            border-bottom: 1px solid #F0E8FF !important;
            transition: background 0.2s ease !important;
        }

        .dataframe tbody tr:hover {
            background: #F9F7FF !important;
        }

        .dataframe tbody td {
            color: #1A1A2E !important;
            padding: 12px !important;
            font-size: 14px !important;
            border: none !important;
        }

        /* ============ 標籤頁 ============ */
        .stTabs [data-baseweb="tab-list"] {
            border-bottom: 1px solid #E8E0FF !important;
            gap: 16px !important;
        }

        .stTabs [data-baseweb="tab-list"] button {
            color: #9CA3AF !important;
            border: none !important;
            border-bottom: 2px solid transparent !important;
            padding: 12px 16px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
            background: transparent !important;
            font-size: 14px !important;
        }

        .stTabs [data-baseweb="tab-list"] button:hover {
            color: #6B21A8 !important;
        }

        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: #6B21A8 !important;
            border-bottom-color: #6B21A8 !important;
            font-weight: 600 !important;
        }

        /* ============ 警告/成功/錯誤框 ============ */
        .stSuccess {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(20, 184, 166, 0.08) 100%) !important;
            border-left: 4px solid #10B981 !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            border-top: none !important;
            border-right: none !important;
            border-bottom: none !important;
        }

        .stError {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(248, 113, 113, 0.08) 100%) !important;
            border-left: 4px solid #EF4444 !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            border-top: none !important;
            border-right: none !important;
            border-bottom: none !important;
        }

        .stWarning {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(251, 191, 36, 0.08) 100%) !important;
            border-left: 4px solid #F59E0B !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            border-top: none !important;
            border-right: none !important;
            border-bottom: none !important;
        }

        .stInfo {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(96, 165, 250, 0.08) 100%) !important;
            border-left: 4px solid #3B82F6 !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            border-top: none !important;
            border-right: none !important;
            border-bottom: none !important;
        }

        /* ============ 展開器 ============ */
        .streamlit-expanderHeader {
            background: #F9F7FF !important;
            border: 1px solid #E8E0FF !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            color: #1A1A2E !important;
        }

        .streamlit-expanderHeader:hover {
            background: #F0E8FF !important;
        }

        /* ============ 文本顏色 ============ */
        p {
            color: #1A1A2E !important;
            font-size: 14px !important;
            line-height: 1.6 !important;
        }

        /* ============ 分割線 ============ */
        hr {
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg, transparent, #E8E0FF, transparent) !important;
            margin: 24px 0 !important;
        }

        /* ============ 代碼塊 ============ */
        pre {
            background: #F9F7FF !important;
            border: 1px solid #E8E0FF !important;
            border-radius: 8px !important;
            padding: 16px !important;
            color: #1A1A2E !important;
        }

        code {
            background: #F9F7FF !important;
            color: #6B21A8 !important;
            padding: 2px 6px !important;
            border-radius: 4px !important;
            font-family: 'Monaco', 'Menlo', monospace !important;
        }

        /* ============ 複選框/單選框 ============ */
        .stCheckbox, .stRadio {
            color: #1A1A2E !important;
        }

        /* ============ 滑塊 ============ */
        .stSlider > div > div > div > div {
            background: linear-gradient(90deg, #10B981 0%, #06B6D4 100%) !important;
        }

        /* ============ 鏈接 ============ */
        a {
            color: #6B21A8 !important;
            text-decoration: none !important;
        }

        a:hover {
            text-decoration: underline !important;
        }

        /* ============ 自定義卡片類 ============ */
        .figma-card {
            background: white !important;
            border: 1px solid #E8E0FF !important;
            border-radius: 12px !important;
            padding: 20px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        .figma-card:hover {
            border-color: #D8C8FF !important;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08) !important;
            transform: translateY(-2px) !important;
        }

        /* ============ 隱藏不需要的元素 ============ */
        #MainMenu {
            visibility: hidden !important;
            display: none !important;
        }

        footer {
            visibility: hidden !important;
            display: none !important;
        }

        header {
            visibility: hidden !important;
            display: none !important;
        }

        .stDeployButton {
            visibility: hidden !important;
            display: none !important;
        }

        /* ============ Plotly圖表 ============ */
        .plotly-graph-div {
            background: white !important;
            border-radius: 12px !important;
        }

        .modebar {
            display: none !important;
        }

        /* ============ 響應式設計 ============ */
        @media (max-width: 640px) {
            h1 {
                font-size: 24px !important;
            }

            h2 {
                font-size: 18px !important;
            }

            .stButton > button {
                width: 100% !important;
            }
        }
    </style>
    """


def apply_aggressive_figma_theme(st):
    """
    應用激進的Figma主題到整個Streamlit應用
    這個函數應該在頁面最上面調用
    """
    st.markdown(get_aggressive_figma_css(), unsafe_allow_html=True)


# ============================================================================
# 簡化的組件函數
# ============================================================================

def create_card(content_html: str, css_class: str = "figma-card"):
    """
    創建自定義卡片

    使用示例:
    st.markdown(create_card(
        '<h3>標題</h3><p>內容</p>'
    ), unsafe_allow_html=True)
    """
    return f'<div class="{css_class}">{content_html}</div>'


def create_metric_card_simple(label: str, value: str, change: str = "", icon: str = ""):
    """簡化版的指標卡片"""
    change_html = f'<span style="color: #10B981; font-size: 12px; font-weight: 600;">{change}</span>' if change else ''

    return f'''
    <div class="figma-card" style="min-height: 100px;">
        <div style="display: flex; justify-content: space-between;">
            <span style="color: #9CA3AF; font-size: 12px; font-weight: 600; text-transform: uppercase;">
                {icon} {label}
            </span>
            {change_html}
        </div>
        <div style="
            font-size: 28px;
            font-weight: 700;
            color: #6B21A8;
            margin-top: 12px;
        ">
            {value}
        </div>
    </div>
    '''


if __name__ == "__main__":
    print("🎨 Aggressive Figma CSS Theme Loaded!")
    print("Use: apply_aggressive_figma_theme(st)")
