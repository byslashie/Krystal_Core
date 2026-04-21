# 2026-04-01 交易系統更新日誌

## 📊 功能改善：初始資金雙模式 + 自動 MD 寫入

### 問題背景
CAGR 異常高企 (+5367320%) 原因：初始資金 $100,000 與實際交易持倉金額相差過大

### 修改內容

#### 1️⃣ 前端：dashboard_v8/index.html

**① 初始資金輸入改為雙模式**（行 1961-1972）
- **自動模式**（預設）：
  - 從 CSV 自動偵測「買進金額」、「持倉金額」等欄位
  - 計算同時期最大的累積持倉作為初始資金
  - Fallback：若無持倉欄位，用 max(|pnl|) × 50 推算
  
- **自定義模式**：
  - 手動輸入初始資金額（支援原有的 input 欄位）

**② 新增函數**
- `calculateMaxPoolCapital(trades)`：計算最大日持倉金額
- `toggleCapitalMode()`：切換模式時控制 UI 顯示/隱藏

**③ 修改 parseCSVFile() 和 parseTradeSheet()**
- 新增 `position` 欄位偵測（搜索順序：買進金額 → 成交金額 → 持倉金額 → position → amount）
- trades 物件格式從 `{pnl, date}` 擴展為 `{pnl, date, position?}`

**④ 修改 analyzeStrategy()**
- 根據選中的模式決定初始資金
- 第一個檔案決定全局初始資金，套用所有後續檔案
- 分析完成後動態更新「自動計算」顯示的值

**⑤ 修改 confirmStrategyImport()**
- 從虛假的 alert 改為真實的 API 調用
- POST 到 `/api/strategy/confirm-preview`，傳入 `strategy_name`, `kpis`, `initial_capital`
- 根據後端返回的 `folder_path` 反饋給用戶

**⑥ 修改 goToStrategyPreview()**
- 動態生成資料夾 ID（簡單實現：S + 時間戳）
- 在預覽頁面中動態顯示完整資料夾路徑

---

#### 2️⃣ 後端：strategy_sync_api.py

**修改 `/api/strategy/confirm-preview` 端點**（行 239）

原有邏輯：必須傳入 `analysis_id` 並讀取對應的 meta.json 文件

新邏輯：
- 若有 `analysis_id` → 使用舊流程（向後相容）
- 若無 `analysis_id` → 直接使用請求中的 kpis，自動生成下一個資料夾 ID

**實現方式：**
```python
if analysis_id and meta_path.exists():
    # 從 meta.json 讀取（舊流程）
    meta = load_from_meta()
else:
    # 新流程：自動計算 S{N}，用請求的 kpis
    next_num = find_max_existing_folder_num() + 1
    meta = {
        'kpis': kpis,
        'next_folder_id': next_num,
        'initial_capital': initial_capital
    }
```

**MD 文件生成改進：**
- 自動提取 kpis 中的各項指標（支援多種欄位命名，如 `winRate` 或 `win_rate`）
- 在 Home.md 的 frontmatter 中記錄 `initial_capital`
- 在正文中新增「回測設定」段落，明確顯示使用的初始資金

**返回值：**
- 新增 `success: True` 布林值欄位（相容前端檢查）

---

### 🎯 使用流程

1. **上傳 CSV**（含買進金額欄位）
2. **分析頁面** → 自動選中「最大投入」
3. **分析按鈕** → 自動計算出最大池倉金額並顯示
4. **進入預覽決策**
5. **批准導入** → 真實 POST 到後端 → 在 `02-策略知識庫/Staging/drafts/` 生成完整資料夾結構和 MD 文件

---

### ✅ 驗證方式

```bash
# 檢查生成的 MD 文件
ls -la "G:\我的雲端硬碟\Krystal_完整系統\02-策略知識庫\Staging\drafts\"

# 檢查 Home.md 是否包含 initial_capital
grep -r "initial_capital" "G:\我的雲端硬碟\Krystal_完整系統\02-策略知識庫\Staging\drafts\"
```

---

### 📝 修改檔案清單

| 檔案 | 行號 | 變更摘要 |
|------|------|--------|
| dashboard_v8/index.html | 1961-1972 | 初始資金雙模式 HTML |
| dashboard_v8/index.html | 5208-5240 | 計算函數 + toggleCapitalMode |
| dashboard_v8/index.html | 5136-5202 | parseCSVFile 加持倉欄位 |
| dashboard_v8/index.html | 5066-5108 | parseTradeSheet 加持倉欄位 |
| dashboard_v8/index.html | 5253-5288 | analyzeStrategy 邏輯改造 |
| dashboard_v8/index.html | 5966-6009 | goToStrategyPreview + confirmStrategyImport |
| strategy_sync_api.py | 252-297 | 無 analysis_id 時的 fallback 邏輯 |
| strategy_sync_api.py | 304-351 | MD 生成改進 + initial_capital 記錄 |
| strategy_sync_api.py | 410-415 | 返回值新增 success 欄位 |

---

**狀態**：✅ 完成，待測試
**提交者**：Claude Code
**日期**：2026-04-01
