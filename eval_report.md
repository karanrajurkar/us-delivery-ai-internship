# System Evaluation Report

**Total Tests:** 10  
**Passed:** 10 / 10  
**Average Quality Score:** 0.97 / 1.0  

## Test Results Summary

| Task | Test ID | Description | Type | Result | Score | Latency (s) |
|---|---|---|---|---|---|---|
| Task 1: Ticket Triage | `T1_TEST_1` | Standard Authentication SSO lockout ticket | Standard | ✅ PASS | **1.0** | 0.6998s |
| Task 1: Ticket Triage | `T1_TEST_2` | API Rate Limit 429 error during migration | Standard | ✅ PASS | **0.8** | 0.5937s |
| Task 1: Ticket Triage | `T1_TEST_3` | Webhook HMAC signature verification failing | Standard | ✅ PASS | **1.0** | 0.7s |
| Task 1: Ticket Triage | `T1_TEST_4` | General payment portal query | Standard | ✅ PASS | **1.0** | 0.5377s |
| Task 1: Ticket Triage | `T1_TEST_5_ADV` | Adversarial: Highly ambiguous multi-issue ticket (Billing dispute + Database outage) | Adversarial | ✅ PASS | **1.0** | 0.5636s |
| Task 2: Account Health Summariser | `T2_TEST_1` | Account ACC-001 with high churn risk tickets | Standard | ✅ PASS | **1.0** | 0.4975s |
| Task 2: Account Health Summariser | `T2_TEST_2` | Pro tier account ACC-004 health summary check | Standard | ✅ PASS | **1.0** | 0.6085s |
| Task 2: Account Health Summariser | `T2_TEST_3` | Determinism verification: duplicate run check on ACC-001 | Standard | ✅ PASS | **1.0** | 0.7944s |
| Task 2: Account Health Summariser | `T2_TEST_4` | Enterprise tier account ACC-005 ticket history check | Standard | ✅ PASS | **1.0** | 0.5958s |
| Task 2: Account Health Summariser | `T2_TEST_5_ADV` | Adversarial: Non-existent account ID 'ACC-99999' | Adversarial | ✅ PASS | **0.85** | 0.0s |

## Detailed Test Logs
### `T1_TEST_1` - Standard Authentication SSO lockout ticket
- **Task:** Task 1: Ticket Triage
- **Status:** PASS (Score: 1.0)
- **Reasoning / Notes:** All criteria satisfied.
- **Output Snippet:** ```json
{
  "product_area": "Authentication",
  "urgency_tier": "P1",
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
  "recommended_team": "Tier 2 Engineering"
}
```

### `T1_TEST_3` - Webhook HMAC signature verification failing
- **Task:** Task 1: Ticket Triage
- **Status:** PASS (Score: 1.0)
- **Reasoning / Notes:** All criteria satisfied.
- **Output Snippet:** ```json
{
  "product_area": "Webhooks",
  "urgency_tier": "P3",
  "matched_kb_doc": "api.md",
  "recommended_team": "Tier 1 Support"
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
  "product_area": "Billing & Invoicing",
  "urgency_tier": "P2",
  "matched_kb_doc": "infrastructure.md",
  "recommended_team": "Billing Ops"
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
  "exec_summary_sentences": 4,
  "risk_flag_count": 10,
  "talking_points_count": 4
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
  "risk_flag_count": 18,
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
  "risk_flag_count": 10,
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
  "risk_flag_count": 15,
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

