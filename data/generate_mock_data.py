import json
import os
import random
from datetime import datetime, timedelta

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(DATA_DIR, "kb")

def create_knowledge_base():
    os.makedirs(KB_DIR, exist_ok=True)
    
    docs = {
        "auth.md": """# Authentication & SSO Guide
## Overview
Our platform supports SAML 2.0, OAuth 2.0, and Okta/Azure AD integration.

## Troubleshooting Common Authentication Issues
- **Error 401 Unauthorized / Token Expired**: JWT tokens expire after 3600 seconds (1 hour). Clients must request a new token using the `/oauth/token` refresh endpoint.
- **SSO Lockout**: If SSO SAML assertion fails due to clock skew, verify your IdP NTP synchronization. If an admin is locked out, use the emergency recovery link sent to the primary security contact email.
- **MFA Reset**: Multi-Factor Authentication reset requires Account Admin confirmation or tier-2 security ticket escalation.
""",
        "billing.md": """# Billing & Invoicing FAQs
## Invoice Generation & Payment Terms
Invoices are generated on the 1st of each calendar month. Payment terms are Net-30 for Enterprise accounts.

## Overage & Seat Licensing
- **Seat Overages**: If seat count exceeds contract limit by >10%, additional seats are automatically billed at $45/user/month.
- **Refund Policy**: Disputes on line items must be submitted within 14 days of invoice issue date.
- **Discounts & Renewals**: Annual prepay offers a 15% discount. Contract cancellations require 30-day written notice before term renewal.
""",
        "api.md": """# API Integration & Rate Limits
## REST API Standards
All requests to `https://api.platform.com/v1/` require an `Authorization: Bearer <API_KEY>` header.

## Rate Limiting (429 Too Many Requests)
- Enterprise Tier: 5,000 requests/min.
- Pro Tier: 1,000 requests/min.
- Starter Tier: 100 requests/min.
When rate limited, headers include `Retry-After` (seconds). Exponential backoff with jitter is strongly recommended.

## Webhooks
Webhooks deliver payload with HMAC-SHA256 signature in `X-Signature-256` header. Timeout is 5.0 seconds per endpoint call. Retries occur 3 times with exponential backoff.
""",
        "infrastructure.md": """# Infrastructure, Performance & Outages
## SLA Specifications
- Enterprise: 99.99% Uptime SLA with 1-hour P1 response time guarantee.
- Pro: 99.9% Uptime SLA.

## Outage Protocols
1. Check global status page at `https://status.platform.com`.
2. P1 Critical tickets trigger automated pager duty alerts to Tier-2 Infrastructure On-Call.
3. Database connection pool exhaustion errors (e.g. `ERR_CONN_POOL_LIMIT`) usually indicate unclosed client database connections or unexpected traffic spikes.
"""
    }
    
    for filename, content in docs.items():
        with open(os.path.join(KB_DIR, filename), "w", encoding="utf-8") as f:
            f.write(content.strip())
    print(f"Created {len(docs)} Knowledge Base documents in {KB_DIR}")

def generate_accounts():
    company_names = [
        "Acme Corp", "Apex Technologies", "BlueSky Cloud", "CyberShield Inc", "DataDynamics",
        "Echo Systems", "FinTech Global", "GlobalLogistics", "HyperScale AI", "Innovate Tech",
        "Jupiter Financial", "Krypton Labs", "Lunar Commerce", "Matrix Digital", "Nova Solutions",
        "Omni Health", "Pinnacle Networks", "Quantum Compute", "Radius Retail", "Starlight Media",
        "Titan Security", "Ultra Data", "Vortex Software", "Wave Telecom", "Zenith Enterprise"
    ]
    tiers = ["Enterprise", "Pro", "Starter"]
    
    accounts = []
    for i in range(1, 51):
        name = company_names[(i - 1) % len(company_names)] if i <= len(company_names) else f"Company {i} Inc"
        tier = random.choice(tiers) if i > 10 else ("Enterprise" if i <= 5 else "Pro")
        mrr = random.randint(15000, 85000) if tier == "Enterprise" else (random.randint(3000, 14000) if tier == "Pro" else random.randint(500, 2500))
        health_score = random.choice(["Healthy", "At-Risk", "Critical"]) if i <= 15 else random.choice(["Healthy", "Healthy", "At-Risk"])
        
        account = {
            "account_id": f"ACC-{i:03d}",
            "company_name": name,
            "tier": tier,
            "mrr": mrr,
            "health_score": health_score,
            "primary_contact": f"contact@{name.lower().replace(' ', '').replace(',', '')}.com",
            "contract_end_date": (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
            "tam_assigned": f"TAM_{((i-1)%5)+1}"
        }
        accounts.append(account)
        
    accounts_path = os.path.join(DATA_DIR, "accounts.json")
    with open(accounts_path, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2)
    print(f"Generated 50 account summaries in {accounts_path}")
    return accounts

def generate_tickets(accounts):
    product_areas = ["Authentication", "Billing & Invoicing", "API Integration", "Webhooks", "Infrastructure & Performance", "Dashboard & UI"]
    
    sample_ticket_templates = [
        # Churn / Escalation templates (Crucial for Task 2 risk detection tests)
        {
            "subject": "URGENT: Considering cancelling contract due to recurring 401 SSO lockouts",
            "body": "Our entire executive team was locked out of SSO during our quarterly board meeting. This is unacceptable. We are actively looking at competitor solutions and considering cancelling our Enterprise contract immediately if this isn't resolved today. I want to speak to our TAM right now.",
            "area": "Authentication",
            "churn_signal": True,
            "urgency": "P1"
        },
        {
            "subject": "API Rate Limit hitting 429 constantly during peak migration",
            "body": "We are getting 429 Too Many Requests errors continuously. Our data migration pipeline has halted. If we cannot get our rate limit increased for ACC-001 by EOD, we will fail our compliance deadline and escalate to executive leadership.",
            "area": "API Integration",
            "churn_signal": True,
            "urgency": "P1"
        },
        {
            "subject": "Incorrect overage charge on invoice INV-2026-08",
            "body": "We were billed $4,500 for seat overages that were never authorized. We demanded a full refund or we will pause all payments and evaluate terminating our subscription.",
            "area": "Billing & Invoicing",
            "churn_signal": True,
            "urgency": "P2"
        },
        # Regular support templates
        {
            "subject": "JWT token expiration behavior query",
            "body": "Hi support, what is the default lifetime of JWT access tokens and how do we configure automatic refresh tokens in Python SDK?",
            "area": "Authentication",
            "churn_signal": False,
            "urgency": "P4"
        },
        {
            "subject": "Webhook HMAC signature verification failing",
            "body": "We are receiving webhooks from your service, but the X-Signature-256 header does not match our calculated SHA256 digest. Is there a documentation reference for key formatting?",
            "area": "Webhooks",
            "churn_signal": False,
            "urgency": "P3"
        },
        {
            "subject": "Database connection pool exhaustion ERR_CONN_POOL_LIMIT",
            "body": "Our production backend reported ERR_CONN_POOL_LIMIT continuously between 10:00 AM and 10:30 AM UTC. Please investigate if there was a platform outage on your database cluster.",
            "area": "Infrastructure & Performance",
            "churn_signal": False,
            "urgency": "P2"
        },
        {
            "subject": "How to update payment method in billing portal?",
            "body": "We need to update our corporate credit card for account renewal next month. Where can we find the billing portal link in the dashboard?",
            "area": "Billing & Invoicing",
            "churn_signal": False,
            "urgency": "P4"
        }
    ]
    
    tickets = []
    now = datetime.now()
    
    for i in range(1, 501):
        acc = random.choice(accounts)
        tmpl = random.choice(sample_ticket_templates)
        # Ensure targeted accounts like ACC-001, ACC-002, ACC-003 get specific churn/escalation tickets for eval tests
        if i <= 50:
            acc = accounts[(i - 1) % 10]
            if i % 3 == 0:
                tmpl = sample_ticket_templates[0] # Churn risk template
            elif i % 3 == 1:
                tmpl = sample_ticket_templates[1] # API P1 template
            else:
                tmpl = sample_ticket_templates[2] # Billing dispute template

        created_days_ago = random.randint(1, 120)
        created_at = (now - timedelta(days=created_days_ago, hours=random.randint(0, 23))).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        ticket = {
            "ticket_id": f"TCK-{i:04d}",
            "account_id": acc["account_id"],
            "subject": tmpl["subject"],
            "body": tmpl["body"],
            "product_area": tmpl["area"],
            "created_at": created_at,
            "status": random.choice(["Open", "Pending Engineer", "Resolved", "Closed"]) if created_days_ago > 7 else "Open",
            "channel": random.choice(["Web Portal", "Email", "Slack Integration", "API"])
        }
        tickets.append(ticket)
        
    tickets_path = os.path.join(DATA_DIR, "tickets.json")
    with open(tickets_path, "w", encoding="utf-8") as f:
        json.dump(tickets, f, indent=2)
    print(f"Generated 500 tickets in {tickets_path}")
    return tickets

if __name__ == "__main__":
    create_knowledge_base()
    accs = generate_accounts()
    generate_tickets(accs)
