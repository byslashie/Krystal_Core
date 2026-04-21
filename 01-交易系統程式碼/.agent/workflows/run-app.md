---
description: 執行 Streamlit 交易儀表板 (app.py)
---

這個工作流將使用 `.venv` 虛擬環境啟動 `app.py`。

### 執行步驟

1. **啟動應用程式**
// turbo
```powershell
& ".venv_research64\Scripts\python.exe" -m streamlit run app.py --server.port=8501
```

### 環境模式說明

根據您的設定，目前有以下三種模式可用：
- **元大模式 (Yuanta32)**: 使用 `.venv_yuanta32` (適用於 DLL / pythonnet)
- **MAC 模式 (MacIB64)**: 使用 `.venv_macib64` (適用於 IB / Streamlit)
- **分析模式 (Research64)**: 使用 `.venv_research64` (適用於 pandas / 分析 / sync)

預設儀表板 (`app.py`) 使用 `.venv` 執行。
