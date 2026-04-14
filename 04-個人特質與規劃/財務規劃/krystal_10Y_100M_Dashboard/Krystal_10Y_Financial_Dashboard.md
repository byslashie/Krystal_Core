# Krystal 10-Year Financial Dashboard（Canvas 說明）

這一張 Canvas 是：「**10 年 1 億資產藍圖 × 投資系統總覽圖**」。  
核心運算在 Excel：`Krystal_10Y_100M_Dashboard_v3.xlsx`，  
Canvas 則是幫你**看懂整體結構、檢查節奏、做年度復盤**。

---

## 1. Canvas 節點總覽

Canvas 檔名：`Krystal_10Y_Financial_Dashboard.canvas`

節點說明：

- **📊 Krystal 10Y Dashboard v3（中央主控節點）**
  - 類型：file node
  - 連結檔案：`Krystal_10Y_100M_Dashboard_v3.xlsx`
  - 功能：開啟整個 10 年財務模型的 Excel 儀表板。

- **Dashboard 使用說明（灰紫 text node）**
  - 放的是總覽說明：目標、每年要更新哪些欄位。

- **📈 年度版_Yearly（藍紫 node）**
  - 顯示 10 年資產成長曲線。
  - 用來對比「實際 vs 計畫」。

- **📆 月度版_Monthly（藍紫 node）**
  - 用月度視角看複利曲線。
  - 幫助理解前期慢、後期快的成長節奏。

- **📉 三情境_Yearly（藍紫 node）**
  - 悲觀 15%、中性 25%、樂觀 35%。
  - 用來管理預期，不被單一年表現影響太大情緒。

- **🎯 倒推目標_GoalSeek（紫色 node）**
  - 問題一：如果鎖定報酬率，要每年投多少？
  - 問題二：如果每年只能投固定金額，要幾 % 報酬率？

- **🧩 資產配置_Alloc（深藍 node）**
  - 放你的多策略組合（ETF / 強勢股 / 期貨日內 / cbAS / Cover Call / 防禦資產）。
  - 調整權重與 APY，看到整體 Portfolio APY。

---

## 2. 建議放在 Obsidian 的位置

建議放在 Vault 中：

- Canvas：`01-LifePlanning/Wealth/Krystal_10Y_Financial_Dashboard.canvas`
- Excel：`01-LifePlanning/Wealth/Krystal_10Y_100M_Dashboard_v3.xlsx`
- 本說明檔：`01-LifePlanning/Wealth/Krystal_10Y_Financial_Dashboard.md`

這樣 Canvas 的檔案連結就會在同一資料夾裡，不容易炸裂。

---

## 3. 每年一次的「財務檢查儀式」

> 建議時間：每年 12 月底或隔年 1 月初，留一個半天。

步驟：

1. 開啟 Excel：`Krystal_10Y_100M_Dashboard_v3.xlsx`。
2. 在 `Dashboard` 分頁更新：
   - 目前資產（B20）。
3. 在 `年度版_Yearly` 新增或更新欄位：
   - `實際期末資產`。
4. 在 `資產配置_Alloc`：
   - 填寫今年各策略大致「實際權重」與「實際 APY」。

然後在本 MD 檔新增一個區塊：

### ▌{{year}} 年財務 × 投資總結

- 期初資產：  
- 期末資產：  
- 年度報酬率（實際）：  
- 年度投入金額（實際）：  
- 相對計畫進度：
  - 計畫資產（Excel 年度版試算）：  
  - 實際資產：  
  - 差距：提前 / 落後 __ 萬

**今年投資表現摘要：**

- 最穩定的策略：  
- 回撤最大的是：  
- 我最滿意的一筆操作：  
- 我最後悔的一筆操作：  
- 我學到的三件事：  
  1.  
  2.  
  3.  

**策略池調整：**

- 明年要：
  - [ ] 提高 ETF / 防禦比重
  - [ ] 提高 強勢股比重
  - [ ] 提高 期貨日內權重
  - [ ] 增加 / 啟動 cbAS 部位
  - [ ] 調整 Cover Call 比例

- 具體調整說明：


**收入與生活：**

- 本業收入變化：  
- 副業收入（聲音教練 / 課程）變化：  
- 是否有接近或超過「每年投入 180 萬」？  
- 對今年「錢 × 生活節奏」的感受：


> 今年我對「錢」的感覺是什麼？  
> （更有掌控感？還是壓力？還是開始覺得好玩？）

---

## 4. 季度小檢查模板（選配，但很適合你）

每季可以在這一檔下面，複製一個區塊：

### ▌Q{{quarter}} 季度檢查

- Q 初資產：  
- Q 末資產：  
- 本季投入金額：  
- 粗略報酬率（rough）：  
- 心情指標（1～10 分）：  
- 本季最值得紀錄的一件事：  


---

## 5. 如何搭配 Canvas 一起用

1. 打開 Obsidian Canvas：`Krystal_10Y_Financial_Dashboard.canvas`
2. 點中央的「📊 Krystal 10Y Dashboard v3」節點 → 開 Excel。
3. 視覺化看：
   - 年度版、月度版、三情境、倒推、資產配置彼此的關係。
4. 每次做完年度檢查：
   - 在本 MD 檔增加一個「今年」區塊。
   - 在 Canvas 裡，可以新增一個小 node，標註今年的關鍵字（例如：「2026：調高期貨權重」）。

---

## 6. 這張圖對你的意義

這張 Canvas + Excel 不是單純的表格，  
而是：

> 「未來 10 年，你如何用系統，慢慢地、溫柔但堅定地，走向 1 億資產的人生地圖。」

你可以每年回來看、每季微調策略、每次把學到的東西寫進來。  
等到哪一天你回頭看這些紀錄，會非常清楚：  

> 「原來，我不是突然成功的，  
>  而是這 10 年來，一步一步，有意識地走出來的。」
