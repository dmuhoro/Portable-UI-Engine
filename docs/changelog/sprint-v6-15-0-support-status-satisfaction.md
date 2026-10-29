# Sprint v6.15.0 — support, status, satisfaction, and an honest payment ledger

**Status:** Shipped and tagged. All gates green: 692 Vitest tests, 10 Deno
edge-function tests, typecheck, lint, i18n parity, STK callback e2e.
**The live Daraja sandbox gate fails by design** — see "What is still blocked".

## Objective

Make the product *legible*. A vendor should be able to find a human, an admin
should be able to tell everyone something without shipping a release, a vendor
should be able to tell us whether we helped, and the legal pages should say what
happens to their money — in Kiswahili.

The unplanned half of this sprint was more valuable than the planned half.
Documenting the payment path honestly surfaced four defects that no test was
watching, one of which loses a vendor real money.

## What shipped

| Area | Change | Why it is not the obvious version |
| --- | --- | --- |
| Support | One address everywhere, plus Contact Support and App Version rows in Settings | `SUPPORT.PHONE` and `POLICY_REVIEWED` were kept; `SUPPORT_WHATSAPP` is derived from the phone rather than becoming a second thing to keep in sync |
| Status | Admin-posted banner, dismissable, retractable | No client INSERT policy — that would let any vendor post to every other vendor. Writes go through `is_admin()`-gated RPCs |
| Satisfaction | One question, 7 days after the first *sale*, as a card | Not a modal. "Already answered" is a server query, not a localStorage flag, so a new phone does not re-ask |
| Legal | Full Kiswahili, new M-Pesa and Billing sections, draft notice | Prices interpolated from `PRICING`, not typed into prose. No typed price can drift from checkout |
| Daraja | Diagnostics endpoint, drill fix, sandbox gate | The gate is built to fail; it has no path to exit 0 without a `CheckoutRequestID` from Safaricom |
| Docs | `docs/vendor-payment-flow.md`, 32 verified citations | Four citations were wrong on the first pass and are corrected |

## Decisions that are not obvious from the diff

**No general feedback modal was built.** The sprint note assumed one existed and
asked for its email to be wired in. There is no feedback UI in the product, and
adding one is a feature, not infrastructure. The survey response is the inbox.
The table is `CREATE`, not the `ALTER` the note specified — the table did not
exist. The flag is `reviewed`, not `notification_sent`, because there is no mailer
and no email should be claimed to have been sent.

**The legal prose is in the dictionaries, not inline conditionals.** The proposed
`isSwahili ? '…' : '…'` inside JSX would have been a 60-line unreadable
expression. More importantly, the existing LegalScreen tests mocked `t()` to
return keys and asserted *English* prose was present — they were actively
enforcing that the Kiswahili surface could never appear. The tests are now written
against the real dictionaries, and one of them fails if a Kiswahili vendor sees
English.

**The draft banner appears on every section, including Support.** A draft notice
on one tab is a notice someone misses. A vendor emailing us because of a clause
has to see that the clause is not binding.

## Security properties, proven against production

Not asserted — executed against the real database during this sprint:

- A vendor calling `publish_status_message` → `NOT_ADMIN`.
- A vendor `INSERT`ing `daftari_status_messages` directly → RLS denial.
- A vendor reading an admin's banner → succeeds. That is the point of a banner.
- A vendor calling `retire_status_message` → `NOT_ADMIN`.
- An admin retiring a banner → gone for everyone on the next fetch, no cache
  purge needed, because the read policy filters on `active` and `expires_at`.
- Retiring a nonexistent id → `NOT_FOUND`, not a false success.
- A vendor reading another user's `daftari_feedback` → empty.

The banner itself can never block the ledger: offline, RLS denial, an unapplied
migration or a malformed row all render `null`, and a failed refresh keeps the
message already on screen rather than clearing it.

## Known gaps, written down rather than quietly left

Full detail and citations in `docs/vendor-payment-flow.md` §7.

1. **A verified subscription payment does not activate the plan.** The only write
   to `daftari_subscriptions` is the signup trigger. Neither
   `settle_subscription_c2b` nor `admin_resolve_subscription` touches it, and RLS
   denies the client. An operator must update the row by hand. **This is a money
   gap and it is the most serious finding of the sprint.**
2. A lost STK callback is never self-healed — STK has no status-query equivalent
   to C2B, so a `PENDING` request waits for a human.
3. An offline STK push is reported to the vendor as *"The payer didn't complete the
   payment"*, because every non-specific error code collapses to `stk_failed`.
4. The device gives up at 5 minutes; `stale_pending` flags at 30.
5. The SMS parser stores the sender's **phone number** in the field named
   `mpesa_code` for the two "received from" patterns.

Gap 1 is the one to pick up next. It is also the reason this release is a minor
bump rather than a patch: the payment path is correct, and it is now written down.

## What is still blocked (operator action, not code)

`scripts/test-stk-sandbox.sh` exits 1, correctly. Resolved wiring:

```
env          sandbox
apiBase      https://sandbox.safaricom.co.ke
merchantKind till
shortcode    3671855
partyB       3631767
txnType      CustomerBuyGoodsOnline
passkey      89 chars   <-- Daraja issues 32 or 64
```

Safaricom returns `HTTP 400 / 400.002.02 / Bad Request - Invalid TransactionType`.

To unblock, copy these from **one** Daraja sandbox product page — they are issued
together and are not interchangeable:

```bash
supabase secrets set --project-ref rjedivbpldkroffswoyb DARAJA_PASSKEY='<32-or-64-char passkey>'
supabase secrets set --project-ref rjedivbpldkroffswoyb DARAJA_STORE_NUMBER='<business shortcode>'
supabase secrets set --project-ref rjedivbpldkroffswoyb DARAJA_TILL_NUMBER='<till number>'
```

`C2B_SHORTCODE` is currently the same value as the till (`3631767`). A till is
generally not a C2B shortcode, so this is worth checking against the portal too.

Then:

```bash
./scripts/test-stk-sandbox.sh          # must print GATE PASSED
./scripts/run-stk-drill.sh 254708374149 1   # full prompt -> callback -> books
```

## Also outstanding

- `support.daftari.app@gmail.com` is published in the app but its monitoring is
  not verified. It is currently a promise we cannot keep.
- The legal pages carry a draft notice. Formal review by counsel has not happened.
