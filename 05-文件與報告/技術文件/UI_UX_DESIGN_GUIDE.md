# 🎨 Krystal AI Trading System - UI/UX 設計規範

## 一、設計理念
**現代亮色系 + AI科技感**

打造專業級量化交易平台視覺體驗，融合現代設計語言與科技感美學，提供直觀、高效的用戶交互。

---

## 二、色彩系統 (Color Palette)

### 🎯 核心配色 - 科技紫蓝系

#### 主色系 (Primary)
| 色名 | 色值 | 用途 |
|------|------|------|
| 主紫蓝 | `#5B47D9` | 主按钮、链接、强调文字 |
| 纯紫 | `#4F46E5` | 按钮悬停、次级强调 |
| 深紫 | `#2C1F5F` | 暗部强调、文字对比 |

#### 辅助色 (Secondary)
| 色名 | 色值 | 用途 |
|------|------|------|
| 现代青 | `#06B6D4` | 次要元素、分割线、图表 |
| 浅青 | `#22D3EE` | 背景强调、卡片边框 |
| 深青 | `#0891B2` | 悬停状态、深色文字 |

#### 强调色 (Accent)
| 色名 | 色值 | 用途 |
|------|------|------|
| 粉紫 | `#EC4899` | 特殊提示、重要警告 |
| 粉紫深 | `#D946EF` | 渐变强调 |

#### 功能色 (Status)
| 色名 | 色值 | 用途 |
|------|------|------|
| 成功绿 | `#10B981` | 正收益、成功状态 |
| 警告黄 | `#F59E0B` | 警告、中等风险 |
| 错误红 | `#EF4444` | 负收益、错误状态 |
| 信息蓝 | `#3B82F6` | 信息提示 |

#### 背景色 (Background)
| 色名 | 色值 | 用途 |
|------|------|------|
| 纯白 | `#FFFFFF` | 卡片、输入框背景 |
| 浅灰 | `#F8FAFC` | 页面背景、容器背景 |
| 较浅灰 | `#F1F5F9` | 辅助背景 |

#### 边框与文字色
| 色名 | 色值 | 用途 |
|------|------|------|
| 亮边框 | `#E5E7EB` | 默认边框 |
| 中等边框 | `#D1D5DB` | 悬停边框 |
| 深边框 | `#9CA3AF` | 禁用元素 |
| 深文字 | `#1F2937` | 主文本 |
| 中文字 | `#4B5563` | 次要文本 |
| 浅文字 | `#9CA3AF` | 说明文字 |

---

## 三、品牌渐变色 (Gradients)

### 关键渐变配置

```css
/* AI科技渐变 - 紫→青 */
linear-gradient(135deg, #5B47D9 0%, #06B6D4 100%)

/* 未来感渐变 - 紫→粉 */
linear-gradient(135deg, #4F46E5 0%, #EC4899 100%)

/* 高端感渐变 - 紫→粉紫 */
linear-gradient(135deg, #5B47D9 0%, #D946EF 100%)

/* 活力感渐变 - 青→绿 */
linear-gradient(135deg, #06B6D4 0%, #10B981 100%)

/* 页面背景渐变 - 微妙感 */
linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)
```

---

## 四、排版系统 (Typography)

### 字体系列
```
system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
```

### 文字尺寸与权重
| 类型 | 尺寸 | 权重 | 行高 | 用途 |
|------|------|------|------|------|
| H1 | 32px | 700 | 1.2 | 页面主标题 |
| H2 | 28px | 700 | 1.3 | 分类标题 |
| H3 | 24px | 600 | 1.4 | 小分类 |
| H4 | 20px | 600 | 1.4 | 次标题 |
| Body Large | 16px | 400 | 1.6 | 大段落文本 |
| Body | 14px | 400 | 1.6 | 常规文本 |
| Small | 12px | 400 | 1.5 | 小标签 |
| Label | 12px | 500 | 1.4 | 表单标签 |
| Caption | 11px | 400 | 1.4 | 说明文字 |

---

## 五、组件设计系统

### 1. 按钮 (Buttons)

#### 主按钮 (Primary)
```css
background: linear-gradient(135deg, #5B47D9 0%, #4F46E5 100%);
color: white;
border-radius: 12px;
padding: 10px 24px;
font-weight: 600;
box-shadow: 0 4px 6px -1px rgba(91, 71, 217, 0.2);
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

**悬停状态**
```css
box-shadow: 0 10px 15px -3px rgba(91, 71, 217, 0.3);
transform: translateY(-2px);
```

### 2. 卡片 (Cards)

```css
background: white;
border: 1px solid #E5E7EB;
border-radius: 12px;
padding: 20px;
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

**悬停状态**
```css
border-color: #5B47D9;
box-shadow: 0 0 20px rgba(91, 71, 217, 0.2);
transform: translateY(-4px);
```

### 3. 输入框 (Input Fields)

```css
border: 2px solid #E5E7EB;
border-radius: 12px;
padding: 10px 16px;
font-size: 14px;
background-color: #FFFFFF;
color: #1F2937;
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

**焦点状态**
```css
border-color: #5B47D9;
box-shadow: 0 0 0 3px rgba(91, 71, 217, 0.1);
```

### 4. 指标卡片 (Metric Cards)

```css
.metric-card {
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.metric-label {
  color: #9CA3AF;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.metric-value {
  background: linear-gradient(135deg, #5B47D9 0%, #06B6D4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 28px;
  font-weight: 700;
}
```

### 5. 信息框 (Info Box)

```css
background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(6, 182, 212, 0.05) 100%);
border-left: 4px solid #3B82F6;
border-radius: 12px;
padding: 16px;
```

### 6. 圆角系统 (Border Radius)
| 级别 | 尺寸 | 用途 |
|------|------|------|
| sm | 6px | 小元素 |
| md | 12px | 默认圆角 |
| lg | 16px | 大容器 |
| xl | 24px | 特殊元素 |
| full | 9999px | 完全圆形 |

### 7. 阴影系统 (Box Shadows)

```css
/* 小阴影 */
0 1px 2px 0 rgba(0, 0, 0, 0.05)

/* 中等阴影 */
0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)

/* 大阴影 */
0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)

/* AI光晕效果 */
0 0 20px rgba(91, 71, 217, 0.3)
```

---

## 六、间距系统 (Spacing)

| 尺寸 | 值 | 用途 |
|------|-----|------|
| xs | 4px | 紧凑间距 |
| sm | 8px | 小间距 |
| md | 12px | 默认间距 |
| lg | 16px | 大间距 |
| xl | 24px | 分隔符级 |
| 2xl | 32px | 大分隔 |
| 3xl | 48px | 版块分隔 |

---

## 七、应用规则

### 页面布局
1. **背景**：使用 `linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)`
2. **容器**：白色卡片 + 1px 浅灰边框
3. **主标题**：使用渐变文字效果
4. **副标题**：纯紫色 `#5B47D9`

### 数据可视化
1. **正值/成功**：绿色 `#10B981`
2. **负值/风险**：红色 `#EF4444`
3. **中等/警告**：琥珀色 `#F59E0B`
4. **图表配色**：
   - 优先：`#5B47D9` (主紫蓝)
   - 次级：`#06B6D4` (青色)
   - 强调：`#EC4899` (粉紫)

### 交互反馈
1. **悬停**：边框颜色变深，阴影增大，微妙上移
2. **点击**：阴影减小，位置回归
3. **禁用**：文字变灰，不可交互

---

## 八、无障碍设计 (Accessibility)

### 颜色对比度
- 所有文本与背景需满足 WCAG AA 标准 (4.5:1 最小对比度)
- 功能不依赖单一颜色区分

### 焦点指示
- 所有可交互元素需明确的焦点样式
- 使用 `box-shadow` 而非仅改变颜色

### 响应式
- 所有组件需在手机、平板、桌面端适配
- 触摸目标最小尺寸 44x44px

---

## 九、页面结构示例

### 标准页面布局
```
┌─────────────────────────────────────┐
│  [渐变标题区]                         │
│  主标题 + 副标题                      │
├─────────────────────────────────────┤
│  [内容区域]                           │
│  ┌─── 卡片 1 ───┐ ┌─── 卡片 2 ───┐  │
│  │ 指标卡片     │ │ 指标卡片      │  │
│  └──────────────┘ └───────────────┘  │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │ 大卡片（图表/表格）               │ │
│  └─────────────────────────────────┘ │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │ 信息框                            │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## 十、更新记录

| 版本 | 日期 | 更改 |
|------|------|------|
| 1.0 | 2026-03-03 | 初版 - 现代亮色系 + AI科技感 |

---

## 十一、设计资源

### CSS 变量
```css
:root {
  --primary: #5B47D9;
  --secondary: #06B6D4;
  --accent: #EC4899;
  --success: #10B981;
  --warning: #F59E0B;
  --error: #EF4444;
  --bg: #FFFFFF;
  --bg-light: #F8FAFC;
  --text: #1F2937;
  --border: #E5E7EB;
}
```

### 快速导入
```python
from utils.ui_theme import apply_theme, format_metric, create_header, create_info_box

# 在 streamlit app 中应用
apply_theme(st)
```

---

## 十二、注意事项

✅ **推荐做法**
- 使用渐变色增强现代感
- 保持充足的白色空间
- 使用微妙的阴影创造深度感
- 优先使用圆角 12px

❌ **避免做法**
- 混合多种对比度不足的颜色
- 过度使用纯黑色文字
- 省略聚焦状态指示
- 使用过多阴影导致厚重感

---

**祝你使用愉快！ 🚀**

由 Claude Code 设计 | Krystal AI Trading System v3.0
