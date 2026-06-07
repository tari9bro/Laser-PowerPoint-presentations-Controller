@echo off
title Laser PPT Controller - Setup
cd /d "%~dp0"

echo.
echo ============================================
echo   Laser PPT Controller - First Time Setup
echo ============================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please download and install Python 3.9+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

:: Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
    echo [OK] Virtual environment created.
) else (
    echo [1/3] Virtual environment already exists, skipping.
)
echo.

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Install dependencies
echo [2/3] Installing dependencies...
pip install -r requirements.txt
echo.

:: Verify installation
echo [3/3] Verifying installation...
python -c "import cv2, numpy, pyautogui, pystray, PIL; print('[OK] All dependencies installed successfully.')"

if %errorlevel% neq 0 (
    echo [ERROR] Some dependencies failed to install. Try running setup.bat again.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Setup complete!
echo   Double-click run.bat to launch the app.
echo ============================================
echo.
pause
