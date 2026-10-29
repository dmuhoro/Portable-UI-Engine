# Sprint 36 — Pareto execution-safety hardening (freeze rail, fail-closed throttle, true local↔broker reconcile)

**Period:** 2026-08-12 → 2026-08-13
**Objective:** Apply the Pareto principle to execution safety — close the few
remaining order-path gaps that carry the most real-money risk. Three gaps, each
proven through the *real* submission/reconciliation path, not a standalone
helper. The through-line is the same red-line as every prior sprint: **fail
closed, never fail open**, and **never let code claim a protection it does not
actually provide.**

Scope is deliberately tight: these are execution-guardrail fixes on the live
order path. Nothing in this sprint touches strategy logic, data ingestion, or
the backtest engine.

---

## Gap 3 — Fatal-exception freeze rail (G-04 / G-05)

**The hazard:** if a critical, *unexpected* exception escapes the trading loop,
the process used to limp on (or die silently) with unknown capital exposure.
An uncaught error in an order path can lose real money or destroy trust.

**What was built:** `infrastructure/fatal_handler.py` →
`FatalExceptionHandler`, an installable `sys.excepthook` installed/uninstalled
by `DaemonController.run_forever` around the run loop. On a fatal escape it:

1. Broadcasts a detailed diagnostic payload (exception, mode, pid, traceback)
   over the real notification seam — console + webhook + on-call as configured.
2. Records `fatal.exception` to the durable audit trail and a metrics counter.
3. Attempts an **exactly-once portfolio flatten** through the true broker
   submission path (`FlattenService.flatten`).
4. **Always** terminates via `sys.exit(1)` — regardless of whether alerting or
   flattening succeeded. A failure to alert or close must never leave a
   half-alive trading process; it dies and forces a human to investigate.

Each of alert/audit/metrics/flatten is independently guarded, so one broken
step can never skip a later one (an alert failure must not skip the flatten; a
broken flatten must never prevent exiting). The unreachable outer guard is
marked `# pragma: no cover`.

**Notification seam fixes that made this real:**
- `NotificationService.info/warning/error/critical` now accept a `metadata`
  dict that rides the event end-to-end.
- `webhook_on_critical` fan-out works, with **no double-send** when the primary
  channel is already `NotificationChannel.WEBHOOK`.
- `oncall.route` receives the metadata (covered).

**Evidence:** `tests/test_fatal_handler.py`, `tests/test_notification_service.py`,
`tests/test_daemon_controller.py::test_run_forever_installs_and_uninstalls_fatal_handler`.

---

## Gap 2 — Fail-closed broker throttle + emergency flatten bypass (G-02 / G-03)

**The hazard (a):** a runaway loop could hammer the broker with orders. The
rate limiter existed but was *opt-in* — i.e. it **failed open** by default. An
unenforced throttle on a live order path is a protection the code claimed but
did not provide.

**The hazard (b):** the kill-switch / fatal flatten must **never** be throttled
or refused by a policy layer. A rate limiter or a size guardrail that can block
an emergency flatten is a safety flaw: when we need to get flat *now*, nothing
may stand in the way.

**What was built:**
- `RateLimitedBroker` is now **enabled by default** (fail closed). Opt out only
  with an explicit `BROKER_RATE_LIMIT_ENABLED=false` (also `0`/`no`);
  `BROKER_RATE_LIMIT_MAX` / `BROKER_RATE_LIMIT_WINDOW` tune the window.
- A dedicated emergency seam `BrokerAdapter.place_flatten_order` (default
  delegates to `place_market_order`) is propagated through the whole broker
  chain, with the right layers bypassed and the right layers kept:
  - `RateLimitedBroker.place_flatten_order` **bypasses** the throttle `_check`.
  - `GuardrailedBroker.place_flatten_order` **bypasses** the size `_guard`.
  - `CircuitBreakeredBroker.place_flatten_order` **stays under** the breaker —
    a tripped broker is a real condition the flatten must not pretend away.
  - `JournaledBroker.place_flatten_order` **still journals** via
    `_submit("place_flatten_order", …)` — the flatten is causally accountable.
- `FlattenService.flatten` now calls `place_flatten_order` (flatten_service.py:75).

Live composition (factory.py:353–375):
`JournaledBroker(CircuitBreakeredBroker(GuardrailedBroker(RateLimitedBroker(raw))))`.

**Evidence:** `tests/test_broker_rate_limiter.py` (default-on + flatten bypass),
`tests/test_order_guardrails.py` (guardrail bypass), `tests/test_journaled_broker.py`
(journaled flatten seam), `tests/test_portfolio_risk_rails.py` (flatten edge paths).

---

## Gap 1 — True local↔broker state reconciliation (G-02)

**The hazard:** startup and periodic broker-state reconciliation ran with **no
local view** — `DaemonController.run_forever` called
`_run_startup_reconciliation()` with empty local state. Any position the local
journal actually held would be flagged `BROKER_ONLY_POSITION`, and — worse — a
healthy state could be mis-read, while a genuinely rogue broker position could
hide behind the noise. Reconciliation without local truth is theatre.

**What was built:**
- `DaemonController` gains an optional `local_state_provider:
  Callable[[], tuple[list[dict], list[dict]]]`. `_fetch_local_state()` returns
  `(positions, orders)` from the provider; with no provider it returns
  `(None, None)` (local treated as empty → any broker-held state is flagged,
  fail closed). A provider **failure** is treated as "local unknown" (never
  crashes the daemon) and still reconciles broker-vs-empty, so an unverifiable
  local state blocks trading via the normal mismatch path instead of silently
  passing.
- `run_forever` fetches local state once for startup reconciliation and
  re-fetches it on **every periodic reconciliation** in the loop.
- `TradingOrchestrator._local_reconciliation_state` builds the local truth from
  the real repositories and is wired as the provider:
  - positions from `portfolio_service.position_repo.list_open()` keyed by
    `symbol = str(market_id)` with `qty/entry_price/current_price`;
  - orders from `portfolio_service.trade_repo.get_open()`, **only** trades that
    carry a broker `external_order_id` (the real id recorded on submit), keyed
    by that id. Pending trades with no broker id are excluded, so paper/synthetic
    ids never cause a false `LOCAL_ONLY_ORDER` block.

**Why the order-id match is real:** `CycleExecutor` records the broker's actual
`fill.order_id` into `trade.external_order_id` (cycle_executor.py:417–418,
607–608), so a local working order and its broker-side counterpart reconcile by
the same id.

**Evidence:** `tests/test_daemon_controller.py` (provider wiring, error swallow,
startup + periodic carry local state, no-provider reconciles broker-vs-empty)
and `tests/test_orchestrator.py` (local-state format, **real** reconciliation
service matches an identical broker snapshot with no false block, and flags a
rogue broker-held position fail-closed).

---

## Quality gates (measured, not declared)

- Full suite: **2193 passed, 7 skipped**.
- Coverage: **100.00%** — 0 missing of 12,453 statements; gate remains
  `fail_under = 100`.
- `pyright src/traderos/`: **0 errors, 0 warnings, 0 informations**.
- `ruff check src/traderos/`: **clean**. (Pre-existing lint debt remains in a
  handful of untouched `tests/` files; CI lints `src/traderos/` only.)
- The single network-gated drill (`test_cost_adjusted_backtest.py` real-market
  walk-forward) skips cleanly when Binance is unreachable — unrelated to this
  sprint.

## Honesty notes

- Closing these three gaps does **not** close G-02 or G-03 in the register. The
  reconciliation is only as true as the local journal and the broker snapshot;
  the continuous unattended paper soak (G-02 exit test) and a live-symbol
  allowlist deployment (G-03) remain operator-run gates.
- The flatten bypass removes the throttle/guardrail on the emergency path **by
  design**; the circuit breaker and the journal are deliberately kept. If a
  future layer is added to the chain, it must explicitly decide whether the
  flatten bypasses it — the default must stay "flatten gets through."
- `infrastructure/async_streaming.py` (asyncio-native market-data ingestor) is
  committed and 100%-tested but **not wired** into any production path. It is a
  tested building block (24 tests), not an active protection — the live data
  path remains the synchronous `market_stream.py` worker; wiring the async
  transport selection into the factory is a future decision and must be proven
  by a drill before it can claim to guard the live loop.
