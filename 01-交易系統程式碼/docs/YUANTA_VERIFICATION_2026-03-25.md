# 元大證券 API 驗證報告
**日期**: 2026-03-25  
**執行者**: Claude Code

---

## ✅ 驗證結果總覽

| 項目 | 狀態 | 說明 |
|------|------|------|
| DLL 載入 | ✅ 成功 | YuantaOneAPI v1.0.17.0 |
| PROD 伺服器連線 | ✅ 成功 | 40.100.0.45 |
| 登入 (Login) | ✅ 成功 | Binary response 含帳號確認 |
| 庫存查詢 RQ | ✅ 送出 / 收到回應 | RtnCode=0（可能空庫存）|

---

## 🔧 環境變更

### .env 更新
```
YUANTA_ENV=PROD          ← 由 UAT 改為 PROD
YUANTA_ACCOUNT=S989C0316437  ← 確認使用 S 開頭帳號
```

### 32-bit Python 安裝
- 安裝位置：`C:\Python311-32\python.exe`
- 版本：Python 3.11.9 32-bit
- 新 venv：`.venv_yuanta32_new\`
- 已安裝套件：`pythonnet 3.0.5`, `python-dotenv 1.2.2`

---

## 📊 Login 事件解析

```
intMark=1, dwIndex=0, strIndex='Login'
Binary response (109 bytes):
  cp950: 00001...S989C0316437...
  → 帳號 S989C0316437 登入成功確認
```

## 📊 庫存查詢事件解析

```
RQ(SetFunctionID(20, 103, 0, 22)) → True
intMark=1, dwIndex=7, strIndex=''
Data: '20.103.0.22 ...RtnCode=0'
  → 查詢執行成功，RtnCode=0
  → 目前庫存可能為空，或需進一步解析 binary 格式
```

---

## ⚠️ 待確認事項

1. **庫存是否為空？** 帳號目前是否有任何台股庫存？
   - 若有庫存但未顯示 → 需要解析 binary 回應格式
   - 若確實無庫存 → API 連線完全正常

2. **venv 路徑更新**  
   背景工作 (`yuanta_background_worker.py`) 目前指向舊的 `.venv_yuanta32`，建議更新為 `.venv_yuanta32_new`：
   ```python
   # workers/yuanta_background_worker.py 中的 Python 路徑需更新
   PYTHON_32BIT = r"H:\...\01-交易系統程式碼\.venv_yuanta32_new\Scripts\python.exe"
   ```

3. **UAT 憑證已過期** (TWA126522566, 2025/5/21)  
   → 若未來需要 UAT 測試，需向元大重新申請

---

## 🔑 Windows 憑證存放區狀態

| 憑證 CN | 到期日 | 狀態 |
|---------|--------|------|
| TWD222061405 Yuanta | 2026/8/12 | ✅ 有效 |
| TWS221742547 Yuanta | 2026/4/1 | ✅ 有效 |
| TWA126522566 Yuanta (UAT) | 2025/5/21 | ❌ 過期 |
| D222061405 (Cathaysec) | 2026/3/23 | ❌ 剛過期 |

---

## 🚀 下一步

```bash
# 使用新的 32-bit venv 執行庫存同步
.venv_yuanta32_new\Scripts\python.exe brokers\sync_yuanta_positions.py

# 或更新背景 worker 路徑後啟動
python workers\yuanta_background_worker.py
```

---
*最後更新: 2026-03-25 | 維護者: Krystal*
