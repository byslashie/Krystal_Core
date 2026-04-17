# 🎨 現代化UI設計指南 - SmartAlgo + CryptoCrack風格

## 一、設計靈感來源

### 參考設計 1: SmartAlgo (深色系統)
- **風格**：專業、暗色、適合長時間交易
- **特點**：
  - 深藍黑背景 (#0F1419)
  - 細邊框卡片設計
  - 漸變圖表線條
  - 簡潔的側邊欄導航

### 參考設計 2: CryptoCrack (亮色系統)
- **風格**：現代、亮色、充滿活力
- **特點**：
  - 淡紫粉色背景 (#F5F0FF)
  - 白色卡片，乾淨簡潔
  - 綠→青漸變按鈕
  - 彩虹色圖表

---

## 二、現代色彩系統

### 亮色模式 (CryptoCrack風格)

```
背景色系
├─ 主背景: #F5F0FF      淡紫粉色
├─ 卡片:  #FFFFFF       純白
└─ 次背景: #F9F7FF      淡紫色

文字色系
├─ 主文字: #1A1A2E      深色
├─ 次文字: #6B7280      灰色
└─ 淡文字: #9CA3AF      淺灰

功能色
├─ 紫色:  #6B21A8       (主色)
├─ 綠色:  #10B981       (成功)
├─ 橙色:  #F59E0B       (警告)
├─ 紅色:  #EF4444       (錯誤)
└─ 藍色:  #3B82F6       (信息)

漸變色
├─ 主漸變: 紫→紫藍
├─ 成功漸變: 綠→青
└─ 圖表漸變: 彩虹色
```

### 暗色模式 (SmartAlgo風格)

```
背景色系
├─ 主背景: #0F1419      深藍黑
├─ 卡片:  #1A1F2E       深灰
└─ 次背景: #232A3B      稍淺灰

文字色系
├─ 主文字: #E5E7EB      淡白
├─ 次文字: #9CA3AF      灰色
└─ 淡文字: #6B7280      淺灰

功能色
├─ 紫色:  #8B5CF6       (主色，更亮)
├─ 綠色:  #10B981       (成功)
├─ 金色:  #FBBF24       (警告)
├─ 紅色:  #F87171       (錯誤)
└─ 藍色:  #60A5FA       (信息)

漸變色
├─ 主漸變: 紫→藍
├─ 成功漸變: 綠→青綠
└─ 圖表漸變: 粉→青
```

---

## 三、組件設計

### 1. 統計卡片 (Stat Card)

**特點**：
- 細邊框 (1px)
- 漸變數值文字
- 懸停時提升效果
- 支持實時數值變化指示

**代碼**：
```python
from utils.ui_theme_modern import create_stat_card

st.markdown(create_stat_card(
    label="年化報酬",
    value="15.5%",
    change="+2.5%",
    icon="📈",
    theme="light"
), unsafe_allow_html=True)
```

### 2. 漸變按鈕

**特點**：
- 綠→青漸變
- 懸停時上移效果
- 柔和陰影
- 圓角設計

### 3. 圖表

**特點**：
- 自適應主題背景
- 彩虹色線條
- 平滑過渡
- 信息豐富

### 4. 卡片容器

**特點**：
- 1px 邊框
- 圓角 12px
- 細微陰影
- 懸停時邊框顏色變化

---

## 四、快速開始

### 基礎設置

```python
import streamlit as st
from utils.ui_theme_modern import apply_modern_theme, get_colors

# 設置頁面
st.set_page_config(layout="wide")

# 選擇主題 ("light" 或 "dark")
theme = "light"  # 或 "dark"

# 應用主題
apply_modern_theme(st, theme=theme)

# 獲取當前主題色彩
colors = get_colors(theme)
```

### 創建統計卡片

```python
from utils.ui_theme_modern import create_stat_card

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(create_stat_card(
        "年化報酬", "15.5%", "+2.5%", "📈", theme="light"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(create_stat_card(
        "Sharpe比率", "2.35", "+0.15", "⚡", theme="light"
    ), unsafe_allow_html=True)

with col3:
    st.markdown(create_stat_card(
        "最大回撤", "-12.5%", "-1.2%", "📉", theme="light"
    ), unsafe_allow_html=True)

with col4:
    st.markdown(create_stat_card(
        "勝率", "58.3%", "+1.2%", "🎯", theme="light"
    ), unsafe_allow_html=True)
```

### 配置圖表

```python
import plotly.express as px
from utils.ui_theme_modern import create_chart_config

theme = "light"
fig = px.line(df, x="date", y="value")
fig.update_layout(**create_chart_config(theme=theme))
st.plotly_chart(fig, use_container_width=True)
```

---

## 五、色彩應用規則

### 亮色模式

✅ **推薦組合**
- 深文字 (#1A1A2E) on 白卡片 (#FFFFFF)
- 紫色 (#6B21A8) on 淡紫背景 (#F5F0FF)
- 綠色按鈕 on 任何背景

### 暗色模式

✅ **推薦組合**
- 淡白文字 (#E5E7EB) on 深卡片 (#1A1F2E)
- 紫色 (#8B5CF6) on 深背景 (#0F1419)
- 綠色按鈕 on 任何背景

---

## 六、組件清單

| 組件 | 用途 | 代碼 |
|------|------|------|
| 統計卡片 | 顯示關鍵指標 | `create_stat_card()` |
| 漸變按鈕 | 主要操作 | CSS 自動應用 |
| 圖表 | 數據可視化 | `create_chart_config()` |
| 卡片容器 | 內容分組 | CSS class `.metric-card` |
| 分割線 | 視覺分隔 | `st.markdown("---")` |

---

## 七、實用代碼片段

### 片段 1：完整頁面設置

```python
import streamlit as st
from utils.ui_theme_modern import apply_modern_theme, create_stat_card, get_colors

# 配置
st.set_page_config(layout="wide", page_icon="📈")

# 主題選擇
theme = "light"  # 可從側邊欄選擇

# 應用主題
apply_modern_theme(st, theme=theme)

# 標題
st.markdown("""
<h1 style="background: linear-gradient(135deg, #6B21A8 0%, #4F46E5 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;">
📈 量化交易儀表板
</h1>
""", unsafe_allow_html=True)

# 內容
st.write("你的內容在這裡...")
```

### 片段 2：四卡片指標行

```python
metrics = [
    ("年化報酬", "15.5%", "+2.5%", "📈"),
    ("Sharpe比率", "2.35", "+0.15", "⚡"),
    ("最大回撤", "-12.5%", "-1.2%", "📉"),
    ("勝率", "58.3%", "+1.2%", "🎯"),
]

cols = st.columns(4)
for col, (label, value, change, icon) in zip(cols, metrics):
    with col:
        st.markdown(create_stat_card(
            label, value, change, icon, theme="light"
        ), unsafe_allow_html=True)
```

### 片段 3：響應式設計

```python
# 根據屏幕寬度調整
def get_columns(width="wide"):
    if width == "mobile":
        return 2
    elif width == "tablet":
        return 3
    else:  # desktop
        return 4

cols = st.columns(get_columns())
```

---

## 八、設計最佳實踐

✅ **做**
- 使用漸變色增強視覺吸引力
- 保持充足的白色空間
- 使用懸停效果增強交互反饋
- 統一邊框寬度和圓角

❌ **不做**
- 混合太多顏色
- 過度使用陰影
- 邊框厚度不一致
- 忽視響應式設計

---

## 九、進階功能

### 主題切換

```python
from utils.theme_switcher import create_theme_selector

# 在側邊欄添加選擇器
create_theme_selector()
```

### 動態顏色

```python
from utils.ui_theme_modern import get_colors

colors = get_colors(theme)
st.markdown(f"<p style='color: {colors['primary']}'>文字</p>",
           unsafe_allow_html=True)
```

### 自定義色彩

```python
from utils.ui_theme_modern import create_stat_card

st.markdown(create_stat_card(
    "自定義", "100%", "", "",
    theme="light",
    accent_color="#FF6B6B"  # 自定義顏色
), unsafe_allow_html=True)
```

---

## 十、文件參考

- `utils/ui_theme_modern.py` - 現代化主題代碼
- `utils/theme_switcher.py` - 主題切換功能
- 本文檔 - 設計指南

---

**祝你創建漂亮的現代化交易平台！🚀**

由 Claude Code 設計 | 基於 SmartAlgo + CryptoCrack 參考設計
