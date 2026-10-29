# Runbook: Daraja STK Push (Lipa na M-PESA) — operations + fail-closed drill

**Scope:** initiate push (`stk-push` edge), ingest the Safaricom callback
(`lipa-na-mpesa-callback` edge), audit every verdict, reconcile money.

## 1. Topology (what is where)

- `stk-push` — JWT edge (the app calls it). Builds payload from protocol, OAuths
  `client_credentials`, POSTs `processrequest`, mirrors a `PENDING` row to
  `daftari_stk_requests`. Never pushes when `DARAJA_*` is incomplete → `503 DARAJA_NOT_CONFIGURED`.
- `lipa-na-mpesa-callback` — public edge (Safaricom calls it). Always ACKs `ResultCode:0`
  (stops retries). Money writes ONLY via `buildCallbackVerdict` against the PENDING request.
- `daftari_stk_requests` — PENDING row (checkout_request_id unique, local_id unique, user/business/amount/phone).
- `daftari_stk_callbacks` — forensic audit of every callback (verdict PAID/FAILED/IGNORED + reason + payload jsonb).

## 2. Environment (Supabase Functions → Secrets)

See operator-guide §2.1 table. `stk-push` resolves the merchant at runtime from
`DARAJA_MERCHANT_KIND` and **fails closed** if the pair it needs is absent, so
these are not optional extras.

Common (both kinds):

| Secret | Meaning |
| --- | --- |
| `DARAJA_ENV` | `sandbox` or `live`. Safaricom issues a **separate** key, secret, passkey and shortcode per environment. |
| `DARAJA_CLIENT_KEY` / `DARAJA_CLIENT_SECRET` | OAuth `client_credentials` pair. Server-side only — never in the Vite bundle. |
| `DARAJA_PASSKEY` | Issued on the product's credentials page in the Daraja portal. Not derivable from any other value. |
| `DARAJA_CALLBACK_URL` | Public URL of `lipa-na-mpesa-callback`. |
| `DARAJA_MERCHANT_KIND` | `till` or `paybill`. |

Routing — the two kinds are **not** interchangeable, and this is the single
most common cause of an upstream `502` on a push that otherwise looks correct:

| Kind | `BusinessShortCode` | `PartyB` | `TransactionType` | Required secrets |
| --- | --- | --- | --- | --- |
| `till` | `DARAJA_STORE_NUMBER` | `DARAJA_TILL_NUMBER` | `CustomerBuyGoodsOnline` | `DARAJA_STORE_NUMBER`, `DARAJA_TILL_NUMBER` |
| `paybill` | `DARAJA_PAYBILL_NUMBER` | `DARAJA_PAYBILL_NUMBER` | `CustomerPayBillOnline` | `DARAJA_PAYBILL_NUMBER` |

Notes that cost real debugging time:

- There is **no** `DARAJA_SHORTCODE` secret in the current contract. Earlier
  revisions of this runbook listed one; it is unused, and setting it changes
  nothing. The store/paybill numbers above are what populate the payload.
- `DARAJA_TILL_NUMBER` is required for a till and is **not** optional. The
  resolver falls back to the store number if it is absent, which produces a
  well-formed request that Safaricom rejects instead of a local error.
- Confirm the exact `BusinessShortCode` and passkey shown for **this**
  environment's product page. Store number, till number and operator ID are
  related but not interchangeable with the Daraja shortcode.
- Check the current state at any time with `scripts/daraja-preflight.sh`, which
  exits non-zero while anything required is missing, and run the real flow with
  `scripts/run-stk-drill.sh <msisdn> <amount>`.

## 2b. STK Push vs C2B — which product does what

Safaricom has several products and they are not interchangeable. Picking the
wrong one is the most common reason a payment integration "works" in a demo and
never settles in production.

| | STK Push (Lipa na M-PESA Online) | C2B (registerurl) | B2B |
| --- | --- | --- | --- |
| Who starts | The **business** pushes a prompt | The **customer** pays from their own M-PESA app | Business pays business by account number |
| Customer sees | An approval prompt | Their normal M-Pesa app | An approval prompt |
| We need to register a URL? | No | **Yes** — ConfirmationURL | No |
| Needs a shortcode | No (store/till/paybill in the request) | **Yes** | Recipient account number |
| Callback | We already hold a PENDING request to correlate | A new payment we never asked for | Correlate by account |
| Daftari use | Collecting from a business's own customers, at checkout | **A user paying Daftari for a subscription** | Paying a supplier from the app |

The distinction that matters operationally: STK Push is safe to trust because we
created a PENDING row first, so a callback always has a request to match
against. C2B has no such row — the money simply arrives — so a C2B payload is a
**claim from an anonymous caller** and is only believed after Safaricom's
Transaction Status Query API confirms the TransID. Never settle a C2B
notification on the strength of the POST body alone.

### C2B setup

```bash
# 1. One-time: register our callback URL. Needs the key/secret in your shell.
export DARAJA_CLIENT_KEY='...' DARAJA_CLIENT_SECRET='...'
scripts/register-c2b-urls.sh <c2b-shortcode>
unset DARAJA_CLIENT_KEY DARAJA_CLIENT_SECRET

# 2. Tell the function which shortcode is ours (done: 3631767).
supabase secrets set --project-ref <ref> C2B_SHORTCODE=<c2b-shortcode>
```

Registration returns `{"Status":"Success"}`. If it is refused, the usual cause is
that the shortcode is not registered for C2B: **a Till number is generally not a
C2B shortcode**, because Safaricom issues a Paybill for C2B. Check the Daraja
dashboard for the C2B product's own shortcode.

Audit trail: `daftari_c2b_notifications` — one row per notification Safaricom
sent, with `safaricom_confirmed`, the verdict, and the raw payload. `UNVERIFIED`
means we could not confirm it and **nothing was settled**; those rows are the
worklist for anyone reconciling by hand.

## 3. Success path (sandbox drill)

1. In the app → Settings → confirm the business profile has a **till/paybill number** (source).
2. Trigger Lipa na M-PESA on a sale → the app calls `stk-push` → gets
   `{ outcome:'ok', checkoutRequestId, merchantRequestId }`.
3. Verify the mirror: `select * from daftari_stk_requests where status='PENDING'` has the row.
4. Complete the payment on the sandbox phone → Safaricom POSTs the callback.
5. Assert money: `select verdict, mpesa_code, amount from daftari_stk_callbacks order by created_at desc limit 1`
   → `verdict='PAID'`, `amount` matches, `mpesa_code` present.
6. Make the app pull (reconnect) → the transaction shows as income, `source='daraja'`.

**Gate:** if the drill ends in `PAID` + matching income, production rotation is safe (§6).

**Time budget:** ~2 hours of engineering time for a full drill, on top of 1–3 business days
for Safaricom sandbox app approval (portal review, not our queue). Do not start the clock
on production rotation until the app is approved and the M-PESA sandbox app is installed
and signed in on the test phone — sandbox pushes do not reach real handsets.

## 4. Fail-closed paths — the drill that must NOT pass

These are the drills that matter. A run that only proves the happy path has proven nothing
about whether a vendor can be harmed.

- **Unconfigured:** unset one `DARAJA_*` secret → `stk-push` returns `503 DARAJA_NOT_CONFIGURED`;
  NO row is written to the canvas, NO push. This is the fail-closed default — never a silent 200.
- **Ledger unavailable:** block the `daftari_stk_requests` write (e.g. revoke the grant) →
  `stk-push` returns `503 LEDGER_UNAVAILABLE`, **not** `ok`. The client says "we could not
  record the payment request" rather than polling a row that does not exist. Expected.
- **Duplicate push:** re-send the same `localId` while it is still PENDING → `409 DUPLICATE_PUSH`.
  The payer is not charged twice. Expected.
- **Business mismatch:** a device user calls `stk-push` for a business they don't own →
  `403 BUSINESS_MISMATCH`.
- **Forged / amount-mismatched callback:** POST a fake callback with wrong amount →
  verdict `IGNORED`, reason `AMOUNT_MISMATCH`, written to `daftari_stk_callbacks`; request row
  stays `PENDING`; **no money write**.
- **Unknown checkout:** callback for a request we don't hold → `IGNORED/UNKNOWN_REQUEST` audit only.
- **Duplicate callback replay:** POST the same valid PAID callback twice → the second insert
  hits the `local_id` unique constraint (`23505`) and is treated as *already credited*.
  Exactly **one** `daftari_transactions` row. Expected.
- **Database down during callback:** make `daftari_transactions` reject writes → the request
  must stay **PENDING** (never PAID) and an `INCOME_WRITE_FAILED` audit row must appear.
  This is the money-without-books guard; if the row ever shows PAID with no income, stop
  and roll back. Expected.
- **Client cannot forge state:** from the browser console, `update daftari_stk_requests set
  status='PAID'` as the signed-in user → must be rejected by RLS (migration
  `20260925000000`). Expected.

**Reconciliation after the drill** — run before production rotation, not after an incident:

```sql
-- Must be zero: payments marked settled with no income row (money-without-books)
select r.checkout_request_id, r.amount
from daftari_stk_requests r
left join daftari_transactions t on t.local_id = r.local_id
where r.status = 'PAID' and t.local_id is null;

-- Must be zero: income rows with no matching request (money-from-nowhere)
select t.local_id, t.amount
from daftari_transactions t
left join daftari_stk_requests r on r.local_id = t.local_id
where t.source = 'daraja' and r.local_id is null;

-- Must be zero: unrecorded payment write failures needing a human
select * from daftari_stk_callbacks where ignore_reason = 'INCOME_WRITE_FAILED';

-- Informational: still-unresolved pushes
select status, count(*) from daftari_stk_requests group by status;
```

## 5. Common incidents

| Symptom | Check | Fix |
|---------|-------|-----|
| Push returns 503 DARAJA_NOT_CONFIGURED | Secrets missing/DARAJA_ENV wrong | Add all secrets; `npx supabase functions deploy` |
| Callback floods (repeated same checkout) | Idempotent — same verdict row | Safe to ignore; Safaricom retries are a non-issue |
| PAID verdict but no income row | The callback writes income **before** marking PAID, so this state means the income write failed | Check for an `INCOME_WRITE_FAILED` audit row; the request stays PENDING on purpose. Fix the DB, then replay the callback — the duplicate is absorbed by the `local_id` unique constraint |
| Amount mismatch in verdict | Callback amount differs from request.amount | Do the drill over; never "auto-fix" — audit is authoritative |
| Callback returns 401 UNAUTHORIZED_NO_AUTH_HEADER | Deployed without `--no-verify-jwt` — Safaricom cannot send a JWT | Redeploy the callback with the flag (§7). **Every payment is being rejected while this is true** |
| Customer charged, request stuck PENDING, callback never logged | Same cause as above, or callback URL misconfigured in the Daraja portal | Fix the flag/callback URL, then replay from the Daraja portal; the handler is idempotent |

## 6. Sandbox→production rotation

```bash
# 1. Sandbox drill passes — including EVERY fail-closed path in §4 and a clean
#    reconciliation run. A happy-path-only drill is not sufficient.
# 2. Obtain the PRODUCTION Daraja app credentials from the Safaricom portal.
#    These are DIFFERENT values from sandbox and must all be replaced together:
#      DARAJA_CLIENT_KEY, DARAJA_CLIENT_SECRET, DARAJA_PASSKEY,
#      DARAJA_SHORTCODE, DARAJA_STORE_NUMBER, DARAJA_ENV
#    Reusing a sandbox key against production fails authentication; a sandbox
#    shortcode against production sends the payer's money nowhere.
#    Keep DARAJA_CALLBACK_URL AS-IS (the public URL is env-agnostic).
supabase functions deploy stk-push lipa-na-mpesa-callback --project-ref <ref>
# 3. First real KES push is the DRY-RUN: 1 unit, a phone you control.
#    Confirm callback PAID + income AND re-run the reconciliation queries in §4
#    before telling anyone the feature is live.
```

**Rule: production rotation is a separate, explicit step — never bundle it with a deploy.**
The repo ships `DARAJA_ENV=sandbox` by default; a production flip is a deliberate operator
action documented here only.

## 7. Deployment — the `--no-verify-jwt` flag is MANDATORY

```bash
# Migrations FIRST. The callback's mark-PAID update cannot succeed without the
# primary key added by 20260925000002.
supabase db push

# stk-push keeps JWT verification (the signed-in app calls it).
supabase functions deploy stk-push --project-ref <ref>

# lipa-na-mpesa-callback MUST be deployed with --no-verify-jwt. See below.
supabase functions deploy lipa-na-mpesa-callback --no-verify-jwt --project-ref <ref>
```

### Why `--no-verify-jwt` is not optional

Supabase Edge Functions verify a JWT at the gateway by default. **Safaricom does
not send a Supabase JWT** — it POSTs only the Daraja callback payload and cannot
be configured to send custom headers. So with the default setting, every
callback is rejected at the gateway with:

```
HTTP 401 {"code":"UNAUTHORIZED_NO_AUTH_HEADER","message":"Missing authorization header"}
```

before reaching the handler. The effect is silent and severe: the customer is
charged, income is never written, and the request stays `PENDING` forever. Every
existing test still passes, because the unit tests call `handleStkCallback`
directly and never traverse the gateway. Only a real request to the deployed
URL reveals it.

**Verified on production 2026-09-25:** before the flag the callback returned
`401 UNAUTHORIZED_NO_AUTH_HEADER`; after redeploying with `--no-verify-jwt` a
malformed payload correctly returned `{"ResultCode":0,"ResultDesc":"Success"}`.

### What replaces gateway auth for the callback

Authorization moves entirely into the handler, which refuses anything it cannot
reconcile against the real `daftari_stk_requests` row:

| Check | Verdict | Effect |
|-------|---------|--------|
| Payload unparseable | `IGNORED / MALFORMED` | acked, audited, no money |
| `checkout_request_id` not in our table | `IGNORED / UNKNOWN_REQUEST` | acked, audited, no money |
| Request already terminal (not `PENDING`) | `IGNORED / TERMINAL` | acked, no double credit |
| Callback amount ≠ request amount | `IGNORED / AMOUNT_MISMATCH` | acked, no credit |
| Receipt number missing | `IGNORED / MISSING_RECEIPT` | acked, no credit |

**Residual risk, stated plainly:** the endpoint is publicly reachable, so an
attacker who learns a live `checkout_request_id` *and* its exact amount could
forge a PAID verdict inside the ~5-minute STK window. The attack requires
knowing a valid in-flight checkout id and its amount; `checkout_request_id` is
generated with a random component (`STK_REF_FALLBACK` prefix plus a unique
suffix) and requests expire. This is the standard Daraja integration model —
Daraja offers no callback signature or shared-secret header. Do not describe
the callback as "authenticated"; it is "verified by reconciliation".

**Health check after any deploy:**

```sql
select * from stk_health;
```

`paid_without_income`, `income_write_failed`, and `duplicate_credits` must all
be `0`. A non-zero `paid_without_income` means a live customer was charged and
not recorded — treat it as a Sev-1 and reconcile before taking more payments.

### Read the view as the user, not as yourself

`stk_health` is `security invoker`, so it only shows the calling user's own rows.
Querying it as `service_role` proves nothing about what an owner sees, and v6.13.0
shipped exactly that mistake: `daftari_stk_callbacks` had RLS enabled with **no
policies** and **no `user_id`**, so `service_role` reported `ignored_callbacks = 3`
while a normal client saw `0`. Both callback-derived counters were structurally
pinned to zero for every customer.

Verify health **as the customer** before trusting it:

```sql
-- service_role: is anything wrong at all?
select * from stk_health;

-- authenticated: is the vendor's own view honest? (set the JWT claims first)
select * from stk_health;
```

The two must agree for that business. They will not agree if a migration half-applied.

`scripts/verify-stk-callback-e2e.sh` is the regression harness for exactly this
defect, and it is worth running after any change to the callback, the protocol
parser, or the health view. It drives the **real public endpoint** with a real Daraja
payload and asserts three things that a unit test cannot:

```
BRANCH 1  amount mismatch -> refused, and VISIBLE TO THE PAYER with a reason
BRANCH 2  exact amount    -> settles, books income, receipt recorded
BRANCH 3  the payer cannot mark paid, forge an audit row, or delete a request
```

It creates and cleans up a throwaway user, so run it against sandbox. It prints no
secrets. Last run against production: all assertions passed, including the refusal
being visible to the customer, which was the specific thing v6.13.0 got wrong.

The customer's equivalent of that query is `Settings -> Payment reconciliation`. It
renders an explicit "could not check" error and suppresses all counters if the fetch
fails, so a failed check can never be mistaken for a healthy one. If a vendor reports
a green screen but a payment is genuinely missing, treat the missing row as the
primary evidence and escalate rather than re-charging.

### Numbers and contacts

| What | Value |
| --- | --- |
| M-Pesa receiving line (`PRICING.MPESA_PAYMENT_NUMBER`) | `254703939236` |
| Notification sim (`PRICING.MPESA_ALERT_NUMBER`) | `254798655485` |
| Support (`SUPPORT.PHONE` / `SUPPORT.EMAIL`) | `+254798655485` / `support.daftari.app@gmail.com` |

Stored international **without a leading `+`**, because the same string is copied to
the clipboard and handed to WhatsApp: `254703939236` pastes cleanly into both, while
`+2547...` and `0703...` each work in only one. The receiving line and the notification
sim are deliberately different numbers — M-Pesa sends transaction alerts to whichever
number the payer dialled from, so sharing one would alert the customer and leave the
owner blind to their own money arriving.

### Deploying

Do not deploy these functions by hand. Use:

```bash
scripts/deploy-edge-functions.sh <project_ref>
```

The script encodes the JWT posture and then *proves* it after deploying: it asserts
the callback still answers an unauthenticated POST (the v6.13.0 outage) and that the
other two still **reject** one (so nobody "fixes" the callback by opening up
everything). A bare `supabase functions deploy` restores the CLI default of
`verify_jwt = true` and silently breaks all payment confirmation.
