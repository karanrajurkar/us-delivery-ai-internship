@echo off
TITLE AI Support & TAM Operations Hub - One-Click Launcher
echo ===================================================================
echo ⚡ AI Support & TAM Operations Hub - 1-Click System Launcher
echo ===================================================================
echo.

REM 1. Copy .env.example to .env if .env does not exist
if not exist ".env" (
    echo [1/4] Creating .env file from template...
    copy .env.example .env >nul
    echo .env created! Please ensure GEMINI_API_KEY or OPENAI_API_KEY is configured.
    echo.
) else (
    echo [1/4] .env file found.
)

REM 2. Setup Virtual Environment if missing
if not exist ".venv" (
    echo [2/4] Creating Python virtual environment (.venv)...
    python -m venv .venv
)

REM 3. Install/verify requirements
echo [3/4] Checking dependencies...
call .\.venv\Scripts\pip.exe install -q -r requirements.txt

REM 4. Run setup & evaluation harness
echo [4/4] Running Mock Data Setup & Evaluation Harness...
echo.
call .\.venv\Scripts\python.exe main.py

echo.
echo ===================================================================
echo ✨ System ready! Starting Interactive Streamlit UI...
echo ===================================================================
echo.
call .\.venv\Scripts\streamlit.exe run ui_demo.py

pause
