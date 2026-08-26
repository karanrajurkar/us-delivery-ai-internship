# US Delivery Internship — Production-Grade AI Support & TAM Operations Hub

Production-grade, LLM-powered internal AI platform built for Technical Support (Tier-1 & Tier-2 engineers) and Technical Account Management (TAM) teams.

---

## 🌟 Overview & System Features

1. **Task 1 · Intelligent Ticket Triage Agent (30 marks)**
   - Accepts raw text or JSON tickets.
   - Classifies tickets into product area, issue category, and urgency tier (`P1`–`P4`) with explicit reasoning.
   - Executes RAG retrieval over Markdown Knowledge Base docs to surface matched context.
   - Suggests recommended internal responder team and auto-drafts customer first-response messages.
   - Exposed as both a callable Python function (`triage_ticket`) and FastAPI REST endpoint (`POST /api/v1/triage`).

2. **Task 2 · TAM Account Health Summariser (25 marks)**
   - Accepts an account ID and pulls CRM account metadata + 90-day ticket history.
   - Synthesizes a deterministic 3-section brief: Executive Summary (3–5 sentences), Open Risks & Flagged Issues (churn/escalation signals with verbatim ticket quotes), and Recommended Talking Points for TAMs.
   - 100% deterministic output (`temperature=0.0`, seed pin, verbatim quote extraction).

3. **Task 3 · Evaluation Harness (20 marks)**
   - Systematic eval framework testing Task 1 and Task 2 across 10 test cases (including adversarial edge cases: ambiguous tickets, missing account IDs).
   - Rules-based validation & quality scoring (0.0 to 1.0) per test case.
   - Generates summary reports: [`eval_report.json`](eval_report.json) and [`eval_report.md`](eval_report.md).

4. **Task 4 · Architectural Design Note (15 marks)**
   - Full 600-word architectural design note included in [`DESIGN_NOTE.md`](DESIGN_NOTE.md) covering Failure Modes, Latency vs Quality, Data Sensitivity (PII), and Scaling.

5. **Bonus Marks (+10 marks)**
   - 🎨 **Thin UI Demo (+5)**: Interactive Streamlit application (`ui_demo.py`).
   - ⚡ **Streaming Output (+3)**: SSE streaming endpoint (`POST /api/v1/triage/stream`).
   - 🔄 **Automated CI (+2)**: GitHub Actions workflow (`.github/workflows/eval.yml`).
   - 📜 **Prompt Versioning (+2)**: Versioned prompt templates (`prompts/triage_v1.py`, `prompts/summariser_v1.py`) with [`PROMPT_CHANGELOG.md`](prompts/PROMPT_CHANGELOG.md).

---

## 🚀 Quickstart & Setup

### Option A: ⚡ 1-Click Automated Launcher (Easiest)
Simply run the 1-click launcher script for your OS (automates `.env` template creation, dependency check, data setup, evaluation harness, and launches the Streamlit UI):

* **Windows**: Double-click [`run.bat`](run.bat) or run in terminal:
  ```powershell
  .\run.bat
  ```
* **Linux / macOS**: Run in terminal:
  ```bash
  chmod +x run.sh
  ./run.sh
  ```

---

### Option B: Manual Setup & Execution

#### 1. Prerequisites & Installation
- Python 3.10+
- Configure API key in `.env` (copied from `.env.example`):
  ```bash
  cp .env.example .env
  # Add your GEMINI_API_KEY or OPENAI_API_KEY
  ```
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

#### 2. Running the System (Single Entry-Point Command)
To run data initialization, execute the full evaluation harness, and view system results:
```bash
python main.py
```

#### 3. Additional Execution Commands & Options
- **Launch Interactive Streamlit UI**: `streamlit run ui_demo.py`
- **Start FastAPI REST Server**: `python main.py --server` *(Runs on `http://localhost:8000`)*
- **Run Evaluation Harness Only**: `python main.py --eval`
- **Run Sample Ticket Triage**: `python main.py --triage-sample`
- **Run Sample TAM Account Brief**: `python main.py --summarise-sample`

---

## 🧪 Evaluation Report Summary

Automated test run results from `python main.py --eval`:

- **Total Test Cases**: 10 (5 Task 1, 5 Task 2)
- **Passed**: 10 / 10 (100%)
- **Average Quality Score**: 0.97 / 1.0

See complete details in [`eval_report.md`](eval_report.md).

---

## 📁 Repository Directory Structure

```
├── data/
│   ├── generate_mock_data.py   # Synthetic 500 tickets, 50 accounts, KB generator
│   ├── accounts.json           # 50 synthetic account summaries
│   ├── tickets.json            # 500 synthetic support tickets
│   └── kb/                     # Markdown Knowledge Base documents
├── prompts/
│   ├── triage_v1.py            # Versioned Task 1 system prompt
│   ├── summariser_v1.py        # Versioned Task 2 system prompt
│   └── PROMPT_CHANGELOG.md     # Prompt versioning log
├── src/
│   ├── api/
│   │   └── app.py              # FastAPI REST endpoints with SSE streaming
│   ├── data/
│   │   └── loader.py           # Data loader & 90-day ticket filter
│   ├── eval/
│   │   └── eval_harness.py     # Task 3 evaluation harness & reporting
│   ├── summariser/
│   │   └── account_summariser.py # Task 2 TAM health summariser module
│   └── triage/
│       ├── rag_retriever.py    # RAG retriever over KB docs
│       └── triage_agent.py     # Task 1 intelligent ticket triage module
├── .env.example                # Template for API keys
├── .gitignore
├── .github/workflows/eval.yml  # Automated CI workflow
├── DESIGN_NOTE.md              # Task 4 Architectural design note
├── eval_report.json            # Task 3 eval results JSON
├── eval_report.md              # Task 3 eval report Markdown table
├── main.py                     # Single entry-point runner
├── ui_demo.py                  # Streamlit UI demonstration app
└── requirements.txt            # Python dependencies
```

---

## 📋 Submission Checklist Verification

- [x] Public/Shared GitHub repo containing code & README
- [x] Setup instructions & single entry-point command (`python main.py`)
- [x] Task 1 & Task 2 working functions & REST endpoints
- [x] Eval harness report files (`eval_report.json` & `eval_report.md`) included
- [x] Design Note included (`DESIGN_NOTE.md`)
- [x] `.env.example` file included (no real secrets committed)
- [x] Bonus points included (Streamlit UI, SSE streaming, GitHub Actions CI, Prompt Versioning)
