"""
🎨 現代化交易系統UI主題 - 融合SmartAlgo深色 + CryptoCrack亮色風格
基於用戶提供的參考設計優化
"""

# ============================================================================
# 🌈 現代色彩系統
# ============================================================================

# 亮色系統 (CryptoCrack風格)
# ────────────────────────────────
LIGHT_MODE = {
    "bg_primary": "#F5F0FF",      # 淡紫粉色背景
    "bg_secondary": "#FFFFFF",    # 純白卡片
    "bg_tertiary": "#F9F7FF",     # 淡紫色背景
    "border": "#E8E0FF",          # 淡紫邊框
    "text_primary": "#1A1A2E",    # 深色文字
    "text_secondary": "#6B7280",  # 灰色文字
    "text_tertiary": "#9CA3AF",   # 淺灰文字

    # 漸變色
    "primary_gradient": "linear-gradient(135deg, #6B21A8 0%, #4F46E5 100%)",  # 紫→紫藍
    "success_gradient": "linear-gradient(135deg, #10B981 0%, #06B6D4 100%)",  # 綠→青
    "chart_gradient": "linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%)",    # 彩虹

    # 功能色
    "primary": "#6B21A8",         # 紫色
    "success": "#10B981",         # 綠色
    "warning": "#F59E0B",         # 橙色
    "error": "#EF4444",           # 紅色
    "info": "#3B82F6",            # 藍色

    "chart_colors": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DFE6E9"]
}

# 暗色系統 (SmartAlgo風格)
# ────────────────────────────────
DARK_MODE = {
    "bg_primary": "#0F1419",      # 深藍黑主背景
    "bg_secondary": "#1A1F2E",    # 深卡片背景
    "bg_tertiary": "#232A3B",     # 稍淺背景
    "border": "#2D3748",          # 深邊框
    "text_primary": "#E5E7EB",    # 淡白文字
    "text_secondary": "#9CA3AF",  # 灰色文字
    "text_tertiary": "#6B7280",   # 淺灰文字

    # 漸變色
    "primary_gradient": "linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%)",  # 紫→藍
    "success_gradient": "linear-gradient(135deg, #10B981 0%, #14B8A6 100%)",  # 綠→青綠
    "chart_gradient": "linear-gradient(135deg, #EC4899 0%, #06B6D4 100%)",    # 粉→青

    # 功能色
    "primary": "#8B5CF6",         # 紫色（更亮）
    "success": "#10B981",         # 綠色
    "warning": "#FBBF24",         # 金色
    "error": "#F87171",           # 淺紅
    "info": "#60A5FA",            # 淺藍

    "chart_colors": ["#EC4899", "#06B6D4", "#8B5CF6", "#10B981", "#F59E0B", "#F87171"]
}

# ============================================================================
# 🎯 現代組件CSS
# ============================================================================

def get_modern_css(theme="light"):
    """獲取現代化CSS樣式"""

    if theme == "dark":
        colors = DARK_MODE
        sidebar_bg = "linear-gradient(180deg, #0F1419 0%, #1A1F2E 100%)"
        card_shadow = "0 4px 20px rgba(0, 0, 0, 0.5)"
    else:
        colors = LIGHT_MODE
        sidebar_bg = "linear-gradient(180deg, #F5F0FF 0%, #FFFFFF 100%)"
        card_shadow = "0 2px 8px rgba(0, 0, 0, 0.1)"

    return f"""
    <style>
        * {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}

        /* 背景和基礎 */
        body, .main {{
            background: {colors['bg_primary']};
            color: {colors['text_primary']};
        }}

        /* 側邊欄 (SmartAlgo風格) */
        [data-testid="stSidebar"] {{
            background: {sidebar_bg};
            border-right: 1px solid {colors['border']};
        }}

        /* 標題 */
        h1 {{
            background: {colors['primary_gradient']};
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 32px;
            font-weight: 800;
            margin-bottom: 24px;
        }}

        h2 {{
            color: {colors['primary']};
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 16px;
        }}

        h3 {{
            color: {colors['text_primary']};
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
        }}

        /* 按鈕 - 漸變風格 */
        .stButton > button {{
            background: {colors['success_gradient']} !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 10px 24px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
        }}

        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4) !important;
        }}

        /* 輸入框 */
        .stTextInput input, .stNumberInput input, .stSelectbox select,
        .stTextArea textarea, .stDateInput input {{
            background: {colors['bg_secondary']} !important;
            border: 2px solid {colors['border']} !important;
            border-radius: 8px !important;
            color: {colors['text_primary']} !important;
            padding: 12px 16px !important;
            transition: all 0.3s ease !important;
        }}

        .stTextInput input:focus, .stNumberInput input:focus,
        .stSelectbox select:focus, .stTextArea textarea:focus {{
            border-color: {colors['primary']} !important;
            box-shadow: 0 0 0 3px rgba(107, 33, 168, 0.1) !important;
        }}

        /* 卡片組件 */
        .metric-card, .chart-box {{
            background: {colors['bg_secondary']};
            border: 1px solid {colors['border']};
            border-radius: 12px;
            padding: 24px;
            box-shadow: {card_shadow};
            transition: all 0.3s ease;
        }}

        .metric-card:hover {{
            border-color: {colors['primary']};
            box-shadow: 0 8px 24px rgba(107, 33, 168, 0.15);
            transform: translateY(-4px);
        }}

        /* 指標數值 */
        .metric-value {{
            background: {colors['primary_gradient']};
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 32px;
            font-weight: 800;
            margin: 8px 0;
        }}

        .metric-label {{
            color: {colors['text_secondary']};
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }}

        /* 分割線 */
        hr {{
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, {colors['border']}, transparent);
            margin: 24px 0;
        }}

        /* 表格 */
        .dataframe {{
            background: {colors['bg_secondary']};
        }}

        .dataframe thead tr {{
            background: {colors['primary_gradient']};
        }}

        .dataframe thead th {{
            color: white;
            font-weight: 600;
            padding: 12px;
        }}

        .dataframe tbody td {{
            color: {colors['text_primary']};
            padding: 12px;
            border-bottom: 1px solid {colors['border']};
        }}

        .dataframe tbody tr:hover {{
            background: {colors['bg_tertiary']};
        }}

        /* 警告/成功/信息框 */
        .stSuccess {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%) !important;
            border-left: 4px solid {colors['success']} !important;
        }}

        .stError {{
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(248, 113, 113, 0.1) 100%) !important;
            border-left: 4px solid {colors['error']} !important;
        }}

        .stWarning {{
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(251, 191, 36, 0.1) 100%) !important;
            border-left: 4px solid {colors['warning']} !important;
        }}

        .stInfo {{
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(96, 165, 250, 0.1) 100%) !important;
            border-left: 4px solid {colors['info']} !important;
        }}

        /* 標籤頁 */
        .stTabs [data-baseweb="tab-list"] button {{
            color: {colors['text_secondary']};
            border: none;
            transition: all 0.3s ease;
        }}

        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
            color: {colors['primary']} !important;
            border-bottom: 3px solid {colors['primary']} !important;
        }}

        /* 展開器 */
        .streamlit-expanderHeader {{
            background: {colors['bg_tertiary']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
        }}
    </style>
    """


# ============================================================================
# 🧩 現代化快速組件
# ============================================================================

def apply_modern_theme(st_obj, theme="light"):
    """應用現代化主題"""
    st_obj.markdown(get_modern_css(theme), unsafe_allow_html=True)


def create_stat_card(label: str, value: str, change: str = "", icon: str = "",
                     theme: str = "light", accent_color: str = None):
    """
    創建現代統計卡片 (SmartAlgo風格)

    參數:
    - label: 標籤文字
    - value: 主數值
    - change: 變化百分比 (如 "+2.5%")
    - icon: 圖標emoji
    - theme: "light" 或 "dark"
    - accent_color: 自定義強調色
    """
    colors = DARK_MODE if theme == "dark" else LIGHT_MODE

    if accent_color is None:
        accent_color = colors['primary']

    change_color = "#10B981" if change.startswith("+") else "#EF4444"

    return f"""
    <div style="
        background: {colors['bg_secondary']};
        border: 1px solid {colors['border']};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    ">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
            <span style="
                color: {colors['text_secondary']};
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
            ">{icon} {label}</span>
            {f'<span style="color: {change_color}; font-size: 12px; font-weight: 700;">{change}</span>' if change else ''}
        </div>
        <div style="
            background: linear-gradient(135deg, {accent_color} 0%, {colors['primary']} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 28px;
            font-weight: 800;
        ">{value}</div>
    </div>
    """


def create_gradient_button_html(text: str, theme: str = "light"):
    """創建漸變按鈕HTML"""
    colors = DARK_MODE if theme == "dark" else LIGHT_MODE

    return f"""
    <button style="
        background: {colors['success_gradient']};
        color: white;
        border: none;
        padding: 12px 32px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    ">
        {text}
    </button>
    """


def create_chart_config(theme: str = "light"):
    """
    返回圖表配置 (Plotly)
    """
    colors = DARK_MODE if theme == "dark" else LIGHT_MODE

    return {
        "template": "plotly_dark" if theme == "dark" else "plotly",
        "plot_bgcolor": colors['bg_secondary'],
        "paper_bgcolor": colors['bg_primary'],
        "font": {"family": "Arial, sans-serif", "size": 12, "color": colors['text_primary']},
        "margin": {"l": 50, "r": 50, "t": 50, "b": 50},
        "hovermode": "x unified",
        "colorway": colors['chart_colors'],
    }


def get_colors(theme: str = "light") -> dict:
    """獲取主題色彩"""
    return DARK_MODE if theme == "dark" else LIGHT_MODE


if __name__ == "__main__":
    print("🎨 Modern Theme Module Loaded!")
    print("Styles: SmartAlgo (Dark) + CryptoCrack (Light)")
