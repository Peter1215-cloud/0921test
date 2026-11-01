@echo off
cd /d "%~dp0"
title DongHwa Food App

echo ======================================================
echo    Dong Hwa Campus Food App - Starting...
echo ======================================================
echo.

if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" gui_app.py
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" gui_app.py
) else (
    python gui_app.py
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with code %errorlevel%
    pause
)
pause
