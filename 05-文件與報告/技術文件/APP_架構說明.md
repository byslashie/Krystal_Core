# APP.PY 架構說明

> 量化交易策略績效分析儀表板，使用 Streamlit 建構。

---

## 一、頁面設定 & 輸入區（全域）

| 元件 | 功能 |
|------|------|
| `initial_capital` | 初始資金輸入框 |
| `uploaded_file` | 上傳策略績效 CSV 檔案 |
| `benchmark_symbols` | 輸入 Benchmark 代碼（如 0050.TW） |
| `use_yf` | 是否啟用 Yahoo Finance Benchmark |

---

## 二、Sidebar（側邊欄）

- **OpenRouter API 金鑰** 輸入
- **AI 模型選擇**（支援 5 個免費模型）：
  - Gemini 2.0 Flash (`google/gemini-2.0-flash-exp:free`)
  - DeepSeek Chat v3 (`deepseek/deepseek-chat-v3-0324:free`)
  - Llama 4 Maverick (`meta-llama/llama-4-maverick:free`)
  - Qwen3 235B (`qwen/qwen3-235b-a22b:free`)
  - Microsoft MAI-DS-R1 (`microsoft/mai-ds-r1:free`)

---

## 三、主要分析流程（CSV 上傳後觸發）

```
CSV 上傳
  ├── 資料清洗（日期轉換、去除 NaN、過濾 2009 後資料）
  ├── 指標計算
  │     ├── 年化報酬率
  │     ├── Sharpe Ratio
  │     ├── 最大回撤 (MDD)
  │     ├── 勝率、淨利、毛利、毛損
  │     └── 平均持倉天數
  │
  └── 視覺化模組（7 個圖表）
        ├── 1. 關鍵績效摘要（指標卡片，matplotlib）
        ├── 2. 策略報酬折線圖（plotly line chart）
        ├── 3. 累積資金曲線 + Benchmark（plotly area + scatter）
        ├── 4. 最大回撤分析（plotly area chart）
        ├── 5. 月度滾動報酬率（plotly line chart）
        ├── 6. 每期持股數（plotly area chart）
        └── 7. 年月報酬熱力圖（plotly density heatmap）
```

---

## 四、Summary Statistics 模組

以 DataFrame 表格顯示 9 個量化指標：

| 指標 | 說明 |
|------|------|
| 年化報酬率 (%) | 策略年化報酬 |
| 最大回撤 (%) | 歷史最大虧損幅度 |
| Sharpe Ratio | 風險調整後報酬 |
| 勝率 (%) | 獲利交易比例 |
| 淨利 | 總淨獲利金額 |
| 毛利 | 所有獲利交易加總 |
| 毛損 | 所有虧損交易加總 |
| 最大投入資金 | 單筆最大投入金額 |
| 平均持倉日數 | 每筆交易平均持有天數 |

---

## 五、AI 策略建議模組

按下「產生 AI 策略建議」按鈕後：
- 將績效摘要送給 **OpenRouter AI**
- AI 角色設定為「資深量化交易策略分析師」
- 回傳與 0050 / VOO 的比較建議及具體優化方向

---

## 使用的套件

| 套件 | 用途 |
|------|------|
| `streamlit` | UI 框架 |
| `pandas` | 資料處理與分析 |
| `numpy` | 數值運算 |
| `matplotlib` | 指標卡片圖（靜態圖） |
| `plotly` | 互動式圖表 |
| `yfinance` | 下載 Benchmark 股價資料 |
| `openai` | 串接 OpenRouter AI API |

---

## CSV 輸入格式需求

上傳的 CSV 需包含以下欄位：

| 欄位名稱 | 說明 |
|----------|------|
| `進場時間` | 買進日期時間 |
| `出場時間` | 賣出日期時間 |
| `進場價格` | 買進價格 |
| `出場價格` | 賣出價格 |
| `商品代碼` | 股票代碼（選填，用於持股數統計） |

> 支援 `cp950`（Big5）或 `utf-8` 編碼。
