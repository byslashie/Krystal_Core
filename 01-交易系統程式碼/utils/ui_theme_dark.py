"""
🌙 現代AI交易系統暗色主題系統
提供專業深色模式與對應的色彩、樣式定義
"""

# ============================================================================
# 🌑 暗色系色彩系統 (Dark Mode Color Palette)
# ============================================================================

# 主色調 - 深紫蓝（科技感，暗色版本）
PRIMARY_GRADIENT_DARK = ["#7C5FFF", "#8B77FF", "#9A8FFF"]  # 更亮的紫色用於暗背景
PRIMARY_LIGHT_DARK = "#9A8FFF"
PRIMARY_DARK_DARK = "#5B47D9"

# 辅助色 - 青色系（現代感，暗色版本）
SECONDARY_LIGHT_DARK = "#13D9E8"  # 更亮的青色
SECONDARY_LIGHTER_DARK = "#4FE5F5"  # 浅青
SECONDARY_DARK_DARK = "#06B6D4"  # 深青

# 強調色 - 粉紫系（柔和感，暗色版本）
ACCENT_PINK_DARK = "#FF6BA6"
ACCENT_PINK_LIGHT_DARK = "#FF8CB8"
ACCENT_PURPLE_DARK = "#E646FF"

# 成功色
SUCCESS_COLOR_DARK = "#13E76E"  # 更亮的綠色
SUCCESS_LIGHT_DARK = "#4FF8A8"
SUCCESS_DARK_DARK = "#10B981"

# 警告色
WARNING_COLOR_DARK = "#FFB833"  # 更亮的黃色
WARNING_LIGHT_DARK = "#FFD180"
WARNING_DARK_DARK = "#F59E0B"

# 錯誤色
ERROR_COLOR_DARK = "#FF5555"  # 更亮的紅色
ERROR_LIGHT_DARK = "#FF9999"
ERROR_DARK_DARK = "#EF4444"

# 信息色
INFO_COLOR_DARK = "#5FA8FF"  # 更亮的藍色
INFO_LIGHT_DARK = "#8FC9FF"
INFO_DARK_DARK = "#3B82F6"

# 背景色 - 深色優先
BG_DARK_PRIMARY = "#0F172A"    # 深藍黑 (主背景)
BG_DARK_SECONDARY = "#1A2641"  # 中藍黑 (卡片背景)
BG_DARK_TERTIARY = "#243454"   # 淺藍黑 (懸停背景)
BG_DARK_LIGHT = "#2D3E5F"      # 邊框/分割線背景

# 文本色 - 暗色版本
TEXT_DARK_LIGHT = "#F0F4F8"     # 亮白文本
TEXT_DARK_MEDIUM = "#CBD5E1"    # 中灰文本
TEXT_DARK_LIGHT_GRAY = "#94A3B8" # 淺灰文本
TEXT_DARK_PLACEHOLDER = "#64748B" # 佔位符文本

# 邊框色 - 暗色版本
BORDER_DARK_LIGHT = "#334155"   # 淺邊框
BORDER_DARK_MEDIUM = "#475569"  # 中邊框
BORDER_DARK_DARK = "#64748B"    # 深邊框

# ============================================================================
# 💅 暗色品牌漸變色 (Dark Gradients)
# ============================================================================

GRADIENT_AI_TECH_DARK = "linear-gradient(135deg, #7C5FFF 0%, #13D9E8 100%)"  # 紫→青
GRADIENT_FUTURE_DARK = "linear-gradient(135deg, #8B77FF 0%, #FF6BA6 100%)"   # 紫→粉
GRADIENT_PREMIUM_DARK = "linear-gradient(135deg, #7C5FFF 0%, #E646FF 100%)"  # 紫→粉紫
GRADIENT_VIBRANT_DARK = "linear-gradient(135deg, #13D9E8 0%, #13E76E 100%)"  # 青→綠

GRADIENT_PAGE_BG_DARK = "linear-gradient(180deg, #0F172A 0%, #1A2641 100%)"  # 深漸變

# ============================================================================
# 🎨 完整CSS暗色主題
# ============================================================================

def get_theme_css_dark():
    """獲取完整的暗色主題CSS"""
    return """
    <style>
        :root {
            --primary-dark: #7C5FFF;
            --secondary-dark: #13D9E8;
            --accent-dark: #FF6BA6;
            --success-dark: #13E76E;
            --warning-dark: #FFB833;
            --error-dark: #FF5555;
            --info-dark: #5FА8FF;
            --bg-dark: #0F172A;
            --bg-dark-secondary: #1A2641;
            --text-dark-light: #F0F4F8;
            --border-dark: #334155;
        }

        * {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        body {
            background: linear-gradient(180deg, #0F172A 0%, #1A2641 100%);
            color: #F0F4F8;
        }

        .main {
            background: linear-gradient(180deg, #0F172A 0%, #1A2641 100%);
        }

        /* 標題樣式 - 亮漸變文字 */
        h1 {
            background: linear-gradient(135deg, #7C5FFF 0%, #13D9E8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            font-size: 32px;
            margin-bottom: 24px;
        }

        h2 {
            color: #7C5FFF;
            font-weight: 700;
            font-size: 28px;
            margin-bottom: 16px;
        }

        h3 {
            color: #F0F4F8;
            font-weight: 600;
            font-size: 24px;
            margin-bottom: 12px;
        }

        /* 按鈕樣式 */
        .stButton > button {
            background: linear-gradient(135deg, #7C5FFF 0%, #8B77FF 100%) !important;
            color: #F0F4F8 !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 10px 24px !important;
            font-weight: 600 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 15px rgba(124, 95, 255, 0.4) !important;
        }

        .stButton > button:hover {
            box-shadow: 0 10px 25px rgba(124, 95, 255, 0.6) !important;
            transform: translateY(-2px) !important;
        }

        .stButton > button:active {
            transform: translateY(0) !important;
        }

        /* 輸入框樣式 */
        .stTextInput input,
        .stNumberInput input,
        .stSelectbox select,
        .stTextArea textarea,
        .stColorPicker input,
        .stDateInput input,
        .stTimeInput input {
            border: 2px solid #334155 !important;
            border-radius: 12px !important;
            padding: 10px 16px !important;
            font-size: 14px !important;
            background-color: #1A2641 !important;
            color: #F0F4F8 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stSelectbox select:focus,
        .stTextArea textarea:focus {
            border-color: #7C5FFF !important;
            box-shadow: 0 0 0 3px rgba(124, 95, 255, 0.2) !important;
        }

        /* 側邊欄 */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0F172A 0%, #1A2641 100%) !important;
            border-right: 1px solid #334155;
        }

        [data-testid="stSidebar"] > div > div {
            padding: 16px !important;
        }

        /* 標籤頁 */
        .stTabs [data-baseweb="tab-list"] button {
            color: #94A3B8;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: #7C5FFF !important;
            border-bottom: 3px solid #7C5FFF !important;
        }

        /* 容器背景 */
        .metric-card {
            background: #1A2641;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .metric-card:hover {
            border-color: #7C5FFF;
            box-shadow: 0 0 20px rgba(124, 95, 255, 0.3);
            transform: translateY(-4px);
        }

        /* 成功/警告/錯誤樣式 */
        .success { color: #13E76E; background-color: rgba(19, 231, 110, 0.1); }
        .warning { color: #FFB833; background-color: rgba(255, 184, 51, 0.1); }
        .error { color: #FF5555; background-color: rgba(255, 85, 85, 0.1); }
        .info { color: #5FA8FF; background-color: rgba(95, 168, 255, 0.1); }

        /* 分割線 */
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #334155, transparent);
            margin: 24px 0;
        }

        /* 代碼塊 */
        pre {
            background-color: #0F172A !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
            padding: 16px !important;
            color: #CBD5E1 !important;
        }

        /* 表格 */
        .dataframe {
            border-collapse: collapse !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
        }

        .dataframe thead tr {
            background: linear-gradient(135deg, #7C5FFF 0%, #8B77FF 100%) !important;
            color: #F0F4F8 !important;
        }

        .dataframe th {
            border: 1px solid #475569 !important;
            padding: 12px !important;
            font-weight: 600 !important;
            text-align: left !important;
            color: #F0F4F8 !important;
        }

        .dataframe td {
            border: 1px solid #334155 !important;
            padding: 12px !important;
            color: #CBD5E1 !important;
        }

        .dataframe tbody tr:hover {
            background-color: #243454 !important;
        }

        /* 警告和錯誤消息 */
        .stAlert {
            border-radius: 12px !important;
            border-left: 4px solid #7C5FFF !important;
            background-color: rgba(124, 95, 255, 0.1) !important;
        }

        /* 進度條 */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #7C5FFF 0%, #13D9E8 100%) !important;
        }

        /* 複選框和單選按鈕 */
        .stCheckbox, .stRadio {
            color: #F0F4F8;
        }

        /* 滑塊 */
        .stSlider > div > div {
            background: linear-gradient(90deg, #7C5FFF 0%, #13D9E8 100%) !important;
        }

        /* 展開器 */
        .streamlit-expanderHeader {
            background-color: #1A2641;
            border: 1px solid #334155;
            border-radius: 12px;
        }

        /* Streamlit 訊息樣式 */
        .stSuccess { background-color: rgba(19, 231, 110, 0.1) !important; color: #13E76E !important; }
        .stInfo { background-color: rgba(95, 168, 255, 0.1) !important; color: #5FA8FF !important; }
        .stWarning { background-color: rgba(255, 184, 51, 0.1) !important; color: #FFB833 !important; }
        .stError { background-color: rgba(255, 85, 85, 0.1) !important; color: #FF5555 !important; }
    </style>
    """


# ============================================================================
# 🧩 快速組件函數（暗色版本）
# ============================================================================

def apply_theme_dark(st):
    """應用完整暗色主題"""
    st.markdown(get_theme_css_dark(), unsafe_allow_html=True)


def format_metric_dark(label: str, value: str, color: str = "#7C5FFF", icon: str = ""):
    """格式化指標卡片（暗色版本）"""
    return f"""
    <div style="
        background: #1A2641;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.3s;
    ">
        <div style="color: #94A3B8; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
            {icon} {label}
        </div>
        <div style="color: {color}; font-size: 28px; font-weight: 700; line-height: 1.2;">
            {value}
        </div>
    </div>
    """


def create_header_dark(title: str, subtitle: str = ""):
    """創建專業標題區域（暗色版本）"""
    html = f"""
    <div style="
        padding: 24px 0;
        border-bottom: 2px solid #334155;
        margin-bottom: 24px;
    ">
        <h1 style="
            margin: 0;
            background: linear-gradient(135deg, #7C5FFF 0%, #13D9E8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 32px;
            font-weight: 700;
        ">{title}</h1>
    """
    if subtitle:
        html += f"""
        <p style="
            color: #94A3B8;
            font-size: 14px;
            margin: 8px 0 0 0;
        ">{subtitle}</p>
        """
    html += "</div>"
    return html


def create_info_box_dark(title: str, content: str, icon: str = "ℹ️", color: str = "#5FA8FF"):
    """創建信息框（暗色版本）"""
    return f"""
    <div style="
        background: linear-gradient(135deg, rgba(124, 95, 255, 0.1) 0%, rgba(19, 217, 232, 0.1) 100%);
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
    ">
        <div style="
            font-weight: 600;
            color: #F0F4F8;
            margin-bottom: 8px;
        ">{icon} {title}</div>
        <div style="
            color: #CBD5E1;
            font-size: 14px;
            line-height: 1.6;
        ">{content}</div>
    </div>
    """


def get_stat_color_dark(value: float, threshold_positive: float = 0) -> str:
    """根據數值返回暗色版本顏色"""
    if value > threshold_positive:
        return "#13E76E"  # 成功綠
    elif value < -threshold_positive:
        return "#FF5555"  # 錯誤紅
    else:
        return "#5FA8FF"  # 信息藍


if __name__ == "__main__":
    print("🌙 Dark Mode Theme Module Loaded!")
    print("Color Palette: Tech Purple-Blue System (Dark Mode)")
