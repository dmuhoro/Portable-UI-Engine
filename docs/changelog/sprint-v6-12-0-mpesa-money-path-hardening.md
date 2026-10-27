# Sprint v6.12.0 — M-PESA money-path hardening + launch integrity

**Status:** Code complete — all gates green. Operator actions outstanding (see below).

## Why this sprint exists

v6.11.0 shipped the Daraja STK Push feature and was tagged as complete. A launch-readiness
audit of that release found defects serious enough that the feature, as shipped, could have
**told a vendor that a successful payment failed**, and **recorded a payment as settled
before the money was booked**. The tag was accurate about what was written; it was not
accurate about whether the money path was safe.

This sprint closes those gaps. It changes product behaviour (payments can no longer be
mis-reported, upgrade payments are refused rather than misdirected, and data survives device
loss), so it ships as a minor version, not a patch.

## Money path

- **Resolution now comes from the server.** `StkPushPanel` polled the Dexie
  `stk_requests` mirror, which only advances when a sync runs. A payment Safaricom had
  confirmed could sit unread and then be declared expired. Added
  `repository.fetchStkRequestFromServer()`; the mirror is now only an offline fallback that
  can prove PAID but can never prove failure. One final server read happens before expiry,
  and a genuinely unknown outcome is reported as **unconfirmed**, not failed.
- **Money lands before PAID.** `lipa-na-mpesa-callback` marked the request PAID and only
  then inserted the income row, discarding both errors. Income is now written first; PAID
  follows only on success. A `23505` unique violation is treated as already-credited
  (success). Any other write failure leaves the request PENDING and writes an
  `INCOME_WRITE_FAILED` audit row, so an unrecorded payment is visible to an operator
  instead of silently lost.
- **No double charging.** `stk-push` refuses a second push while the same `local_id` is
  PENDING (`409 DUPLICATE_PUSH`); the panel reuses one `local_id` across retries so the
  boundary can collapse them.
- **No double counting.** Manual Save is disabled while a push is in flight, closing the
  path where the callback and the vendor both recorded the same sale.
- **The callback is testable.** It was a top-level `serve()` with zero tests — the only
  code that writes M-PESA income was untested. Extracted to `handler.ts` behind an
  injectable store; 7 Deno tests cover money ordering, duplicate callbacks, income-write
  failure, forged callbacks, and amount mismatch.

## Fail-closed configuration

- `PRICING.MPESA_PAYMENT_NUMBER` shipped as the literal `YOUR_MPESA_NUMBER_HERE` and was
  rendered in the upgrade sheet with a copy button and an "I have paid" button. It now
  ships empty, and `MPESA_PAYMENT_CONFIGURED` is derived from it so the two cannot drift.
  With no number the sheet refuses to collect payment instead of displaying a paybill that
  looks real.
- `stk-push` now returns `LEDGER_UNAVAILABLE` when it cannot record the authoritative
  PENDING row, instead of returning `ok` and leaving the client to poll a row that does
  not exist. `paymentMethod` is validated at the boundary.

## Data durability

- **The sync queue deadlocked.** Past 50 pending items `flushQueue()` returned
  `{synced: 0}` and opened the circuit breaker, so the count could never fall and every
  write was stranded on the device permanently. `MAX_BATCH` now bounds work per pass and
  the flush loops until the queue drains.
- **Writes are pushed out, not hoarded.** The queue only flushed on mount and reconnect,
  so a vendor who worked a shift on a stable connection and then lost the device lost every
  sale of that shift. `addToQueue()` now schedules a debounced flush (3s quiet period, 15s
  ceiling) and app background/hide forces a final flush.
- **Restore stopped lying.** One failing table threw out of `pullFromSupabase`, silently
  skipping every table after it, and customers/daily_closes discarded their errors
  entirely. Each table is now pulled independently and failures are named. Tables that
  are simply not deployed are reported as a separate `skipped` list, so a restore never
  claims coverage it does not have.

## Entitlement and schema truth

- `useSubscription` fetched once on mount. A vendor whose upgrade an operator had just
  approved kept seeing the paywall until they force-closed the app. It now re-checks every
  60s and on foreground.
- Migration `20260925000000` drops INSERT/UPDATE/DELETE policies on `daftari_stk_requests`.
  The v6.11.0 migration called the table "server-owned" with a "read-only mirror" while
  granting clients full write — reachable from the browser console to flip a PENDING row
  to PAID and forge an `mpesa_code`. The client only ever reads the table.

## Honesty corrections

- The v6.11.0 CHANGELOG claimed `check:functions` was "wired into npm + CI". It was only
  in npm. CI now runs `deno check` **and** `deno test` over `supabase/functions/`, and the
  v6.11.0 entry is corrected in place to say what was true at that tag.

## Final gate state (v6.12.0)

typecheck ✅ · lint ✅ · check:i18n ✅ (338 keys) · check:functions ✅ · test:functions ✅ 7 ·
test:run ✅ 56 files / 584 · build ✅

## Operator actions outstanding

These cannot be done from the repo and gate real-world use:

1. `supabase db push` — applies `20260925000000_stk_requests_server_owned.sql`.
2. Deploy both Edge Functions: `supabase functions deploy stk-push lipa-na-mpesa-callback`.
3. Add the 8 `DARAJA_*` secrets to Supabase Functions → Secrets (sandbox values first).
4. Set `PRICING.MPESA_PAYMENT_NUMBER` to the real receiving number, or leave it empty and
   take upgrade payments over WhatsApp — the app now refuses self-serve payment until then.
5. Run the Safaricom sandbox drill (`docs/runbook/daraja-stk-push.md`) before any live
   traffic.
6. Merge to `main` — CI deploys only from `main`, so nothing is live until then.
