# Infrastructure, Performance & Outages
## SLA Specifications
- Enterprise: 99.99% Uptime SLA with 1-hour P1 response time guarantee.
- Pro: 99.9% Uptime SLA.

## Outage Protocols
1. Check global status page at `https://status.platform.com`.
2. P1 Critical tickets trigger automated pager duty alerts to Tier-2 Infrastructure On-Call.
3. Database connection pool exhaustion errors (e.g. `ERR_CONN_POOL_LIMIT`) usually indicate unclosed client database connections or unexpected traffic spikes.