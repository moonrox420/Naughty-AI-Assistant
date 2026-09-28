@echo off
cd /d "%~dp0"

echo =======================================================
echo    Creating Desktop Shortcuts for Naughty AI Assistant
echo =======================================================
echo.

set SCRIPT_DIR=%~dp0
set TARGET_APP=%SCRIPT_DIR%start_app.bat
set TARGET_ALL=%SCRIPT_DIR%start_all.bat

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$desk = [System.Environment]::GetFolderPath('Desktop'); " ^
    "$s1 = $ws.CreateShortcut((Join-Path $desk 'Naughty AI Assistant.lnk')); " ^
    "$s1.TargetPath = '%TARGET_APP%'; " ^
    "$s1.WorkingDirectory = '%SCRIPT_DIR%'; " ^
    "$s1.Description = 'Naughty AI Assistant - Local Conversational Companion'; " ^
    "$s1.Save(); " ^
    "$s2 = $ws.CreateShortcut((Join-Path $desk 'Naughty AI + SD Forge.lnk')); " ^
    "$s2.TargetPath = '%TARGET_ALL%'; " ^
    "$s2.WorkingDirectory = '%SCRIPT_DIR%'; " ^
    "$s2.Description = 'Naughty AI Assistant with Stable Diffusion Forge'; " ^
    "$s2.Save(); " ^
    "Write-Host '[SUCCESS] Desktop shortcuts created successfully!'"

echo.
echo Shortcuts created on your Windows Desktop:
echo   - "Naughty AI Assistant.lnk"
echo   - "Naughty AI + SD Forge.lnk"
echo.
pause
