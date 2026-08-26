# Prompt Changelog & Versioning

Track all iterations and prompt version changes for the US Delivery Internship AI System.

## [v1.0] - 2026-08-26
### Added
- `prompts/triage_v1.py`: Initial version for Task 1 Intelligent Ticket Triage Agent.
  - Urgency classification rules (P1 to P4).
  - Categorization and RAG knowledge base doc association.
  - Draft first-response message formatting.
- `prompts/summariser_v1.py`: Initial version for Task 2 TAM Account Health Summariser.
  - Strict 3-section brief output structure.
  - Strict rule requiring exact verbatim quotes from tickets for churn/escalation risk flags.
  - Executive summary constraints (3-5 sentences).
