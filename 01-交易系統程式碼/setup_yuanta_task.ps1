# ============================================================================
# 元大庫存自動同步 - Windows Task Scheduler 設置腳本
# 每個交易日 09:15 自動執行 sync_yuanta_positions.py
# 使用方法（需管理員 PowerShell）：
#   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
#   .\setup_yuanta_task.ps1
# ============================================================================

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "ERROR: 請以管理員身份運行此腳本" -ForegroundColor Red
    Write-Host "右鍵 PowerShell -> 以系統管理員身份執行" -ForegroundColor Yellow
    exit 1
}

$taskName    = "Krystal-元大庫存同步-0915"
$projectPath = "h:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"
$batFile     = "$projectPath\sync_yuanta_09h15.bat"

Write-Host ""
Write-Host "=== 元大庫存同步 Task Scheduler 設置 ===" -ForegroundColor Cyan
Write-Host "任務名稱 : $taskName"
Write-Host "執行時間 : 每天 09:15 (週一~週五)"
Write-Host "批次文件 : $batFile"
Write-Host ""

# 確認 bat 檔存在
if (-not (Test-Path $batFile)) {
    Write-Host "ERROR: 找不到 $batFile" -ForegroundColor Red
    exit 1
}
Write-Host "OK  批次文件存在" -ForegroundColor Green

# 刪除舊任務
$old = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($old) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "OK  舊任務已移除" -ForegroundColor Green
}

# 觸發器：每天 09:15，只在週一~週五
$trigger = New-ScheduledTaskTrigger -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
    -At "09:15"

# 動作：執行 bat 檔
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$batFile`"" `
    -WorkingDirectory $projectPath

# 設定：即使電池供電也執行；錯過時啟動
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

# 以當前使用者身分執行（不需要密碼存起來）
Register-ScheduledTask `
    -TaskName $taskName `
    -Description "每個交易日 09:15 自動同步元大現貨庫存到 Google Sheets" `
    -Trigger $trigger `
    -Action $action `
    -Settings $settings `
    -RunLevel Highest | Out-Null

# 驗證
$t = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($t) {
    Write-Host "OK  Task 已成功建立！" -ForegroundColor Green
    $info = Get-ScheduledTaskInfo -TaskName $taskName
    Write-Host "    下次執行時間 : $($info.NextRunTime)"
} else {
    Write-Host "ERROR: 建立失敗" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "完成！日誌位置: $projectPath\logs\yuanta_sync_*.log" -ForegroundColor Cyan
