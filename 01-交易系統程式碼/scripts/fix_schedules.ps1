# fix_schedules.ps1 - 修正所有元大排程的 Execute/Arguments/WorkingDir

$bat_sync = 'h:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼\sync_yuanta_09h15.bat'
$bat_nav  = 'h:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼\record_daily_nav.bat'

$tasks = @(
    @{ Name='Krystal-元大同步-0915'; Bat=$bat_sync; Time='09:45' },
    @{ Name='Krystal-元大同步-1230'; Bat=$bat_sync; Time='12:30' },
    @{ Name='Krystal-元大同步-1335'; Bat=$bat_sync; Time='13:35' },
    @{ Name='Krystal-每日後記錄-1340'; Bat=$bat_nav;  Time='13:40' }
)

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

foreach ($t in $tasks) {
    # 統一用 cmd.exe /c "bat路徑"，不設 WorkingDirectory（bat 自己 cd /d）
    $action = New-ScheduledTaskAction `
        -Execute  'cmd.exe' `
        -Argument ('/c "' + $t.Bat + '"')

    $trigger = New-ScheduledTaskTrigger `
        -Weekly `
        -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
        -At $t.Time

    Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false -ErrorAction SilentlyContinue
    $result = Register-ScheduledTask `
        -TaskName $t.Name `
        -Action   $action `
        -Trigger  $trigger `
        -Settings $settings `
        -RunLevel Highest `
        -Force

    if ($result) {
        Write-Host ('[OK] ' + $t.Name + ' -> ' + $t.Time) -ForegroundColor Green
    } else {
        Write-Host ('[FAIL] ' + $t.Name) -ForegroundColor Red
    }
}

Write-Host ''
Write-Host '=== 修正後排程 ==='
Get-ScheduledTask | Where-Object { $_.TaskName -like 'Krystal-*' } | ForEach-Object {
    $info = Get-ScheduledTaskInfo -TaskName $_.TaskName -EA SilentlyContinue
    $a = $_.Actions[0]
    Write-Host ($_.TaskName + ' | Exec=' + $a.Execute + ' | Args=' + $a.Arguments + ' | WorkDir=' + $a.WorkingDirectory)
}
