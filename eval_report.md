# System Evaluation Report

**Total Tests:** 10  
**Passed:** 9 / 10  
**Average Quality Score:** 0.88 / 1.0  

## Test Results Summary

| Task | Test ID | Description | Type | Result | Score | Latency (s) |
|---|---|---|---|---|---|---|
| Task 1: Ticket Triage | `T1_TEST_1` | Standard Authentication SSO lockout ticket | Standard | ✅ PASS | **0.8** | 11.8356s |
| Task 1: Ticket Triage | `T1_TEST_2` | API Rate Limit 429 error during migration | Standard | ✅ PASS | **0.8** | 11.0276s |
| Task 1: Ticket Triage | `T1_TEST_3` | Webhook HMAC signature verification failing | Standard | ❌ FAIL | **0.5** | 67.9735s |
| Task 1: Ticket Triage | `T1_TEST_4` | General payment portal query | Standard | ✅ PASS | **1.0** | 25.9539s |
| Task 1: Ticket Triage | `T1_TEST_5_ADV` | Adversarial: Highly ambiguous multi-issue ticket (Billing dispute + Database outage) | Adversarial | ✅ PASS | **1.0** | 8.9454s |
| Task 2: Account Health Summariser | `T2_TEST_1` | Account ACC-001 with high churn risk tickets | Standard | ✅ PASS | **1.0** | 10.3034s |
| Task 2: Account Health Summariser | `T2_TEST_2` | Pro tier account ACC-004 health summary check | Standard | ✅ PASS | **1.0** | 11.4266s |
| Task 2: Account Health Summariser | `T2_TEST_3` | Determinism verification: duplicate run check on ACC-001 | Standard | ✅ PASS | **1.0** | 14.8345s |
| Task 2: Account Health Summariser | `T2_TEST_4` | Enterprise tier account ACC-005 ticket history check | Standard | ✅ PASS | **0.85** | 37.9493s |
| Task 2: Account Health Summariser | `T2_TEST_5_ADV` | Adversarial: Non-existent account ID 'ACC-99999' | Adversarial | ✅ PASS | **0.85** | 0.0s |

## Detailed Test Logs
### `T1_TEST_1` - Standard Authentication SSO lockout ticket
- **Task:** Task 1: Ticket Triage
- **Status:** PASS (Score: 0.8)
- **Reasoning / Notes:** Expected urgency 'P1', got 'P2'
- **Output Snippet:** ```json
{
  "product_area": "Authentication",
  "urgency_tier": "P2",
  "matched_kb_doc": "auth.md",
  "recommended_team": "Security Ops"
}
```

### `T1_TEST_2` - API Rate Limit 429 error during migration
- **Task:** Task 1: Ticket Triage
- **Status:** PASS (Score: 0.8)
- **Reasoning / Notes:** Expected urgency 'P1', got 'P2'
- **Output Snippet:** ```json
{
  "product_area": "API Integration",
  "urgency_tier": "P2",
  "matched_kb_doc": "api.md",
  "recommended_team": "Tier 1 Support"
}
```

### `T1_TEST_3` - Webhook HMAC signature verification failing
- **Task:** Task 1: Ticket Triage
- **Status:** FAIL (Score: 0.5)
- **Reasoning / Notes:** Expected area 'Webhooks', got 'Authentication | Billing & Invoiicing | API Integration | Webhooks | Infrastructure & Performance | Dashrboard & UI'; Expected urgency 'P3', got 'P2'
- **Output Snippet:** ```json
{
  "product_area": "Authentication | Billing & Invoiicing | API Integration | Webhooks | Infrastructure & Performance | Dashrboard & UI",
  "urgency_tier": "P2",
  "matched_kb_doc": "api.md",
  "recommended_team": "Tier 1 Support | Tier 2 Engineering | Billing OpS | Security OpS | TAM EscrAmIcALoCy"
}
```

### `T1_TEST_4` - General payment portal query
- **Task:** Task 1: Ticket Triage
- **Status:** PASS (Score: 1.0)
- **Reasoning / Notes:** All criteria satisfied.
- **Output Snippet:** ```json
{
  "product_area": "Billing & Invoicing",
  "urgency_tier": "P4",
  "matched_kb_doc": "billing.md",
  "recommended_team": "Billing Ops"
}
```

### `T1_TEST_5_ADV` - Adversarial: Highly ambiguous multi-issue ticket (Billing dispute + Database outage)
- **Task:** Task 1: Ticket Triage
- **Status:** PASS (Score: 1.0)
- **Reasoning / Notes:** All criteria satisfied.
- **Output Snippet:** ```json
{
  "product_area": "Infrastructure & Performance",
  "urgency_tier": "P1",
  "matched_kb_doc": "infrastructure.md",
  "recommended_team": "Tier 2 Engineering"
}
```

### `T2_TEST_1` - Account ACC-001 with high churn risk tickets
- **Task:** Task 2: Account Health Summariser
- **Status:** PASS (Score: 1.0)
- **Reasoning / Notes:** All criteria satisfied.
- **Output Snippet:** ```json
{
  "account_id": "ACC-001",
  "company_name": "Acme Corp",
  "exec_summary_sentences": 5,
  "risk_flag_count": 10,
  "talking_points_count": 3
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
  "talking_points_count": 3
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
  "exec_summary_sentences": 5,
  "risk_flag_count": 10,
  "talking_points_count": 3
}
```

### `T2_TEST_4` - Enterprise tier account ACC-005 ticket history check
- **Task:** Task 2: Account Health Summariser
- **Status:** PASS (Score: 0.85)
- **Reasoning / Notes:** Exec summary sentence count is 1 (expected 3-5)
- **Output Snippet:** ```json
{
  "account_id": "ACC-005",
  "company_name": "DataDynamics",
  "exec_summary_sentences": 1,
  "risk_flag_count": 10,
  "talking_points_count": 2
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

