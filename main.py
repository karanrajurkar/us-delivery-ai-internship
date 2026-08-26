import argparse
import sys
import os

from data.generate_mock_data import create_knowledge_base, generate_accounts, generate_tickets
from src.eval.eval_harness import EvaluationHarness
from src.triage.triage_agent import triage_ticket
from src.summariser.account_summariser import summarise_account_health

def setup_data():
    print("Initializing Knowledge Base & Mock Data...")
    create_knowledge_base()
    accs = generate_accounts()
    generate_tickets(accs)
    print("Data setup complete!\n")

def run_evals():
    print("Running Evaluation Harness...")
    harness = EvaluationHarness()
    results = harness.run_all_evals()
    passed = sum(1 for r in results if r.passed)
    print(f"\nFinal Eval Result: {passed}/{len(results)} Passed.")
    return 0 if passed == len(results) else 1

def start_server(port=8000):
    import uvicorn
    print(f"Starting FastAPI REST server on http://localhost:{port}...")
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=port, reload=False)

def main():
    parser = argparse.ArgumentParser(description="US Delivery Internship AI Support System")
    parser.add_argument("--setup", action="store_true", help="Generate mock data files")
    parser.add_argument("--eval", action="store_true", help="Run system evaluation harness")
    parser.add_argument("--server", action="store_true", help="Start FastAPI REST server")
    parser.add_argument("--triage-sample", action="store_true", help="Run sample ticket triage")
    parser.add_argument("--summarise-sample", action="store_true", help="Run sample TAM account brief for ACC-001")
    
    args = parser.parse_args()

    # Always ensure mock data exists
    if not os.path.exists("data/tickets.json"):
        setup_data()

    if args.setup:
        setup_data()
    elif args.eval:
        sys.exit(run_evals())
    elif args.server:
        start_server()
    elif args.triage_sample:
        sample_ticket = {
            "subject": "URGENT: SSO Lockout during executive meeting",
            "body": "Our entire executive team was locked out of SSO during our board meeting. We are considering cancelling our Enterprise contract immediately."
        }
        print("Sample Ticket Triage Output:")
        res = triage_ticket(sample_ticket)
        import json
        print(json.dumps(res, indent=2))
    elif args.summarise_sample:
        print("Sample Account Health Brief for ACC-001:")
        res = summarise_account_health("ACC-001")
        import json
        print(json.dumps(res, indent=2))
    else:
        # Default single entry-point action: Run mock setup + Run Eval Harness + Output summary
        print("=== US Delivery Internship AI System Default Runner ===")
        setup_data()
        eval_code = run_evals()
        print("\nSystem ready! You can also run:")
        print(" - `python main.py --server` to start FastAPI REST server")
        print(" - `streamlit run ui_demo.py` to start interactive Streamlit UI")
        sys.exit(eval_code)

if __name__ == "__main__":
    main()
