@echo off
chcp 65001 >nul
echo toyosatomimi Audio Separation Application
echo ==========================================
echo.

REM Move to project directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

echo Starting GUI application using Python...
echo.

REM Start GUI application
python -m src.audio_separator.gui

echo.
echo Application has ended
pause