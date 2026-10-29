# Daftari — Launch Readiness for the First 100 Users

**As of v6.12.0.** Written against the code, not against intent. Every claim below is
either verified by a test in this repo or flagged as an operator action.

## Verdict

**Not ready for 100 real users yet — but the reasons are now enumerable and short.**

The core accounting engine is sound: offline-first writes, money as integer cents, RLS
scoped per user, a 30-day trial created by a database trigger with client writes denied,
and a fail-closed entitlement model that unlocks nothing until a fetch proves it. The
v6.12.0 sprint closed the five defects that would have caused real financial harm.

What remains is dominated by things no code can decide: Safaricom credentials, a sandbox
drill, and a real M-Pesa number.

## 1. How long does the sandbox drill take, and what makes it real-world ready?

### The drill

Procedure is in `docs/runbook/daraja-stk-push.md`. Budget **2–4 hours** for the first
run, most of it waiting on Safaricom app provisioning rather than on us.

| Step | Time | Notes |
| --- | --- | --- |
| Safaricom app approval (first time only) | 1–3 business days | Portal review, not engineering time |
| Push a live sandbox STK request | 5 min | M-PESA sandbox app must be installed on the test phone |
| Callback received, income written | seconds | Visible in `daftari_stk_callbacks` + `daftari_transactions` |
| Declined / cancelled by payer | 10 min | Proves the refusal path |
| Wrong-amount forgery attempt | 10 min | Proves `IGNORED` and that no money is written |
| Duplicate callback replay | 5 min | Proves no double credit |
| Database down during callback | 10 min | Proves income-write failure leaves it PENDING + audited |
| Queue backlog (60+ items) | 15 min | Proves the old deadlock is gone |
| Device-loss drill (record 5 sales, kill app) | 10 min | Proves write-through sync |
| **Total engineering time** | **~2 hours** | Plus calendar time for app approval |

### What "ready for real world" actually requires

1. **All four fail-closed drill outcomes observed**, not just the happy path. A drill that
   only proves success has proven nothing about the failure modes.
2. **Reconciliation query returns zero orphans** — every `daftari_stk_requests` row in
   `PAID` has exactly one `daftari_transactions` row, and no `PENDING` row is older than
   the expiry window.
3. **`INCOME_WRITE_FAILED` audit rows are zero** over the drill period.
4. **Real credentials, sandbox→production rotation rehearsed.** The passkey and shortcode
   are *different* in production; an untested rotation means discovering the difference
   during a live payment.
5. **A reconciliation UI or runbook an operator can follow at 2am** with a stuck payment.
   Today this is a SQL query in the runbook — acceptable at 100 users, not at 10,000.

## 2. What the Safaricom sandbox app requires

From the Daraja developer portal, for the **Lipa na M-PESA (STK Push)** product:

- **Sandbox app approval** on the Daraja portal (new app, sandbox environment).
- **Product enabled:** Lipa na M-PESA / STK Push — *not* the C2B/Bill Pay product.
- **Paybill number (shortcode)** and, if using till numbers, the **store number** and
  `DARAJA_STORE_NUMBER`. These exist in sandbox and differ from production.
- **Passkey**, **consumer key**, **consumer secret** — all three sandbox-specific.
- **Callback URL** = `DARAJA_CALLBACK_URL`: a public HTTPS endpoint for
  `lipa-na-mpesa-callback`, reachable from Safaricom's servers. It is **not** a Vercel
  env var and must not be behind auth — the edge always ACKs with `ResultCode: 0` and
  records refusals in `daftari_stk_callbacks` instead.
- **Test MSISDN** with the M-PESA sandbox app installed and signed in. Sandbox pushes do
  not reach real phones; the payer must use the sandbox app to complete them.

These map 1:1 to the `DARAJA_*` block in `.env.example` and operator-guide §2.1.

## 3. What is blocking the first 100 users

### Blockers — cannot launch without these

| # | Blocker | Owner | Fix | Status |
| --- | --- | --- | --- | --- |
| 1 | Branch not merged to `main`; CI deploys only from `main`, so **nothing is live** | Dev | Merge + deploy | **done** — `main` at `bcabc99`, CI `check` + `deploy` green, live bundle serves `6.13.0` |
| 2 | `20260925000000` not applied — clients can still forge PAID rows | Dev | `supabase db push` | **done** (verified live) |
| 3 | Edge Functions not deployed | Dev | `supabase functions deploy` | **done** (3 ACTIVE) |
| 4 | No `DARAJA_*` secrets configured | Operator | Supabase Functions → Secrets | **partial** — key+secret set and validated; passkey/shortcode/store number/callback URL outstanding |
| 5 | Sandbox drill not run | Operator | Runbook, ~2h after approval | blocked on #4 |
| 6 | No real M-Pesa receiving number | Operator | Set `PRICING.MPESA_PAYMENT_NUMBER` | **done** — `254703939236` (v6.14.0) |
| 7 | No legal/privacy pages and no real support contact | Operator | Policy decision, not code | **done** (v6.14.0) — privacy/terms/support screen, `SUPPORT.EMAIL` + `SUPPORT.PHONE`; **legal review still outstanding** |
| 8 | `stk_health` reported a **false all-clear** to the user it was meant to protect | Dev | Add `user_id` + owner RLS to `daftari_stk_callbacks` | **done** (v6.14.0) — `20260926000000`; see below |
| 9 | **Every returning PWA user saw a blank white screen after any deploy** | Dev | Stop serving a precached document; make a missing asset a real 404 | **done** (v6.14.1) — see below |

### High — fix before 100 users, not before 10

- **~~No reconciliation UI.~~** Shipped v6.14.0: `Settings -> Payment reconciliation`
  renders the per-user health counters and the callback trail. A failed check renders an
  explicit error and **suppresses all counters** rather than showing zeros.
- **Returning PWA users got a blank white screen after a deploy.** Found by
  on-device verification on 2026-09-26, immediately after v6.14.0 shipped. Live since
  the PWA was first installed; the deploy only exposed it. The service worker served
  every navigation from a **precached `index.html`**, which names content-hashed
  assets that the deploy had already purged, and Vercel's catch-all SPA rewrite
  answered those missing assets with `index.html` and **HTTP 200** — so the browser
  executed HTML as an ES module, React never mounted, and `#root` stayed empty. The
  `200` is why it was silent: a missing asset should be a 404 the app can react to.
  This would have hit **every existing customer on the first deploy after launch**.
  Fixed in v6.14.1: no document is precached, navigations are `NetworkFirst`,
  `/assets/*` is excluded from the SPA rewrite, and a blank mount now triggers one
  network reload. `src/lib/pwaDeploySafety.test.ts` pins all three configs.
  **Lesson: the PWA deploy path was never exercised. A device check that only
  confirms "the app launched" would have missed this entirely — the app launched,
  and rendered nothing.**
- **`stk_health` was structurally incapable of reporting a callback failure.** Found in
  v6.14.0 by querying the view as a normal client instead of as an operator:
  `daftari_stk_callbacks` had RLS on with **no policies** and **no `user_id`**, so a
  signed-in user saw `ignored_callbacks = 0` where `service_role` saw `3`. The callback
  counters (`income_write_failed`, `ignored_callbacks`) could never be non-zero for a
  user. Fixed by `20260926000000_stk_callbacks_user_scope.sql`, which backfills `user_id`
  and adds an owner policy that also derives visibility from the checkout, so a callback
  inserted without an owner is still shown to the customer who paid. **A monitor that
  cannot fail is worse than no monitor — it manufactures confidence.**
- **Edge Functions have no error tracker.** A failing callback fails silently — Safaricom
  sees `ResultCode: 0` and retries nothing. Mitigated in v6.13.0 by structured JSON logs
  in both edges plus `stk_health`; a real alerting provider is still not wired. An
  exception tracker alone would NOT have caught the `verify_jwt` outage below, because
  the function never ran — it was rejected at the gateway. That is why reconciliation,
  not exception counting, is the primary signal.
- **The onboarding orphan path.** An auth failure mid-onboarding creates a business with
  `user_id: undefined, synced: 0`, repaired only by `adoptOrphanedRecords` on next launch.
  Rare, but it silently drops a business.
- **No E2E coverage of the M-PESA flow.** Playwright suites exist; none exercise a push.
- **The callback is publicly reachable.** It must be deployed `--no-verify-jwt` (Safaricom
  cannot send a JWT), so authorization is by reconciliation, not by a secret. See the
  residual-risk note in `docs/runbook/daraja-stk-push.md` §7.

### Production defects found by deploying, not by testing

Both were invisible to a fully green local suite, because both live at the
*boundary* between our code and the platform. This is the single most important
lesson in this document.

1. **`daftari_stk_requests` had no primary key** while being published to
   `supabase_realtime`. PostgreSQL refuses `UPDATE` on a published table with no
   replica identity, so the callback's mark-PAID step would have failed on
   **every** payment: customer charged, income written, request stuck `PENDING`
   forever. All 8 Deno tests passed because they drive `handleStkCallback`
   against a mock store and never touch the real table.
2. **The callback was deployed with `verify_jwt` on** (the Supabase default).
   Safaricom does not send a Supabase JWT, so every callback was rejected at the
   gateway with `401 UNAUTHORIZED_NO_AUTH_HEADER` before reaching the handler —
   the same total loss of the money path, again invisible to the suite.

Both are fixed (`20260925000002`, and `--no-verify-jwt` in the runbook) and were
confirmed fixed against the live project. The lesson generalises: **a green test
suite proves our logic, not our deployment.** Anything that depends on platform
configuration must be verified by talking to the real thing.

### Corrected: trial expiry needs NO scheduled job

An earlier draft of this document listed "the trial-expiry job has never been run
against real data" as a risk. **That was wrong, and claiming a dependency that
does not exist is worse than omitting it.** Expiry is enforced at *read* time on
both sides, so there is nothing to run:

- **Server:** the `user_subscription` view computes `is_active` per query —
  `(status = 'active') or (status = 'trial' and coalesce(trial_ends_at, now()) >= now())`
  (`20260922000000_create_subscriptions.sql:112-113`). A lapsed trial stops
  unlocking features on the very next read, with no scheduler involved.
- **Client:** `isSubscriptionActive` compares `trial_ends_at` against `now`
  (`src/lib/subscription.ts:16-24`), so the UI lapses on the next poll (60s) or
  foreground refresh.

A cron job would only be *hygiene* — flipping the stored `status` from `trial`
to `expired` so reports read cleanly. That is worth doing eventually, but it is
**not** a launch blocker and must never be described as the thing that enforces
expiry. Nothing depends on it, and no test may assume a job has run.

### Acceptable at this scale

- Manual subscription approval (fine below ~100 users).
- SMS-parse fallback retained alongside STK (ADR-004 still valid for non-push methods).
- No automated reconciliation job (the runbook query is adequate at this size).

## 4. What the ecosystem can do once M-PESA is live

This is the part worth being clear about, because it is larger than "customers can pay
by phone".

- **Every Kenyan vendor accepts card payments today.** Daraja brings the same
  conversion to M-PESA: a vendor's customer pays from the phone already in their hand,
  with no till, no card reader, no bank trip, and no fee for a card machine.
- **The sale books itself.** The callback writes the income server-side, so the ledger
  updates whether or not the vendor's phone has signal. A vendor in a weak-signal market
  is no longer losing sales to connectivity.
- **Trust compounds into credit.** A business with a clean, verified transaction history
  in Daftari is a better credit candidate than one with a shoebox of paper receipts.
  That is the bridge from bookkeeping tool to financial record.
- **Receipts become searchable.** M-Pesa receipts (`mpesa_code`) are captured per
  transaction, so a vendor can answer "did this customer actually pay?" instead of
  arguing from memory.
- **Reconciliation stops being a chore.** Today a vendor reconciles by reading SMS. With
  server-owned STK records, "which pushes are still unresolved?" is a query.
- **The subscription business gets a payment rail.** The same Daraja integration that
  takes a vendor's customer payment can take Daftari's own subscription payment, which
  is why the placeholder paybill mattered so much.

The honest framing: the M-PESA integration is not a feature. It is the difference between
a bookkeeping app that Kenyan vendors tolerate and one they cannot run their shop
without.
