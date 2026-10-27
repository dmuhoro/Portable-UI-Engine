# Vendor payment flow — what actually happens to a vendor's money

This documents the two M-Pesa flows in Daftari **as the code behaves today**, with a
`file:line` for every claim. Where the code does not do what its naming implies, that is
called out in [§7](#7-known-gaps-verified-not-inferred) rather than smoothed over.

Read this before changing anything on the payment path. Two of the gaps in §7 lose a
vendor real money and are not covered by unit tests.

---

## 1. There are TWO M-Pesa flows, and they are unrelated

They share a provider and nothing else. Conflating them is the most common source of
wrong conclusions about this codebase.

| | **Flow A — vendor collects** | **Flow B — vendor pays us** |
|---|---|---|
| Direction | Customer → vendor | Vendor → Daftari |
| Product | Daraja **STK Push** | Manual M-Pesa + **C2B** confirmation |
| Function | `stk-push` | `c2b-confirmation` |
| Server-authoritative? | Yes | Partly — a human verifies |
| Entry point | `src/features/transactions/RecordSale.tsx:338` | `src/screens/UpgradeScreen.tsx:91` |
| Lands in | `daftari_transactions` (income) | `daftari_subscription_requests` |

Flow A is a real integrated payment. Flow B is a claim plus a human (or a C2B query)
confirming it.

---

## 2. Flow A — a vendor collects money from a customer

### 2.1 The vendor's path

1. `Add → Ongeza Mauzo` (card at `src/screens/AddScreen.tsx:38`, routed at
   `src/components/AppShell.tsx:246`) → `RecordSale`.
2. The STK panel only renders when the chosen payment method is STK-eligible —
   `till_number` or `paybill` (`src/features/transactions/RecordSale.tsx:119`,
   `src/lib/constants.ts:172`). A cash-only vendor never sees it.
3. The panel fires a push (`src/features/mpesa/StkPushPanel.tsx:205`) and moves through
   `idle → initiating → pending → paid | failed` (`:25-31`).
4. **While a push is pending, manual Save is disabled** (`:357`). This is deliberate:
   it stops the same sale being written twice, once by the vendor and once by the
   callback (`:120`).
5. The customer's phone shows the M-Pesa prompt. Only they can approve it.
6. The device polls the server every 5s (`STK_POLL_INTERVAL_MS`,
   `src/lib/constants.ts:174`) and gives up locally after 5 minutes
   (`STK_EXPIRE_AFTER_MS`, `src/lib/constants.ts:176`).

### 2.2 The request contract

`amount`, `phone`, `accountReference`, `transactionDesc`, `businessId`, `userId`,
`localId`, `paymentMethod` — declared once in `StkPushInput`,
`supabase/functions/_shared/daraja/protocol.ts:201` (first field `:203`).

`businessId` is compared against `daftari_businesses.local_id`, **not** the row UUID.
Getting this wrong produces a refusal that looks like a payment failure.

### 2.3 The callback

Safaricom POSTs to `DARAJA_CALLBACK_URL` and lands in
`supabase/functions/lipa-na-mpesa-callback/handler.ts`. It resolves to exactly one of
three outcomes, and its guarantees are enumerated in the doc comment at the top of that
file — most importantly:

- It **always** acks `200 / ResultCode 0`, including for refusals. Safaricom retries a
  non-ack forever, so the HTTP response is *not* a signal about money. The
  `stk_callback.verdict` log line is (`:101`).
- The amount comes from **our** request row, never from the callback payload
  (`:68-79`). The payload is attacker-reachable.
- The income row is written **before** the request is flipped to `PAID` (`:109-115`).
  "Paid but unrecorded" is the state that silently loses a sale.
- A duplicate callback is a **success**, not an error — `local_id` is UNIQUE, so a
  Safaricom retry hits a constraint violation and the books are already correct (`:130`).

### 2.4 Where the money lands

`daftari_transactions`, written with the service role (`:115-125`):

```
type: 'income'   category: 'mpesa'   source: 'daraja'   synced: 1
```

**Not** written on that row: `business_id`, `payment_method`, `mpesa_code`. The receipt
number goes on the **request** row instead (`:158-167`). Consequences a vendor will
notice:

- No "M-Pesa" payment-method label on the sale row — the label renders only when
  `payment_method` is set (`src/components/history/TransactionRow.tsx:52`).
- The M-Pesa receipt is visible in the STK panel once paid
  (`src/features/mpesa/StkPushPanel.tsx:87`) and in the reconciliation callback list
  (`src/screens/ReconciliationScreen.tsx:192`), but **not** on the per-sale receipt
  sheet, which renders `mpesa_sender` only
  (`src/components/history/ReceiptSheet.tsx:100`).
- `category: 'mpesa'` is in no category template
  (`src/features/transactions/RecordSale.tsx:42`), so Daraja income does not bucket with
  the vendor's own income categories.

---

## 3. Flow B — a vendor pays Daftari

1. Trial banner → `UpgradeScreen` (`src/components/AppShell.tsx:206`).
2. The vendor pays to the paybill/number and types the receipt themselves
   (`src/screens/UpgradeScreen.tsx:50-77`). **No edge function is called here** — the app
   records the claim and nothing more.
3. `daftari_subscription_requests` row inserted with status `pending`
   (`src/screens/UpgradeScreen.tsx:91`). Self-insert is allowed; self-approval is denied
   (`supabase/migrations/20260922000001_create_subscription_requests.sql:26`).
4. Confirmation arrives two ways:
   - **C2B** — `c2b-confirmation` records the notification, then **independently queries
     Safaricom** and settles only if confirmed
     (`supabase/functions/c2b-confirmation/handler.ts:11`).
   - **Manual** — an admin resolves it in `AdminScreen` via `admin_resolve_subscription`
     (`src/lib/admin.ts`).

Unlike STK, C2B **does** re-query the upstream, so a lost notification is recoverable.

---

## 4. When the network is not there

**STK is server-authoritative; IndexedDB is a mirror only.** Client INSERT/UPDATE/DELETE
on `daftari_stk_requests` is revoked
(`supabase/migrations/20260925000000_stk_requests_server_owned.sql:19`) — all writes go
through the two edge functions.

- Records written locally first, then synced (`src/features/sync/syncQueue.ts:10`), so a
  **sale** is safe offline. An **STK push is not**: there is no local queue for initiating
  one.
- If connectivity drops *after* the push was accepted, the server row and the eventual
  callback still settle correctly. The device keeps polling the mirror and then reports
  *unconfirmed* rather than *failed*, because the money may still be coming
  (`StkPushPanel.tsx:128-140`).
- A vendor with no connectivity at all gets `REMOTE_ERROR`, which the panel renders as
  **"The payer didn't complete the payment"** — see §6.

---

## 5. What the vendor sees when it goes wrong

`src/lib/daraja/client.ts:11-18` defines the codes. The panel maps them at
`StkPushPanel.tsx:218-228`:

| Code | Vendor sees |
|---|---|
| `DAROJA_NOT_CONFIGURED` | "not set up" (correct) |
| `LEDGER_UNAVAILABLE` | dedicated message (correct) |
| `DUPLICATE_PUSH` | dedicated message (correct) |
| `NOT_AUTHENTICATED` | sign-in message (correct) |
| **everything else** | **"The payer didn't complete the payment"** |

That last row is a real defect: an offline `REMOTE_ERROR`, a server-side `INVALID_INPUT`
and a genuine Safaricom decline are **indistinguishable to the vendor**. The copy is
`stk_failed` (`src/i18n/en.json:334`).

---

## 6. Operator: checking and fixing

| Question | Command |
|---|---|
| Is Daraja sane right now? | `./scripts/test-stk-sandbox.sh` |
| What did the function actually resolve? | `./scripts/daraja-diagnostics.sh` |
| Full prompt→approve→callback→books loop | `./scripts/run-stk-drill.sh <msisdn> 1` |
| Callback logic in isolation | `./scripts/verify-stk-callback-e2e.sh` |
| Subscription disputes | Admin → payment queue (`src/screens/AdminScreen.tsx`) |

`scripts/test-stk-sandbox.sh` is the gate: it exits non-zero unless Safaricom returns a
`CheckoutRequestID`. It treats HTTP 200 as **not** success, because the function returns
200 with `result: "FAILED"` on an upstream refusal.

Anomaly counters live in `stk_health` (`supabase/migrations/20260925000001_stk_health_view.sql:5`):
`paid_without_income`, `income_without_request`, `income_write_failed`, `stale_pending`,
`duplicate_credits`, `ignored_callbacks`. Surfaced to the vendor at
`src/screens/ReconciliationScreen.tsx`.

---

## 7. Known gaps (verified, not inferred)

Each of these was read in the code during this pass. None is fixed yet.

### 7.1 A verified payment does not activate the subscription — **money gap**

`daftari_subscriptions` is written in exactly one place: the signup trigger
(`supabase/migrations/20260922000000_create_subscriptions.sql:83`). RLS denies client
insert/update/delete (`:62-71`), and **no RPC updates it after payment** — neither
`settle_subscription_c2b`
(`supabase/migrations/20260926010100_c2b_customer_initiated_payments.sql:60`) nor
`admin_resolve_subscription` touches that table. The app only reads it
(`src/hooks/useSubscription.ts:46`).

So a vendor can pay, have the receipt verified as correct, and still not receive the plan.
An operator must additionally update the row by hand, and **no documented or coded path
does this**. This is the most serious finding in this document.

### 7.2 A lost STK callback is never self-healed

STK has no status-query equivalent to C2B. There is nothing to query until the customer
approves the prompt, so a lost callback leaves the request `PENDING` for a human. The
guarantee is *not* eventual settlement — it is that a callback cannot create unearned
money or record unattributable money.

### 7.3 Offline is reported as "the payer didn't pay" — FIXED in v6.16.0

Every code that failed before Safaricom was reached (`REMOTE_ERROR`, `NOT_AUTHENTICATED`,
`BUSINESS_MISMATCH`, `INVALID_INPUT`) rendered one string blaming the payer. Each now maps
to what actually happened, an offline device is refused before the push, and the generic
fallback was reworded to "We couldn't start this payment". `REMOTE_ERROR` says to check
with the payer, because we genuinely cannot know whether the push landed.

### 7.4 The "stuck" threshold disagreed with itself — FIXED in v6.16.0

The device gave up at 5 minutes while `stale_pending` flagged at 30, so for 25 minutes a
vendor had been told the payment failed while the operator dashboard read "all clear" —
in the one window where the payer may have been charged with the callback lost.

Three changes, because the threshold alone was not the whole defect:

- the view now uses 5 minutes (`supabase/migrations/20260926030001_stk_health_pending_threshold.sql`);
- `stale_pending` was **excluded from `healthNeedsAttention` and shaded amber** — the only
  money counter that could be non-zero on a healthy-looking screen. It now raises an alarm
  and renders red (`src/lib/reconciliation.ts`, `src/screens/ReconciliationScreen.tsx`);
- the copy claimed "Nothing was charged", which is not knowable. It now says we cannot
  tell and to check the customer's M-Pesa statement.

`scripts/verify-stk-callback-e2e.sh` BRANCH 4 reads `STK_EXPIRE_AFTER_MS` from
`constants.ts` and asserts a request one minute past the device's give-up point is flagged
while one minute before it is not, so the two cannot drift apart again unnoticed. Verified
load-bearing by changing the constant to 1 minute: the branch fails and exits non-zero.

### 7.5 The SMS parser conflated the receipt code with the payer's phone — FIXED in v6.16.0

For the two "received from …" patterns, `code` was capture group 3 — the **sender's phone
number** (`src/features/sms/parseMpesa.ts:144,159`) — while every other pattern used
`extractCode()`. The same value was then written to two places
(`src/features/sms/SMSParser.tsx`):

- `daftari_transactions.mpesa_code`, where an operator matches against the Till statement,
  so a phone number in that column is unmatchable;
- `daftari_customers.phone`, so for every pattern that *does* carry a code, a receipt code
  like `SFG9P8D1A2` was stored as the customer's phone number.

`ParsedMpesa` now carries `code` and `phone` as separate fields, patterns A and B use
`extractCode()`, and the customer record is written from `phone`. The column still has no
format constraint (`supabase/migrations/20260606101253_add_mpesa_fields.sql:2`); the parser
test now asserts across all eight patterns that a 9-13 digit run never appears as a code,
which is what catches this if it is reintroduced.

Checked production for damage: **no rows affected.** No transaction carries a
phone-shaped `mpesa_code` and no customer carries a code-shaped `phone`, so no data repair
was needed. The defect was latent.

### 7.6 Dead and misleading declarations

- `DARAJA.CB2_CALLBACK_FUNCTION` (`src/lib/constants.ts:170`) has zero references; the
  real source of truth is the `DARAJA_CALLBACK_URL` secret.
- `INCOME_CATEGORIES` (`src/lib/constants.ts:156`) is referenced by nothing.
- `daftari_payment_confirmations` (`supabase/migrations/20260923000001_admin_ceo_dashboard.sql:69`)
  is named like an active confirmation registry and is referenced by nothing.
- `DB.VERSION = 8` (`src/lib/constants.ts:39`) vs the Dexie constructor's `version(7)`
  (`src/lib/db.ts:182`). Affects backup `_version` metadata, not the schema.

### 7.7 Test coverage is unit-only, and that has already cost us

There are no e2e or multi-device tests touching mpesa/daraja/stk. The canonical example of
what that misses: `daftari_stk_requests` shipped **without a primary key** while in the
realtime publication, so the callback's `PENDING → PAID` update failed with *"cannot
update table … does not have a replica identity"*. Every payment would have been charged,
income written, and the request stuck `PENDING` forever — and a mock-store unit suite
passed throughout. Fixed in
`supabase/migrations/20260925000002_stk_requests_primary_key.sql`.

---

## 8. Verifying this document

Claims here are checkable. To re-verify the flow:

```bash
npm run typecheck && npm run lint && npm run test:run   # 692 tests
deno test --allow-env supabase/functions/**/*_test.ts    # edge function logic
./scripts/verify-stk-callback-e2e.sh                     # callback settlement
./scripts/test-stk-sandbox.sh                            # live Daraja gate
```

The last one **currently fails by design** — the sandbox passkey is 89 characters where
Daraja issues 32 or 64, so Safaricom refuses every push with `400.002.02`. See
`docs/runbook/daraja-stk-push.md` §2.
