"""
🎨 现代AI交易系统设计主题系统 - 科技紫蓝系
提供一致的颜色、样式、和UI组件定义
作者: Krystal AI Trading System
"""

# ============================================================================
# 🌈 色彩系统 (Color Palette) - 科技紫蓝系
# ============================================================================

# 主色调 - 深紫蓝（科技感）
PRIMARY_GRADIENT = ["#5B47D9", "#4F46E5", "#4338CA"]  # 深紫->纯紫->深紫
PRIMARY_LIGHT = "#8B7FDB"
PRIMARY_DARK = "#2C1F5F"

# 辅助色 - 青色系（现代感）
SECONDARY_LIGHT = "#06B6D4"  # 青色
SECONDARY_LIGHTER = "#22D3EE"  # 浅青
SECONDARY_DARK = "#0891B2"  # 深青

# 强调色 - 粉紫系（柔和感）
ACCENT_PINK = "#EC4899"
ACCENT_PINK_LIGHT = "#F472B6"
ACCENT_PURPLE = "#D946EF"

# 成功色
SUCCESS_COLOR = "#10B981"  # 绿色
SUCCESS_LIGHT = "#6EE7B7"
SUCCESS_DARK = "#059669"

# 警告色
WARNING_COLOR = "#F59E0B"  # 琥珀色
WARNING_LIGHT = "#FCD34D"
WARNING_DARK = "#D97706"

# 错误色
ERROR_COLOR = "#EF4444"  # 红色
ERROR_LIGHT = "#FCA5A5"
ERROR_DARK = "#DC2626"

# 信息色
INFO_COLOR = "#3B82F6"  # 蓝色
INFO_LIGHT = "#93C5FD"
INFO_DARK = "#1D4ED8"

# 背景色
BG_WHITE = "#FFFFFF"
BG_LIGHT = "#F8FAFC"
BG_LIGHTER = "#F1F5F9"
BG_DARK = "#0F172A"

# 文本色
TEXT_DARK = "#1F2937"
TEXT_MEDIUM = "#4B5563"
TEXT_LIGHT = "#9CA3AF"
TEXT_LIGHTEST = "#D1D5DB"

# 边框色
BORDER_LIGHT = "#E5E7EB"
BORDER_MEDIUM = "#D1D5DB"
BORDER_DARK = "#9CA3AF"

# ============================================================================
# 💅 品牌渐变色 (Gradients)
# ============================================================================

GRADIENT_AI_TECH = "linear-gradient(135deg, #5B47D9 0%, #06B6D4 100%)"  # 紫->青
GRADIENT_FUTURE = "linear-gradient(135deg, #4F46E5 0%, #EC4899 100%)"   # 紫->粉
GRADIENT_PREMIUM = "linear-gradient(135deg, #5B47D9 0%, #D946EF 100%)"  # 紫->粉紫
GRADIENT_VIBRANT = "linear-gradient(135deg, #06B6D4 0%, #10B981 100%)"  # 青->绿

GRADIENT_PAGE_BG = "linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)"  # 微妙渐变

# ============================================================================
# 🔤 排版系统 (Typography)
# ============================================================================

FONT_FAMILY = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

TYPOGRAPHY = {
    "h1": {"size": 32, "weight": 700, "line_height": 1.2},
    "h2": {"size": 28, "weight": 700, "line_height": 1.3},
    "h3": {"size": 24, "weight": 600, "line_height": 1.4},
    "h4": {"size": 20, "weight": 600, "line_height": 1.4},
    "body_lg": {"size": 16, "weight": 400, "line_height": 1.6},
    "body": {"size": 14, "weight": 400, "line_height": 1.6},
    "body_sm": {"size": 12, "weight": 400, "line_height": 1.5},
    "label": {"size": 12, "weight": 500, "line_height": 1.4},
    "caption": {"size": 11, "weight": 400, "line_height": 1.4},
}

# ============================================================================
# 🎯 圆角系统 (Border Radius)
# ============================================================================

RADIUS = {
    "sm": 6,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "full": 9999,
}

# ============================================================================
# 🌑 阴影系统 (Box Shadows)
# ============================================================================

SHADOWS = {
    "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
    "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    "2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
    "glow": "0 0 20px rgba(91, 71, 217, 0.3)",
    "glow_cyan": "0 0 20px rgba(6, 182, 212, 0.3)",
}

# ============================================================================
# 🎨 完整CSS主题
# ============================================================================

def get_theme_css():
    """获取完整的主题CSS"""
    return """
    <style>
        :root {
            --primary: #5B47D9;
            --secondary: #06B6D4;
            --accent: #EC4899;
            --success: #10B981;
            --warning: #F59E0B;
            --error: #EF4444;
            --info: #3B82F6;
            --bg: #FFFFFF;
            --bg-light: #F8FAFC;
            --text: #1F2937;
            --text-light: #9CA3AF;
            --border: #E5E7EB;
        }

        * {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        body {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            color: #1F2937;
        }

        .main {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        }

        /* 标题样式 */
        h1 {
            background: linear-gradient(135deg, #5B47D9 0%, #06B6D4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: auto;
            background-clip: text;
            color: #5B47D9;
            font-weight: 700;
            font-size: 32px;
            margin-bottom: 24px;
        }

        h2 {
            color: #5B47D9;
            font-weight: 700;
            font-size: 28px;
            margin-bottom: 16px;
        }

        h3 {
            color: #1F2937;
            font-weight: 600;
            font-size: 24px;
            margin-bottom: 12px;
        }

        /* 按钮样式 */
        .stButton > button {
            background: linear-gradient(135deg, #5B47D9 0%, #4F46E5 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 10px 24px !important;
            font-weight: 600 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 6px -1px rgba(91, 71, 217, 0.2) !important;
        }

        .stButton > button:hover {
            box-shadow: 0 10px 15px -3px rgba(91, 71, 217, 0.3) !important;
            transform: translateY(-2px) !important;
        }

        .stButton > button:active {
            transform: translateY(0) !important;
        }

        /* 输入框样式 */
        .stTextInput input,
        .stNumberInput input,
        .stSelectbox select,
        .stTextArea textarea,
        .stColorPicker input,
        .stDateInput input,
        .stTimeInput input {
            border: 2px solid #E5E7EB !important;
            border-radius: 12px !important;
            padding: 10px 16px !important;
            font-size: 14px !important;
            background-color: #FFFFFF !important;
            color: #1F2937 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stSelectbox select:focus,
        .stTextArea textarea:focus {
            border-color: #5B47D9 !important;
            box-shadow: 0 0 0 3px rgba(91, 71, 217, 0.1) !important;
        }

        /* 侧边栏 */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
            border-right: 1px solid #E5E7EB;
        }

        [data-testid="stSidebar"] > div > div {
            padding: 16px !important;
        }

        /* 标签页 */
        .stTabs [data-baseweb="tab-list"] button {
            color: #9CA3AF;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: #5B47D9 !important;
            border-bottom: 3px solid #5B47D9 !important;
        }

        /* 容器背景 */
        .metric-card {
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .metric-card:hover {
            border-color: #5B47D9;
            box-shadow: 0 0 20px rgba(91, 71, 217, 0.2);
            transform: translateY(-4px);
        }

        /* 成功/警告/错误样式 */
        .success { color: #10B981; background-color: rgba(16, 185, 129, 0.1); }
        .warning { color: #F59E0B; background-color: rgba(245, 158, 11, 0.1); }
        .error { color: #EF4444; background-color: rgba(239, 68, 68, 0.1); }
        .info { color: #3B82F6; background-color: rgba(59, 130, 246, 0.1); }

        /* 分割线 */
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #E5E7EB, transparent);
            margin: 24px 0;
        }

        /* 代码块 */
        pre {
            background-color: #F1F5F9 !important;
            border: 1px solid #E5E7EB !important;
            border-radius: 12px !important;
            padding: 16px !important;
        }

        /* 表格 */
        .dataframe {
            border-collapse: collapse !important;
            border: 1px solid #E5E7EB !important;
            border-radius: 12px !important;
        }

        .dataframe thead tr {
            background: linear-gradient(135deg, #5B47D9 0%, #4F46E5 100%) !important;
            color: white !important;
        }

        .dataframe th {
            border: 1px solid #D1D5DB !important;
            padding: 12px !important;
            font-weight: 600 !important;
            text-align: left !important;
        }

        .dataframe td {
            border: 1px solid #E5E7EB !important;
            padding: 12px !important;
        }

        .dataframe tbody tr:hover {
            background-color: #F8FAFC !important;
        }

        /* 警告和错误消息 */
        .stAlert {
            border-radius: 12px !important;
            border-left: 4px solid #5B47D9 !important;
        }

        /* 进度条 */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #5B47D9 0%, #06B6D4 100%) !important;
        }

        /* 复选框和单选按钮 */
        .stCheckbox, .stRadio {
            color: #1F2937;
        }

        /* 滑块 */
        .stSlider > div > div {
            background: linear-gradient(90deg, #5B47D9 0%, #06B6D4 100%) !important;
        }

        /* 展开器 */
        .streamlit-expanderHeader {
            background-color: #F8FAFC;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
        }
    </style>
    """


# ============================================================================
# 🧩 UI 组件函数
# ============================================================================

def apply_theme(st):
    """应用完整主题"""
    st.markdown(get_theme_css(), unsafe_allow_html=True)


def format_metric(label: str, value: str, color: str = "#5B47D9", icon: str = ""):
    """格式化指标卡片"""
    return f"""
    <div style="
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s;
    ">
        <div style="color: #9CA3AF; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
            {icon} {label}
        </div>
        <div style="color: {color}; font-size: 28px; font-weight: 700; line-height: 1.2;">
            {value}
        </div>
    </div>
    """


def create_header(title: str, subtitle: str = ""):
    """创建专业标题区域"""
    html = f"""
    <div style="
        padding: 24px 0;
        border-bottom: 2px solid #E5E7EB;
        margin-bottom: 24px;
    ">
        <h1 style="
            margin: 0;
            background: linear-gradient(135deg, #5B47D9 0%, #06B6D4 100%);
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
            color: #9CA3AF;
            font-size: 14px;
            margin: 8px 0 0 0;
        ">{subtitle}</p>
        """
    html += "</div>"
    return html


def create_info_box(title: str, content: str, icon: str = "ℹ️", color: str = "#3B82F6"):
    """创建信息框"""
    return f"""
    <div style="
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(6, 182, 212, 0.05) 100%);
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
    ">
        <div style="
            font-weight: 600;
            color: #1F2937;
            margin-bottom: 8px;
        ">{icon} {title}</div>
        <div style="
            color: #4B5563;
            font-size: 14px;
            line-height: 1.6;
        ">{content}</div>
    </div>
    """


def get_stat_color(value: float, threshold_positive: float = 0) -> str:
    """根据数值返回颜色"""
    if value > threshold_positive:
        return "#10B981"  # 成功绿
    elif value < -threshold_positive:
        return "#EF4444"  # 错误红
    else:
        return "#3B82F6"  # 信息蓝


if __name__ == "__main__":
    print("🎨 AI Trading System Theme Module Loaded!")
    print("Color Palette: Tech Purple-Blue System")
