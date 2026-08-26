#!/bin/bash
echo "==================================================================="
echo "⚡ AI Support & TAM Operations Hub - 1-Click System Launcher"
echo "==================================================================="
echo ""

if [ ! -f ".env" ]; then
    echo "[1/4] Creating .env file from template..."
    cp .env.example .env
    echo ".env created! Configure GEMINI_API_KEY or OPENAI_API_KEY if needed."
    echo ""
fi

if [ ! -d ".venv" ]; then
    echo "[2/4] Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
fi

echo "[3/4] Checking dependencies..."
.venv/bin/pip install -q -r requirements.txt

echo "[4/4] Running Mock Data Setup & Evaluation Harness..."
echo ""
.venv/bin/python main.py

echo ""
echo "==================================================================="
echo "✨ System ready! Starting Interactive Streamlit UI..."
echo "==================================================================="
echo ""
.venv/bin/streamlit run ui_demo.py
