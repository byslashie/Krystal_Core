# Windows Task Scheduler setup for daily NAV sync
# Execute as Administrator
# Command: powershell -ExecutionPolicy Bypass -File setup_daily_nav_scheduler.ps1

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "Error: Please run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

$taskName = "Krystal Daily NAV Sync"
$taskDescription = "Auto sync broker positions and portfolio NAV to Google Sheets at startup, 8:00 AM, 9:00 AM, and 1:30 PM daily"
$projectPath = "C:\Projects\Krystal_完整系統\01-交易系統程式碼"
$scriptPath = "$projectPath\run_daily_nav.bat"

Write-Host "`n=== Task Scheduler Setup ===" -ForegroundColor Cyan
Write-Host "Task: Daily NAV Sync" -ForegroundColor Cyan
Write-Host "Triggers: At startup + Daily 8:00 AM + 9:00 AM + 1:30 PM" -ForegroundColor Cyan

# Check if script exists
if (-not (Test-Path $scriptPath)) {
    Write-Host "`nError: $scriptPath not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "`nStep 1: Remove existing task..." -ForegroundColor Yellow
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
    Write-Host "Removed old task" -ForegroundColor Green
}

# Create triggers
Write-Host "Step 2: Create triggers..." -ForegroundColor Yellow
$trigger1 = New-ScheduledTaskTrigger -AtStartup -Delay (New-TimeSpan -Seconds 30)
$trigger2 = New-ScheduledTaskTrigger -Daily -At 08:00am
$trigger3 = New-ScheduledTaskTrigger -Daily -At 09:00am
$trigger4 = New-ScheduledTaskTrigger -Daily -At 01:30pm
Write-Host "Triggers created" -ForegroundColor Green

# Create action
Write-Host "Step 3: Create action..." -ForegroundColor Yellow
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath`"" -WorkingDirectory $projectPath

# Create settings
Write-Host "Step 4: Configure settings..." -ForegroundColor Yellow
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew

# Register task
Write-Host "Step 5: Register task..." -ForegroundColor Yellow
try {
    Register-ScheduledTask -TaskName $taskName -Description $taskDescription -Trigger @($trigger1, $trigger2, $trigger3, $trigger4) -Action $action -Settings $settings -RunLevel Highest -Force -ErrorAction Stop | Out-Null
    Write-Host "Task registered successfully!" -ForegroundColor Green
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Verify
Write-Host "Step 6: Verify task..." -ForegroundColor Yellow
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($task) {
    Write-Host "`n=== Task Details ===" -ForegroundColor Green
    Write-Host "Name: $($task.TaskName)"
    Write-Host "State: $($task.State)"
    Write-Host "Triggers: $($task.Triggers.Count)"
    Write-Host "`nSuccess! Task is ready." -ForegroundColor Green
    Write-Host "Logs: $projectPath\_logs\daily_nav.log" -ForegroundColor Cyan
} else {
    Write-Host "Verification failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "`nPress Enter to close"
Read-Host
