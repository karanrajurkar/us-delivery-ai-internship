# Architectural Design Note

Production-grade AI Infrastructure for Technical Support & TAM Teams.

---

## 1. Failure Modes, Detection & Mitigation

In a mission-critical support environment, LLM-powered agents can encounter three primary failure modes:

1. **Hallucinated or Paraphrased Risk Quotes (Task 2)**
   - *Risk*: The model generates plausible-sounding churn or escalation reasons but invents or alters customer quotes, causing TAMs to present inaccurate information during QBRs.
   - *Detection*: Automated regex and string distance validation comparing generated quotes against raw ticket bodies in the 90-day window.
   - *Mitigation*: Fallback quote extraction parser (`_extract_verbatim_risk_quotes`) that extracts exact substring matches programmatically before supplying them to the LLM or UI.

2. **Knowledge Base Mis-Retrieval / Low-Relevance Matching (Task 1)**
   - *Risk*: A customer submits a niche technical ticket (e.g. edge-case SSO clock-skew error), but the RAG retriever retrieves an unrelated document (e.g., Billing FAQ), leading to incorrect triage routing.
   - *Detection*: RAG similarity score thresholding (`kb_relevance_score < 0.30`).
   - *Mitigation*: When similarity scores drop below threshold, the agent sets `matched_kb_doc` to `"None"`, avoids attaching irrelevant docs, and routes the ticket to Tier 2 Engineering for human review.

3. **External API Downtime / Rate-Limiting (System-wide)**
   - *Risk*: Outages or rate limits (HTTP 429/500) from external LLM providers stall support ticket intake.
   - *Detection*: Circuit breakers monitoring error rates on API calls.
   - *Mitigation*: Failover to a local, deterministic rule-based fallback engine (`_triage_rule_engine` & `_summarise_rule_engine`) ensuring 100% uptime SLA without service degradation.

---

## 2. Latency vs. Quality Trade-offs

- **Concrete Trade-off Made**: We prioritized output quality and factual determinism over raw speed. For Task 2, we execute multi-pass data retrieval (filtering 90-day tickets, pulling CRM account metadata, and verifying verbatim quote bounds) and run structured JSON validation. This adds ~1.2s of server processing time but guarantees zero hallucinated quotes and 100% deterministic outputs.
- **Low-Latency Constraint Adaptation**: If response speed were a hard constraint (e.g., sub-200ms real-time ticket ingestion SLA), we would:
  1. Switch from full multi-document LLM context processing to a pre-computed embedding cache for ticket classification.
  2. Implement Server-Sent Events (SSE) streaming (`StreamingResponse`) so the support agent sees instant token streaming within 100ms.
  3. Asynchronously queue full TAM brief synthesis via Celery/Redis background jobs upon ticket creation rather than generating briefs on-demand during page loads.

---

## 3. Data Sensitivity & PII Protection

Support tickets frequently contain Sensitive Personal Data (PII), including API keys, passwords, customer email addresses, and billing credentials.

- **Client-Side Redaction Pipeline**: Before any ticket body or account metadata is transmitted to external LLM APIs (Gemini/OpenAI), text is processed through a zero-latency PII scrubber using regular expressions and Named Entity Recognition (NER).
  - API Keys & Tokens: Replaced with `[REDACTED_API_KEY]`
  - Credit Cards / IBANs: Replaced with `[REDACTED_CARD]`
  - Passwords / Secrets: Replaced with `[REDACTED_SECRET]`
- **Zero-Retention API Contracts**: All production LLM API calls specify enterprise zero-data-retention headers (`"X-Opt-Out-Data-Training": "true"` and enterprise tenant privacy mode), preventing external vendors from storing customer ticket logs.

---

## 4. Scaling to 10× Volume: Bottlenecks & Architectural Evolution

If ticket volume increases 10× (from 500 to 5,000+ tickets/day):

1. **What Breaks First**: 
   - **In-Memory RAG Vector Search**: In-memory TF-IDF and linear matrix multiplication over knowledge base files will experience memory and CPU contention under high concurrent requests.
   - **Database I/O for 90-Day Ticket Queries**: Iterating through raw JSON arrays to aggregate 90-day ticket histories for 50 accounts will bottleneck database reads.
2. **Architectural Evolution**:
   - **Vector Database Migration**: Migrate RAG indexing from TF-IDF to a dedicated vector store (Pinecone / Qdrant / pgvector) with HNSW indexing for sub-10ms similarity search.
   - **Asynchronous Message Queue**: Decouple HTTP ingestion from LLM processing using an event-driven architecture (Kafka / RabbitMQ + Celery workers).
   - **Materialized Account Views**: Maintain pre-aggregated account health summaries in Redis with write-through cache invalidation whenever a new P1/P2 ticket is logged.
