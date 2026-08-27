# System Evaluation Report

**Total Tests:** 10  
**Passed:** 5 / 10  
**Average Quality Score:** 0.76 / 1.0  

## Test Results Summary

| Task | Test ID | Description | Type | Result | Score | Latency (s) |
|---|---|---|---|---|---|---|
| Task 1: Ticket Triage | `T1_TEST_1` | Standard Authentication SSO lockout ticket | Standard | ❌ FAIL | **0.7** | 7.2966s |
| Task 1: Ticket Triage | `T1_TEST_2` | API Rate Limit 429 error during migration | Standard | ❌ FAIL | **0.5** | 3.2904s |
| Task 1: Ticket Triage | `T1_TEST_3` | Webhook HMAC signature verification failing | Standard | ❌ FAIL | **0.5** | 2.7591s |
| Task 1: Ticket Triage | `T1_TEST_4` | General payment portal query | Standard | ❌ FAIL | **0.5** | 3.4153s |
| Task 1: Ticket Triage | `T1_TEST_5_ADV` | Adversarial: Highly ambiguous multi-issue ticket (Billing dispute + Database outage) | Adversarial | ✅ PASS | **1.0** | 3.1581s |
| Task 2: Account Health Summariser | `T2_TEST_1` | Account ACC-001 with high churn risk tickets | Standard | ❌ FAIL | **0.55** | 4.8485s |
| Task 2: Account Health Summariser | `T2_TEST_2` | Pro tier account ACC-004 health summary check | Standard | ✅ PASS | **1.0** | 62.0445s |
| Task 2: Account Health Summariser | `T2_TEST_3` | Determinism verification: duplicate run check on ACC-001 | Standard | ✅ PASS | **1.0** | 62.0405s |
| Task 2: Account Health Summariser | `T2_TEST_4` | Enterprise tier account ACC-005 ticket history check | Standard | ✅ PASS | **1.0** | 62.0371s |
| Task 2: Account Health Summariser | `T2_TEST_5_ADV` | Adversarial: Non-existent account ID 'ACC-99999' | Adversarial | ✅ PASS | **0.85** | 0.0s |

## Detailed Test Logs
### `T1_TEST_1` - Standard Authentication SSO lockout ticket
- **Task:** Task 1: Ticket Triage
- **Status:** FAIL (Score: 0.7)
- **Reasoning / Notes:** Expected area 'Authentication', got 'Authentication | Billing & Invoicing | API Integration | Webhooks | Infra & Performance | Dashboard & UI'
- **Output Snippet:** ```json
{
  "product_area": "Authentication | Billing & Invoicing | API Integration | Webhooks | Infra & Performance | Dashboard & UI",
  "urgency_tier": "P1",
  "matched_kb_doc": "auth.md",
  "recommended_team": "TAM Escalation"
}
```

### `T1_TEST_2` - API Rate Limit 429 error during migration
- **Task:** Task 1: Ticket Triage
- **Status:** FAIL (Score: 0.5)
- **Reasoning / Notes:** Expected area 'API Integration', got 'Authentication | Billing & Invocaing | API Integration | Webhooks | Infraestructure & Performance | Dasbord & UI'; Expected urgency 'P1', got 'P2'
- **Output Snippet:** ```json
{
  "product_area": "Authentication | Billing & Invocaing | API Integration | Webhooks | Infraestructure & Performance | Dasbord & UI",
  "urgency_tier": "P2",
  "matched_kb_doc": "api.md",
  "recommended_team": "Tier 1 Support | Tier 2 Engineering | Billing OpS | Security OpS | TAM Escalation"
}
```

### `T1_TEST_3` - Webhook HMAC signature verification failing
- **Task:** Task 1: Ticket Triage
- **Status:** FAIL (Score: 0.5)
- **Reasoning / Notes:** Expected area 'Webhooks', got 'Authentication | Billing & Invocing | API Integration | Webhooks | Infrastructure & Performance | Dashboard & UI'; Expected urgency 'P3', got 'P1'
- **Output Snippet:** ```json
{
  "product_area": "Authentication | Billing & Invocing | API Integration | Webhooks | Infrastructure & Performance | Dashboard & UI",
  "urgency_tier": "P1",
  "matched_kb_doc": "api.md",
  "recommended_team": "TAM Escalation"
}
```

### `T1_TEST_4` - General payment portal query
- **Task:** Task 1: Ticket Triage
- **Status:** FAIL (Score: 0.5)
- **Reasoning / Notes:** Expected area 'Billing & Invoicing', got 'Authentication | Billing & Invoiicing | API Integration | Webhooks | Infrastructure & Performance | Dashrboard & UI'; Expected urgency 'P4', got 'P2'
- **Output Snippet:** ```json
{
  "product_area": "Authentication | Billing & Invoiicing | API Integration | Webhooks | Infrastructure & Performance | Dashrboard & UI",
  "urgency_tier": "P2",
  "matched_kb_doc": "billing.md",
  "recommended_team": "Tier 1 Support | Tier 2 Engineering | Billing OpS|Security Ops|TAM Eskaletion"
}
```

### `T1_TEST_5_ADV` - Adversarial: Highly ambiguous multi-issue ticket (Billing dispute + Database outage)
- **Task:** Task 1: Ticket Triage
- **Status:** PASS (Score: 1.0)
- **Reasoning / Notes:** All criteria satisfied.
- **Output Snippet:** ```json
{
  "product_area": "Authentication | Billing & Invoiicing | API Integration | Webhooks | Infrastructure & Performance | Dashboard & UI",
  "urgency_tier": "P1",
  "matched_kb_doc": "infrastructure.md",
  "recommended_team": "Tier 1 Support"
}
```

### `T2_TEST_1` - Account ACC-001 with high churn risk tickets
- **Task:** Task 2: Account Health Summariser
- **Status:** FAIL (Score: 0.55)
- **Reasoning / Notes:** Exec summary sentence count is 1 (expected 3-5); Fewer than 2 recommended talking points produced
- **Output Snippet:** ```json
{
  "account_id": "ACC-001",
  "company_name": "Acme Corp",
  "exec_summary_sentences": 1,
  "risk_flag_count": 11,
  "talking_points_count": 1
}
```

### `T2_TEST_2` - Pro tier account ACC-004 health summary check
- **Task:** Task 2: Account Health Summariser
- **Status:** PASS (Score: 1.0)
- **Reasoning / Notes:** All criteria satisfied.
- **Output Snippet:** ```json
{
  "account_id": "ACC-004",
  "company_name": "CyberShield Inc",
  "exec_summary_sentences": 4,
  "risk_flag_count": 10,
  "talking_points_count": 4
}
```

### `T2_TEST_3` - Determinism verification: duplicate run check on ACC-001
- **Task:** Task 2: Account Health Summariser
- **Status:** PASS (Score: 1.0)
- **Reasoning / Notes:** All criteria satisfied.
- **Output Snippet:** ```json
{
  "account_id": "ACC-001",
  "company_name": "Acme Corp",
  "exec_summary_sentences": 4,
  "risk_flag_count": 11,
  "talking_points_count": 4
}
```

### `T2_TEST_4` - Enterprise tier account ACC-005 ticket history check
- **Task:** Task 2: Account Health Summariser
- **Status:** PASS (Score: 1.0)
- **Reasoning / Notes:** All criteria satisfied.
- **Output Snippet:** ```json
{
  "account_id": "ACC-005",
  "company_name": "DataDynamics",
  "exec_summary_sentences": 4,
  "risk_flag_count": 16,
  "talking_points_count": 4
}
```

### `T2_TEST_5_ADV` - Adversarial: Non-existent account ID 'ACC-99999'
- **Task:** Task 2: Account Health Summariser
- **Status:** PASS (Score: 0.85)
- **Reasoning / Notes:** Exec summary sentence count is 2 (expected 3-5)
- **Output Snippet:** ```json
{
  "account_id": "ACC-99999",
  "company_name": "Unknown Account",
  "exec_summary_sentences": 2,
  "risk_flag_count": 1,
  "talking_points_count": 2
}
```

