# 🌙 暗色系快速開始指南

## ⚡ 3 秒快速啟動

```python
import streamlit as st
from utils.theme_switcher import apply_theme_switcher, create_theme_toggle_button

# 應用主題（支持亮色和暗色切換）
apply_theme_switcher(st)

# 在側邊欄添加切換按鈕
create_theme_toggle_button(position="sidebar")

# 完成！你的應用現在支持亮色/暗色
st.title("📈 我的應用")
```

---

## 🎨 暗色系色彩速查

```
🟣 #7C5FFF  ← 主色 (按鈕、標題) - 比亮色版本更亮
🟦 #13D9E8  ← 輔助色 (圖表、次級) - 提高了飽和度
💕 #FF6BA6  ← 粉紫 (警告、強調)
✅ #13E76E  ← 成功綠 - 更亮的版本
⚠️ #FFB833  ← 警告黃 - 更亮的版本
❌ #FF5555  ← 錯誤紅 - 更亮的版本

背景：
🖤 #0F172A  ← 主背景 (深藍黑)
🩶 #1A2641  ← 卡片背景
⚪ #F0F4F8  ← 文字色 (亮白而非純白)
```

---

## 📝 常見代碼片段

### 1. 只使用暗色主題
```python
import streamlit as st
from utils.ui_theme_dark import apply_theme_dark

st.set_page_config(layout="wide")
apply_theme_dark(st)

st.title("📈 暗色主題應用")
```

### 2. 支持主題切換
```python
import streamlit as st
from utils.theme_switcher import (
    apply_theme_switcher,
    create_theme_toggle_button,
    get_current_theme
)

st.set_page_config(layout="wide")
apply_theme_switcher(st)

# 側邊欄切換按鈕
create_theme_toggle_button(position="sidebar")

# 根據主題調整內容
if get_current_theme() == "dark":
    st.write("🌙 暗色模式")
else:
    st.write("☀️ 亮色模式")
```

### 3. 使用主題感知顏色
```python
from utils.theme_switcher import get_color, get_theme_colors

# 方式 1: 獲取特定顏色
primary = get_color("primary")  # 當前主題的主色
success = get_color("success")  # 當前主題的成功色

# 方式 2: 獲取整個配色方案
colors = get_theme_colors()
bg = colors["bg_primary"]
text = colors["text_primary"]
```

### 4. 創建主題化卡片
```python
from utils.theme_switcher import create_themed_box

st.markdown(create_themed_box(
    "💡 暗色模式提示",
    "這個框會自動適應亮色或暗色主題",
    theme_color="info"
), unsafe_allow_html=True)
```

### 5. 指標卡片（暗色版）
```python
from utils.ui_theme_dark import format_metric_dark

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(format_metric_dark(
        "年化報酬",
        "15.5%",
        color="#13E76E",
        icon="📈"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(format_metric_dark(
        "Sharpe Ratio",
        "2.35",
        color="#7C5FFF",
        icon="⚡"
    ), unsafe_allow_html=True)

with col3:
    st.markdown(format_metric_dark(
        "最大回撤",
        "-12.5%",
        color="#FF5555",
        icon="📉"
    ), unsafe_allow_html=True)
```

---

## 🎯 暗色系色彩應用

### 文字色
```html
<!-- 主文字（亮白） -->
<p style="color: #F0F4F8;">主要文本</p>

<!-- 次文字（中灰） -->
<p style="color: #CBD5E1;">次要文本</p>

<!-- 說明文字（淺灰） -->
<p style="color: #94A3B8;">說明和輔助文本</p>

<!-- 主色強調 -->
<p style="color: #7C5FFF;">強調文字</p>

<!-- 成功狀態 -->
<p style="color: #13E76E;">✅ 成功</p>

<!-- 錯誤狀態 -->
<p style="color: #FF5555;">❌ 錯誤</p>
```

### 背景色
```html
<!-- 卡片背景 -->
<div style="background: #1A2641;">深藍黑卡片</div>

<!-- 漸變背景 -->
<div style="background: linear-gradient(135deg, #7C5FFF 0%, #13D9E8 100%);">
    漸變背景
</div>

<!-- 信息框（半透明漸變） -->
<div style="background: linear-gradient(135deg, rgba(124, 95, 255, 0.1) 0%, rgba(19, 217, 232, 0.1) 100%);">
    信息框背景
</div>
```

---

## 📊 亮色 vs 暗色快速對比

| 元素 | 亮色 | 暗色 |
|------|------|------|
| 背景 | `#FFFFFF` | `#0F172A` |
| 文字 | `#1F2937` | `#F0F4F8` |
| 主色 | `#5B47D9` | `#7C5FFF` |
| 邊框 | `#E5E7EB` | `#334155` |
| 成功 | `#10B981` | `#13E76E` |
| 卡片陰影 | 0.1 alpha | 0.3 alpha |

---

## 🔧 常見任務

### 任務：全頁面應用暗色主題

```python
import streamlit as st
from utils.theme_switcher import apply_theme_switcher, create_theme_selector

st.set_page_config(layout="wide", page_icon="📈")

# 應用主題切換
apply_theme_switcher(st)

# 在側邊欄添加選擇器
create_theme_selector()

# 後續代碼正常使用
st.title("📈 量化交易系統")
```

### 任務：根據主題改變內容

```python
from utils.theme_switcher import get_current_theme

if get_current_theme() == "dark":
    background_image = "assets/dark-bg.png"
    accent_color = "#7C5FFF"
else:
    background_image = "assets/light-bg.png"
    accent_color = "#5B47D9"

st.markdown(f"<div style='color: {accent_color};'>主題感知內容</div>",
           unsafe_allow_html=True)
```

### 任務：創建主題化圖表

```python
import plotly.express as px
from utils.theme_switcher import get_theme_colors

colors = get_theme_colors()

fig = px.line(df, x="date", y="value")
fig.update_layout(
    plot_bgcolor=colors["bg_secondary"],
    paper_bgcolor=colors["bg_primary"],
    font=dict(color=colors["text_primary"])
)

st.plotly_chart(fig, use_container_width=True)
```

### 任務：動態顏色卡片

```python
from utils.theme_switcher import get_color

def create_stat_card(label, value, metric_type="positive"):
    if metric_type == "positive":
        color = get_color("success")
    elif metric_type == "negative":
        color = get_color("error")
    else:
        color = get_color("info")

    return f"""
    <div style="
        background: #1A2641;
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 12px;
    ">
        <div style="color: #94A3B8;">{label}</div>
        <div style="color: {color}; font-size: 24px; font-weight: bold;">
            {value}
        </div>
    </div>
    """

st.markdown(create_stat_card("年化報酬", "15.5%", "positive"),
           unsafe_allow_html=True)
```

---

## 💡 設計提示

✅ **做**
- 使用主題切換器讓用戶選擇
- 在暗色模式中使用更亮的主色
- 提高對比度（最少 4.5:1）
- 測試長時間使用的舒適度

❌ **不做**
- 使用相同的色值（在暗背景上看不清）
- 使用純白 (#FFFFFF) 或純黑 (#000000)
- 忽視對比度檢查
- 過度使用鮮艷的顏色

---

## 📚 更多資源

| 資源 | 說明 |
|------|------|
| [UI_UX_DESIGN_GUIDE.md](UI_UX_DESIGN_GUIDE.md) | 亮色系完整設計規範 |
| [UI_UX_DARK_GUIDE.md](UI_UX_DARK_GUIDE.md) | 暗色系完整設計規範 |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | 亮色系快速參考 |
| `utils/ui_theme.py` | 亮色主題代碼 |
| `utils/ui_theme_dark.py` | 暗色主題代碼 |
| `utils/theme_switcher.py` | 主題切換工具 |

---

## 🚀 下一步

1. ✅ 在你的頁面添加主題切換
2. ✅ 測試亮色和暗色模式
3. ✅ 收集用戶反饋
4. ✅ 調整顏色（如需要）

**現在開始享受雙主題的專業設計！🌙☀️**

---

由 Claude Code 設計 | Krystal AI Trading System v3.0
