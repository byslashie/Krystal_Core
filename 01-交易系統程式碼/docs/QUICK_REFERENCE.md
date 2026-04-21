# ⚡ UI 主題快速參考

## 🎨 色彩速查表

```
🟣 #5B47D9  ← 主色 (按鈕、標題)
🟦 #06B6D4  ← 輔助色 (圖表、次級)
💕 #EC4899  ← 粉紫 (警告、強調)
✅ #10B981  ← 成功綠
⚠️ #F59E0B  ← 警告黃
❌ #EF4444  ← 錯誤紅
```

---

## 📝 代碼示例

### 1. 基本設置
```python
import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from utils.ui_theme import apply_theme

st.set_page_config(layout="wide")
apply_theme(st)  # 必須！
```

### 2. 創建標題
```python
st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #5B47D9 0%, #06B6D4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
">📈 My Title</h1>
""", unsafe_allow_html=True)
```

### 3. 指標卡片
```python
from utils.ui_theme import format_metric

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(format_metric(
        "收益率",
        "15.5%",
        color="#10B981",
        icon="📈"
    ), unsafe_allow_html=True)
```

### 4. 創建信息框
```python
from utils.ui_theme import create_info_box

st.markdown(create_info_box(
    "提示標題",
    "這是提示內容",
    icon="💡",
    color="#3B82F6"
), unsafe_allow_html=True)
```

### 5. 信息卡片
```python
st.markdown("""
<div style="
    background: linear-gradient(135deg, rgba(91, 71, 217, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
    border: 1px solid rgba(91, 71, 217, 0.2);
    border-radius: 12px;
    padding: 20px;
">
    <h4 style="color: #5B47D9; margin-top: 0;">📌 標題</h4>
    <p style="color: #4B5563;">內容文本</p>
</div>
""", unsafe_allow_html=True)
```

---

## 🎯 常用組件

### 按鈕樣式
```python
# 自動應用主題 (使用 st.button)
if st.button("點擊我"):
    st.write("已點擊!")
```

### 表格樣式
```python
# 表格自動使用新樣式
df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
st.dataframe(df, use_container_width=True)
```

### 圖表優化
```python
import plotly.express as px

fig = px.line(df, x="date", y="value")
fig.update_layout(
    plot_bgcolor="rgba(240, 245, 250, 0.5)",
    paper_bgcolor="white",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)
```

---

## 🎨 快速色彩應用

### 文字色
```html
<!-- 深色 (主文本) -->
<p style="color: #1F2937;">主文本</p>

<!-- 中等灰 (次文本) -->
<p style="color: #4B5563;">次文本</p>

<!-- 淺灰 (說明) -->
<p style="color: #9CA3AF;">說明文字</p>

<!-- 主色 (強調) -->
<p style="color: #5B47D9;">強調文字</p>

<!-- 成功 (正值) -->
<p style="color: #10B981;">✅ 成功</p>

<!-- 錯誤 (負值) -->
<p style="color: #EF4444;">❌ 錯誤</p>
```

### 背景色
```html
<!-- 純白 (卡片) -->
<div style="background: #FFFFFF;">卡片背景</div>

<!-- 淺灰 (頁面) -->
<div style="background: #F8FAFC;">頁面背景</div>

<!-- 漸變 (特殊) -->
<div style="background: linear-gradient(135deg, #5B47D9 0%, #06B6D4 100%);">
    漸變背景
</div>
```

---

## 📏 尺寸標準

### 圓角
```
6px  ← 小元素
12px ← 默認圓角 (推薦)
16px ← 大容器
24px ← 特殊元素
```

### 間距
```
4px  ← xs (緊湊)
8px  ← sm
12px ← md (默認)
16px ← lg
24px ← xl
32px ← 2xl
```

### 陰影
```css
/* 小陰影 */
box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);

/* 中等陰影 */
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);

/* 大陰影 */
box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

/* AI 光暈 */
box-shadow: 0 0 20px rgba(91, 71, 217, 0.3);
```

---

## 🔧 常見任務

### 任務：改變按鈕顏色
❌ **不要**: 直接使用 st.button + CSS
✅ **要**: 自動應用主題的 st.button 就是漸變紫色

### 任務：突出正值
```python
color = "#10B981" if value > 0 else "#EF4444"
st.markdown(f"<p style='color: {color};'>{value}%</p>", unsafe_allow_html=True)
```

### 任務：創建卡片
```python
st.markdown("""
<div style="
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
">
    卡片內容
</div>
""", unsafe_allow_html=True)
```

### 任務：添加懸停效果
```python
st.markdown("""
<style>
.hover-card {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.hover-card:hover {
    border-color: #5B47D9;
    box-shadow: 0 0 20px rgba(91, 71, 217, 0.2);
    transform: translateY(-4px);
}
</style>
<div class="hover-card" style="
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 20px;
">
    可懸停的卡片
</div>
""", unsafe_allow_html=True)
```

---

## 📚 完整資源

| 資源 | 文件 | 用途 |
|------|------|------|
| 詳細規範 | `UI_UX_DESIGN_GUIDE.md` | 完整設計規範 |
| 實施報告 | `DESIGN_IMPLEMENTATION.md` | 實施細節與建議 |
| 主題代碼 | `utils/ui_theme.py` | 可複用組件函數 |
| 本指南 | `QUICK_REFERENCE.md` | 速查表 |

---

## ⚡ 快速啟動

### 最小化設置 (3 行代碼)
```python
import streamlit as st
from utils.ui_theme import apply_theme
apply_theme(st)  # ← 就這樣!
```

### 添加標題與卡片
```python
from utils.ui_theme import create_header, format_metric

st.markdown(create_header("📈 標題", "副標題"), unsafe_allow_html=True)
st.markdown(format_metric("標籤", "100%", color="#5B47D9"), unsafe_allow_html=True)
```

---

## 💡 提示

✅ 所有新代碼都應該使用 `utils/ui_theme.py` 中的顏色
✅ 使用 `unsafe_allow_html=True` 時務必驗證內容安全性
✅ 測試所有顏色在深色模式下的對比度
✅ 移動設備上測試響應式布局

---

**需要更多幫助? 查看 `UI_UX_DESIGN_GUIDE.md` 或 `DESIGN_IMPLEMENTATION.md`**

祝你設計愉快! 🚀
