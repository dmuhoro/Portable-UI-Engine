# ADR-014 — M-Pesa STK Push Adoption (greenleaf as Schema Donor)

**Status:** Accepted
**Date:** 2026-08-25
**Applies to:** kays-wellness-centre money path

---

## Context

The pilot decision (confirmed by product owner) is **CSV reconciliation only** for day-1, but the
product owner explicitly asked for **automatic payment sync** — reducing manual payment recording and
letting M-Pesa transactions sync automatically. That is exactly what STK Push provides: the clinic
initiates a payment request to the patient's phone; Safaricom calls back on success; the platform
records the payment and marks the invoice paid without manual entry.

greenleaf-dental already contains a proven STK Push schema + Daraja API pattern (see
`supabase/migrations/20260319_mpesa_stk_push.sql`, `app/api/payments/stkpush/route.ts`,
`app/api/payments/stkpush/callback/route.ts`). This is the donor.

## Decision

1. Port the STK Push flow into kays-wellness-centre with kays conventions:
   - Table `mpesa_stk_push_requests`, **`organization_id`-scoped** (not `clinic_id`), linked to
     `invoices` and `clinic_leads`.
   - New `src/lib/api/mpesa.server.ts` with:
     - `initiateStkPush(orgId, { invoiceId, amount, phone, accountRef })` — Daraja oauth token +
       STK processrequest, rate-limited `mpesa_stk:${orgId}` (10/60s), inserts a pending request row.
     - `handleStkCallback(payload)` — resolves org from the request row by `CheckoutRequestID`,
       verifies callback secret, updates status, and on success records the payment idempotently via
       the existing `recordPayment` helper (same locks, same receipt-number minting).
   - Webhook route `src/routes/api/webhooks/mpesa.ts` (h3 eventHandler like `whatsapp.ts`).
2. Callback security: `MPESA_CALLBACK_SECRET` check via `x-callback-secret` header or `?secret=`.
3. Idempotency: unique `(organization_id, checkout_request_id, mpesa_receipt_number)`; replayed
   callback returns `{ ok: true, idempotent: true }`.
4. Env vars (Zod schema): `MPESA_BASE_URL` (default sandbox), `MPESA_CONSUMER_KEY`,
   `MPESA_CONSUMER_SECRET`, `MPESA_SHORTCODE`, `MPESA_PASSKEY`, `MPESA_CALLBACK_URL`,
   `MPESA_CALLBACK_SECRET`, `MPESA_TRANSACTION_TYPE` (default `CustomerPayBillOnline`).
5. CSV reconciliation stays (ADR supports both paths; STK is the automatic one).

## Consequences

- Payments sync automatically when a patient pays via STK push — no manual entry.
- CSV reconciliation remains for walk-in/deposit reconciliation.
- New money path requires: tests (initiate, callback, idempotency, RBAC gate), env-guard, and
  `db-contracts.md` update (new table + writers) — per AGENTS.md rules 2, 3, 8.

## Alternatives Rejected

- **STK only, drop CSV** — loses manual reconciliation for deposits/partials; CSV is already tested
  and the day-1 decision.
- **Full Daraja invoice-pay via APIs (C2B)** — more complex, needs paybill registration with
  Safaricom; STK push is the faster, well-trodden path.