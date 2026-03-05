@echo off
title ZENITH SECURITY AUDITOR V5
setlocal

:: Get the directory of the batch file
set "DIR=%~dp0"
cd /d "%DIR%"

echo [DEBUG] Starting ZENITH...
echo [DEBUG] Working Directory: %CD%

echo Checking for Python...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from python.org and try again.
    pause
    exit /b
)

echo Checking dependencies...
pip install -r "%DIR%requirements.txt"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    echo Please check your internet connection or run 'pip install rich google-generativeai' manually.
    pause
    exit /b
)

echo.
echo Launching Zenith Auditor...
echo.
python "%DIR%auditor.py"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Zenith Auditor crashed with exit code %errorlevel%.
)

pause
