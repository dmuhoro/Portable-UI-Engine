# Sprint v6.16.0 — the four defects behind the payment path

**Date:** 2026-09-26
**Previous:** v6.15.0 (support, status, satisfaction, legal disclosures)
**Theme:** the payment path was correct, and the product was still wrong.

## Why this sprint exists

v6.15.0 ended by writing down the payment path end to end in
`docs/vendor-payment-flow.md` and listing four defects behind it. This sprint fixes
all four.

The framing matters, because it is the same failure shape four times over: the
machinery was right and the *claim* about it was not. A vendor paid and did not get
the plan. A vendor was told their customer walked away when our network dropped. An
operator saw a green screen while a payer might have been out of pocket. A receipt
code column held a phone number. In each case a system reported a comfortable
conclusion it had not actually established.

## What shipped

### 1. A verified payment grants the plan (revenue-blocking)

`daftari_subscriptions` had exactly one writer: the signup trigger. Both settlement
paths — `admin_resolve_subscription()` and `settle_subscription_c2b()` — ended at
`update daftari_subscription_requests set status = 'verified'` and never touched
entitlement. RLS denies every client write, so nothing else could. The documented
operator step had no code behind it.

Activation now fires on the `pending -> verified` transition via
`trg_activate_subscription_on_verified_request`
(`supabase/migrations/20260926030000_subscription_activation.sql`). One boundary,
so all settlement paths are covered structurally rather than by remembering to edit
each function. The trigger shares the verifying transaction: a failure rolls the
verification back rather than recording an ungranted payment.

The client already polled every 60s for this, so no app change was needed — a vendor
now sees the plan within a minute of payment.

### 2. Our faults stopped being reported as the payer's

`REMOTE_ERROR`, `NOT_AUTHENTICATED`, `BUSINESS_MISMATCH` and `INVALID_INPUT` all
rendered "The payer didn't complete the payment". All four fail *before* Safaricom is
reached, so none is the payer's doing. Each maps to what happened now; an offline
device is refused before the push; the generic fallback no longer names the payer.
`REMOTE_ERROR` says to check with the payer, because we genuinely cannot know whether
the push landed.

### 3. A possibly-lost payment can no longer read as an all-clear

The threshold was the smaller half of this one. The device gives up at 5 minutes and
tells the vendor the payment failed; `stale_pending` flagged at 30, so for 25 minutes
the operator screen read "all clear" in the one window where the payer may have been
debited with the callback lost. `stale_pending` was also excluded from
`healthNeedsAttention` and shaded amber — the only money counter that could be
non-zero on a healthy-looking screen. It now fires at 5 minutes, raises an alarm, and
renders red, and the copy no longer claims "Nothing was charged".

### 4. `mpesa_code` no longer holds a payer's phone number

Two SMS patterns returned the sender's phone as the receipt code, and that value was
written to both the transaction's code column and the customer's phone field — so
receipt codes were also being stored as phone numbers. Separate fields now, with the
parser test asserting across all eight patterns that a 9-13 digit run is never a code.

## Gates that were decorative

Three checks in this area could not have caught the defects they sat next to. Each
was confirmed by reintroducing the bug and watching the gate fail, because a gate
that has never been seen to fail is an assumption.

| Gate | What it actually did | Now |
|---|---|---|
| `ReconciliationScreen.test.tsx` | hand-copied `healthNeedsAttention` into its module mock, so it asserted against a second implementation no production change could reach | uses the real function via `importOriginal` |
| `parseMpesa.test.ts` | was named "extracts transaction code from pattern A" and expected `'254712345678'` — asserting the defect as intent | asserts a phone is never returned as a code, all 8 patterns |
| `verify-subscription-activation.sh` | three refusals passed on an HTTP 401 from a mis-set `apikey` header, i.e. the request never reached the permission check | `refused()` fails loudly on 401, and entitlements are asserted by reading state, never by HTTP code |

A fourth: the 5/30 threshold agreement is now pinned by BRANCH 4 of
`scripts/verify-stk-callback-e2e.sh`, which reads `STK_EXPIRE_AFTER_MS` from
`constants.ts` and asserts a request one minute past the give-up point is flagged
while one minute before is not. Verified load-bearing by setting the constant to 1
minute — the branch fails and exits non-zero.

### Found while verifying, after the tag

Running the callback proof again post-release turned up a fifth decorative gate.
`as_user` in `scripts/verify-stk-callback-e2e.sh` accepted a filter argument and
then silently dropped it, so all three call sites that passed one were querying the
whole table and reading whichever row came back first. "The request is marked PAID"
was therefore order-dependent: it passed or failed depending on whether Postgres
returned the PAID row or a PENDING one first. BRANCH 4 added more PENDING rows for
the same user, which is what finally made it fail — the fix exposed a latent flake
rather than introducing one.

Worth recording because the first attempt to verify the fix produced its own false
signal: the first "5 clean runs" were the script *aborting* on `$3: unbound
variable` under `set -u`, before reaching a single assertion. A run reporting zero
failures is only evidence if it also reports the assertions it executed. Stability
is now confirmed on the assertion count (17 OK, 0 FAIL) across six consecutive runs.

This is a verification-script fix and changes no product behaviour, so per the
release procedure it is a patch to the tagged release rather than a new version.

## Verification

- `scripts/verify-subscription-activation.sh` — **33/33** against production,
  driving the real vendor sign-in, admin RPC, and C2B settlement paths. Proves
  activation on both settlement paths, that a rejection grants nothing, that an
  unconfirmed C2B notification still cannot move money, that re-saving a verified
  request does not extend the period, and that the RLS wall still stands.
- Threshold behaviour proven live: a PENDING request aged 6 minutes is flagged, 2
  minutes is not, and resolving it returns the counter to zero.
- Production data checked for the parser defect: **no rows affected**, so the bug was
  latent and no data repair was needed.
- Suites: 725 tests / 65 files (from 700), 51 Deno, typecheck, lint, i18n parity
  (425 keys in use, 431 per locale), build.

## Known gaps that remain

These are unchanged and still real:

- **STK cannot take a live payment.** `DARAJA_PASSKEY` is 89 characters; Daraja
  sandbox keys are 32 or 64. Safaricom returns `400.002.02 Invalid TransactionType`.
  Run `./scripts/test-stk-sandbox.sh` after copying the passkey, shortcode and till
  from one Daraja product page, then `./scripts/run-stk-drill.sh 254708374149 1`.
- **`C2B_SHORTCODE` is set to the till number** (`3631767`). A till is generally not a
  C2B shortcode; worth confirming before a real C2B customer.
- **A lost STK callback is never re-queried.** If Safaricom's callback never arrives,
  the request now becomes *visible* at 5 minutes, but nothing self-heals — an operator
  still has to resolve it by hand.
- `support.daftari.app@gmail.com` is published in the app but nobody has confirmed it
  is monitored.
- The legal pages carry a draft notice pending review by counsel.
