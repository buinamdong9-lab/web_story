@echo off
setlocal
cd /d "%~dp0"

echo ================================================================
echo    DANG KY TU DONG CRAWL VAO WINDOWS TASK SCHEDULER (MOI 6 TIENG)
echo ================================================================

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$action = New-ScheduledTaskAction -Execute 'pythonw.exe' -Argument ('\"' + (Join-Path (Get-Location) 'auto_crawler.py') + '\"') -WorkingDirectory (Get-Location).Path;" ^
    "$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 6);" ^
    "$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable;" ^
    "Register-ScheduledTask -TaskName 'AkayTruyenAutoCrawler' -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null;"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Da cai dat thanh cong vao Windows Task Scheduler!
    echo Task Name: AkayTruyenAutoCrawler
    echo Tan suat: Chay ngam moi 6 tieng.
) else (
    echo.
    echo [ERROR] Loi khi dang ky task. Vui long click chuot phai vao file va chon 'Run as administrator'.
)

echo.
pause
