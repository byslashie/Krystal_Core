# Krystal Fitness Tracker GAS 版 — 部署說明

## 架構
```
手機 → Google Apps Script (Web App)
         ├── Google Sheets (資料庫：meals / daily_log / workout_log)
         ├── Google Drive (食物圖片)
         └── Gemini API (食物辨識)
```

---

## 步驟 1：建立 Google Sheets

1. 開 [sheets.new](https://sheets.new) → 新增空白試算表
2. 命名為「Krystal Fitness DB」
3. 複製網址列的 ID（`/d/` 和 `/edit` 之間那段）→ 這是 `SPREADSHEET_ID`
https://docs.google.com/spreadsheets/d/11mHYI0xBwFL3y-Ci25UESqK29jA7GVJy5oKVhabxMAE/edit?usp=sharing
11mHYI0xBwFL3y-Ci25UESqK29jA7GVJy5oKVhabxMAE
---

## 步驟 2：建立 Drive 資料夾

1. 開 Google Drive → 新增資料夾，命名「FoodPhotos」
2. 進入資料夾，複製網址列最後的 ID → 這是 `DRIVE_FOLDER_ID`
https://drive.google.com/drive/folders/1UdLmr9IVqOxfKW4rFbfNS3y9TWhIhCmY?usp=drive_link

1UdLmr9IVqOxfKW4rFbfNS3y9TWhIhCmY?usp
---

## 步驟 3：建立 Apps Script 專案

1. 開 [script.google.com](https://script.google.com) → 新增專案
2. 命名為「Krystal Fitness」
3. 刪除預設的 `function myFunction() {}`

### 貼入 Code.gs
- 點左側「Code.gs」
- 把 `Code.gs` 的內容全部貼進去

### 新增 Index.html
- 點上方「+」→「HTML」→ 命名「Index」（不要加 .html）
- 把 `Index.html` 的內容全部貼進去

---

## 步驟 4：設定 Script Properties

1. 左上角「專案設定」（齒輪圖示）
2. 往下找「指令碼屬性」→「新增屬性」
3. 加入以下三個：

| 屬性名稱              | 值                 |
| ----------------- | ----------------- |
| `SPREADSHEET_ID`  | 步驟1複製的ID          |
| `GEMINI_API_KEY`  | 你的 Gemini API Key |
| `DRIVE_FOLDER_ID` | 步驟2複製的ID          |

> Gemini API Key 申請：[aistudio.google.com](https://aistudio.google.com) → Get API Key（免費）

---

## 步驟 5：部署 Web App

1. 點右上角「部署」→「新增部署作業」
2. 類型選「網頁應用程式」
3. 設定：
   - **說明**：v1
   - **執行身分**：我（你的 Google 帳戶）
   - **有權存取的使用者**：所有人（Anyone）← 選這個，有連結就能用，不需登入
4. 按「部署」→ 授權 → 複製網址

---

## 步驟 6：加到手機主畫面

### iPhone：
1. Safari 開啟 Web App 網址
2. 分享 → 加入主畫面

### Android：
1. Chrome 開啟網址
2. 選單 → 加入主畫面

---

## 更新版本

每次修改 Code.gs 或 Index.html 後：
1. 「部署」→「管理部署作業」→ 編輯（鉛筆圖示）
2. 版本改為「新版本」→「部署」

---

## Sheets 欄位說明

自動建立，不需手動設定：

**meals**：id, date, meal_type, description, calories, protein, carbs, fat, image_url, created_at

**daily_log**：date, exercise, day_type

**workout_log**：id, date, day_label, exercise, planned, actual_weight, reps, sets, feeling, notes

---

## 訓練排程

自動依今天日期計算：
- W1 起始：2026/03/24
- 週一：A日（臀腿或深蹲）
- 週三：B日（推或拉）
- 週五：C日（全身代謝）
- 其他日：顯示休息

---

## 注意事項

- GAS 免費版每天 6 小時執行時間，個人使用完全夠用
- Gemini API 免費版有每日限制，正常使用不會超過
- 圖片儲存在 Drive，Sheets 只存連結（省空間）
