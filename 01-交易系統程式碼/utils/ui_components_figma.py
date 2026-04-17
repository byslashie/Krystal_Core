"""
🎨 Figma風格UI組件 - 精確複製Figma設計的Streamlit實現
針對CryptoCrack參考設計最佳化
"""

# ============================================================================
# 亮色系統 - 完全按照Figma設計
# ============================================================================

LIGHT_COLORS = {
    # 背景
    "page_bg": "#F5F0FF",        # 淡紫粉色頁面背景
    "card_bg": "#FFFFFF",        # 純白卡片
    "sidebar_bg": "#FFFFFF",     # 白色側邊欄
    "hover_bg": "#F9F7FF",       # 懸停背景

    # 文字
    "text_primary": "#1A1A2E",   # 深色主文字
    "text_secondary": "#6B7280", # 灰色次文字
    "text_tertiary": "#9CA3AF",  # 淺灰輔助文字

    # 邊框
    "border": "#E8E0FF",         # 淡紫邊框
    "border_light": "#F0E8FF",   # 更淡的邊框

    # 功能色
    "primary": "#6B21A8",        # 紫色
    "success": "#10B981",        # 綠色
    "warning": "#F59E0B",        # 橙色
    "error": "#EF4444",          # 紅色

    # 漸變
    "success_gradient": "linear-gradient(135deg, #10B981 0%, #06B6D4 100%)",
    "chart_gradient_1": "linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%)",
    "chart_gradient_2": "linear-gradient(135deg, #45B7D1 0%, #96CEB4 100%)",
}

# ============================================================================
# Figma風格的CSS
# ============================================================================

def get_figma_css():
    """獲取完全按照Figma設計的CSS"""
    return """
    <style>
        /* 全局樣式 */
        * {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            box-sizing: border-box;
        }

        /* 頁面背景 */
        body, .main {
            background: linear-gradient(180deg, #F5F0FF 0%, #FFFFFF 100%);
            color: #1A1A2E;
        }

        /* 側邊欄 */
        [data-testid="stSidebar"] {
            background: white;
            border-right: 1px solid #E8E0FF;
        }

        /* 標題 - 漸變文字 */
        h1 {
            background: linear-gradient(135deg, #6B21A8 0%, #4F46E5 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 32px;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin-bottom: 32px;
        }

        h2 {
            color: #1A1A2E;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 16px;
            letter-spacing: -0.3px;
        }

        h3 {
            color: #1A1A2E;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
        }

        /* 按鈕 - 精確的Figma風格 */
        .stButton > button {
            background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25) !important;
            transition: all 0.2s ease !important;
            cursor: pointer !important;
        }

        .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 16px rgba(16, 185, 129, 0.35) !important;
        }

        .stButton > button:active {
            transform: translateY(0) !important;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25) !important;
        }

        /* 卡片容器 - 精確的Figma風格 */
        .figma-card {
            background: white;
            border: 1px solid #E8E0FF;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .figma-card:hover {
            border-color: #D8C8FF;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
            transform: translateY(-2px);
        }

        /* 輸入框 */
        .stTextInput input, .stNumberInput input, .stSelectbox select,
        .stTextArea textarea, .stDateInput input {
            background: white !important;
            border: 1px solid #E8E0FF !important;
            border-radius: 8px !important;
            color: #1A1A2E !important;
            padding: 10px 16px !important;
            font-size: 14px !important;
            transition: all 0.2s ease !important;
        }

        .stTextInput input:focus, .stNumberInput input:focus,
        .stSelectbox select:focus, .stTextArea textarea:focus {
            border-color: #6B21A8 !important;
            box-shadow: 0 0 0 3px rgba(107, 33, 168, 0.1) !important;
            outline: none !important;
        }

        /* 表格 */
        .dataframe {
            background: white !important;
            border-collapse: collapse !important;
            border: 1px solid #E8E0FF !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }

        .dataframe thead tr {
            background: linear-gradient(90deg, #F9F7FF 0%, #F5F0FF 100%) !important;
            border-bottom: 2px solid #E8E0FF !important;
        }

        .dataframe thead th {
            color: #6B7280;
            font-weight: 600;
            padding: 12px;
            text-align: left;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .dataframe tbody td {
            color: #1A1A2E;
            padding: 12px;
            border-bottom: 1px solid #F0E8FF;
            font-size: 14px;
        }

        .dataframe tbody tr:hover {
            background: #F9F7FF !important;
        }

        /* 標籤頁 */
        .stTabs [data-baseweb="tab-list"] button {
            color: #9CA3AF;
            border: none;
            border-bottom: 2px solid transparent;
            padding: 12px 16px;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: #6B21A8 !important;
            border-bottom-color: #6B21A8 !important;
        }

        /* 分割線 */
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #E8E0FF, transparent);
            margin: 24px 0;
        }

        /* 訊息框 */
        .stSuccess {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(20, 184, 166, 0.08) 100%) !important;
            border-left: 4px solid #10B981 !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
        }

        .stError {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(248, 113, 113, 0.08) 100%) !important;
            border-left: 4px solid #EF4444 !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
        }

        .stWarning {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(251, 191, 36, 0.08) 100%) !important;
            border-left: 4px solid #F59E0B !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
        }

        .stInfo {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(96, 165, 250, 0.08) 100%) !important;
            border-left: 4px solid #3B82F6 !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
        }

        /* 展開器 */
        .streamlit-expanderHeader {
            background: #F9F7FF;
            border: 1px solid #E8E0FF;
            border-radius: 8px;
            padding: 12px 16px;
        }
    </style>
    """


# ============================================================================
# Figma風格的組件函數
# ============================================================================

def apply_figma_theme(st_obj):
    """應用Figma風格主題"""
    st_obj.markdown(get_figma_css(), unsafe_allow_html=True)


def create_metric_card(label: str, value: str, change: str = "", icon: str = ""):
    """
    創建Figma風格的指標卡片

    參數:
    - label: 標籤 (如 "年化報酬")
    - value: 主數值 (如 "15.5%")
    - change: 變化指示 (如 "+2.5%")
    - icon: emoji圖標
    """
    change_color = "#10B981" if (change.startswith("+") or not change) else "#EF4444"
    change_html = f'<span style="color: {change_color}; font-size: 12px; font-weight: 600;">{change}</span>' if change else ''

    return f"""
    <div class="figma-card" style="min-height: 100px; display: flex; flex-direction: column; justify-content: space-between;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <span style="color: #9CA3AF; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                {icon} {label}
            </span>
            {change_html}
        </div>
        <div style="
            background: linear-gradient(135deg, #6B21A8 0%, #4F46E5 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 32px;
            font-weight: 700;
            line-height: 1;
        ">
            {value}
        </div>
    </div>
    """


def create_chart_card(title: str, content_html: str):
    """
    創建Figma風格的圖表卡片

    參數:
    - title: 卡片標題
    - content_html: 圖表的HTML或Streamlit圖表對象
    """
    return f"""
    <div class="figma-card">
        <h3 style="margin: 0 0 20px 0; color: #1A1A2E; font-size: 16px; font-weight: 600;">
            {title}
        </h3>
        {content_html}
    </div>
    """


def create_section_header(title: str, subtitle: str = ""):
    """創建Figma風格的分段標題"""
    subtitle_html = f'<p style="color: #9CA3AF; font-size: 14px; margin: 4px 0 0 0;">{subtitle}</p>' if subtitle else ''

    return f"""
    <div style="margin-bottom: 24px;">
        <h2 style="margin: 0; color: #1A1A2E; font-size: 20px; font-weight: 700;">
            {title}
        </h2>
        {subtitle_html}
    </div>
    """


def create_gradient_button(text: str, icon: str = ""):
    """創建Figma風格的漸變按鈕HTML"""
    icon_html = f"<span style='margin-right: 8px;'>{icon}</span>" if icon else ""

    return f"""
    <button style="
        background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        font-family: inherit;
    ">
        {icon_html}{text}
    </button>
    """


def create_stat_row(metrics: list):
    """
    創建Figma風格的指標行

    參數:
    - metrics: 列表，每個元素是 (label, value, change, icon)
    """
    html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">'

    for label, value, change, icon in metrics:
        html += create_metric_card(label, value, change, icon)

    html += '</div>'

    return html


if __name__ == "__main__":
    print("🎨 Figma Style Components Module Loaded!")
