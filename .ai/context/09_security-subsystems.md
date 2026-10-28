# Security Subsystems Brief

> Details on encryption, webhooks, rate limits, fallback. Canonical: `docs/security-subsystems.md`.

## Encryption (D11 infra — being wired this sprint)

- `encryptPII(orgId, plaintext)` → `ENC:{iv,tag,data,keyVersion}` hex
- `decryptPII(orgId, ciphertext)` → plaintext (passes through non-ENC)
- `encryptFields(orgId, record, fields)` / `decryptFields(...)` — batch helpers
- `rotateOrgKey(orgId)` → new key version, old keys still decrypt
- `isEncrypted(value)` → boolean
- Key cache: 5-min TTL, per-org + per-version entries; `wipeKeyCache()` for tests

## Webhooks

- `registerWebhook(orgId, url, events, secret?)` → HMAC-SHA256 signing secret
- `deliverWebhook(...)` → signed delivery, exponential backoff, circuit breaker
- Delivery records in `webhook_deliveries`

## Rate Limiting

- `checkRateLimit(key, max, windowMs)` → boolean; in-memory + optional shared
- Configured: login 5/60s, submitLead 30/60s, whatsapp 20/60s, reconcile 10/60s
- **New:** STK push initiate → `mpesa_stk:${orgId}` 10/60s; callback NOT rate-limited (webhook, must not drop)

## Fallback Circuit Breaker

- `channel_health` per (org, channel); on failures open circuit, re-route webhook→whatsapp→sms
- Used by dispatch path; STK push does NOT use fallback (payment must be exact)

## Queue

- `notification_queue` — idempotency keys (SHA-256), retry w/ exponential backoff, max_retries
- `processQueue(batchSize, tenantId?)` — unscoped default; callers role-gated