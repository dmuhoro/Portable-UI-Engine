# ADR-015 — PII Encryption Wired Into Write/Read Paths (D11 Reversal)

**Status:** Accepted
**Date:** 2026-08-25
**Supersedes:** D11 descope (decisions.md) — partially reversed
**Applies to:** kays-wellness-centre data layer

---

## Context

D11 (Sprint 34) descoped PII encryption: the infrastructure (`encryption.server.ts`, AES-256-GCM,
per-org derived keys, key rotation, `ENC:` marker) was built and tested (8 adversarial tests) but not
wired into write paths. PII (name, phone, email) is stored in plaintext.

The product is moving to real-money pilot with a real patient base. Storing patient names/phones in
plaintext when charging real money is an avoidable exposure. The encryption infrastructure already
exists and is tested — the remaining cost is the wiring.

## Decision

1. **Encrypt on write, decrypt on read** for the highest-value PII surfaces:
   - `clinic_leads`: `name`, `phone`, `email` — encrypt before INSERT (all write paths:
     `submitLead`, `updateLead` when these fields change), decrypt after SELECT (read paths:
     `fetchLeads`, dispatch lookups, reconciliation phone matching).
   - `mpesa_stk_push_requests.phone` (new table) — encrypt on insert, decrypt on read/display.
2. `encryptFields`/`decryptFields` helpers are used so the change is localized.
3. `decryptPII` already passes through non-`ENC:` values — old plaintext rows remain readable
   (no blocking migration required). A **lazy migration** path: any read that encounters plaintext
   returns it as-is; optionally re-encrypt on write.
4. Logging: never log plaintext PII; keep using redacted key names (`phone`, `email`, `name`).
5. Tests: add coverage that (a) INSERT stores `ENC:` values, (b) SELECT returns plaintext,
   (c) old plaintext rows still read correctly, (d) key rotation keeps decrypting.

## Consequences

- Patient PII is encrypted at rest for new writes.
- The WhatsApp dispatch + reconciliation phone matching must handle both plaintext and encrypted
  values — matching is done on the **decrypted** value (read path decrypts first).
- `docs/db-contracts.md` notes the encrypted columns.

## Scope Boundary

- Wired THIS sprint: `clinic_leads.name/phone/email` (encrypt on write, decrypt on read across all
  paths), `mpesa_stk_push_requests.phone` (encrypt on insert, decrypt in the list DTO).
- Decrypt sites: `fetchLeads`, `queue.server.ts` (WhatsApp), `dispatch.server.ts` (WhatsApp),
  `api/automation.server.ts` (WhatsApp ×3), `marketing/automation.server.ts` (retention),
  `marketing/reviews.server.ts` (satisfaction), `exports.server.ts` (CSV), `forecasting.server.ts`
  (analytics), `reconciliation.server.ts` (phone match — decrypt before compare),
  `routes/api/webhooks/whatsapp.ts` (inbound match — decrypt-aware).
- Encrypt sites: `submitLead`, `bulkImportLeads`, `mpesa.initiateStkPushRaw` (phone).
- NOT wired this sprint: `message_ledger.body`, `invoices.notes`, `feedback_responses.comment`,
  `audit_logs.metadata`. Those remain plaintext (lower-value, and audit logs are append-only).
- `invoices`/`payments` amounts are NOT PII (they are the money model; leave unencrypted for
  accounting/reconciliation queries).

## Lazy Migration

- `decryptPII` passes through non-`ENC:` values, so existing plaintext rows remain readable.
- No blocking migration. New writes are encrypted; old reads still work. Optionally re-encrypt on
  write (all write paths encrypt unconditionally, so any lead that is edited becomes encrypted).

## Alternatives Rejected

- **Keep D11 descoped** — rejected because the product now stores real patient data for real money.
- **Full encrypt-everything migration** — rejected: blocking migration on all tables is high-risk
  for the pilot; lazy path (read-through plaintext) is safer and matches existing tested helpers.