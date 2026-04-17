$startup = [Environment]::GetFolderPath('Startup')
$batPath = 'h:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼\start_discord_bot.bat'
$shortcut = (New-Object -COM WScript.Shell).CreateShortcut("$startup\Krystal-Discord-Bot.lnk")
$shortcut.TargetPath = 'cmd.exe'
$shortcut.Arguments = "/c `"$batPath`""
$shortcut.WorkingDirectory = 'h:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼'
$shortcut.WindowStyle = 7
$shortcut.Save()
Write-Output "已建立開機啟動捷徑：$startup\Krystal-Discord-Bot.lnk"
