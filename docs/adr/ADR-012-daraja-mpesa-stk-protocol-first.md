# ADR-012: Daraja MPESA — protocol-first, fail-closed edges (STK Push live)

**Status:** Accepted (implements the deferred Phase 2 from ADR-004)
**Date:** 2026-09-11

## Context

ADR-004 deferred Daraja to Phase 2 because the pilot (Hellen) had no till number. The
SMS-parsing MVP proved the domain and grew a real usage shape: vendors *do* collect M-Pesa
payments, and the app now targets till/paybill holders (DSTV-style niche use). The owner
wants the "SMS parse → manual paste" friction removed where a till number exists — without
ever letting a third party cause an unverifiable income write.

Daraja's contract is exacting and failure modes are sharp: an amount mismatch, a phone
rewrite, a timestamp in the wrong timezone, or a forged callback can each mint a **fake
money claim** or silently drop a *real* payment. The MVP SMS path and the device repository
already mirror `daftari_transactions`; the income write must not branch into new, untested
rules at the boundary.

## Decision

Ship Daraja as **two Deno edge functions backed by one tested protocol module**, wired as
mirrors — not as ad-hoc fetch code embedded in the React app:

- `supabase/functions/_shared/daraja/protocol.ts` — the single source of truth: Daraja
  types (`DarajaStkConfig`, `StkPushInput`, `StkPushPayload`, `StkPushEnvelope`),
  phone normalization to 254, KES range enforcement (1–150,000 whole shillings), the
  `AccountReference`/`TransactionDesc` length caps, Safaricom timestamp + STK password
  builders, `buildStkPushPayload`, `parseInitiateResponse`, `parseStkCallback`,
  `buildCallbackVerdict`. Imported by BOTH edges and by 32 vitest tests.
- `stk-push/index.ts` — **JWT-authenticated** initiate edge. Verifies the caller owns the
  business (`daftari_businesses.user_id`), refuses (`503 DARAJA_NOT_CONFIGURED`) when any
  Daraja env var is missing, normalizes the phone, builds + signs the payload via the
  protocol, OAuths (client_credentials) then posts `processrequest`, and mirrors a
  `PENDING` row into `daftari_stk_requests` so the device pull converges.
- `lipa-na-mpesa-callback/index.ts` — **public** Safaricom callback edge. Always ACKs
  `{ ResultCode: 0 }` (Daraja requires it to stop retrying — a failure ack would loop),
  but the money write happens ONLY through `buildCallbackVerdict` against the PENDING
  request row: amount must match, receipt must be present, request must be `PENDING`.
  Verdict `PAID` flips the request to `PAID`; every callback (PAID/FAILED/IGNORED) is
  appended to `daftari_stk_callbacks` for forensic audit. **A forged/mismatched callback
  never writes money — it lands in the audit table as IGNORED.**

Every edge is `deno check`-ed (and that check is a real npm/CI gate via
`check:functions`), matching the protocol's tested behavior.

## Consequences

**Positive:**
- Both edges are type-checked against the SAME protocol the vitest suite trusts — a
  callback cannot silently diverge to "trust the wire".
- Fail-closed: missing `DARAJA_*` env → `503 DARAJA_NOT_CONFIGURED`; business mismatch →
  `403 BUSINESS_MISMATCH`; every callback verdict is audited regardless of outcome.
- The device keeps its current sync shape: it pulls the `PENDING` request, the PAID
  callback completes it, and `daftari_transactions` income is written by the app's
  existing mirror path — no new client-side fetch branch.
- `source = 'daraja'` slot reserved in ADR-004 is now actually consumable.

**Negative:**
- No Safaricom registration-only offline fallback: if the vendor has no till/paybill, the
  SMS-parse path (ADR-004) remains the primary collection mechanism. Daraja requires a
  registered shortcode — Daftari can't conjure one.
- Requires real Daraja sandbox credentials to test the live OAuth+processrequest round
  trip; tests use a mocked upstream because no CI can reach the real sandbox.

## Supersedes
This ADR supersedes **ADR-004**'s Phase 2 deferral for the Daraja C2B/STK decision
(decision itself stood; the "deferred to Phase 2" part is now shipped). SMS Parsing remains
the default for unregistered numbers; Daraja STK is the path when a till number exists.

## Rollback
Remove the two edge functions + the `daftari_stk_requests`/`daftari_stk_callbacks` tables,
and the app keeps working exactly as before (SMS parsing; the `source` field stays neutral).
