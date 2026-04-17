@echo off
setlocal EnableDelayedExpansion
title Krystal - Autostart Setup

cd /d "%~dp0"

echo.
echo  ==========================================
echo   Krystal AI - Windows Autostart Setup
echo  ==========================================
echo.

:: Check admin
net session >nul 2>&1
if !errorlevel! neq 0 (
    echo  Need admin rights. Restarting as admin...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -Verb RunAs"
    exit /b
)

:: Remove old task if exists
schtasks /delete /tn "Krystal_Trading_Autostart" /f >nul 2>&1

:: Create task
echo  [1/2] Creating scheduled task...
schtasks /create /tn "Krystal_Trading_Autostart" /tr "\"%~dp0START_KRYSTAL.bat\"" /sc ONLOGON /ru "%USERNAME%" /rl HIGHEST /delay 0000:30 /f

if !errorlevel! equ 0 (
    echo.
    echo  [2/2] Done!
    echo.
    echo  ==========================================
    echo   Auto-starts 30s after next login:
    echo     Backend  http://localhost:8889
    echo     Frontend http://localhost:5000
    echo  ==========================================
    echo.
    echo  Manage commands:
    echo    Disable : schtasks /change /tn "Krystal_Trading_Autostart" /disable
    echo    Enable  : schtasks /change /tn "Krystal_Trading_Autostart" /enable
    echo    Delete  : schtasks /delete /tn "Krystal_Trading_Autostart" /f
    echo    Run now : schtasks /run /tn "Krystal_Trading_Autostart"
) else (
    echo  FAILED. Adding to Startup folder instead...
    set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Krystal_Trading.lnk"
    powershell -NoProfile -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('!LNK!');$s.TargetPath='%~dp0START_KRYSTAL.bat';$s.WorkingDirectory='%~dp0';$s.Save()"
    echo  Shortcut created in Startup folder.
)

echo.
pause
endlocal
