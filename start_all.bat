@echo off
title Naughty AI Suite Launcher (Assistant + SD Forge)
cd /d "%~dp0"

echo =======================================================
echo    Naughty AI Suite - Complete Local Ecosystem Launcher
echo =======================================================
echo.

set FORGE_DIR=C:\Users\droxa\stable-diffusion-webui-forge

if exist "%FORGE_DIR%\webui-user.bat" (
    echo [INFO] Launching Stable Diffusion WebUI Forge in background window...
    start "Stable Diffusion WebUI Forge" /d "%FORGE_DIR%" cmd /c "webui-user.bat"
    echo [INFO] Forge starting on http://127.0.0.1:7860...
    timeout /t 5 /nobreak >nul
) else (
    echo [WARNING] SD WebUI Forge not found at %FORGE_DIR%.
    echo [WARNING] Continuing with Naughty AI Assistant only...
    echo.
)

echo [INFO] Starting Naughty AI Assistant...
call "%~dp0start_app.bat"
