#!/usr/bin/env bash
set -e

echo "==================================================================="
echo "⚡ AI Support & TAM Operations Hub - 1-Click System Launcher"
echo "==================================================================="
echo ""

# 1. Environment file check
if [ ! -f ".env" ]; then
    echo "[1/4] Creating .env file from template..."
    cp .env.example .env
    echo ".env created! Configure GEMINI_API_KEY or OPENAI_API_KEY if needed."
    echo ""
else
    echo "[1/4] .env file found."
fi

# 2. Find Python 3 binary
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python 3 is not installed or not in PATH."
    exit 1
fi

# 3. Setup Virtual Environment
if [ ! -d ".venv" ]; then
    echo "[2/4] Creating Python virtual environment (.venv)..."
    $PYTHON_CMD -m venv .venv
else
    echo "[2/4] Virtual environment found."
fi

# 4. Install Dependencies
echo "[3/4] Checking dependencies..."
.venv/bin/pip install -q -r requirements.txt

# 5. Execute Setup & Evaluation Harness
echo "[4/4] Running Mock Data Setup & Evaluation Harness..."
echo ""
.venv/bin/python main.py

echo ""
echo "==================================================================="
echo "✨ System ready! Starting Interactive Streamlit UI..."
echo "==================================================================="
echo ""
.venv/bin/streamlit run ui_demo.py
