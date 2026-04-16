# Claude Code + Financial Services Plugins
## Krystal AI Trading System 整合指南

> **更新時間**：2026-03-19  
> **參考來源**：https://github.com/anthropics/financial-services-plugins

---

## 1. 前置需求

| 項目 | 要求 | 確認指令 |
|---|---|---|
| Node.js | >= 18 | `node --version` |
| Claude Code CLI | 已安裝 | `claude --version` |
| Anthropic API Key | 已取得 | [console.anthropic.com](https://console.anthropic.com) |

---

## 2. 環境設定

### 2.1 設定 API Key（只需做一次）

```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxxxxx"
```

> 建議加入 `~/.zshrc` 或 `~/.bash_profile` 讓它永久生效：
> ```bash
> echo 'export ANTHROPIC_API_KEY="sk-ant-xxx..."' >> ~/.zshrc
> source ~/.zshrc
> ```

### 2.2 啟動 Claude Code

```bash
# 進入 Krystal 系統目錄
cd "/Users/chenyu/Library/CloudStorage/GoogleDrive-yuchiehchen1230@gmail.com/我的雲端硬碟/Krystal_AI_Trading_System"

# 啟動
claude
```

---

## 3. 安裝 Financial Services Plugins

### 3.1 加入 Plugin Marketplace

```bash
claude plugin marketplace add anthropics/financial-services-plugins
```

### 3.2 安裝套件

```bash
# ✅ 核心套件（必裝，其他 plugin 都依賴它）
claude plugin install financial-analysis@financial-services-plugins

# 選配：股票研究（適合分析 MU、XLE 等持倉）
claude plugin install equity-research@financial-services-plugins

# 其他選配（視需求安裝）
claude plugin install investment-banking@financial-services-plugins
claude plugin install private-equity@financial-services-plugins
claude plugin install wealth-management@financial-services-plugins
```

### 3.3 套件功能對照

| Plugin | 主要功能 | Krystal 使用場景 |
|---|---|---|
| `financial-analysis` ⭐ | DCF、Comps、LBO、Excel 模型輸出 | 持倉估值（MU、XLE 等） |
| `equity-research` | 法說會分析、研究報告、晨報 | MU 法說會 + 進出場判斷 |
| `investment-banking` | CIM、買家名單、併購模型 | ❌ 投行業務，暫不需要 |
| `private-equity` | 盡調清單、IC Memo、KPI 追蹤 | ❌ PE 業務，暫不需要 |
| `wealth-management` | 投資組合再平衡、客戶報告 | 可選，投組管理參考 |

---

## 4. 可用的 Slash 指令

安裝完成後，在 Claude 對話中可直接使用：

```bash
# === financial-analysis ===
/comps [公司/股票代號]         # 可比公司分析（EV/EBITDA、P/E 等）
/dcf [公司/股票代號]           # DCF 折現現金流估值模型
/one-pager [公司]              # 一頁公司摘要

# === equity-research ===
/earnings [公司] [季度]        # 法說會後分析報告
/morning-note                  # 每日晨報

# === wealth-management ===
/client-review [持倉]          # 投資組合審查
```

**實際範例（針對 Krystal 持倉）：**
```bash
/comps MU                      # 美光科技 vs 三星/SK Hynix/Micron
/dcf XLE                       # 能源 ETF 估值
/earnings MU Q1 2026           # MU 最新法說會分析
/comps USO                     # 油價 ETF 比較
```

---

## 5. MCP 數據源連接

`financial-analysis` 核心套件內建 11 個 MCP 數據源連接器：

| Provider | MCP URL | 訂閱需求 | 建議優先度 |
|---|---|---|---|
| **MT Newswires** | `https://vast-mcp.blueskyapi.com/mtnewswires` | 低成本新聞 | ⭐⭐⭐ 適合地緣政治新聞 |
| **Morningstar** | `https://mcp.morningstar.com/mcp` | 中等 | ⭐⭐ 持倉基本面 |
| **LSEG** | `https://api.analytics.lseg.com/lfa/mcp` | 中高 | ⭐⭐ FX、能源數據 |
| **Aiera** | `https://mcp-pub.aiera.com` | 中等 | ⭐⭐ 法說會音訊摘要 |
| **FactSet** | `https://mcp.factset.com/mcp` | 企業級 | ⭐ 財務預估 |
| **S&P Global** | `https://kfinance.kensho.com/integrations/mcp` | 企業級 | ⭐ 財報 |
| PitchBook | `https://premium.mcp.pitchbook.com/mcp` | 企業級 | ❌ 一級市場，不適用 |

> ⚠️ **注意**：Plugin 本身免費，但各 MCP 數據源需要向各供應商申請帳號/API Key。  
> 你現有的 **IB API** 可替代大部分市場數據需求。

---

## 6. 整合 Krystal 系統的自訂 Plugin（進階）

### 6.1 建立 Krystal Trading Plugin 結構

```bash
mkdir -p .claude-plugin-krystal/{.claude-plugin,commands,skills}
```

目錄結構：
```
.claude-plugin-krystal/
├── .claude-plugin/plugin.json   # Plugin 設定
├── .mcp.json                    # 連接你的 Google Sheets / IB API
├── commands/
│   ├── oil-risk.md              # /oil-risk 指令（對應 intel_scraper）
│   └── portfolio-status.md     # /portfolio-status 指令
└── skills/
    └── krystal-trading.md      # 教 Claude 你的交易邏輯
```

### 6.2 `plugin.json` 範例

```json
{
  "name": "krystal-trading",
  "version": "1.0.0",
  "description": "Krystal AI Trading System - 地緣政治風險 + 能源交易策略",
  "author": { "name": "Krystal" }
}
```

### 6.3 自訂 `.mcp.json`（連接 Google Sheets）

```json
{
  "mcpServers": {
    "google-sheets": {
      "type": "http",
      "url": "https://mcp-server.egnyte.com/mcp"
    },
    "mtnewswire": {
      "type": "http",
      "url": "https://vast-mcp.blueskyapi.com/mtnewswires"
    }
  }
}
```

### 6.4 `/oil-risk` 指令範例（`commands/oil-risk.md`）

```markdown
---
description: 波斯灣地緣政治風險評估 + 能源交易建議
argument-hint: "[可選：指定事件類型]"
---

# Oil Risk Assessment

## Workflow
1. 從 Google Sheets `intel_events` 讀取最新 AIS 異常事件
2. 評估 Hormuz 海峽風險等級（NORMAL / HIGH / CRITICAL）
3. 若 severity=CRITICAL：建議 buy XLE/XOP，activate S5 空頭對沖
4. 生成風險摘要（繁體中文）
```

---

## 7. Plugin 架構說明

> 所有 Plugin 內容都是 **純 Markdown + JSON**，沒有任何程式碼。  
> Claude 本身就是執行引擎，讀完 Skill/Command 後自動呼叫 MCP API 執行。

```
plugin-name/
├── .claude-plugin/plugin.json   # Manifest（套件識別）
├── .mcp.json                    # 數據源 URL 設定
├── commands/                    # 你主動觸發的 /指令（Markdown）
├── hooks/                       # 自動觸發條件
└── skills/                      # Claude 背景學習的領域知識（Markdown）
```

---

## 8. 參考資源

- **官方 Repo**：https://github.com/anthropics/financial-services-plugins
- **Plugin 安裝入口**：https://claude.com/plugins
- **MCP 協議文件**：https://modelcontextprotocol.io
- **Anthropic Console（API Key 管理）**：https://console.anthropic.com
