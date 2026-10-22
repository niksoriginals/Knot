@echo off
setlocal enabledelayedexpansion
title KNOT Ecosystem - Setup & Launcher

echo =====================================================================
echo                KNOT LOCAL ECOSYSTEM LAUNCHER
echo =====================================================================
echo.

:: 1. Navigate to current directory
cd /d "%~dp0"

:: 2. Check Python installation
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not found in your PATH!
    echo Please install Python 3.10+ and make sure to check "Add Python to PATH".
    echo.
    pause
    exit /b 1
)
python --version
echo.

:: 3. Setup Virtual Environment
if not exist "venv\Scripts\activate.bat" (
    echo [2/4] Setting up Python virtual environment (venv)...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
) else (
    echo [2/4] Virtual environment already exists.
)

:: Activate venv
call venv\Scripts\activate.bat

:: 4. Install requirements
echo.
echo [3/4] Installing / Updating requirements from backend\requirements.txt...
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements!
    pause
    exit /b 1
)

:: 5. Launch Backend (Port 5000)
echo.
echo [4/4] Launching Backend and Frontend servers...
start "KNOT - Backend (Port 5000)" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && cd backend && set FLASK_ENV=development && python main.py"

:: 6. Launch Frontend (Port 3000)
start "KNOT - Frontend (Port 3000)" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && python serve_frontend.py"

:: Wait 3 seconds for servers to initialize
timeout /t 3 /nobreak >nul

:: Open browser automatically
start http://localhost:3000

cls
echo =====================================================================
echo                  KNOT ECOSYSTEM IS NOW RUNNING!
echo =====================================================================
echo.
echo   [Frontend Web] : http://localhost:3000
echo   [Backend API]  : http://localhost:5000
echo.
echo   * Both Frontend and Backend are fully connected.
echo   * Test login OTP will display directly in the Backend terminal.
echo.
echo   To STOP servers:
echo   Close the two opened cmd windows (Backend and Frontend).
echo =====================================================================
echo.
pause
