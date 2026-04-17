@echo off
chcp 65001 > nul
title 設定元大庫存排程

set BAT=%~dp0..\同步元大庫存.bat
set BAT_FULL=%~f1
:: 取得完整路徑
for %%i in ("%~dp0..\同步元大庫存.bat") do set BAT_FULL=%%~fi

echo.
echo ========================================
echo  元大庫存同步 - 設定 Windows 排程
echo ========================================
echo  排程時間：
echo    09:35 (台股開盤後)
echo    13:35 (台股收盤後)
echo    17:05 (交易回顧前)
echo.
echo  BAT 路徑：%BAT_FULL%
echo ========================================
echo.

:: ── 刪除舊排程（若存在）──
schtasks /delete /tn "Krystal_元大同步_0935" /f > nul 2>&1
schtasks /delete /tn "Krystal_元大同步_1335" /f > nul 2>&1
schtasks /delete /tn "Krystal_元大同步_1705" /f > nul 2>&1

:: ── 建立新排程（週一到週五）──
schtasks /create /tn "Krystal_元大同步_0935" ^
    /tr "cmd /c \"%BAT_FULL%\"" ^
    /sc WEEKLY /d MON,TUE,WED,THU,FRI ^
    /st 09:35 /f /rl HIGHEST
if %ERRORLEVEL% == 0 (echo [OK] 09:35 排程建立完成) else (echo [FAIL] 09:35 排程失敗)

schtasks /create /tn "Krystal_元大同步_1335" ^
    /tr "cmd /c \"%BAT_FULL%\"" ^
    /sc WEEKLY /d MON,TUE,WED,THU,FRI ^
    /st 13:35 /f /rl HIGHEST
if %ERRORLEVEL% == 0 (echo [OK] 13:35 排程建立完成) else (echo [FAIL] 13:35 排程失敗)

schtasks /create /tn "Krystal_元大同步_1705" ^
    /tr "cmd /c \"%BAT_FULL%\"" ^
    /sc WEEKLY /d MON,TUE,WED,THU,FRI ^
    /st 17:05 /f /rl HIGHEST
if %ERRORLEVEL% == 0 (echo [OK] 17:05 排程建立完成) else (echo [FAIL] 17:05 排程失敗)

echo.
echo ── 現有元大排程 ──
schtasks /query /fo LIST /tn "Krystal_元大*" 2>&1

echo.
pause
