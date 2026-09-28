@echo off
title Naughty AI Assistant
cd /d "%~dp0"

echo =======================================================
echo    Naughty AI Assistant - Local Roleplay and Companion
echo =======================================================
echo.

if exist ".venv\Scripts\python.exe" (
    echo [INFO] Starting server using virtual environment...
    ".venv\Scripts\python.exe" run.py %*
) else (
    echo [INFO] Virtual environment not found. Trying system python...
    python run.py %*
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with error code %ERRORLEVEL%.
    pause
)
