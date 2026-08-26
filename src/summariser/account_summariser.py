import os
import json
import re
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from src.data.loader import DataLoader
from prompts.summariser_v1 import SUMMARISER_SYSTEM_PROMPT, SUMMARISER_PROMPT_VERSION

class RiskFlag(BaseModel):
    signal_type: str = Field(description="Signal type: 'churn_risk' or 'escalation_signal'")
    ticket_id: str = Field(description="ID of the ticket triggering the flag")
    justification_quote: str = Field(description="EXACT verbatim quote from the ticket body justifying the flag")

LAST_GEMINI_SUMM_CALL_TIME = 0.0

def _throttle_gemini_summ_api():
    global LAST_GEMINI_SUMM_CALL_TIME
    now = time.time()
    elapsed = now - LAST_GEMINI_SUMM_CALL_TIME
    if elapsed < 4.0:
        time.sleep(4.0 - elapsed)
    LAST_GEMINI_SUMM_CALL_TIME = time.time()

def _redact_key(text: Any) -> str:
    s = str(text)
    s = re.sub(r'key=[A-Za-z0-9_\.-]+', 'key=***REDACTED***', s)
    s = re.sub(r'sk-[A-Za-z0-9_\.-]+', 'sk-***REDACTED***', s)
    s = re.sub(r'Bearer\s+[A-Za-z0-9_\.-]+', 'Bearer ***REDACTED***', s)
    return s

class AccountBrief(BaseModel):
    account_id: str
    company_name: str
    tier: str
    mrr: int
    health_score: str
    executive_summary: str = Field(description="3 to 5 sentence concise executive summary")
    open_risks_and_flagged_issues: List[RiskFlag] = Field(default_factory=list, description="List of flagged risks with verbatim quotes")
    recommended_talking_points: List[str] = Field(default_factory=list, description="Actionable points for TAM during QBR")
    prompt_version: str = Field(default=SUMMARISER_PROMPT_VERSION)
    execution_mode: str = Field(default="RULE_ENGINE_FALLBACK", description="Execution mode: 'LLM_GEMINI', 'LLM_OPENAI', or 'RULE_ENGINE_FALLBACK'")

class TAMAccountSummariser:
    def __init__(self, loader: Optional[DataLoader] = None):
        self.loader = loader or DataLoader()

    def summarise_account(self, account_id: str) -> AccountBrief:
        api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()

        account = self.loader.get_account_by_id(account_id)
        if not account:
            # Handle missing / non-existent account data (Adversarial test case support)
            return AccountBrief(
                account_id=account_id,
                company_name="Unknown Account",
                tier="N/A",
                mrr=0,
                health_score="Unknown",
                executive_summary=f"Account '{account_id}' was not found in the customer database. No historical ticket data or active contract records are available for analysis.",
                open_risks_and_flagged_issues=[
                    RiskFlag(
                        signal_type="escalation_signal",
                        ticket_id="NONE",
                        justification_quote=f"Account record {account_id} missing from CRM database."
                    )
                ],
                recommended_talking_points=[
                    "Verify customer account ID in primary billing database.",
                    "Ensure CRM sync is active for newly onboarded tenants."
                ],
                execution_mode="RULE_ENGINE_FALLBACK"
            )

        tickets_90d = self.loader.get_account_tickets(account_id, days=90)

        # Deterministic Risk & Churn Quote Extraction
        risks = self._extract_verbatim_risk_quotes(tickets_90d)

        # Step 2: Check provider preference
        target_provider = (os.getenv("PREFERRED_LLM_PROVIDER") or "").lower().strip()
        use_local_llm = os.getenv("USE_LOCAL_LLM", "false").lower() in ("true", "1", "yes")
        if use_local_llm and not target_provider:
            target_provider = "ollama"

        gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        has_valid_gemini = len(gemini_key) > 10 and not gemini_key.startswith(("your_", "YOUR_"))
        has_valid_openai = len(openai_key) > 10 and (openai_key.startswith("sk-") or not openai_key.startswith("your_"))

        # Explicit Rule Engine choice
        if target_provider == "rule_engine":
            return self._summarise_rule_engine(account, tickets_90d, risks)

        # Explicit Ollama choice
        if target_provider == "ollama":
            try:
                return self._summarise_with_local_llm(account, tickets_90d, risks)
            except Exception as e:
                print(f"[TAMSummariser] Local LLM call failed: {e}. Falling back to Rule Engine.")
                return self._summarise_rule_engine(account, tickets_90d, risks)

        # Target: Gemini requested (or default provider)
        if target_provider == "gemini" or not target_provider:
            if has_valid_gemini:
                try:
                    return self._summarise_with_gemini(account, tickets_90d, risks)
                except Exception as e:
                    err_detail = _redact_key(e)
                    print(f"[TAMSummariser] Gemini API failed ({err_detail}). Attempting failover...")
                    try:
                        res = self._summarise_with_local_llm(account, tickets_90d, risks)
                        res.execution_mode = f"LLM_LOCAL_OLLAMA (tinyllama) [Fallback: Gemini API Error ({err_detail})]"
                        return res
                    except Exception:
                        res = self._summarise_rule_engine(account, tickets_90d, risks)
                        res.execution_mode = f"RULE_ENGINE_FALLBACK [Fallback: Gemini API Error ({err_detail})]"
                        return res
            else:
                err_detail = "Invalid/Missing Gemini API Key"
                print(f"[TAMSummariser] {err_detail}. Attempting failover...")
                try:
                    res = self._summarise_with_local_llm(account, tickets_90d, risks)
                    res.execution_mode = f"LLM_LOCAL_OLLAMA (tinyllama) [Fallback: {err_detail}]"
                    return res
                except Exception:
                    res = self._summarise_rule_engine(account, tickets_90d, risks)
                    res.execution_mode = f"RULE_ENGINE_FALLBACK [Fallback: {err_detail}]"
                    return res

        # Target: OpenAI requested
        if target_provider == "openai":
            if has_valid_openai:
                try:
                    return self._summarise_with_openai(account, tickets_90d, risks)
                except Exception as e:
                    err_detail = _redact_key(e)
                    print(f"[TAMSummariser] OpenAI API failed ({err_detail}). Attempting failover...")
                    try:
                        res = self._summarise_with_local_llm(account, tickets_90d, risks)
                        res.execution_mode = f"LLM_LOCAL_OLLAMA (tinyllama) [Fallback: OpenAI API Error ({err_detail})]"
                        return res
                    except Exception:
                        res = self._summarise_rule_engine(account, tickets_90d, risks)
                        res.execution_mode = f"RULE_ENGINE_FALLBACK [Fallback: OpenAI API Error ({err_detail})]"
                        return res
            else:
                err_detail = "Invalid/Missing OpenAI API Key"
                print(f"[TAMSummariser] {err_detail}. Attempting failover...")
                try:
                    res = self._summarise_with_local_llm(account, tickets_90d, risks)
                    res.execution_mode = f"LLM_LOCAL_OLLAMA (tinyllama) [Fallback: {err_detail}]"
                    return res
                except Exception:
                    res = self._summarise_rule_engine(account, tickets_90d, risks)
                    res.execution_mode = f"RULE_ENGINE_FALLBACK [Fallback: {err_detail}]"
                    return res

        return self._summarise_rule_engine(account, tickets_90d, risks)

    def _summarise_with_gemini(self, account: Dict[str, Any], tickets: List[Dict[str, Any]], risks: List[RiskFlag]) -> AccountBrief:
        import requests
        gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        t_summary = f"Total 90d Tickets: {len(tickets)}.\n" + "\n".join([f"- [{t.get('ticket_id')}] ({t.get('product_area')}): {t.get('subject')}" for t in tickets[:10]])
        prompt = f"Account Metadata:\nID: {account.get('account_id')}\nCompany: {account.get('company_name')}\nTier: {account.get('tier')}\nMRR: ${account.get('mrr'):,}\nHealth: {account.get('health_score')}\n\nTicket History:\n{t_summary}"
        payload = {
            "contents": [{"parts": [{"text": f"{SUMMARISER_SYSTEM_PROMPT}\n\n{prompt}"}]}],
            "generationConfig": {"temperature": 0.0, "seed": 42, "responseMimeType": "application/json"}
        }
        res = None
        for attempt in range(2):
            _throttle_gemini_summ_api()
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code in (400, 401, 403):
                break
            if res.status_code == 429:
                time.sleep(2)
                continue
            break
        res.raise_for_status()
        text_out = res.json()['candidates'][0]['content']['parts'][0]['text']
        parsed = json.loads(text_out)
        if risks:
            parsed["open_risks_and_flagged_issues"] = [r.model_dump() for r in risks]
        parsed["execution_mode"] = "LLM_GEMINI"
        return AccountBrief(
            account_id=account.get("account_id"),
            company_name=account.get("company_name"),
            tier=account.get("tier"),
            mrr=account.get("mrr"),
            health_score=account.get("health_score"),
            **parsed
        )

    def _summarise_with_openai(self, account: Dict[str, Any], tickets: List[Dict[str, Any]], risks: List[RiskFlag]) -> AccountBrief:
        import requests
        openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        t_summary = f"Total 90d Tickets: {len(tickets)}.\n" + "\n".join([f"- [{t.get('ticket_id')}] ({t.get('product_area')}): {t.get('subject')}" for t in tickets[:10]])
        prompt = f"Account Metadata:\nID: {account.get('account_id')}\nCompany: {account.get('company_name')}\nTier: {account.get('tier')}\nMRR: ${account.get('mrr'):,}\nHealth: {account.get('health_score')}\n\nTicket History:\n{t_summary}"
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
        payload = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": SUMMARISER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        text_out = res.json()['choices'][0]['message']['content']
        parsed = json.loads(text_out)
        if risks:
            parsed["open_risks_and_flagged_issues"] = [r.model_dump() for r in risks]
        parsed["execution_mode"] = "LLM_OPENAI"
        return AccountBrief(
            account_id=account.get("account_id"),
            company_name=account.get("company_name"),
            tier=account.get("tier"),
            mrr=account.get("mrr"),
            health_score=account.get("health_score"),
            **parsed
        )

    def _summarise_with_local_llm(self, account: Dict[str, Any], tickets: List[Dict[str, Any]], risks: List[RiskFlag]) -> AccountBrief:
        import requests
        local_url = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/api/generate").strip()
        model_name = os.getenv("LOCAL_LLM_MODEL", "tinyllama").strip()
        
        t_summary = f"Total 90d Tickets: {len(tickets)}.\n"
        for t in tickets[:5]:
            t_summary += f"- [{t.get('ticket_id')}] ({t.get('product_area')}): {t.get('subject')} - {t.get('body', '')[:120]}\n"

        prompt = f"""{SUMMARISER_SYSTEM_PROMPT}

Account Metadata:
ID: {account.get('account_id')}
Company: {account.get('company_name')}
Tier: {account.get('tier')}
MRR: ${account.get('mrr'):,}
Health Score: {account.get('health_score')}
Contract End: {account.get('contract_end_date')}

Recent 90-Day Ticket History:
{t_summary}

Return valid JSON only matching the schema.
"""
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        res = requests.post(local_url, json=payload, timeout=60)
        res.raise_for_status()
        text_out = res.json().get("response", "")
        
        try:
            parsed_raw = json.loads(text_out)
        except Exception:
            match = re.search(r'\{.*\}', text_out, re.DOTALL)
            if match:
                try:
                    parsed_raw = json.loads(match.group(0))
                except Exception:
                    parsed_raw = {}
            else:
                parsed_raw = {}

        if isinstance(parsed_raw, list) and len(parsed_raw) > 0:
            parsed = parsed_raw[0]
        elif isinstance(parsed_raw, dict):
            parsed = parsed_raw
        else:
            parsed = {}

        if risks:
            parsed["open_risks_and_flagged_issues"] = [r.model_dump() for r in risks]
        else:
            raw_risks = parsed.get("open_risks_and_flagged_issues", [])
            clean_risks = []
            if isinstance(raw_risks, list):
                for r in raw_risks:
                    if isinstance(r, dict):
                        clean_risks.append({
                            "signal_type": str(r.get("signal_type", "escalation_signal")),
                            "ticket_id": str(r.get("ticket_id", "NONE")),
                            "justification_quote": str(r.get("justification_quote", "Risk flagged from ticket data."))
                        })
            parsed["open_risks_and_flagged_issues"] = clean_risks

        raw_points = parsed.get("recommended_talking_points") or parsed.get("strategic_talking_points") or ["Review contract terms ahead of renewal", "Conduct technical check-in with TAM team"]
        clean_points = []
        if isinstance(raw_points, list):
            for pt in raw_points:
                if isinstance(pt, str):
                    clean_points.append(pt)
                elif isinstance(pt, dict):
                    clean_points.append(str(pt.get("talking_point") or pt.get("justification_quote") or pt.get("signal_type") or str(pt)))
                else:
                    clean_points.append(str(pt))
        else:
            clean_points = [str(raw_points)]

        clean_dict = {
            "executive_summary": str(parsed.get("executive_summary", f"{account.get('company_name')} account health overview. Ticket volume monitored over 90 days.")),
            "open_risks_and_flagged_issues": parsed.get("open_risks_and_flagged_issues", []),
            "recommended_talking_points": clean_points or ["Review contract terms ahead of renewal", "Conduct technical check-in with TAM team"],
            "execution_mode": f"LLM_LOCAL_OLLAMA ({model_name})"
        }
        return AccountBrief(
            account_id=account.get("account_id"),
            company_name=account.get("company_name"),
            tier=account.get("tier"),
            mrr=account.get("mrr", 0),
            health_score=account.get("health_score", "Healthy"),
            **clean_dict
        )

    def _extract_verbatim_risk_quotes(self, tickets: List[Dict[str, Any]]) -> List[RiskFlag]:
        """
        Scans ticket bodies for exact churn or escalation trigger phrases, returning exact verbatim quotes.
        """
        churn_keywords = [
            r"cancelling.*contract", r"cancelling.*subscription", r"looking at competitor",
            r"terminate.*subscription", r"refund", r"demand a full refund", r"unacceptable",
            r"escalate to executive", r"speak to our TAM right now", r"fail our compliance deadline"
        ]
        
        risks = []
        for t in tickets:
            t_id = t.get("ticket_id", "UNKNOWN")
            body = t.get("body", "")
            
            # Split body into sentences to get precise quotes
            sentences = re.split(r'(?<=[.!?])\s+', body)
            for sentence in sentences:
                sent_clean = sentence.strip()
                for pattern in churn_keywords:
                    if re.search(pattern, sent_clean, re.IGNORECASE):
                        sig_type = "churn_risk" if any(w in sent_clean.lower() for w in ["cancel", "competitor", "refund", "terminate"]) else "escalation_signal"
                        risks.append(RiskFlag(
                            signal_type=sig_type,
                            ticket_id=t_id,
                            justification_quote=sent_clean
                        ))
                        break # avoid duplicate flags for same sentence
        return risks

    def _summarise_rule_engine(self, account: Dict[str, Any], tickets: List[Dict[str, Any]], risks: List[RiskFlag]) -> AccountBrief:
        name = account.get("company_name", "Account")
        tier = account.get("tier", "Pro")
        mrr = account.get("mrr", 0)
        h_score = account.get("health_score", "Healthy")
        c_end = account.get("contract_end_date", "2026-12-31")
        acc_id = account.get("account_id", "")
        
        open_tickets = [t for t in tickets if t.get("status") in ["Open", "Pending Engineer"]]
        
        # 3-5 sentence Executive Summary
        exec_summary = (
            f"{name} ({acc_id}) is a strategic {tier} tier customer generating ${mrr:,} in monthly recurring revenue with a current account health rating of '{h_score}'. "
            f"Over the last 90 days, the customer submitted {len(tickets)} support tickets, with {len(open_tickets)} tickets remaining in open status. "
            f"Key support activity centered primarily around authentication and API integration workflows. "
            f"The account contract term expires on {c_end}, requiring proactive TAM engagement to address active operational friction before renewal."
        )

        # Recommended Talking Points
        talking_points = [
            f"Review recent support ticket resolution velocity and address open tickets with engineering team.",
            f"Discuss contract renewal terms and annual prepay discount options prior to expiration on {c_end}.",
            f"Offer dedicated technical onboarding session for API rate-limit management and SSO best practices."
        ]
        
        if risks:
            talking_points.insert(0, f"Acknowledge escalated feedback regarding: '{risks[0].justification_quote[:80]}...' and outline mitigation roadmap.")

        return AccountBrief(
            account_id=acc_id,
            company_name=name,
            tier=tier,
            mrr=mrr,
            health_score=h_score,
            executive_summary=exec_summary,
            open_risks_and_flagged_issues=risks,
            recommended_talking_points=talking_points[:4],
            execution_mode="RULE_ENGINE_FALLBACK"
        )

# Callable Python function required by spec
def summarise_account_health(account_id: str) -> Dict[str, Any]:
    summariser = TAMAccountSummariser()
    result = summariser.summarise_account(account_id)
    return result.model_dump()
