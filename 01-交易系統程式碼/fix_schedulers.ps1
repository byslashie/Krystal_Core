$projectPath = "C:\Projects\Krystal_完整系統\01-交易系統程式碼"

# ── Task 1: 全套同步 (開機 + 08:00 + 13:30) ──────────────────
$task1 = "KrystalDailyNAV"
Unregister-ScheduledTask -TaskName $task1 -Confirm:$false -ErrorAction SilentlyContinue

$bat1 = "$projectPath\run_daily_nav.bat"
$t1a = New-ScheduledTaskTrigger -AtStartup
$t1a.Delay = "PT30S"
$t1b = New-ScheduledTaskTrigger -Daily -At "08:00am"
$t1c = New-ScheduledTaskTrigger -Daily -At "13:30pm"

$action1 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$bat1`"" -WorkingDirectory $projectPath
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -WakeToRun $true

Register-ScheduledTask -TaskName $task1 -Trigger @($t1a,$t1b,$t1c) -Action $action1 -Settings $settings -RunLevel Highest -Force | Out-Null
$t1 = Get-ScheduledTask -TaskName $task1
Write-Host "Task1 OK: $($t1.TaskName) - Triggers: $($t1.Triggers.Count) - Action: $($t1.Actions[0].Execute) $($t1.Actions[0].Arguments)"

# ── Task 2: 元大盤中同步 (09:00-13:30 每 30 分鐘) ────────────
$task2 = "KrystalNAV_Intraday"
Unregister-ScheduledTask -TaskName $task2 -Confirm:$false -ErrorAction SilentlyContinue

$bat2 = "$projectPath\run_yuanta_sync.bat"
$times = @("09:00","09:30","10:00","10:30","11:00","11:30","12:00","12:30","13:00","13:30")
$triggers2 = $times | ForEach-Object { New-ScheduledTaskTrigger -Daily -At $_ }

$action2 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$bat2`"" -WorkingDirectory $projectPath
Register-ScheduledTask -TaskName $task2 -Trigger $triggers2 -Action $action2 -Settings $settings -RunLevel Highest -Force | Out-Null
$t2 = Get-ScheduledTask -TaskName $task2
Write-Host "Task2 OK: $($t2.TaskName) - Triggers: $($t2.Triggers.Count) - Action: $($t2.Actions[0].Execute) $($t2.Actions[0].Arguments)"

Write-Host ""
Write-Host "全部排程設定完成！"
Write-Host "Task1 ($task1): 開機+30s, 每天 08:00, 13:30 -> run_daily_nav.bat"
Write-Host "Task2 ($task2): 每天 09:00-13:30 每30分鐘 -> run_yuanta_sync.bat"
