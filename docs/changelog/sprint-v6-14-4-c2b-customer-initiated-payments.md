# Sprint v6.14.4 — C2B: customer-initiated payments settle without a human

**Status:** Shipped. Code, migration, function and audit trail are live and the
security property is proven against production. **No real Safaricom transaction
has been processed** — registration and credentials are still outstanding.

## Objective

v6.14.3 left one gap with an architectural cause: a customer who pays the Till
by typing the number into their own M-PESA app produces **no Daraja callback at
all**. Daraja calls us back only for pushes we initiate. So the operator had to
match an M-Pesa receipt by eye against the Till statement.

C2B is the product that closes it. Register a ConfirmationURL and Safaricom
POSTs every payment into our shortcode.

## Which product is which

| Product | Who starts | Register a URL? | Daftari use |
| --- | --- | --- | --- |
| STK Push | Business pushes a prompt | No | Collecting from a business's customers at checkout |
| **C2B** | Customer pays from their own M-Pesa app | **Yes** | **A user paying Daftari for a subscription** |
| B2B | Business pays business by account number | No | Paying a supplier from the app |

The operational difference: STK Push is trustworthy because we created a PENDING
row first, so a callback always has a request to match. C2B has no such row, so
its payload is a claim from an anonymous caller.

## The security property

The ConfirmationURL is public and unauthenticated, so its body is
attacker-controlled. A payload is recorded as a claim and is only believed after
the handler independently asks Safaricom's Transaction Status Query API whether
the TransID is real. If that check cannot run, the notification stays
`UNVERIFIED` and the upgrade stays pending.

Proven against production:

| Attempt | Result |
| --- | --- |
| Forged confirmation POSTed by a stranger | `200`, recorded `safaricom_confirmed=false`, `UNVERIFIED` |
| Client inserts a fake audit row | denied by RLS |
| Anonymous caller invokes settlement | `permission denied` |
| Service role forces a settlement | `NOT_CONFIRMED: ... was never confirmed with Safaricom` |

Matching is strict on purpose: exact receipt wins, else exact amount, and two
identical-amount pending requests with no receipt is refused rather than guessed.

## The bug that would have shipped silently

`c2b-confirmation` would have deployed JWT-gated, because that is the Supabase
CLI default, and Safaricom sends no JWT. Every customer-initiated payment would
have been rejected at the gateway — the v6.13.0 outage recurring on a new
endpoint, and invisibly, because a rejected callback still looks clean to a
health view. The deploy script now deploys it `--no-verify-jwt` and asserts the
posture, while still proving `stk-push` stays authenticated.

## Also shipped

- `scripts/guard-public-secrets.sh`, wired ahead of `npm run build`, after a
  Daraja Postman collection was found deployed out of `public/`.
- Admin provisioned for `hellodannymuhoro@gmail.com`; promotion no longer needs
  the account password handed to a script.

## Outstanding

| Gate | Unblocked by |
| --- | --- |
| `DARAJA_PASSKEY` unset; STK drill never run | Daraja portal product page, then `run-stk-drill.sh` |
| C2B not registered | `register-c2b-urls.sh <c2b-shortcode>` — a Till is generally **not** a C2B shortcode; Safaricom issues a Paybill |
| No alerting | Monitoring on `stk_health` + `daftari_c2b_notifications` |
| `support@daftari.app` unverified | Confirm the mailbox and escalation path |
| Legal unreviewed, English-only | Counsel review + language decision |
