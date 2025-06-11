@echo off
chcp 65001 >nul
echo toyosatomimi Audio Separation Application
echo ==========================================
echo.

REM Move to project directory
cd /d "%~dp0"

REM Check if uv is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo Error: uv is not installed
    echo Please install uv and try again: https://docs.astral.sh/uv/
    pause
    exit /b 1
)

echo Starting GUI application using uv...
echo.

REM Start GUI application
uv run python -m src.audio_separator.gui

echo.
echo Application has ended
pause