@echo off
echo ===================================================================
echo AI Support ^& TAM Operations Hub - 1-Click System Launcher
echo ===================================================================
echo.

if not exist ".env" (
    echo [1/4] Creating .env file from template...
    copy .env.example .env
) else (
    echo [1/4] .env file found.
)

if not exist ".venv" (
    echo [2/4] Creating Python virtual environment .venv...
    python -m venv .venv
) else (
    echo [2/4] Virtual environment found.
)

echo [3/4] Checking dependencies...
.\.venv\Scripts\pip.exe install -q -r requirements.txt

echo [4/4] Running Mock Data Setup and Evaluation Harness...
.\.venv\Scripts\python.exe main.py

echo.
echo ===================================================================
echo System ready! Starting Interactive Streamlit UI...
echo ===================================================================
echo.
.\.venv\Scripts\python.exe -m streamlit run ui_demo.py
