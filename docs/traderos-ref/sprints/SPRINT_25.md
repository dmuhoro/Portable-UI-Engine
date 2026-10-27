# Sprint 25 — Idempotent order submission at the Alpaca adapter boundary

**Period:** 2026-08-04
**Objective:** Close one precise G-02 slice — **no duplicate orders under
adapter-internal retry**. When the broker accepts an order server-side but the
response is dropped (timeout), the adapter's `retry_with_backoff` re-submits; a
stable, retry-reused `client_order_id` makes that second attempt a dedupe, not a
double order. One-hour, tightly-scoped fix; paper/backtest path untouched.

**Scope (per directive):** `client_order_id` on the four Alpaca submit methods +
a test-injection seam + two proof tests through the real `CycleExecutor` path +
evidence + governance. No WS reconnect, no soak test, no paper/backtest changes.

**Reference docs:** `docs/evidence/2026-08-02_sprint25_idempotent_submit_alpaca.log`,
`docs/engineering/GAP_READINESS.md` (G-02: live order ops, 35/CRITICAL).

---

## Work Package Register

| ID | Work package | Gate |
|----|--------------|------|
| WP-I1 | Stable `client_order_id` generated once per logical order, reused on every retry attempt | retry attempts carry identical `client_order_id` |
| WP-I2 | Test-injection seam for a fake Alpaca client | proof drives the real `AlpacaBrokerAdapter`, not a stub of it |
| WP-I3 | Proof through the real `CycleExecutor → AlpacaBrokerAdapter` path | timeout-after-record ⇒ exactly one order; distinct orders ⇒ distinct ids |

## Ground truth (verified, not assumed)
- Live chain (`application/factory.py:182-223`): `CycleExecutor →
  JournaledBroker → GuardrailedBroker → RateLimitedBroker →
  AlpacaBrokerAdapter.submit_order`. Order call site `cycle_executor.py:268`.
- `place_market_order` (line 66) built `MarketOrderRequest` with **no
  `client_order_id`**, wrapped in `retry_with_backoff(max_retries=2)` (line 92);
  identical gap in `place_limit_order`, `place_stop_order`,
  `place_trailing_stop_order`.
- **Premise correction:** `modify_order` uses `replace_order_by_id` — alpaca-py
  `ReplaceOrderRequest` has **no** `client_order_id` field, so it is excluded.
- `JournaledBroker._submit(method_name, *args, **kwargs)` forwards kwargs
  through the decorator chain unchanged — a `client_order_id` kwarg threads
  cleanly; its journal key (`uuid5(order:{market}:{side}:{qty}:{method})`) is
  time-insensitive and was not the duplicate source here.
- `market_stream.py` (`BinanceStreamTransport`) is **not** wired into any live
  path (0 references under `application/`) — out of scope.

## Work Completed

### WP-I1 — Stable, retry-reused `client_order_id`
- New `_new_client_order_id()` helper (module-level, `uuid4`) — generated **once
  before the first submit attempt** and reused verbatim by every retry of that
  logical order. A dropped-response/timeout can no longer produce a duplicate at
  the broker: Alpaca dedupes by `client_order_id` within the trading day.
- Wired into the request objects of all four submit methods, inside their
  `_submit` closures (the `retry_with_backoff` boundary): market (line 104),
  limit (146), stop (190), trailing-stop (234).

### WP-I2 — Test seam
- `AlpacaBrokerAdapter.__init__` gains optional `client=` injection; the fake
  server in tests implements `submit_order` (with server-side dedupe by
  `client_order_id`) plus the read/account methods the executor path touches.

### WP-I3 — Proof through the real path (`tests/test_alpaca_idempotent_submit.py`)
Real `AlpacaBrokerAdapter` driven by a real `CycleExecutor` against a fake
Alpaca client whose server drops the response after recording the order:
1. `test_timeout_after_record_creates_exactly_one_order` — 2 submit attempts,
   **1** server-side order; retry reused the same `client_order_id`.
2. `test_different_orders_get_different_client_order_ids` — negative control:
   two runs produce distinct ids (no cross-order collisions).

### Evidence (`docs/evidence/2026-08-02_sprint25_idempotent_submit_alpaca.log`)
- Proof tests PASS; full suite `1284 passed, 1 skipped`; coverage 92.55%;
  black/isort/ruff clean; pyright 0 errors; pre-commit hooks pass.

### Gate
- [x] Retry attempts carry an identical `client_order_id` (provably, in the real path)
- [x] Timeout-after-record yields exactly one order at the fake broker
- [x] Distinct logical orders get distinct ids
- [x] Paper/backtest path unaffected (full suite green); `modify_order` excluded by design

## Not in scope / still open
- Network-level broker outage soak, WS reconnect, lost-order reconciliation
  beyond the journal layer, kill-flatten + portfolio-cap live drill — all G-02
  follow-ups scheduled for larger work blocks. Closing this one gap does **not**
  mean live-ops risk is complete.
