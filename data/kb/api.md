# API Integration & Rate Limits
## REST API Standards
All requests to `https://api.platform.com/v1/` require an `Authorization: Bearer <API_KEY>` header.

## Rate Limiting (429 Too Many Requests)
- Enterprise Tier: 5,000 requests/min.
- Pro Tier: 1,000 requests/min.
- Starter Tier: 100 requests/min.
When rate limited, headers include `Retry-After` (seconds). Exponential backoff with jitter is strongly recommended.

## Webhooks
Webhooks deliver payload with HMAC-SHA256 signature in `X-Signature-256` header. Timeout is 5.0 seconds per endpoint call. Retries occur 3 times with exponential backoff.