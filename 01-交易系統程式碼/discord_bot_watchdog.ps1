#Requires -Version 5.1
<#
Krystal Discord Bot Watchdog
- 每 5 分鐘由工作排程器 Krystal_Discord_Bot_Watchdog 觸發
- 檢查是否有 python 進程在跑 discord_bot.py
- 沒有就啟動 Boot 任務
- log 寫到 watchdog.log（最近 200 行）
#>

$ErrorActionPreference = 'Continue'
$BotPath  = 'c:\Projects\Krystal_完整系統\01-交易系統程式碼\discord_bot.py'
$BootTask = 'Krystal_Discord_Bot_Boot'
$LogFile  = 'c:\Projects\Krystal_完整系統\01-交易系統程式碼\watchdog.log'

function Write-Log {
    param([string]$msg)
    $line = "[{0:yyyy-MM-dd HH:mm:ss}] {1}" -f (Get-Date), $msg
    $line | Out-File -FilePath $LogFile -Append -Encoding utf8
}

# 修剪 log（>200 行就只保留尾 200 行）
if (Test-Path $LogFile) {
    $lines = Get-Content $LogFile
    if ($lines.Count -gt 200) {
        $tail = $lines | Select-Object -Last 200
        $tail | Out-File -FilePath $LogFile -Encoding utf8
    }
}

# 找有沒有 python 在跑 discord_bot.py（python.exe 或 pythonw.exe 都算）
$running = Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" |
    Where-Object { $_.CommandLine -match 'discord_bot\.py' }

if ($running) {
    # 注意：在 venv 模式下，同一個 bot 會顯示 2 個進程（launcher + 實際），這正常
    $pids = ($running | ForEach-Object { $_.ProcessId }) -join ','
    Write-Log ("OK bot alive PIDs={0}" -f $pids)
    exit 0
}

# bot 不在 → 嘗試用 Boot 任務拉起
Write-Log 'DOWN bot not running, triggering Boot task...'
try {
    Start-ScheduledTask -TaskName $BootTask -ErrorAction Stop
    Start-Sleep -Seconds 10
    $afterStart = Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" |
        Where-Object { $_.CommandLine -match 'discord_bot\.py' }
    if ($afterStart) {
        $pids = ($afterStart | ForEach-Object { $_.ProcessId }) -join ','
        Write-Log ("RESTARTED PIDs={0}" -f $pids)
        exit 0
    } else {
        Write-Log 'FAIL Boot task ran but no python process found after 10s'
        exit 1
    }
} catch {
    Write-Log ("ERROR Start-ScheduledTask failed: {0}" -f $_.Exception.Message)
    exit 1
}
