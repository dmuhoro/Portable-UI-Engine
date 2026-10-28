# Decisions (ADR Log) Brief

> Condensed from `docs/decisions.md`. Canonical decisions file wins.

## Decision Index

| # | Decision | Status |
|---|----------|--------|
| D1 | TanStack Start over Next.js | Accepted |
| D2 | Raw SQL via `postgres` over ORM | Accepted |
| D3 | PasscodeGate interim auth | Superseded by server RBAC |
| D4 | localStorage offline queue over IndexedDB | Accepted |
| D5 | HMAC-signed JWT over encrypted session | Accepted |
| D6 | Structured JSON logging with key-name PII redaction | Accepted |
| D7 | `requireOrg()` manual tenant scope (no middleware) | Accepted, documented risk |
| D8 | Client-side role checks are UI guards (not security) | Accepted |
| D9 | Vercel deploy with no CI pipeline | Accepted (later superseded: CI exists now) |
| D10 | `postgres` pool with dynamic import obfuscation | Accepted |
| D11 | PII encryption DESCoped from v1 pilot | **REVERSED (Sprint 35)** — wired per ADR-015 |
| D12 | JWT revocation not supported — logout client-side only | Accepted (Sprint 34) |

## The Two That Matter For This Sprint

### D11 — PII Encryption (now WIRED per ADR-015)

- Infrastructure (`encryption.server.ts`) is complete + tested (8 adversarial tests): `encryptPII`,
  `decryptPII`, `encryptFields`, `decryptFields`, `rotateOrgKey`, key versioning, per-org derived keys.
- **Wired** (Sprint 35): `clinic_leads.name/phone/email` + `mpesa_stk_push_requests.phone` encrypted
  on write, decrypted on read. Lazy migration — plaintext rows pass through.

### D12 — JWT Revocation Not Supported

- Logout clears the cookie only; token valid until 24h expiry.
- No server-side denylist/version counter. Accepted for pilot.
- Mitigation for this sprint: keep password change as the revoke path; document in runbook.

## New ADRs This Sprint (docs/adr/)

| ADR | Topic |
|-----|-------|
| ADR-013 | M-Pesa STK Push adoption (greenleaf as schema donor, wired into kays money path) |
| ADR-014 | D11 reversal — PII encryption wired into lead + STK push write paths |
| ADR-015 | Engine consolidation — kays-wellness-centre is the single engine; greenleaf/dentalos are UI/schema donors |
| ADR-016 | Pilot deployment topology — Supabase Postgres + Vercel + WhatsApp Business number |