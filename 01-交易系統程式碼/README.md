# Krystal 完整系統

整合自：
- `Krystal_AI_Trading_System`（Google Drive）— Python 交易應用程式
- `Krystal_Trading_Vault_v13`（本機）— 知識庫與策略文件

合併日期：2026-03-20

---

## 資料夾結構

| 資料夾              | 來源                           | 內容說明                                                  |
| ---------------- | ---------------------------- | ----------------------------------------------------- |
| `01-交易系統程式碼/`    | Krystal_AI_Trading_System    | Flask/Streamlit 交易應用程式、Broker API（Schwab、元大、IB）、UI 頁面 |
| `02-策略知識庫/`      | Vault / 01-Modules           | 策略模組、分類器、執行、風控、績效監控、資金配置                              |
| `03-XScript知識庫/` | Vault / XSAI資料庫              | XQ 語法參考、函式手冊、回測範例、開發筆記                                |
| `04-個人特質與規劃/`    | Vault / 00-願景規劃              | 個人特質分析、職涯規劃、財務規劃、心理與能量                                |
| `05-文件與報告/`      | 兩邊合併                         | 技術文件（docs/）、績效週報、決策記錄、市場研究                            |
| `06-資料字典/`       | Vault / 02-Data Dictionaries | 回測、策略、市場狀態的資料欄位定義                                     |
| `07-工具/`         | Vault / _tools               | FoodTracker、xsgpt、xshelp 等獨立工具                        |
| `08-模板/`         | Vault / 99-Templates         | 模組、回測、週報、運營的 Markdown 模板                              |
| `09-附件截圖/`       | Vault / attachments截圖        | 系統架構圖、UI 截圖                                           |
| `10-AI設定/`       | Vault / .claude              | Claude agents、自訂指令、skills                             |

---

## 注意事項

- **執行交易程式**：進入 `01-交易系統程式碼/`，需重建 Python 虛擬環境（原 venv 已排除以節省空間）
  ```bash
  python3 -m venv .venv
  pip install -r requirements.txt  # 若有 requirements.txt
  ```
- **虛擬環境**：原本的 `.venv_macib64`（約 1GB）已排除，需重新安裝依賴
- **憑證檔案**：`credentials.json`、`api.env`、`key/` 資料夾包含敏感資訊，請勿上傳至公開版本庫
