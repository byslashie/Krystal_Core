$alreadyRunning = Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" | Where-Object { $_.CommandLine -match 'discord_bot' }
if (-not $alreadyRunning) {
    Start-Process -FilePath "c:\Projects\Krystal_完整系統\.venv\Scripts\pythonw.exe" -ArgumentList "c:\Projects\Krystal_完整系統\01-交易系統程式碼\discord_bot.py" -WorkingDirectory "c:\Projects\Krystal_完整系統\01-交易系統程式碼" -WindowStyle Hidden
}
