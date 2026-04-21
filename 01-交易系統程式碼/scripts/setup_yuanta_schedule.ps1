# setup_yuanta_schedule.ps1
# 設定元大庫存同步排程（每週一~五 3 個時段）

$bat = 'h:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼\同步元大庫存.bat'
$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument "/c `"$bat`""
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

$schedule = @(
    @{ Name = 'Krystal_元大同步_0935'; Time = '09:35' },
    @{ Name = 'Krystal_元大同步_1335'; Time = '13:35' },
    @{ Name = 'Krystal_元大同步_1705'; Time = '17:05' }
)

foreach ($s in $schedule) {
    $trigger = New-ScheduledTaskTrigger `
        -Weekly `
        -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
        -At $s.Time

    # 刪除舊的（忽略錯誤）
    Unregister-ScheduledTask -TaskName $s.Name -Confirm:$false -ErrorAction SilentlyContinue

    # 建立
    $task = Register-ScheduledTask `
        -TaskName $s.Name `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -RunLevel Highest `
        -Force

    if ($task) {
        Write-Host "[OK] $($s.Name) - 每週一~五 $($s.Time)" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] $($s.Name)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== 現有 Krystal 排程 ===" -ForegroundColor Cyan
Get-ScheduledTask | Where-Object { $_.TaskName -like 'Krystal*' } |
    Select-Object TaskName, State |
    Format-Table -AutoSize
