@echo off
TITLE AI Support ^& TAM Operations Hub - One-Click Launcher
echo ===================================================================
echo ⚡ AI Support ^& TAM Operations Hub - 1-Click System Launcher
echo ===================================================================
echo.

if not exist ".env" (
    echo [1/4] Creating .env file from template...
    copy .env.example .env >nul
    echo .env created!
    echo.
) else (
    echo [1/4] .env file found.
)

if not exist ".venv" (
    echo [2/4] Creating Python virtual environment...
    python -m venv .venv
) else (
    echo [2/4] Virtual environment found.
)

echo [3/4] Checking dependencies...
call .\.venv\Scripts\pip.exe install -q -r requirements.txt

echo [4/4] Running Mock Data Setup ^& Evaluation Harness...
echo.
call .\.venv\Scripts\python.exe main.py

echo.
echo ===================================================================
echo ✨ System ready! Starting Interactive Streamlit UI...
echo ===================================================================
echo.
call .\.venv\Scripts\streamlit.exe run ui_demo.py
