$projectPath = "C:\Projects\Krystal_完整系統\01-交易系統程式碼"
$python64 = "C:\Users\krystalchen\AppData\Local\Programs\Python\Python311\python.exe"

# ── Task 1: 全套同步 (開機 + 08:00 + 13:30) ──────────────────
$task1 = "Krystal Daily NAV Sync"
Unregister-ScheduledTask -TaskName $task1 -Confirm:$false -ErrorAction SilentlyContinue

$bat1 = "$projectPath\run_daily_nav.bat"
$t1a = New-ScheduledTaskTrigger -AtStartup
$t1a.Delay = "PT30S"
$t1b = New-ScheduledTaskTrigger -Daily -At 08:00am
$t1c = New-ScheduledTaskTrigger -Daily -At 13:30pm

$action1 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$bat1`"" -WorkingDirectory $projectPath
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -WakeToRun $true

Register-ScheduledTask -TaskName $task1 -Trigger @($t1a,$t1b,$t1c) -Action $action1 -Settings $settings -RunLevel Highest -Force | Out-Null
Write-Host "Task1 OK: $task1 - Triggers: $((Get-ScheduledTask -TaskName $task1).Triggers.Count)"

# ── Task 2: 元大盤中同步 (09:00-13:30 每 30 分鐘) ────────────
$task2 = "Krystal Yuanta Intraday Sync"
Unregister-ScheduledTask -TaskName $task2 -Confirm:$false -ErrorAction SilentlyContinue

$bat2 = "$projectPath\run_yuanta_sync.bat"
$times = @("09:00","09:30","10:00","10:30","11:00","11:30","12:00","12:30","13:00","13:30")
$triggers2 = $times | ForEach-Object { New-ScheduledTaskTrigger -Daily -At $_ }

$action2 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$bat2`"" -WorkingDirectory $projectPath
Register-ScheduledTask -TaskName $task2 -Trigger $triggers2 -Action $action2 -Settings $settings -RunLevel Highest -Force | Out-Null
Write-Host "Task2 OK: $task2 - Triggers: $((Get-ScheduledTask -TaskName $task2).Triggers.Count)"

Write-Host "`n全部排程設定完成！"
