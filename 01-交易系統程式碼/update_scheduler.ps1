$taskName = "Krystal Daily NAV Sync"
$projectPath = "C:\Projects\Krystal_完整系統\01-交易系統程式碼"
$scriptPath = "$projectPath\run_daily_nav.bat"

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$t1 = New-ScheduledTaskTrigger -AtStartup
$t1.Delay = "PT30S"
$t2 = New-ScheduledTaskTrigger -Daily -At 08:00am
$t3 = New-ScheduledTaskTrigger -Daily -At 09:00am
$t4 = New-ScheduledTaskTrigger -Daily -At 01:30pm

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath`"" -WorkingDirectory $projectPath
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $taskName -Trigger @($t1,$t2,$t3,$t4) -Action $action -Settings $settings -RunLevel Highest -Force | Out-Null

$task = Get-ScheduledTask -TaskName $taskName
Write-Host "Done! Triggers: $($task.Triggers.Count)"
$task.Triggers | ForEach-Object { Write-Host "  $_" }
