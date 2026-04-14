# Flask 交易儀表板啟動腳本 (Windows PowerShell)

$ScriptDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
$TradingDir = Join-Path $ScriptDir "01-交易系統程式碼"

Write-Host "📂 切換到目錄: $TradingDir" -ForegroundColor Green

Set-Location $TradingDir

# 檢查 Python
Write-Host "🔍 檢查 Python..." -ForegroundColor Cyan
if (-Not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python 未安裝" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python 已安裝" -ForegroundColor Green

# 激活虛擬環境（如果存在）
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "✅ 激活虛擬環境..." -ForegroundColor Green
    & ".\venv\Scripts\Activate.ps1"
}

# 檢查 Flask
Write-Host "🔍 檢查 Flask..." -ForegroundColor Cyan
python -c "import flask" -ErrorAction SilentlyContinue
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Flask 未安裝，正在安裝..." -ForegroundColor Yellow
    pip install flask
}

# 啟動 Flask
Write-Host "🚀 啟動 Flask 應用..." -ForegroundColor Green
Write-Host "📊 訪問地址: http://127.0.0.1:8888" -ForegroundColor Green
Write-Host "💡 按 Ctrl+C 停止應用" -ForegroundColor Yellow
Write-Host ""

python app_html_flask.py
