import os
import json
import re
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field

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

class TicketTriageAgent:
    def __init__(self, retriever: Optional[KBRetriever] = None):
        self.retriever = retriever or KBRetriever()
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

    def triage(self, ticket_input: Union[str, Dict[str, Any], TriageInput]) -> TriageOutput:
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

        # Step 2: LLM API or Local Rule Engine Classification
        if self.api_key:
            try:
                return self._triage_with_llm(subject, body, matched_kb, kb_score, kb_context)
            except Exception as e:
                print(f"[TriageAgent] LLM API call failed: {e}. Falling back to rule engine.")

        return self._triage_rule_engine(subject, body, matched_kb, kb_score)

    def _triage_with_llm(self, subject: str, body: str, matched_kb: str, kb_score: float, kb_context: str) -> TriageOutput:
        import requests
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        prompt = f"""Ticket Subject: {subject}
Ticket Body: {body}

Matched Knowledge Base Document: {matched_kb}
KB Context Snippet:
{kb_context[:500]}
"""

        if gemini_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": f"{TRIAGE_SYSTEM_PROMPT}\n\n{prompt}"}]}],
                "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
            }
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            res.raise_for_status()
            res_json = res.json()
            text_out = res_json['candidates'][0]['content']['parts'][0]['text']
            parsed = json.loads(text_out)
            parsed["matched_kb_doc"] = matched_kb
            parsed["kb_relevance_score"] = round(kb_score, 3)
            return TriageOutput(**parsed)
        elif openai_key:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            res.raise_for_status()
            text_out = res.json()['choices'][0]['message']['content']
            parsed = json.loads(text_out)
            parsed["matched_kb_doc"] = matched_kb
            parsed["kb_relevance_score"] = round(kb_score, 3)
            return TriageOutput(**parsed)

        return self._triage_rule_engine(subject, body, matched_kb, kb_score)

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
            draft_response=draft
        )

# Module function shortcut required by spec
def triage_ticket(ticket_input: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    agent = TicketTriageAgent()
    result = agent.triage(ticket_input)
    return result.model_dump()
