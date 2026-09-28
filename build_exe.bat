@echo off
title Build Naughty AI Standalone Executable
cd /d "%~dp0"

echo =======================================================
echo    Building Standalone NaughtyAI.exe via PyInstaller
echo =======================================================
echo.

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
)

echo [1/3] Checking PyInstaller installation...
"%PYTHON_CMD%" -m pip install --upgrade pyinstaller

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install or verify PyInstaller.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] Cleaning previous build artifacts...
if exist "dist\NaughtyAI.exe" del /f /q "dist\NaughtyAI.exe"
if exist "build\NaughtyAI" rmdir /s /q "build\NaughtyAI"

echo.
echo [3/3] Compiling standalone executable...
"%PYTHON_CMD%" -m PyInstaller naughty_ai.spec --clean --noconfirm

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] PyInstaller build failed with exit code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =======================================================
echo    BUILD SUCCESSFUL!
echo =======================================================
echo Executable generated at:
echo   %~dp0dist\NaughtyAI.exe
echo.
pause
