@echo off
REM Start Amiibo GUI Client on Windows

echo ==========================================
echo Starting Amiibo GUI Client
echo ==========================================
echo.

REM Change to script directory
cd /d "%~dp0\amiibo_emulator"

REM Check if client file exists
if not exist "client_gui.py" (
    echo Error: client_gui.py not found!
    echo Make sure you're in the correct directory
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3 from python.org
    pause
    exit /b 1
)

echo Starting GUI client...
echo.

REM Run the GUI
python client_gui.py

if errorlevel 1 (
    echo.
    echo GUI closed with error
    pause
)
