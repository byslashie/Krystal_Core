# 🌙 Krystal AI Trading System - 暗色主題設計指南

## 一、暗色系設計理念

**專業深色交易平台 + AI科技感**

打造夜間使用友好、眼睛舒適、專業度更高的交易平台體驗，融合暗色美學與科技漸變。

---

## 二、暗色系色彩系統 (Dark Color Palette)

### 🎯 核心配色 - 科技紫蓝系（深色版）

#### 主色系 (Primary - 更亮用於暗背景)
| 色名 | 色值 | 用途 |
|------|------|------|
| 主紫蓝 | `#7C5FFF` | 主按钮、标题、强调 |
| 纯紫 | `#8B77FF` | 按钮悬停、次级强调 |
| 深紫 | `#5B47D9` | 暗部强调 |

#### 辅助色 (Secondary - 提高亮度)
| 色名 | 色值 | 用途 |
|------|------|------|
| 現代青 | `#13D9E8` | 次要元素、圖表 |
| 浅青 | `#4FE5F5` | 背景強調 |
| 深青 | `#06B6D4` | 悬停状态 |

#### 強調色 (Accent)
| 色名 | 色值 | 用途 |
|------|------|------|
| 粉紫 | `#FF6BA6` | 特殊提示、警告 |
| 粉紫深 | `#E646FF` | 漸變強調 |

#### 功能色 (Status - 調整亮度)
| 色名 | 色值 | 用途 |
|------|------|------|
| 成功绿 | `#13E76E` | 正收益、成功状态 |
| 警告黄 | `#FFB833` | 警告、中等风险 |
| 錯誤紅 | `#FF5555` | 負收益、錯誤 |
| 信息藍 | `#5FA8FF` | 信息提示 |

#### 背景色 (Background)
| 色名 | 色值 | 用途 |
|------|------|------|
| 主背景 | `#0F172A` | 頁面背景 |
| 卡片背景 | `#1A2641` | 容器、卡片 |
| 懸停背景 | `#243454` | 交互背景 |
| 邊框背景 | `#2D3E5F` | 分割線 |

#### 文字色 (Text)
| 色名 | 色值 | 用途 |
|------|------|------|
| 亮白文字 | `#F0F4F8` | 主文本 |
| 中灰文字 | `#CBD5E1` | 次要文本 |
| 淺灰文字 | `#94A3B8` | 說明文字 |
| 占位符 | `#64748B` | 禁用、占位符 |

#### 邊框色 (Border)
| 色名 | 色值 | 用途 |
|------|------|------|
| 亮邊框 | `#334155` | 默認邊框 |
| 中等邊框 | `#475569` | 懸停邊框 |
| 深邊框 | `#64748B` | 禁用邊框 |

---

## 三、暗色系品牌漸變色

### 關鍵漸變配置

```css
/* AI科技漸變 - 紫→青 (暗色版) */
linear-gradient(135deg, #7C5FFF 0%, #13D9E8 100%)

/* 未來感漸變 - 紫→粉 (暗色版) */
linear-gradient(135deg, #8B77FF 0%, #FF6BA6 100%)

/* 高端感漸變 - 紫→粉紫 (暗色版) */
linear-gradient(135deg, #7C5FFF 0%, #E646FF 100%)

/* 活力感漸變 - 青→綠 (暗色版) */
linear-gradient(135deg, #13D9E8 0%, #13E76E 100%)

/* 頁面背景漸變 - 深色 */
linear-gradient(180deg, #0F172A 0%, #1A2641 100%)
```

---

## 四、組件設計系統（暗色版）

### 1. 按鈕 (Buttons - 暗色版)

```css
background: linear-gradient(135deg, #7C5FFF 0%, #8B77FF 100%);
color: #F0F4F8;
border-radius: 12px;
padding: 10px 24px;
font-weight: 600;
box-shadow: 0 4px 15px rgba(124, 95, 255, 0.4);
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

**悬停状态**
```css
box-shadow: 0 10px 25px rgba(124, 95, 255, 0.6);
transform: translateY(-2px);
```

### 2. 卡片 (Cards - 暗色版)

```css
background: #1A2641;
border: 1px solid #334155;
border-radius: 12px;
padding: 20px;
box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

**悬停状态**
```css
border-color: #7C5FFF;
box-shadow: 0 0 20px rgba(124, 95, 255, 0.3);
transform: translateY(-4px);
```

### 3. 輸入框 (Input Fields - 暗色版)

```css
border: 2px solid #334155;
border-radius: 12px;
padding: 10px 16px;
font-size: 14px;
background-color: #1A2641;
color: #F0F4F8;
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

**焦點状态**
```css
border-color: #7C5FFF;
box-shadow: 0 0 0 3px rgba(124, 95, 255, 0.2);
```

### 4. 指標卡片 (Metric Cards - 暗色版)

```css
.metric-card {
  background: #1A2641;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

.metric-label {
  color: #94A3B8;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.metric-value {
  background: linear-gradient(135deg, #7C5FFF 0%, #13D9E8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 28px;
  font-weight: 700;
}
```

### 5. 信息框 (Info Box - 暗色版)

```css
background: linear-gradient(135deg, rgba(124, 95, 255, 0.1) 0%, rgba(19, 217, 232, 0.1) 100%);
border-left: 4px solid #5FA8FF;
border-radius: 12px;
padding: 16px;
```

---

## 五、亮色vs暗色對比

### 色彩對照表

| 用途 | 亮色 | 暗色 | 說明 |
|------|------|------|------|
| **主色** | `#5B47D9` | `#7C5FFF` | 暗色版本更亮，提高可讀性 |
| **輔助色** | `#06B6D4` | `#13D9E8` | 暗色版本提高飽和度和亮度 |
| **背景** | `#FFFFFF` | `#0F172A` | 完全相反，適應環境 |
| **文字** | `#1F2937` | `#F0F4F8` | 完全相反，確保對比度 |
| **邊框** | `#E5E7EB` | `#334155` | 適應背景的淺淡邊框 |
| **成功** | `#10B981` | `#13E76E` | 暗色版本提高亮度 |

---

## 六、無障礙設計（暗色版）

### 色彩對比度檢查

✅ **推薦組合**
- `#F0F4F8` (白文字) on `#0F172A` (深背景) = 16:1 (超優)
- `#F0F4F8` (白文字) on `#1A2641` (卡片) = 14:1 (優)
- `#7C5FFF` (主色) on `#0F172A` (深背景) = 6:1 (足夠)

❌ **避免組合**
- 淺色文字 + 淺色背景
- 飽和度過低的文字
- 純白 (#FFFFFF) on 深色（過度刺眼）

### 響應式設計
- 觸摸目標最小尺寸 44x44px
- 所有交互元素需明確焦點指示
- 手機、平板、桌面端完全適配

---

## 七、使用主題切換器

### 基礎用法

```python
import streamlit as st
from utils.theme_switcher import apply_theme_switcher, create_theme_toggle_button

# 應用主題
apply_theme_switcher(st)

# 添加切換按鈕
create_theme_toggle_button(position="sidebar")

# 後續正常使用Streamlit
st.title("📈 我的應用")
st.write("會自動適應亮色或暗色！")
```

### 高級用法

```python
from utils.theme_switcher import (
    get_current_theme,
    get_theme_colors,
    get_color,
    create_themed_box
)

# 獲取當前主題
theme = get_current_theme()  # 返回 "light" 或 "dark"

# 獲取配色方案
colors = get_theme_colors()
primary = colors["primary"]

# 獲取特定顏色
success_color = get_color("success")

# 創建主題化內容
st.markdown(create_themed_box(
    "💡 提示",
    "這會自動適應當前主題",
    theme_color="info"
), unsafe_allow_html=True)
```

### 主題選擇器

```python
from utils.theme_switcher import create_theme_selector

# 在側邊欄添加主題選擇器
create_theme_selector()
```

---

## 八、設計最佳實踐

### ✅ 暗色模式最佳實踐

1. **使用更亮的主色**
   - 亮色: `#5B47D9` → 暗色: `#7C5FFF`
   - 確保在深色背景上清晰可見

2. **提高對比度**
   - 最小對比度 4.5:1（WCAG AA）
   - 推薦 7:1（WCAG AAA）

3. **避免純白和純黑**
   - 純白 (#FFFFFF) 在深色背景上太刺眼
   - 使用 `#F0F4F8` 代替純白

4. **調整陰影**
   - 深色模式使用更大的陰影（提高視覺深度）
   - `0 4px 15px rgba(0, 0, 0, 0.3)` 而非 `rgba(0, 0, 0, 0.1)`

5. **漸變色調整**
   - 確保漸變兩端都足夠亮
   - 避免過暗的漸變終點

### ❌ 常見錯誤

- ❌ 使用相同的主色（在暗背景上看不清）
- ❌ 忽視對比度檢查
- ❌ 使用純白文字在純黑背景上
- ❌ 陰影太淡（深色背景難以區分）
- ❌ 沒有測試長時間閱讀的舒適度

---

## 九、頁面結構示例（暗色版）

### 標準頁面布局

```
┌─────────────────────────────────────┐
│  [漸變標題區 - 紫→青]               │
│  主標題 + 副標題                    │
├─────────────────────────────────────┤
│  [內容區域 - 深藍黑背景]             │
│  ┌─── 卡片 1 ───┐ ┌─── 卡片 2 ───┐ │
│  │ 指標卡片      │ │ 指標卡片      │ │
│  │ (亮紫漸變)    │ │ (亮紫漸變)    │ │
│  └──────────────┘ └───────────────┘ │
│                                      │
│  ┌─────────────────────────────────┐ │
│  │ 大卡片（圖表/表格）              │ │
│  │ 邊框: #334155                   │ │
│  └─────────────────────────────────┘ │
│                                      │
│  ┌─────────────────────────────────┐ │
│  │ 信息框（漸變背景）               │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## 十、文件與資源

### CSS 變數（暗色模式）

```css
:root {
  --primary-dark: #7C5FFF;
  --secondary-dark: #13D9E8;
  --accent-dark: #FF6BA6;
  --success-dark: #13E76E;
  --warning-dark: #FFB833;
  --error-dark: #FF5555;
  --bg-dark: #0F172A;
  --bg-dark-secondary: #1A2641;
  --text-dark-light: #F0F4F8;
  --border-dark: #334155;
}
```

### 快速導入

```python
from utils.ui_theme_dark import apply_theme_dark, format_metric_dark
from utils.theme_switcher import apply_theme_switcher, create_theme_toggle_button

# 僅使用暗色主題
apply_theme_dark(st)

# 或使用主題切換器（支援亮/暗）
apply_theme_switcher(st)
create_theme_toggle_button()
```

---

## 十一、更新記錄

| 版本 | 日期 | 更改 |
|------|------|------|
| 1.0 (亮色) | 2026-03-03 | 初版 - 科技紫藍亮色系 |
| 1.0 (暗色) | 2026-03-03 | 新增 - 專業深色系 + 主題切換 |

---

## 十二、注意事項

✅ **推薦做法**
- 同時測試亮色和暗色模式
- 使用主題切換器讓用戶自由選擇
- 定期檢查色彩對比度
- 在不同光線環境下測試

❌ **避免做法**
- 為兩個主題使用相同的色值
- 忽視暗色模式下的可讀性
- 使用純白 (#FFFFFF) 和純黑 (#000000)
- 陰影設定不當

---

**祝你享受專業的雙主題體驗！🌙☀️**

由 Claude Code 設計 | Krystal AI Trading System v3.0
