# Sprint 35 — Pilot Hardening: STK Push, PII Encryption, Deployment Prep

## Summary

Closed the gap between the Sprint-34 engine and a pilot-ready product for Dr. Jackie's
business, applying the Pareto principle (the 20% of work producing 80% of pilot value):

1. **M-Pesa STK Push** (ADR-014) — automatic payment sync. Ported greenleaf-dental's proven
   schema + Daraja patterns into the kays engine with kays conventions. Payments now sync
   automatically when a patient pays via M-Pesa push — no manual entry.
2. **D11 PII Encryption wired** (ADR-015) — lead name/phone/email + STK phone encrypted at rest,
   decrypted on read. Lazy migration (legacy plaintext readable).
3. **Governance structure** (Layer 0) — `.ai/context`, ADRs 013–016, Constitution, runbooks,
   evidence, releases, CHANGELOG.
4. **Deployment prep** — production build verified, Supabase project linked; live deploy blocked
   on owner-held credentials (documented with evidence).

**683 tests / 60 files — all passing** (+16 from baseline 667/58).

## Engine Consolidation (ADR-013)

- **kays-wellness-centre is the single engine.** Earlier strategy proposed greenleaf-dental as the
  engine; verified against code, the opposite is true: kays has the 667-test engine, greenleaf has
  1 placeholder test. greenleaf/dentalos are donors (schema + UI ideas), not runtimes.

## M-Pesa STK Push (ADR-014)

### Schema

`mpesa_stk_push_requests` table added to `ensureSchema()`:

- `organization_id`-scoped (kays convention, not greenleaf's `clinic_id`)
- Links to `invoices` (ON DELETE SET NULL) and `clinic_leads`
- Idempotency: `UNIQUE(organization_id, checkout_request_id, mpesa_receipt_number)`
- Status `pending | success | failed`; raw Daraja response stored in `raw_response`
- Indexes: org+created, checkout_request_id, status, invoice_id

### Module: `src/lib/api/mpesa.server.ts`

| Function | Role |
|----------|------|
| `normalizePhone` | `+254...` / `0...` / `254...` → `254...` |
| `formatDarajaTimestamp` | `YYYYMMDDHHMMSS` |
| `getDarajaAccessToken` | OAuth client_credentials against Daraja |
| `initiateStkPushRaw` | STK processrequest → pending row (phone encrypted) |
| `initiateStkPush` | createServerFn — RBAC owner/admin, 10/60s rate limit, invoice checks |
| `handleStkCallback` | callback processing — replay-safe, idempotent payment via `recordPayment` |
| `fetchStkPushRequests` | serializable DTO (raw_response excluded, phone decrypted) |

### Webhook: `src/routes/api/webhooks/mpesa.ts`

- h3 eventHandler (matches WhatsApp webhook pattern)
- Callback-secret auth (`x-callback-secret` header or `?secret=`) — **fail closed** (rejects when
  secret unset)
- Success → `recordPayment` (same lock + receipt minting as manual entry) → invoice auto-paid

### Env

`MPESA_BASE_URL` (default sandbox), `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`,
`MPESA_SHORTCODE`, `MPESA_PASSKEY`, `MPESA_CALLBACK_URL`, `MPESA_CALLBACK_SECRET`,
`MPESA_TRANSACTION_TYPE` (default `CustomerPayBillOnline`).

## PII Encryption Wiring (ADR-015, reverses D11 descope)

### Encrypt sites (write path)

- `submitLead` → `encryptLeadPII` (name/phone/email)
- `bulkImportLeads` → name/phone/email
- `mpesa.initiateStkPushRaw` → phone

### Decrypt sites (read path)

- `fetchLeads` → `decryptLeadRows`
- `queue.server.ts` (WhatsApp dispatch), `dispatch.server.ts`, `api/automation.server.ts` (×3)
- `marketing/automation.server.ts` (retention), `marketing/reviews.server.ts` (satisfaction)
- `exports.server.ts` (leads + invoices CSV)
- `forecasting.server.ts` (analytics)
- `reconciliation.server.ts` (phone match — decrypt before compare)
- `routes/api/webhooks/whatsapp.ts` (inbound — now decrypt-aware, last-9-digit compare instead of SQL LIKE)

### Lazy migration

`decryptPII` passes through non-`ENC:` values — legacy plaintext rows remain readable. No blocking
migration. New writes are encrypted; edited leads re-encrypt.

## Governance Structure (Layer 0)

- `.ai/context/` (12 briefs) + `.ai/agents/` + `.ai/VERSION`
- `docs/engineering/CONSTITUTION.md` — execution-safety rules
- `docs/adr/ADR-013..016`
- `docs/runbooks/` (deployment, mpesa-stk-push, whatsapp)
- `docs/evidence/` — 3 verification files
- `docs/releases/`, `CHANGELOG.md`

## Deployment (ADR-016)

### Verified

- `npm run build` → PASS (56s, `BUILD_EXIT=0`)
- Supabase project `kays-wellness-centre` (ref `yztalvyiixvlyxrlfnqn`) ACTIVE_HEALTHY, PG 17.6
- `supabase link` → PASS
- STK code bundled into `.vercel/output` serverless function

### Blocked on owner-held credentials

- `DATABASE_URL` (Supabase DB password), Vercel login, WhatsApp token, M-Pesa Daraja credentials
- Full steps in `docs/runbooks/deployment.md`

## Test Summary

| File | Tests | Coverage |
|------|-------|----------|
| `mpesa-stk-push.test.ts` | 12 | STK full flow + idempotency + RBAC |
| `leads-encryption.test.ts` | 4 | D11 write/read/lazy migration |
| Full suite | **683** | 60 files, all green |

## Files Changed (this sprint)

- New: `src/lib/api/mpesa.server.ts`, `src/routes/api/webhooks/mpesa.ts`,
  `src/__tests__/mpesa-stk-push.test.ts`, `src/__tests__/leads-encryption.test.ts`
- Modified: `env.server.ts`, `logger.server.ts`, `audit.server.ts`, `db.server.ts`,
  `leads.server.ts`, `import.server.ts`, `queue.server.ts`, `dispatch.server.ts`,
  `automation.server.ts`, `marketing/automation.server.ts`, `marketing/reviews.server.ts`,
  `exports.server.ts`, `forecasting.server.ts`, `reconciliation.server.ts`,
  `routes/api/webhooks/whatsapp.ts`
- Docs: ADRs 013–016, decisions.md, db-contracts.md, release-readiness.md, CHANGELOG.md,
  Constitution, runbooks, evidence, .ai/context

## Commits (this sprint)

1. `docs: establish governance structure` (8c6a9a3)
2. `docs: answer pilot-hardening Q&A` (f79fb48)
3. `feat(mpesa): add M-Pesa STK Push automatic payment sync` (7286d91)
4. `feat(pii): wire D11 PII encryption into lead + STK push write/read paths` (1cf9a74)
5. `docs(evidence): record deployment, test suite, and STK/encryption verification` (8e76e9e)

## Next Steps

1. Owner provides credentials → complete live deployment + WhatsApp/M-Pesa verification
2. Onboard Dr. Jackie (pilot-scope-day-1.md workflows)
3. Wire D12 session revocation if scale demands (documented future)