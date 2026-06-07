@echo off
title Laser PPT Controller
cd /d "%~dp0"

:: Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo [ERROR] Virtual environment not found.
    echo Please run setup.bat first to install the app.
    echo.
    pause
    exit /b 1
)

:: Activate virtual environment and run app
call .venv\Scripts\activate.bat
python main.py

:: If app crashes, keep window open so user can read the error
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] App exited with an error. See message above.
    pause
)
