"""
🎨 主題切換器 - 在亮色和暗色模式之間切換
支援跨頁面的主題持久化
"""

import streamlit as st
from utils.ui_theme import get_theme_css
from utils.ui_theme_dark import get_theme_css_dark

# ============================================================================
# 主題管理
# ============================================================================

def init_theme():
    """初始化主題設定"""
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "light"  # 默認亮色模式


def toggle_theme():
    """切換主題"""
    st.session_state.theme_mode = "dark" if st.session_state.theme_mode == "light" else "light"


def get_current_theme():
    """獲取當前主題"""
    return st.session_state.get("theme_mode", "light")


def apply_theme_switcher(st_obj):
    """
    應用主題並添加切換按鈕

    使用方法：
    ```python
    import streamlit as st
    from utils.theme_switcher import apply_theme_switcher, create_theme_toggle_button

    apply_theme_switcher(st)
    create_theme_toggle_button()
    ```
    """
    init_theme()

    # 應用當前主題的CSS
    if get_current_theme() == "dark":
        st_obj.markdown(get_theme_css_dark(), unsafe_allow_html=True)
    else:
        st_obj.markdown(get_theme_css(), unsafe_allow_html=True)


def create_theme_toggle_button(position: str = "sidebar"):
    """
    創建主題切換按鈕

    參數:
    - position: "sidebar" (側邊欄) 或 "top" (頂部)
    """
    init_theme()

    current_theme = get_current_theme()
    button_text = "🌙 暗色模式" if current_theme == "light" else "☀️ 亮色模式"

    if position == "sidebar":
        if st.sidebar.button(button_text, use_container_width=True, key="theme_toggle"):
            toggle_theme()
            st.rerun()
    else:
        # 頂部放置
        col1, col2, col3 = st.columns([1, 1, 0.3])
        with col3:
            if st.button(button_text, key="theme_toggle"):
                toggle_theme()
                st.rerun()


def create_theme_selector():
    """創建主題選擇器（更高級的版本）"""
    init_theme()

    theme_options = {
        "☀️ 亮色模式": "light",
        "🌙 暗色模式": "dark"
    }

    selected_theme = st.sidebar.selectbox(
        "🎨 選擇主題",
        options=list(theme_options.keys()),
        index=0 if get_current_theme() == "light" else 1,
        key="theme_selector"
    )

    if theme_options[selected_theme] != get_current_theme():
        st.session_state.theme_mode = theme_options[selected_theme]
        st.rerun()


# ============================================================================
# 色彩方案對照表
# ============================================================================

def get_theme_colors(theme: str = None):
    """獲取指定主題的色彩方案"""
    if theme is None:
        theme = get_current_theme()

    if theme == "dark":
        return {
            "primary": "#7C5FFF",
            "secondary": "#13D9E8",
            "accent": "#FF6BA6",
            "success": "#13E76E",
            "warning": "#FFB833",
            "error": "#FF5555",
            "info": "#5FA8FF",
            "bg_primary": "#0F172A",
            "bg_secondary": "#1A2641",
            "text_primary": "#F0F4F8",
            "text_secondary": "#CBD5E1",
            "border": "#334155",
        }
    else:  # light
        return {
            "primary": "#5B47D9",
            "secondary": "#06B6D4",
            "accent": "#EC4899",
            "success": "#10B981",
            "warning": "#F59E0B",
            "error": "#EF4444",
            "info": "#3B82F6",
            "bg_primary": "#FFFFFF",
            "bg_secondary": "#F8FAFC",
            "text_primary": "#1F2937",
            "text_secondary": "#4B5563",
            "border": "#E5E7EB",
        }


# ============================================================================
# 實用工具函數
# ============================================================================

def get_color(color_name: str, theme: str = None) -> str:
    """
    根據名稱和主題獲取顏色

    使用例：
    ```python
    primary_color = get_color("primary")  # 獲取當前主題的主色
    success_color = get_color("success", theme="dark")  # 獲取暗色模式的成功色
    ```
    """
    if theme is None:
        theme = get_current_theme()

    colors = get_theme_colors(theme)
    return colors.get(color_name, "#000000")


def create_themed_box(title: str, content: str, theme_color: str = "primary"):
    """創建主題化的信息框"""
    theme = get_current_theme()
    colors = get_theme_colors(theme)

    color_value = colors.get(theme_color, colors["primary"])

    if theme == "dark":
        bg_color = "rgba(124, 95, 255, 0.1)"
        text_color = "#F0F4F8"
    else:
        bg_color = "rgba(91, 71, 217, 0.1)"
        text_color = "#1F2937"

    return f"""
    <div style="
        background: {bg_color};
        border-left: 4px solid {color_value};
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
    ">
        <div style="
            font-weight: 600;
            color: {text_color};
            margin-bottom: 8px;
        ">{title}</div>
        <div style="
            color: {'#CBD5E1' if theme == 'dark' else '#4B5563'};
            font-size: 14px;
            line-height: 1.6;
        ">{content}</div>
    </div>
    """


# ============================================================================
# 頁面範例代碼
# ============================================================================

EXAMPLE_CODE = """
# 📄 在Streamlit頁面中使用主題切換

```python
import streamlit as st
from utils.theme_switcher import apply_theme_switcher, create_theme_toggle_button

# 應用主題
apply_theme_switcher(st)

# 在側邊欄添加切換按鈕
create_theme_toggle_button(position="sidebar")

# 或在頂部添加
# create_theme_toggle_button(position="top")

# 設置頁面
st.set_page_config(layout="wide")

# 現在可以正常使用Streamlit
st.title("📈 我的應用")
st.write("主題會自動應用到所有元素！")
```

---

## 更高級用法

### 獲取當前主題
```python
from utils.theme_switcher import get_current_theme

theme = get_current_theme()
if theme == "dark":
    st.write("🌙 暗色模式")
else:
    st.write("☀️ 亮色模式")
```

### 根據主題設定顏色
```python
from utils.theme_switcher import get_theme_colors, get_color

# 方式 1: 獲取整個配色方案
colors = get_theme_colors()
primary_color = colors["primary"]

# 方式 2: 直接獲取特定顏色
success_color = get_color("success")
```

### 創建主題化的內容
```python
from utils.theme_switcher import create_themed_box

st.markdown(create_themed_box(
    "💡 提示",
    "這是一個會自動適應主題的信息框",
    theme_color="info"
), unsafe_allow_html=True)
```

### 使用主題選擇器
```python
from utils.theme_switcher import create_theme_selector

# 在側邊欄添加高級主題選擇器
create_theme_selector()
```
"""

if __name__ == "__main__":
    print("🎨 Theme Switcher Module Loaded!")
    print(EXAMPLE_CODE)
