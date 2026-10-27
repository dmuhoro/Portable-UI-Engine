# Security Brief

> Condensed from `docs/security.md` + `docs/security-subsystems.md`. The invariants that must never break.

## Auth Flow

1. Login: `auth.server.ts:login()` — rate-limited (5/60s per email), PBKDF2 SHA-512 verify
2. Session: HMAC-SHA256 signed JWT in `kwc_session` httpOnly cookie, base64url, 24h expiry
3. Every request: `requireOrg()` reads session → `{ orgId, userId, role }`
4. RBAC: `super_admin`(100) > `admin`(50) > `staff`(10); `requireRole()` gates server functions

## Tenant Isolation (THE invariant)

- Every query binds `organization_id = $N`. No auto-scoping (D7).
- Cross-tenant access = P0. 5 P0s fixed in Sprint 34, proven by 22 adversarial tests.
- **When adding `api/mpesa.server.ts`, every query must bind orgId.** The STK webhook route resolves
  org by `organization_id` on the request row (NOT by client-supplied org).

## Security Subsystems

| Subsystem | Location | Notes |
|-----------|----------|-------|
| Encryption | `encryption.server.ts` | AES-256-GCM, per-org PBKDF2 keys, versioned, `ENC:` prefix |
| Webhooks | `webhooks.server.ts` | HMAC-SHA256 signed outbound, retry w/ backoff, circuit breaker |
| Rate limiting | `rate-limit.server.ts` | login 5/60s, submitLead 30/60s, WhatsApp 20/60s, reconcile 10/60s |
| Fallback | `fallback.server.ts` | channel health circuit breaker (webhook → whatsapp → sms) |
| Audit | `audit.server.ts` | all mutations → `audit_logs` (tenant_id) |
| Event bus | `event-bus.server.ts` | `live_events` → SSE long-poll |

## Webhook Security (WhatsApp pattern to reuse for M-Pesa)

- GET = verification handshake (verify_token)
- POST = HMAC-SHA256 signature check (`x-hub-signature-256`) when secret configured
- Never trust client-supplied org in a webhook — resolve from the payload/record.

## M-Pesa Callback Security (NEW)

- Require callback secret (`x-callback-secret` header or `?secret=` query) when `MPESA_CALLBACK_SECRET` is set.
- Match by `CheckoutRequestID` → row's `organization_id`.
- Idempotency: unique on `(organization_id, checkout_request_id, mpesa_receipt_number)` so a replayed
  callback never double-records a payment.

## PII Encryption (D11 wiring)

- Write path: `encryptFields(orgId, row, ['name','phone','email'])` before INSERT.
- Read path: `decryptFields(orgId, row, [...])` after SELECT.
- Ciphertext marker: `ENC:{...}`. `decryptPII` passes through non-`ENC:` values.
- Key rotation: `rotateOrgKey(orgId)` — old versions still decrypt (tested).
- **Do NOT log plaintext PII** — logger redacts `phone`/`email`/`name`/`raw_payload` keys.