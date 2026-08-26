import json
import os
import time
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from src.triage.triage_agent import TicketTriageAgent
from src.summariser.account_summariser import TAMAccountSummariser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestCaseResult(BaseModel):
    task_name: str
    test_id: str
    description: str
    is_adversarial: bool
    passed: bool
    quality_score: float
    reasoning: str
    latency_seconds: float
    execution_mode: str = Field(default="RULE_ENGINE_FALLBACK")
    output_snippet: Dict[str, Any]

class EvaluationHarness:
    def __init__(self):
        self.triage_agent = TicketTriageAgent()
        self.account_summariser = TAMAccountSummariser()

    def run_all_evals(self) -> List[TestCaseResult]:
        results = []
        print("\n--- Running Task 1: Ticket Triage Evals ---")
        results.extend(self.eval_task1_triage())
        
        print("\n--- Running Task 2: Account Health Summariser Evals ---")
        results.extend(self.eval_task2_summariser())
        
        self.generate_reports(results)
        return results

    def eval_task1_triage(self) -> List[TestCaseResult]:
        triage_tests = [
            {
                "id": "T1_TEST_1",
                "desc": "Standard Authentication SSO lockout ticket",
                "adversarial": False,
                "input": {"subject": "SSO Lockout error 401", "body": "Our entire executive team was locked out of SSO during our quarterly board meeting."},
                "expected": {"area": "Authentication", "urgency": "P1", "kb": "auth.md"}
            },
            {
                "id": "T1_TEST_2",
                "desc": "API Rate Limit 429 error during migration",
                "adversarial": False,
                "input": {"subject": "API 429 Too Many Requests", "body": "We are getting 429 Too Many Requests errors continuously. Our data migration pipeline has halted."},
                "expected": {"area": "API Integration", "urgency": "P1", "kb": "api.md"}
            },
            {
                "id": "T1_TEST_3",
                "desc": "Webhook HMAC signature verification failing",
                "adversarial": False,
                "input": {"subject": "Webhook HMAC verification", "body": "We are receiving webhooks, but X-Signature-256 header fails digest check."},
                "expected": {"area": "Webhooks", "urgency": "P3"}
            },
            {
                "id": "T1_TEST_4",
                "desc": "General payment portal query",
                "adversarial": False,
                "input": {"subject": "Payment method query", "body": "Where can we update credit card details in the billing portal?"},
                "expected": {"area": "Billing & Invoicing", "urgency": "P4"}
            },
            {
                "id": "T1_TEST_5_ADV",
                "desc": "Adversarial: Highly ambiguous multi-issue ticket (Billing dispute + Database outage)",
                "adversarial": True,
                "input": {"subject": "OVERCHARGED BILL AND DATABASE CRASH", "body": "We were overcharged $10k on invoice AND our ERR_CONN_POOL_LIMIT database is crashing!"},
                "expected": {"urgency_in": ["P1", "P2"]}
            }
        ]

        results = []
        for t in triage_tests:
            start_time = time.time()
            out = self.triage_agent.triage(t["input"])
            latency = time.time() - start_time
            out_dict = out.model_dump()

            passed = True
            reasons = []
            score = 1.0

            # Rule checks
            exp = t["expected"]
            if "area" in exp and out_dict["product_area"] != exp["area"]:
                passed = False
                score -= 0.3
                reasons.append(f"Expected area '{exp['area']}', got '{out_dict['product_area']}'")

            if "urgency" in exp and out_dict["urgency_tier"] != exp["urgency"]:
                score -= 0.2
                reasons.append(f"Expected urgency '{exp['urgency']}', got '{out_dict['urgency_tier']}'")

            if "urgency_in" in exp and out_dict["urgency_tier"] not in exp["urgency_in"]:
                passed = False
                score -= 0.4
                reasons.append(f"Expected urgency in {exp['urgency_in']}, got '{out_dict['urgency_tier']}'")

            if "kb" in exp and out_dict["matched_kb_doc"] != exp["kb"]:
                score -= 0.1
                reasons.append(f"KB doc match '{out_dict['matched_kb_doc']}' differed from expected '{exp['kb']}'")

            if not out_dict.get("draft_response") or len(out_dict.get("draft_response")) < 30:
                passed = False
                score -= 0.3
                reasons.append("Draft response missing or too short")

            score = max(0.0, round(score, 2))
            reasoning = "All criteria satisfied." if not reasons else "; ".join(reasons)
            
            results.append(TestCaseResult(
                task_name="Task 1: Ticket Triage",
                test_id=t["id"],
                description=t["desc"],
                is_adversarial=t["adversarial"],
                passed=passed,
                quality_score=score,
                reasoning=reasoning,
                latency_seconds=round(latency, 4),
                execution_mode=out_dict.get("execution_mode", "RULE_ENGINE_FALLBACK"),
                output_snippet={
                    "product_area": out_dict["product_area"],
                    "urgency_tier": out_dict["urgency_tier"],
                    "matched_kb_doc": out_dict["matched_kb_doc"],
                    "recommended_team": out_dict["recommended_team"]
                }
            ))
            mode_tag = out_dict.get("execution_mode", "RULE_ENGINE_FALLBACK")
            print(f"[{t['id']}] {'PASS' if passed else 'FAIL'} (Score: {score}) [{mode_tag}] - {t['desc']}")
            time.sleep(1.5)

        return results

    def eval_task2_summariser(self) -> List[TestCaseResult]:
        summariser_tests = [
            {
                "id": "T2_TEST_1",
                "desc": "Account ACC-001 with high churn risk tickets",
                "adversarial": False,
                "account_id": "ACC-001",
                "expect_risk_flags": True
            },
            {
                "id": "T2_TEST_2",
                "desc": "Pro tier account ACC-004 health summary check",
                "adversarial": False,
                "account_id": "ACC-004",
                "expect_risk_flags": False
            },
            {
                "id": "T2_TEST_3",
                "desc": "Determinism verification: duplicate run check on ACC-001",
                "adversarial": False,
                "account_id": "ACC-001",
                "check_determinism": True
            },
            {
                "id": "T2_TEST_4",
                "desc": "Enterprise tier account ACC-005 ticket history check",
                "adversarial": False,
                "account_id": "ACC-005",
                "expect_talking_points": 3
            },
            {
                "id": "T2_TEST_5_ADV",
                "desc": "Adversarial: Non-existent account ID 'ACC-99999'",
                "adversarial": True,
                "account_id": "ACC-99999",
                "expect_graceful_handling": True
            }
        ]

        results = []
        for t in summariser_tests:
            start_time = time.time()
            out1 = self.account_summariser.summarise_account(t["account_id"])
            latency = time.time() - start_time
            out_dict = out1.model_dump()

            passed = True
            reasons = []
            score = 1.0

            # Section 1 check: Executive Summary (3-5 sentences)
            exec_sum = out_dict.get("executive_summary", "")
            sentence_count = len([s for s in exec_sum.split('.') if len(s.strip()) > 5])
            if not (3 <= sentence_count <= 6):
                score -= 0.15
                reasons.append(f"Exec summary sentence count is {sentence_count} (expected 3-5)")

            # Section 2 check: Risk flags and verbatim quotes
            risks = out_dict.get("open_risks_and_flagged_issues", [])
            if t.get("expect_risk_flags") and len(risks) == 0:
                score -= 0.3
                reasons.append("Expected churn/escalation risk flags, but none detected")

            for r in risks:
                if not r.get("justification_quote"):
                    passed = False
                    score -= 0.3
                    reasons.append(f"Risk flag in ticket {r.get('ticket_id')} missing justification quote")

            # Section 3 check: Talking points
            t_points = out_dict.get("recommended_talking_points", [])
            if len(t_points) < 2:
                passed = False
                score -= 0.3
                reasons.append("Fewer than 2 recommended talking points produced")

            # Determinism test
            if t.get("check_determinism"):
                out2 = self.account_summariser.summarise_account(t["account_id"]).model_dump()
                if out1.executive_summary != out2["executive_summary"]:
                    passed = False
                    score -= 0.4
                    reasons.append("Determinism failure: Executive summary differed on identical input")

            score = max(0.0, round(score, 2))
            reasoning = "All criteria satisfied." if not reasons else "; ".join(reasons)

            results.append(TestCaseResult(
                task_name="Task 2: Account Health Summariser",
                test_id=t["id"],
                description=t["desc"],
                is_adversarial=t["adversarial"],
                passed=passed,
                quality_score=score,
                reasoning=reasoning,
                latency_seconds=round(latency, 4),
                execution_mode=out_dict.get("execution_mode", "RULE_ENGINE_FALLBACK"),
                output_snippet={
                    "account_id": out_dict["account_id"],
                    "company_name": out_dict["company_name"],
                    "exec_summary_sentences": sentence_count,
                    "risk_flag_count": len(risks),
                    "talking_points_count": len(t_points)
                }
            ))
            mode_tag = out_dict.get("execution_mode", "RULE_ENGINE_FALLBACK")
            print(f"[{t['id']}] {'PASS' if passed else 'FAIL'} (Score: {score}) [{mode_tag}] - {t['desc']}")
            time.sleep(1.5)

        return results

    def generate_markdown_report(self, results: List[TestCaseResult]) -> str:
        passed_count = sum(1 for r in results if r.passed)
        avg_score = round(sum(r.quality_score for r in results) / len(results), 2)
        
        md_content = f"""# System Evaluation Report

**Total Tests:** {len(results)}  
**Passed:** {passed_count} / {len(results)}  
**Average Quality Score:** {avg_score} / 1.0  

## Test Results Summary

| Task | Test ID | Description | Type | Result | Score | Latency (s) |
|---|---|---|---|---|---|---|
"""
        for r in results:
            t_type = "Adversarial" if r.is_adversarial else "Standard"
            status = "✅ PASS" if r.passed else "❌ FAIL"
            md_content += f"| {r.task_name} | `{r.test_id}` | {r.description} | {t_type} | {status} | **{r.quality_score}** | {r.latency_seconds}s |\n"

        md_content += "\n## Detailed Test Logs\n"
        for r in results:
            md_content += f"### `{r.test_id}` - {r.description}\n"
            md_content += f"- **Task:** {r.task_name}\n"
            md_content += f"- **Status:** {'PASS' if r.passed else 'FAIL'} (Score: {r.quality_score})\n"
            md_content += f"- **Reasoning / Notes:** {r.reasoning}\n"
            md_content += f"- **Output Snippet:** ```json\n{json.dumps(r.output_snippet, indent=2)}\n```\n\n"

        return md_content

    def generate_reports(self, results: List[TestCaseResult]):
        # Save eval_report.json
        report_json_path = os.path.join(BASE_DIR, "eval_report.json")
        json_data = {
            "total_test_cases": len(results),
            "passed_count": sum(1 for r in results if r.passed),
            "avg_quality_score": round(sum(r.quality_score for r in results) / len(results), 2),
            "test_cases": [r.model_dump() for r in results]
        }
        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)
        print(f"\nSaved eval report to {report_json_path}")

        # Save eval_report.md
        report_md_path = os.path.join(BASE_DIR, "eval_report.md")
        md_content = self.generate_markdown_report(results)

        with open(report_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"Saved markdown report to {report_md_path}")

if __name__ == "__main__":
    harness = EvaluationHarness()
    harness.run_all_evals()
