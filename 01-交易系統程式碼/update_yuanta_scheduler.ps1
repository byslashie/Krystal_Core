$taskName = "Krystal Yuanta Intraday Sync"
$projectPath = "C:\Projects\Krystal_完整系統\01-交易系統程式碼"
$scriptPath = "$projectPath\run_yuanta_sync.bat"

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# 09:00 - 13:30 每 30 分鐘，共 10 個時間點
$times = @("09:00","09:30","10:00","10:30","11:00","11:30","12:00","12:30","13:00","13:30")
$triggers = $times | ForEach-Object { New-ScheduledTaskTrigger -Daily -At $_ }

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath`"" -WorkingDirectory $projectPath
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $taskName -Trigger $triggers -Action $action -Settings $settings -RunLevel Highest -Force | Out-Null

$task = Get-ScheduledTask -TaskName $taskName
Write-Host "Done! Task: $($task.TaskName), Triggers: $($task.Triggers.Count)"
