# Sprint 37 — Tick-fed async execution loop (Pareto ingestor wired into the real submission path)

**Period:** 2026-08-13
**Objective:** Replace the polling cadence of the trading daemon with an
**asyncio event loop that is driven by fresh market ticks**. The already-committed
but unwired `ParetoWebSocketIngestor` (Sprint 1 building block) is now the source
of those ticks, feeding the **real** `CycleExecutor` submission path — the same
broker chain and risk gate the synchronous loop trades through. Proxy-free proof
was written **first** (red), then the implementation made it green.

Scope is deliberately tight: an execution-path wiring change. No strategy logic,
risk rules, or backtest engine were touched.

---

## Proof-first (red) — the evidence shape

Before any implementation, `tests/test_async_daemon_controller.py` and
`tests/test_factory_ingestion.py` pinned the contract and failed because the
`AsyncDaemonController` did not exist. The proofs that now guard the feature:

1. **A fresh tick for a wired market reaches the real broker seam exactly once**
   (real `CycleExecutor`, real authorize path `can_trade -> assess_trade ->
   authorize_order -> broker.place_market_order`, recording broker at the seam).
2. **A duplicate/stale tick never re-triggers** a cycle (freshness gate).
3. **A refused signal never reaches the broker** (`broker.calls == []` —
   concrete proof the seam is not invoked).
4. **A tick for an unwired symbol never trades** — it is audited and counted
   (`async_daemon.unknown_symbol`), never silently dropped, never routed.
5. **The real `ParetoWebSocketIngestor` pipeline drives the submission path**
   end-to-end: a scripted trade frame through `run_pipeline`/`run_forever` lands
   on the broker once, and in-flight cycles are drained on shutdown.
6. **The factory composes the async daemon over the production symbol map**
   (`uuid5("traderos/{symbol}")`, identical to the sync wiring) and the real
   wrapped broker chain (`CircuitBreakeredBroker`), and fails closed when the
   streaming transport cannot be constructed.

---

## The real constraint discovered (OT-011, proven, not assumed)

The first green attempt ran the cycle with `asyncio.to_thread` and **failed on
the thread-bound SQLite services**: `SQLite objects created in a thread can only
be used in that same thread`. That was a genuine correctness finding, not a test
artifact — a raw `sqlite3.Connection` shared across a worker thread cannot be the
worker-thread isolation claim.

The fix uses the **production thread-safe connection layer the factory already
requires for the load-sensitive API path** (`ThreadSafeSQLiteConnection`, OT-011,
`infrastructure/database/connection.py`): every statement executes under a
process-wide reentrant lock, so one connection is safe to share across the loop
thread (audit/metrics/health) and the cycle worker threads. The async daemon is
the same architecture as the production orchestrator: worker-thread cycles,
serialized statement access.

**Honesty note:** this isolation claim is only as real as the DB layer beneath
it. With the OT-011 wrapper (or PostgreSQL) the worker-thread cycle is safe; a
raw thread-bound connection is not. The proof deliberately uses the wrapper, not
a mock.

---

## What was built

- `application/async_daemon.py` — `AsyncDaemonController`:
  - `handle_tick(tick)` — the single decision point: map `Tick.symbol` -> market
    via the production symbol map, gate on freshness, run the real
    `CycleExecutor.run` in a worker thread (`asyncio.to_thread`) so a slow broker
    call never blocks the loop.
  - Fail-closed routing: unwired symbol -> audit + metric + notification (no
    silent drop); stale/duplicate -> counted and skipped (never re-submits);
    duplicate symbol mapping across markets -> `ValueError` at construction
    (ambiguous routing is a boot error, not a runtime guess).
  - Contained cycles: a failing cycle records `async_daemon.cycle_panics`,
    degrades health for that market, and never escapes the loop or other markets.
  - `on_tick` — sync bridge consumed by the ingestor pipeline; in-flight
    `handle_tick` tasks are tracked.
  - `run_forever(shutdown_timeout)` — owns the `ParetoWebSocketIngestor`
    pipeline; **fails closed with no feed** (`ServiceError`) rather than idling a
    tick-driven loop; on stop, drains in-flight cycles up to the timeout then
    cancels (the sync loop's graceful-drain equivalent).
- `application/factory.py` — `build_async_daemon(mode, market_ids, config)`:
  composes the async daemon over the **same** `TradingOrchestrator` services and
  the same deterministic symbol->market map as the sync loop, and wires a real
  `ParetoWebSocketIngestor` when `data_collection.binance.streaming` is enabled
  (a broken transport degrades to "no feed" and the daemon then fails closed).
- `application/orchestrator.py` — public read-only `cycle_executor` property so
  the async daemon provably drives the orchestrator's own real executor.

---

## Quality gates (measured, not declared)

- Full suite: **2207 passed, 7 skipped** (up from 2193/7).
- Coverage: **100.00%** — 0 missing of 12,590 statements; gate remains
  `fail_under = 100`.
- `pyright src/traderos/`: **0 errors, 0 warnings, 0 informations**.
- `ruff check src/traderos/ tests/`: **clean**.

## Honesty notes

- Moving the cycle to a worker thread is only correct because the DB layer is
  the OT-011 thread-safe wrapper (or PostgreSQL). This must be stated rather than
  asserted: the isolation protection is real exactly where the wrapper is real.
- The async daemon does **not** yet capture every guardrail of the sync
  `DaemonController` (supervision heartbeat, HA failover leasing, broker
  reconciliation hooks, fatal handler) — those remain on the sync loop and are a
  future layer. The async loop is genuine and proven for the tick-driven path it
  claims, and claims no more.
- The sync daemon (`DaemonController`) remains the CLI default; the async loop is
  the tick-driven path proven to hit the same real submission boundary. The
  operator choosing async must enable `data_collection.binance.streaming`
  (streaming feed), which the factory already requires.
