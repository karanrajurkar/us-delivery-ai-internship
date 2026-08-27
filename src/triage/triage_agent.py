import os
import json
import re
import time
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from src.triage.rag_retriever import KBRetriever
from prompts.triage_v1 import TRIAGE_SYSTEM_PROMPT, TRIAGE_PROMPT_VERSION

class TriageInput(BaseModel):
    subject: str = ""
    body: str
    account_id: Optional[str] = None

class TriageOutput(BaseModel):
    product_area: str = Field(description="Product Area (Authentication, Billing & Invoicing, API Integration, Webhooks, Infrastructure & Performance, Dashboard & UI)")
    issue_category: str = Field(description="Issue Category (Bug, Feature Request, Configuration Error, Outage / Downtime, Security / Access Lockout)")
    urgency_tier: str = Field(description="Urgency Tier (P1, P2, P3, P4)")
    urgency_reasoning: str = Field(description="Reasoning for urgency rating")
    matched_kb_doc: str = Field(description="Title or filename of relevant KB document")
    kb_relevance_score: float = Field(default=0.0, description="RAG retrieval similarity score")
    recommended_team: str = Field(description="Target internal team (Tier 1 Support, Tier 2 Engineering, Billing Ops, Security Ops, TAM Escalation)")
    draft_response: str = Field(description="Suggested draft first response for support agent")
    prompt_version: str = Field(default=TRIAGE_PROMPT_VERSION)
    execution_mode: str = Field(default="RULE_ENGINE_FALLBACK", description="Execution mode: 'LLM_GEMINI', 'LLM_OPENAI', or 'RULE_ENGINE_FALLBACK'")

LAST_GEMINI_CALL_TIME = 0.0

def _throttle_gemini_api():
    global LAST_GEMINI_CALL_TIME
    now = time.time()
    elapsed = now - LAST_GEMINI_CALL_TIME
    if elapsed < 4.0:
        time.sleep(4.0 - elapsed)
    LAST_GEMINI_CALL_TIME = time.time()

def _redact_key(text: Any) -> str:
    s = str(text)
    s = re.sub(r'key=[A-Za-z0-9_\.-]+', 'key=***REDACTED***', s)
    s = re.sub(r'sk-[A-Za-z0-9_\.-]+', 'sk-***REDACTED***', s)
    s = re.sub(r'Bearer\s+[A-Za-z0-9_\.-]+', 'Bearer ***REDACTED***', s)
    return s

class TicketTriageAgent:
    def __init__(self, retriever: Optional[KBRetriever] = None):
        self.retriever = retriever or KBRetriever()

    def triage(self, ticket_input: Union[str, Dict[str, Any], TriageInput], provider: Optional[str] = None) -> TriageOutput:
        # Normalize input
        if isinstance(ticket_input, str):
            try:
                data = json.loads(ticket_input)
                subject = data.get("subject", "")
                body = data.get("body", ticket_input)
            except Exception:
                subject = ""
                body = ticket_input
        elif isinstance(ticket_input, dict):
            subject = ticket_input.get("subject", "")
            body = ticket_input.get("body", "")
        elif isinstance(ticket_input, TriageInput):
            subject = ticket_input.subject
            body = ticket_input.body
        else:
            subject = ""
            body = str(ticket_input)

        full_text = f"{subject}\n{body}".strip()

        # Step 1: Knowledge Base RAG Retrieval
        retrieved_docs = self.retriever.retrieve(full_text, top_k=1)
        matched_kb = "None"
        kb_score = 0.0
        kb_context = ""
        if retrieved_docs and retrieved_docs[0][1] > 0.05:
            matched_kb, kb_score, kb_context = retrieved_docs[0]

        # Step 2: Check provider preference
        target_provider = (provider or os.getenv("PREFERRED_LLM_PROVIDER") or "").lower().strip()
        use_local_llm = os.getenv("USE_LOCAL_LLM", "false").lower() in ("true", "1", "yes")
        if use_local_llm and not target_provider:
            target_provider = "ollama"

        gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        has_valid_gemini = len(gemini_key) > 10 and not gemini_key.startswith(("your_", "YOUR_"))
        has_valid_openai = len(openai_key) > 10 and (openai_key.startswith("sk-") or not openai_key.startswith("your_"))

        # Explicit Rule Engine choice
        if target_provider == "rule_engine":
            return self._triage_rule_engine(subject, body, matched_kb, kb_score)

        # Explicit Ollama choice
        if target_provider == "ollama":
            try:
                return self._triage_with_local_llm(subject, body, matched_kb, kb_score, kb_context)
            except Exception as e:
                print(f"[TriageAgent] Local LLM execution failed: {e}. Falling back to Rule Engine.")
                return self._triage_rule_engine(subject, body, matched_kb, kb_score)

        # Target: Gemini requested (or default provider)
        if target_provider == "gemini" or not target_provider:
            if has_valid_gemini:
                try:
                    return self._triage_with_gemini(subject, body, matched_kb, kb_score, kb_context)
                except Exception as e:
                    err_detail = _redact_key(e)
                    print(f"[TriageAgent] Gemini API call failed ({err_detail}). Attempting failover...")
                    # Fallback to Ollama if available
                    try:
                        res = self._triage_with_local_llm(subject, body, matched_kb, kb_score, kb_context)
                        res.execution_mode = f"LLM_LOCAL_OLLAMA (tinyllama) [Fallback: Gemini API Error ({err_detail})]"
                        return res
                    except Exception:
                        res = self._triage_rule_engine(subject, body, matched_kb, kb_score)
                        res.execution_mode = f"RULE_ENGINE_FALLBACK [Fallback: Gemini API Error ({err_detail})]"
                        return res
            else:
                # Key is missing or invalid placeholder
                err_detail = "Invalid/Missing Gemini API Key"
                print(f"[TriageAgent] {err_detail}. Attempting failover...")
                try:
                    res = self._triage_with_local_llm(subject, body, matched_kb, kb_score, kb_context)
                    res.execution_mode = f"LLM_LOCAL_OLLAMA (tinyllama) [Fallback: {err_detail}]"
                    return res
                except Exception:
                    res = self._triage_rule_engine(subject, body, matched_kb, kb_score)
                    res.execution_mode = f"RULE_ENGINE_FALLBACK [Fallback: {err_detail}]"
                    return res

        # Target: OpenAI requested
        if target_provider == "openai":
            if has_valid_openai:
                try:
                    return self._triage_with_openai(subject, body, matched_kb, kb_score, kb_context)
                except Exception as e:
                    err_detail = _redact_key(e)
                    print(f"[TriageAgent] OpenAI API call failed ({err_detail}). Attempting failover...")
                    try:
                        res = self._triage_with_local_llm(subject, body, matched_kb, kb_score, kb_context)
                        res.execution_mode = f"LLM_LOCAL_OLLAMA (tinyllama) [Fallback: OpenAI API Error ({err_detail})]"
                        return res
                    except Exception:
                        res = self._triage_rule_engine(subject, body, matched_kb, kb_score)
                        res.execution_mode = f"RULE_ENGINE_FALLBACK [Fallback: OpenAI API Error ({err_detail})]"
                        return res
            else:
                err_detail = "Invalid/Missing OpenAI API Key"
                print(f"[TriageAgent] {err_detail}. Attempting failover...")
                try:
                    res = self._triage_with_local_llm(subject, body, matched_kb, kb_score, kb_context)
                    res.execution_mode = f"LLM_LOCAL_OLLAMA (tinyllama) [Fallback: {err_detail}]"
                    return res
                except Exception:
                    res = self._triage_rule_engine(subject, body, matched_kb, kb_score)
                    res.execution_mode = f"RULE_ENGINE_FALLBACK [Fallback: {err_detail}]"
                    return res

        # Ultimate fallback
        return self._triage_rule_engine(subject, body, matched_kb, kb_score)

    def _triage_with_gemini(self, subject: str, body: str, matched_kb: str, kb_score: float, kb_context: str) -> TriageOutput:
        import requests
        gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        prompt = f"Ticket Subject: {subject}\nTicket Body: {body}\nMatched KB: {matched_kb}\nKB Context: {kb_context[:500]}"
        payload = {
            "contents": [{"parts": [{"text": f"{TRIAGE_SYSTEM_PROMPT}\n\n{prompt}"}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
        }
        res = None
        for attempt in range(4):
            _throttle_gemini_api()
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                if res.status_code in (400, 401, 403):
                    break
                if res.status_code in (429, 500, 502, 503, 504):
                    time.sleep(5.0 * (attempt + 1))
                    continue
                break
            except requests.exceptions.RequestException:
                if attempt == 3:
                    raise
                time.sleep(5.0 * (attempt + 1))
        res.raise_for_status()
        text_out = res.json()['candidates'][0]['content']['parts'][0]['text']
        parsed = json.loads(text_out)
        parsed["matched_kb_doc"] = matched_kb
        parsed["kb_relevance_score"] = round(kb_score, 3)
        parsed["execution_mode"] = "LLM_GEMINI"
        return TriageOutput(**parsed)

    def _triage_with_openai(self, subject: str, body: str, matched_kb: str, kb_score: float, kb_context: str) -> TriageOutput:
        import requests
        openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        prompt = f"Ticket Subject: {subject}\nTicket Body: {body}\nMatched KB: {matched_kb}\nKB Context: {kb_context[:500]}"
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
        payload = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        text_out = res.json()['choices'][0]['message']['content']
        parsed = json.loads(text_out)
        parsed["matched_kb_doc"] = matched_kb
        parsed["kb_relevance_score"] = round(kb_score, 3)
        parsed["execution_mode"] = "LLM_OPENAI"
        return TriageOutput(**parsed)

    def _triage_with_local_llm(self, subject: str, body: str, matched_kb: str, kb_score: float, kb_context: str) -> TriageOutput:
        import requests
        local_url = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/api/generate").strip()
        model_name = os.getenv("LOCAL_LLM_MODEL", "tinyllama").strip()
        
        prompt = f"""{TRIAGE_SYSTEM_PROMPT}

Ticket Subject: {subject}
Ticket Body: {body}
Matched Knowledge Base Document: {matched_kb}
"""
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        res = requests.post(local_url, json=payload, timeout=15)
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

        urgency = parsed.get("urgency_tier") or parsed.get("urgency_tiers") or "P2"
        if isinstance(urgency, dict):
            urgency = list(urgency.keys())[0] if urgency else "P2"
        elif isinstance(urgency, list):
            urgency = urgency[0] if urgency else "P2"
        urgency_str = str(urgency).strip().upper()
        if not any(urgency_str.startswith(p) for p in ["P1", "P2", "P3", "P4"]):
            urgency_str = "P1" if "outage" in body.lower() or "lockout" in body.lower() or "urgent" in subject.lower() else "P2"
        else:
            urgency_str = urgency_str[:2]
            
        reasoning = parsed.get("urgency_reasoning") or parsed.get("reasoning") or "Classified via Local LLM (tinyllama)"
            
        clean_dict = {
            "product_area": str(parsed.get("product_area", "Authentication")),
            "issue_category": str(parsed.get("issue_category", "Security / Access Lockout")),
            "urgency_tier": urgency_str,
            "urgency_reasoning": str(reasoning),
            "recommended_team": str(parsed.get("recommended_team", "TAM Escalation")),
            "draft_response": str(parsed.get("draft_response", "Thank you for reaching out. Our engineering team is investigating your issue immediately.")),
            "matched_kb_doc": matched_kb,
            "kb_relevance_score": round(kb_score, 3),
            "execution_mode": f"LLM_LOCAL_OLLAMA ({model_name})"
        }
        return TriageOutput(**clean_dict)

    def _triage_rule_engine(self, subject: str, body: str, matched_kb: str, kb_score: float) -> TriageOutput:
        text = f"{subject} {body}".lower()
        
        # Product Area & Category
        if any(w in text for w in ["sso", "saml", "jwt", "login", "locked out", "auth", "mfa", "token", "password"]):
            area = "Authentication"
            if any(w in text for w in ["locked out", "security", "unauthorized"]):
                category = "Security / Access Lockout"
            else:
                category = "Configuration Error"
        elif any(w in text for w in ["invoice", "billed", "overage", "payment", "charge", "refund", "subscription", "pricing"]):
            area = "Billing & Invoicing"
            category = "Bug" if "incorrect" in text or "dispute" in text else "Configuration Error"
        elif any(w in text for w in ["api", "429", "rate limit", "endpoint", "bearer"]):
            area = "API Integration"
            category = "Outage / Downtime" if "429" in text or "failed" in text else "Configuration Error"
        elif any(w in text for w in ["webhook", "hmac", "sha256", "signature"]):
            area = "Webhooks"
            category = "Bug"
        elif any(w in text for w in ["outage", "slow", "performance", "err_conn_pool_limit", "database", "500", "crash"]):
            area = "Infrastructure & Performance"
            category = "Outage / Downtime"
        else:
            area = "Dashboard & UI"
            category = "Feature Request" if "how to" in text or "add" in text else "Bug"

        # Urgency Tier Logic
        if any(w in text for w in ["outage", "entire executive team", "cancelling contract", "locked out", "production down", "critical", "board meeting"]):
            urgency = "P1"
            reasoning = "Critical business impact affecting executive access, severe outage, or immediate contract churn threat."
        elif any(w in text for w in ["429", "halted", "dispute", "err_conn_pool_limit", "urgent", "migration"]):
            urgency = "P2"
            reasoning = "Major operational disruption or data pipeline stall without immediate workaround."
        elif any(w in text for w in ["failing", "error", "hmac", "investigate"]):
            urgency = "P3"
            reasoning = "Moderate issue with active troubleshooting required."
        else:
            urgency = "P4"
            reasoning = "General inquiry or non-critical documentation query."

        # Responder Team Assignment
        if urgency == "P1" and "contract" in text:
            team = "TAM Escalation"
        elif area == "Authentication" and "locked" in text:
            team = "Security Ops"
        elif area == "Billing & Invoicing":
            team = "Billing Ops"
        elif area in ["Infrastructure & Performance", "API Integration"] and urgency in ["P1", "P2"]:
            team = "Tier 2 Engineering"
        else:
            team = "Tier 1 Support"

        # Draft Response
        draft = (
            f"Hello,\n\nThank you for reaching out to Technical Support. We have received your request regarding {area.lower()} "
            f"and classified it as an urgent priority ({urgency}). Our {team} has been assigned to investigate.\n\n"
        )
        if matched_kb != "None":
            draft += f"In the meantime, you may find helpful resolution steps in our documentation: '{matched_kb}'.\n\n"
        draft += "Best regards,\nCustomer Technical Support Team"

        return TriageOutput(
            product_area=area,
            issue_category=category,
            urgency_tier=urgency,
            urgency_reasoning=reasoning,
            matched_kb_doc=matched_kb,
            kb_relevance_score=round(kb_score, 3),
            recommended_team=team,
            draft_response=draft,
            execution_mode="RULE_ENGINE_FALLBACK"
        )

# Module function shortcut required by spec
def triage_ticket(ticket_input: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    agent = TicketTriageAgent()
    result = agent.triage(ticket_input)
    return result.model_dump()
