# ============================================================================
# 🔄 Windows Task Scheduler 自動配置腳本
# 功能：自動創建每日自動同步任務
# 使用方法：
#   1. 以管理員身份運行 PowerShell
#   2. cd 到項目目錄
#   3. Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
#   4. .\setup_task_scheduler.ps1
# ============================================================================

# 檢查管理員權限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "❌ 錯誤：請以管理員身份運行此腳本！" -ForegroundColor Red
    Write-Host "請右鍵點擊 PowerShell → '以管理員身份運行'" -ForegroundColor Yellow
    exit 1
}

# 配置參數
$taskName = "Krystal AI - 元大持倉自動同步"
$taskDescription = "每天上午 9:00 自動同步元大持倉到 Google Sheets"
$projectPath = "g:\我的雲端硬碟\Krystal_AI_Trading_System"
$scriptPath = "$projectPath\sync_daily.bat"
$pythonPath = "python"  # 或完整路徑如 "C:\Python\python.exe"

Write-Host "
╔══════════════════════════════════════════════════════════════╗
║  🔄 Windows Task Scheduler 自動配置                         ║
║  任務名稱：$taskName          ║
║  計劃時間：每天上午 09:00                                    ║
╚══════════════════════════════════════════════════════════════╝
" -ForegroundColor Cyan

# 檢查腳本文件是否存在
if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ 錯誤：找不到 $scriptPath" -ForegroundColor Red
    Write-Host "請確保 sync_daily.bat 已創建在項目目錄中" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ 已找到批次文件：$scriptPath" -ForegroundColor Green

# 步驟 1：刪除舊任務（如果存在）
Write-Host "`n📍 步驟 1：清理舊任務..." -ForegroundColor Yellow
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "   找到舊任務，正在刪除..." -ForegroundColor Gray
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false | Out-Null
    Write-Host "   ✅ 舊任務已刪除" -ForegroundColor Green
} else {
    Write-Host "   無舊任務，跳過" -ForegroundColor Gray
}

# 步驟 2：創建任務觸發器（每天 09:00）
Write-Host "`n📍 步驟 2：創建任務觸發器..." -ForegroundColor Yellow
$trigger = New-ScheduledTaskTrigger -Daily -At 09:00am

# 步驟 3：創建任務操作
Write-Host "`n📍 步驟 3：創建任務操作..." -ForegroundColor Yellow
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$scriptPath`"" `
    -WorkingDirectory $projectPath

# 步驟 4：創建任務設置
Write-Host "`n📍 步驟 4：配置任務設置..." -ForegroundColor Yellow
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

# 步驟 5：註冊任務
Write-Host "`n📍 步驟 5：註冊任務..." -ForegroundColor Yellow
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Description $taskDescription `
        -Trigger $trigger `
        -Action $action `
        -Settings $settings `
        -RunLevel Highest | Out-Null

    Write-Host "✅ 任務已成功創建！" -ForegroundColor Green
} catch {
    Write-Host "❌ 創建任務失敗：$_" -ForegroundColor Red
    exit 1
}

# 步驟 6：驗證
Write-Host "`n📍 步驟 6：驗證任務..." -ForegroundColor Yellow
$task = Get-ScheduledTask -TaskName $taskName
if ($task) {
    Write-Host "✅ 任務已驗證！" -ForegroundColor Green
    Write-Host "`n任務詳情：" -ForegroundColor Cyan
    Write-Host "   名稱：$($task.TaskName)"
    Write-Host "   狀態：$($task.State)"
    Write-Host "   下次運行：$($task.Triggers[0].StartBoundary)"
} else {
    Write-Host "❌ 驗證失敗" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + ("=" * 62) -ForegroundColor Cyan
Write-Host "✅ 自動同步已成功配置！" -ForegroundColor Green
Write-Host "=" * 62 -ForegroundColor Cyan
Write-Host "`n📅 同步計劃：每天上午 09:00" -ForegroundColor Cyan
Write-Host "📂 日誌位置：$projectPath\logs\sync_*.txt" -ForegroundColor Cyan
Write-Host "`n💡 提示：" -ForegroundColor Yellow
Write-Host "   • 可在 Windows 工作排程器中手動調整時間"
Write-Host "   • 日誌會自動保存到 logs 資料夾"
Write-Host "   • 如要禁用任務，可右鍵選擇 '停用'" -ForegroundColor Yellow
Write-Host ""
