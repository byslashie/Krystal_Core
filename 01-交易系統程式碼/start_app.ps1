cd "g:\我的雲端硬碟\Krystal_AI_Trading_System"

# 清理舊進程
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

Start-Sleep -Seconds 2

# 啟動應用
$env:PYTHONIOENCODING = "utf-8"
& ".\.venv_research64\Scripts\python.exe" -m streamlit run app_minimal.py `
  --server.port 8888 `
  --server.headless false `
  --logger.level error

# 保持窗口開放
Read-Host "Press Enter to exit"
