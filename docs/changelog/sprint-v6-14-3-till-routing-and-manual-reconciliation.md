# Sprint v6.14.3 — Real Till routing + auditable manual-payment reconciliation

**Status:** Shipped, with one external dependency outstanding (`DARAJA_PASSKEY`).

> Superseded in part by **v6.14.4**, which adds C2B so customer-initiated
> payments settle automatically instead of by hand. The manual queue below stays
> as the fallback for anything C2B cannot confirm.

## Objective

The app told customers to pay a M-Pesa Till, but two things were true and neither
was acceptable:

1. `stk-push` hardcoded `CustomerPayBillOnline` with the store number as both
   `BusinessShortCode` and `PartyB` — paybill routing for a till merchant, which
   Safaricom refuses.
2. "I Have Paid" inserted a `pending` row and nothing else. RLS correctly stopped
   the customer from editing it, and no service-role path existed either, so a
   paid upgrade could only be closed by hand-writing SQL.

This sprint wires collection to the real Till and gives hand-paid payments an
audited closing path.

## What the Till actually is

| Field | Value | Role |
| --- | --- | --- |
| Store number | `3671855` | `BusinessShortCode` |
| Till number | `3631767` | `PartyB` |
| Operator ID | `DM` | Till metadata only, not sent in the payload |
| Mobile fallback | `254703939236` | Secondary, shown in-app |
| Notification line | `254798655485` | Alerts / WhatsApp |

A hand-paid Till payment generates **no** Daraja callback. Daraja calls back only
for pushes we initiate, so a customer who types the Till number by hand leaves
Daftari with no signal at all. The M-Pesa receipt code is the only unique
identifier linking money to a request, which is why recording it is what makes
reconciliation possible rather than a nicety.

## Work completed

**Till routing (`43348a2`)**

- Merchant kind is explicit; routing resolves per kind and throws at the config
  boundary on an unknown kind or a missing pair, surfacing as
  `503 DARAJA_NOT_CONFIGURED`.
- The STK password hashes the same `BusinessShortCode` the payload carries.
- 10 Deno routing/payload tests, including the till and paybill cases that were
  previously interchangeable by accident.

**Reconciliation database (`caefa08`)**

- `mpesa_receipt`, `resolved_at`, `resolved_by`; a verified row cannot exist
  without a receipt, and a receipt cannot settle two requests.
- `admin_subscription_queue()` and `admin_resolve_subscription()`, both
  `security definer` + `is_admin()`.
- 17-check production proof: non-admin RPCs refused, customer `PATCH` updates
  nothing, receiptless/invalid/duplicate receipts rejected, and a full positive
  verify path with audit fields and re-resolve conflict.

**Operator surface (`d21385c`)**

- Queue in the admin dashboard, receipt field, Confirm/Reject, refusal reasons
  surfaced. A rejected approval keeps the row.
- Receipt captured in the upgrade sheet, trimmed and uppercased so the unique
  index cannot see ` abc` and `ABC` as two receipts; omitted when blank so an
  empty string cannot fail the insert.
- 666 Vitest, 10 Deno, typecheck, lint, i18n (375 keys each), production build.

**Drill harness (`d8bbab5`)**

Three defects, all found by running it rather than reading it: no business was
created (all-zero `businessId` → `403`); the row used `owner_id` and a UUID where
the gate needs `user_id` and `local_id`; and cleanup left the income row behind.
Verified against the live function: the push now clears ownership and stops only
at the missing passkey.

## Defects that only real calls could find

- `PGRST202` — a `default null` parameter made the resolution RPC's signature
  ambiguous, so the one function an operator needs was unreachable.
- `42804` — `auth.users.email` is `varchar` but the queue declared `text`.
- AdminScreen awaited the queue fetch in the effect that clears the loading
  state, so any queue failure stranded the whole CEO dashboard on "Loading…".
  An auxiliary payment queue must not be able to hide revenue.
- A test claimed to verify the receipt-required guard through a mocked function,
  bypassing the guard under test. Deleted rather than kept as a green lie.

## Outstanding — launch gates, not code debt

| Gate | Why it blocks | Unblocked by |
| --- | --- | --- |
| `DARAJA_PASSKEY` + confirmed `BusinessShortCode` | No push has ever reached Safaricom; nothing is proven live | Portal credentials page, then `scripts/run-stk-drill.sh` |
| No admin provisioned | Queue and dashboard unreachable in production | `scripts/bootstrap-admin.sh <existing-email>` |
| No alerting | Failures are invisible until someone opens the app | Monitoring on the `stk_health` view and function logs |
| `support@daftari.app` unverified | Customers have no monitored channel | Confirm the mailbox and its escalation path |
| Legal text unreviewed, English-only | Compliance exposure; trust gap against a Kiswahili interface | Counsel review + a language decision |

Nothing in this sprint is claimed to be proven against Safaricom. The Till
numbers are configured and the code is correct to the documented contract; the
transaction itself is unverified.
