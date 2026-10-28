# Sprint v6.14.0 — Reconciliation, legal, and an honest health view

**Date:** 2026-09-26
**Branch:** `feat/subscription-billing`
**Previous:** v6.13.0 (`bcabc99`)
**Outcome:** The `stk_health` view no longer reports a false all-clear; the customer
can see their own payment health; the product has legal pages and a real support
contact; the M-Pesa numbers are live. **The end-to-end payment drill is still
unproven** — that is unchanged and still operator-gated.

---

## The headline: a monitor that could not fail

v6.13.0 shipped an `stk_health` view and declared it done. Then we queried it the way
a real client would, instead of the way an operator would:

```
service_role sees:      ignored_callbacks = 3
a normal client sees:   ignored_callbacks = 0
```

`daftari_stk_callbacks` had RLS enabled, **no policies at all**, and **no `user_id`
column**. So a signed-in user could not see a single callback row, ever. Two of the
six health counters were therefore structurally pinned to zero.

This is the same class of defect as the two found in v6.13.0 — something invisible
unless you interrogate the real boundary. A green suite, a green migration, and a
working `service_role` query all hid it. Had the reconciliation UI been built without
this check, every owner would have seen a permanent green tick while their
charged-but-unbooked payments went unrecorded.

**The rule we are adopting: a monitor that cannot fail is worse than no monitor,
because it manufactures confidence.**

### The fix

`20260926000000_stk_callbacks_user_scope.sql`:

1. Add `user_id`, backfilled from the request each callback resolves.
2. Owner SELECT policy; client roles still hold **no** INSERT/UPDATE/DELETE, so an
   audit row cannot be forged.
3. Redefine `stk_health` so the callback counters are the caller's own truth.
4. Raise if the column is missing, so it cannot half-apply.

The policy is written defensively:

```sql
using (
  (select auth.uid()) = user_id
  or exists (select 1 from public.daftari_stk_requests r
             where r.checkout_request_id = daftari_stk_callbacks.checkout_request_id
               and (select auth.uid()) = r.user_id)
)
```

The second branch is the point. If the Edge Function ever inserts a callback without
an owner, the naive `user_id = auth.uid()` version hides it **permanently** — the
customer who paid could never see that their payment failed. Deriving visibility from
the checkout means a NULL owner degrades to "still visible to the right person" rather
than "invisible forever". A forgery matches neither branch and stays hidden.

### Verified against a real Postgres

| Check | Result |
| --- | --- |
| Alice (4 seeded failures) | sees `1 / 0 / 1 / 1 / 0 / 2` — exactly her own problems |
| Bob (clean business) | sees all zeros — no cross-user leakage |
| Re-run with `user_id` NULL | still correct — the fallback works |
| `authenticated` forging a callback | `ERROR: permission denied` |
| `service_role` writing the audit row | `INSERT 0 1` |

---

## Reconciliation screen

`Settings -> Payment reconciliation`. Shows the six counters and the callback trail.

The behaviour that matters is the failure path, and it is the thing most screens get
wrong. `fetchStkHealth` returns `null` on **any** error — query failure, RLS refusal,
malformed row, or a renamed view column. `null` renders an explicit "could not check,
try again" state and **suppresses every counter**. It never renders zeros.

The test that pins this:

```ts
it('renders an explicit error, NOT zeros, when the health check fails', ...)
it('hides every counter when the check failed, so no false 0 is displayed', ...)
```

A further judgement call: `healthNeedsAttention` deliberately does **not** fire on
`ignored_callbacks` or `stale_pending`. Refusing a forged callback is the system
working, and an abandoned checkout cost the customer nothing. A screen that cried wolf
on those would train the owner to ignore it, which defeats the alarm that matters.

---

## Legal pages and support contact

`Settings -> Privacy policy`, with privacy / terms / support tabs.

The content is written to match what the code actually does, and the tests assert the
substantive claims rather than that a string rendered:

- Local-first storage stated plainly (records are written to the device first).
- **M-Pesa disclosed as a payment processor**, and the callback endpoint named as
  something we operate. A privacy policy that omitted a genuine third party would be
  misleading, so `toContain('M-Pesa')` is an assertion.
- Data-subject rights: access, correction, deletion, plus account deletion removing
  server records.
- Terms state Daftari is not a tax or accounting authority, that records are the
  vendor's responsibility, and that a charged-but-unrecorded payment must be reported
  rather than paid again.

`SUPPORT` is a single constant so the legal pages, upgrade sheet, and reconciliation
screen cannot drift into giving three different answers about how to reach a human.

---

## The numbers

| Constant | Value | Purpose |
| --- | --- | --- |
| `MPESA_PAYMENT_NUMBER` | `254703939236` | receiving line; unblocks self-serve upgrades |
| `MPESA_ALERT_NUMBER` | `254798655485` | notification sim |
| `SUPPORT.PHONE` | `+254798655485` | the notification sim, so alerts and support SMS land together |

Stored international, **no leading `+`**, because the same string is copied to the
clipboard and handed to WhatsApp: `254703939236` pastes cleanly into both, while
`+2547...` and `0703...` each work in only one.

The two numbers are kept deliberately different and a test enforces it. M-Pesa sends
transaction alerts to whichever number the payer dialled from, so pointing the owner
at the receiving line would alert the customer and leave the owner blind to their own
money arriving.

The original fail-closed guard is preserved in spirit: the constants test still
asserts the number is not a placeholder (`/YOUR_|HERE|TODO|PLACEHOLDER|XXX/i`) and now
also asserts the `254` + 9-digit shape. The "fails closed when absent" behaviour is
tested directly rather than inferred from the shipped value.

---

## Refused, and why

An operator asked to hide the Daraja consumer secret inside the build — an
"invisible" path in the bundle or a shell profile — on the reasoning that it would be
harder to find.

Declined. A Vite PWA is static JavaScript delivered to every phone. It is minified, not
encrypted. Anything in it is readable by anyone who opens DevTools. The consumer secret
in the bundle would let an attacker authenticate to Safaricom as Daftari: generate
tokens, initiate pushes against our shortcode, and attempt forged confirmations.

The architecture already solves this and needs no concealment:

```
browser ──JWT──> stk-push edge ──secret──> Safaricom
                    secret never crosses the first hop
```

The browser never talks to Daraja, so it has no use for the secret. The keys live in
Supabase's encrypted store, and the repo's `.env*` is already gitignored (verified:
`git add .env.local` is refused). Adding the secret to the build would have *removed*
the protection while creating the impression it added one.

---

## Still open — honestly

- **No end-to-end payment drill.** `DARAJA_PASSKEY`, `DARAJA_SHORTCODE`,
  `DARAJA_STORE_NUMBER`, and the public HTTPS `DARAJA_CALLBACK_URL` are still missing.
  `stk-push` fails closed with `503 DARAJA_NOT_CONFIGURED`. **No customer has ever
  been charged through this system.** Everything in this release makes the product
  *ready* for that drill; none of it substitutes for it.
- **No alerting.** Logs and the view exist; nothing pages a human.
- **Legal review.** The policy text is drafted to match the code, but it has not been
  reviewed by a lawyer and Kenya's Data Protection Act obligations should be confirmed
  before launch.
- **`PRICING.MPESA_PAYMENT_NUMBER` is now live**, so the upgrade sheet will show a
  real number and will accept payment. If the drill has not passed, that surface should
  not be advertised until it has — a vendor can now send real money to a real number
  for a product whose payment confirmation is untested.

## Carried forward

- Run the full fail-closed drill set (runbook §4) once the Daraja credentials land.
- Add E2E coverage for the push flow; Playwright exists but never exercises a push.
- Rotate the sandbox credentials before production use — they were shared in chat.
- Consider a `stk_health` alert so `paid_without_income` reaches a human, not just a
  screen nobody opens.
