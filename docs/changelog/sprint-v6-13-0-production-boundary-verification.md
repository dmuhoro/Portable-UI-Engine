# Sprint v6.13.0 — Production boundary verification

**Date:** 2026-09-25
**Branch:** `feat/subscription-billing`
**Previous:** v6.12.0 (`3a84ac7`)
**Outcome:** Two production-breaking defects found and fixed; the money path is
deployed and reconciled, but the end-to-end payment drill remains blocked on
Daraja portal credentials.

---

## Why this sprint existed

v6.12.0 shipped a fully green suite: 586 Vitest tests, 8 Deno tests, typecheck,
lint, i18n parity, and a production build. Then the code was deployed for real —
and the M-PESA money path was broken in two independent ways. Neither defect was
reachable by a local test.

This is the finding that shaped the sprint: **a green suite proves our logic, not
our deployment.** Both defects were found by talking to the live project.

---

## Defect 1 — the callback could never confirm a payment (no primary key)

`daftari_stk_requests` was created without a `PRIMARY KEY`; it had only `UNIQUE`
constraints on `checkout_request_id` and `local_id`. The table was also added to
the `supabase_realtime` publication.

Those two facts together break the money path. PostgreSQL's default replica
identity resolves `UPDATE`/`DELETE` through a **primary key** — a unique
constraint is not a substitute. So on a published table with no PK:

```
ERROR: cannot update table "daftari_stk_requests" because it does not have a
       replica identity and publishes updates
```

That error fires on the callback's core operation: flipping `PENDING` → `PAID`.
Every real payment would have been charged by the customer, income written, and
the request left in `PENDING` permanently.

**Why 8 passing Deno tests missed it:** they drive `handleStkCallback` against an
in-memory `StkCallbackStore` double. No real table is ever touched, so a schema
defect is invisible by construction.

**Found by:** executing the migrations against a real PostgreSQL 16 in Docker
while verifying the money path and the RLS boundary, rather than trusting the
green suite.

**Fix:** `20260925000002_stk_requests_primary_key.sql`
- `REPLICA IDENTITY FULL` **first** — the backfill `UPDATE` is itself blocked
  until a replica identity exists, so ordering it last is a chicken-and-egg trap.
- Then add `id uuid default gen_random_uuid()`, backfill, `SET NOT NULL`, add the PK.
- Idempotent (guarded by a `contype = 'p'` check) and it raises an exception if the
  PK is still absent, so a future regression fails at migration time rather than at
  3am during a live payment.

**Verified in production:** `daftari_stk_requests_pkey PRIMARY KEY ("id")` and
`REPLICA IDENTITY FULL` both present in the live schema dump.

## Defect 2 — every callback rejected at the gateway (`verify_jwt`)

Supabase Edge Functions verify a JWT at the gateway **by default**. Safaricom
does not send a Supabase JWT and cannot be configured to send custom headers, so
the deployed callback answered:

```
HTTP 401 {"code":"UNAUTHORIZED_NO_AUTH_HEADER","message":"Missing authorization header"}
```

before the handler ever ran. Same total loss of the money path, same invisibility
to the suite — the function was not failing, it was never being called.

**Fix:** deploy `lipa-na-mpesa-callback --no-verify-jwt`, now documented as
mandatory in the runbook with the reasoning and the residual risk. `stk-push`
deliberately keeps JWT verification because the signed-in app calls it.

**Verified in production:** malformed payload now returns
`{"ResultCode":0,"ResultDesc":"Success"}` (the always-ack, so Safaricom does not
retry-loop), and a forged callback with an unknown `checkout_request_id` was
audited `IGNORED / UNKNOWN_REQUEST` with zero money moved.

**Security model after the change:** authorization is by reconciliation, not by a
shared secret. The handler requires a known `checkout_request_id`, a `PENDING`
request, an exact amount match, and a receipt number. The endpoint is publicly
reachable, so the runbook states the residual risk plainly instead of implying
the callback is "authenticated".

## Hardening 3 — `service_role` grants made explicit

`20260925000000` revokes client writes but originally relied on Supabase's
default grants to leave the Edge Functions working. `BYPASSRLS` bypasses
row-level *policies*; it does **not** bypass table-level `GRANT`/`REVOKE`
permission checks. An ungranted `service_role` was observed denied writes in a
real Postgres even with RLS bypassed. The migration now grants explicitly, so
the money path does not depend on a platform default.

## Observability — logs and `stk_health`

Chose structured logging and a health view over an exception tracker, deliberately.
The callback returns `200` for every outcome by design, so a tracker would report
a healthy service while money quietly failed to post — false confidence, the exact
failure this sprint is correcting. Defect 2 is the proof: an exception tracker would
have shown nothing, because the function never ran.

- `_shared/daraja/logging.ts` — one JSON line per event, with phone redaction.
- `20260925000001_stk_health_view.sql` — `select * from stk_health;` returns six
  should-be-zero counts, each a named failure mode.
- 2 new Deno tests assert the log line is actually emitted on the failure paths,
  so the observability claim is itself tested rather than asserted.

---

## Production evidence

| Check | Result |
| --- | --- |
| `supabase migration list` | all 4 applied remotely |
| `supabase functions list` | 3 functions `ACTIVE` |
| Live schema dump | PK + `REPLICA IDENTITY FULL` present |
| Grants on `daftari_stk_requests` | `authenticated`/`anon` have no INSERT/UPDATE/DELETE; `service_role` has ALL |
| `select * from stk_health` | all critical columns `0` |
| Forged callback | audited `UNKNOWN_REQUEST`, no money moved |
| Daraja sandbox OAuth | `HTTP 200`, access token granted (3599s) |
| CLI | upgraded v2.115.0 → v2.118.0 (npm global; **not** in apt) |

---

## Still open — honestly

- **No end-to-end payment drill.** `DARAJA_PASSKEY`, `DARAJA_SHORTCODE`,
  `DARAJA_STORE_NUMBER`, and the public HTTPS `DARAJA_CALLBACK_URL` are all
  outstanding. `stk-push` correctly fails closed with `503 DARAJA_NOT_CONFIGURED`.
  The happy path is **unproven**, and no amount of local testing substitutes.
- **No real M-PESA receiving number** (`PRICING.MPESA_PAYMENT_NUMBER` is `''`, and
  `UpgradeScreen` refuses payment when unconfigured).
- **No reconciliation UI**; `stk_health` is the interim answer.
- **No alerting.** Logs and the view exist; nothing pages a human.
- **Legal/privacy pages and a real support contact** — operator policy decisions.

## Credential hygiene note

Sandbox `DARAJA_CLIENT_KEY` / `DARAJA_CLIENT_SECRET` were handled in-memory and
via a temp file outside the repo that was shredded after use; no secret is
tracked. They were shared in plaintext chat during this sprint, so **rotate before
production use** even though sandbox keys are low-risk. Keep production keys out
of chat and out of any tracked file — Supabase secrets only.

## Carried forward

- Re-run the full fail-closed drill set in the runbook §4 once credentials land —
  a happy-path-only drill is not sufficient.
- Add E2E coverage for the push flow; Playwright exists but never exercises a push.
- Watch for the onboarding-orphan path (a business with `user_id: undefined`).
