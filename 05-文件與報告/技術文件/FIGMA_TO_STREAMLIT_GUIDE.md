# 📐 Figma設計轉換為Streamlit - 完整指南

## 問題：為什麼Streamlit看起來不像Figma設計？

### 根本原因

Streamlit有**設計系統的限制**：

1. **CSS覆蓋困難**
   - Streamlit的組件使用特定的CSS類名
   - 很多樣式被設置為 `!important` 且難以覆蓋
   - 某些組件的外觀無法完全自定義

2. **組件結構固定**
   - `st.button()` 的HTML結構是固定的
   - `st.metric()` 的佈局無法改變
   - 無法實現像Figma那樣的自由度

3. **細節損失**
   - 邊框寬度、圓角大小的控制有限
   - 陰影效果難以精確調整
   - 懸停效果的執行受限

### 解決方案：使用自定義HTML

不是依賴Streamlit組件，而是**用純HTML/CSS實現**，這樣你就能完全控制設計。

---

## 方案對比

### ❌ 舊方案（使用Streamlit組件）
```python
# 這樣看起來不像Figma
col1, col2 = st.columns(2)
with col1:
    st.metric("年化報酬", "15.5%")
```

**問題**：
- Streamlit的 `st.metric()` 有固定的樣式
- 無法自定義邊框、陰影、懸停效果
- 看起來很通用，不像Figma設計

### ✅ 新方案（使用自定義HTML）
```python
# 這樣看起來完全像Figma
st.markdown(create_metric_card(
    label="年化報酬",
    value="15.5%",
    change="+2.5%",
    icon="📈"
), unsafe_allow_html=True)
```

**優點**：
- 完全控制所有視覺元素
- 精確匹配Figma設計
- 支持自定義CSS和動畫

---

## 新的Figma風格組件

### 使用方法

#### 1. 應用主題
```python
from utils.ui_components_figma import apply_figma_theme

apply_figma_theme(st)
```

#### 2. 創建指標卡片
```python
from utils.ui_components_figma import create_metric_card

st.markdown(create_metric_card(
    label="年化報酬",
    value="15.5%",
    change="+2.5%",
    icon="📈"
), unsafe_allow_html=True)
```

#### 3. 創建分段標題
```python
from utils.ui_components_figma import create_section_header

st.markdown(create_section_header(
    title="📊 資產概覽",
    subtitle="您的投資組合表現概況"
), unsafe_allow_html=True)
```

#### 4. 創建指標行（自動佈局）
```python
from utils.ui_components_figma import create_stat_row

metrics = [
    ("總資產", "$125,345", "+2.34%", "💰"),
    ("年度報酬", "15.5%", "+5.12%", "📈"),
    ("持倉數", "4", "+1", "📊"),
    ("風險評分", "中", "-0.5", "⚡"),
]

st.markdown(create_stat_row(metrics), unsafe_allow_html=True)
```

---

## 色彩系統 - 精確匹配Figma

### 亮色模式（CryptoCrack風格）

| 元素 | 色值 | 用途 |
|------|------|------|
| 頁面背景 | `#F5F0FF` | 淡紫粉色漸變背景 |
| 卡片背景 | `#FFFFFF` | 純白卡片 |
| 主文字 | `#1A1A2E` | 深色主文字 |
| 次文字 | `#6B7280` | 灰色次文字 |
| 邊框 | `#E8E0FF` | 淡紫邊框 |
| 主色 | `#6B21A8` | 紫色漸變 |
| 成功色 | `#10B981` | 綠→青漸變 |
| 警告色 | `#F59E0B` | 橙色 |

---

## 組件詳解

### 指標卡片 (Metric Card)

**視覺特徵**：
- 純白背景
- 1px淡紫邊框
- 12px圓角
- 柔和陰影 (0 2px 8px)
- 懸停時：邊框變深、陰影增強、上移2px

**HTML結構**：
```html
<div class="figma-card">
    <div style="display: flex; justify-content: space-between;">
        <span>標籤</span>
        <span>變化百分比</span>
    </div>
    <div style="gradient text">數值</div>
</div>
```

### 按鈕

**視覺特徵**：
- 綠→青漸變背景
- 白色文字
- 8px圓角
- 柔和陰影
- 懸停時：輕微上移、陰影增強

**配置**：
```python
background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%);
box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
padding: 12px 24px;
```

### 卡片容器

**視覺特徵**：
- 白色背景
- 淡紫邊框 (1px)
- 12px圓角
- 細微陰影
- 懸停時提升效果

**CSS類**：
```css
.figma-card {
    background: white;
    border: 1px solid #E8E0FF;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## 圖表配置

### Plotly圖表最佳化

```python
import plotly.express as px

fig = px.line(df, x="Date", y="Price")

fig.update_layout(
    plot_bgcolor="white",           # 白色圖表背景
    paper_bgcolor="white",          # 白色容器背景
    font=dict(
        family="Arial, sans-serif",
        size=12,
        color="#1A1A2E"
    ),
    margin=dict(l=50, r=50, t=30, b=50),
    hovermode="x unified",
    xaxis=dict(
        showgrid=True,
        gridcolor="#F0E8FF",        # 淡紫網格
        showline=True,
        linecolor="#E8E0FF"
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="#F0E8FF",
        showline=True,
        linecolor="#E8E0FF"
    )
)

fig.update_traces(
    line=dict(color="#6B21A8", width=3),  # 紫色線條
    hovertemplate="<b>%{x|%b %d}</b><br>$%{y:,.2f}<extra></extra>"
)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
```

---

## 完整頁面模板

```python
import streamlit as st
from utils.ui_components_figma import apply_figma_theme, create_section_header, create_metric_card

st.set_page_config(layout="wide")
apply_figma_theme(st)

# 主標題
st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #6B21A8 0%, #4F46E5 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
">
📈 交易儀表板
</h1>
""", unsafe_allow_html=True)

# 分段標題
st.markdown(create_section_header(
    "📊 資產概覽",
    "您的投資組合表現概況"
), unsafe_allow_html=True)

# 指標卡片
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(create_metric_card("總資產", "$125,345", "+2.34%", "💰"), unsafe_allow_html=True)

# ... 其他內容
```

---

## 為什麼這樣效果更好？

### 1️⃣ **完全控制**
- 可以精確調整每個像素
- 實現Figma的所有細節
- 支持高級CSS效果

### 2️⃣ **一致性**
- 所有頁面使用相同的組件
- 保證視覺統一
- 易於維護和更新

### 3️⃣ **性能**
- HTML/CSS比依賴Streamlit組件更快
- 減少不必要的重新渲染
- 支持複雜的動畫

### 4️⃣ **可定制**
- 每個組件都可以自定義
- 支持主題變換
- 易於擴展新功能

---

## 常見問題

### Q: 為什麼不用 `st.metric()` 和 `st.button()`？
A: 因為它們的樣式是固定的，無法完全自定義。用HTML就能實現完全相同的功能，但設計自由度更高。

### Q: 性能會不會差？
A: 不會。實際上HTML/CSS比Streamlit組件更輕量級。

### Q: 如何響應式設計？
A: 使用CSS Grid 和 Flexbox，自動適配不同屏幕尺寸。

### Q: 如何添加互動效果？
A: 可以在HTML中添加JavaScript，或使用Streamlit的回調函數。

---

## 後續優化

### 可以添加的功能

1. **深色模式** - 創建 `DARK_COLORS` 變體
2. **主題切換** - 在側邊欄切換亮/暗
3. **動畫效果** - 添加更多CSS動畫
4. **響應式佈局** - 優化手機顯示
5. **自定義組件庫** - 擴展更多組件

---

## 立即開始

### 方式 1：運行完整示例
```bash
streamlit run example_figma_dashboard.py
```

### 方式 2：在你的頁面中使用
```python
from utils.ui_components_figma import apply_figma_theme, create_metric_card

apply_figma_theme(st)
st.markdown(create_metric_card("標籤", "數值", "+變化%", "🎯"), unsafe_allow_html=True)
```

---

## 文件位置

| 文件 | 說明 |
|------|------|
| `utils/ui_components_figma.py` | 所有Figma風格組件和CSS |
| `example_figma_dashboard.py` | 完整儀表板示例 |
| 本文檔 | 使用指南 |

---

**祝你創建漂亮的Streamlit應用！🎨**

由 Claude Code 設計 | 基於Figma CryptoCrack參考設計
