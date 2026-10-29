# Sprint 38 — Market Brain: the chart watcher fronting the real execution paths

**Period:** 2026-08-13
**Objective:** Give the Custom Expert Advisor a real "chart watcher". The Market
Brain is a per-market, tick-fed domain service that reads history + live ticks
into a `StateSnapshot` (regime, trend stage, volatility percentile, momentum,
RSI, liquidity) and returns ranked `Advice` whose risk fraction is hard-capped.
Wired into **both** real submission paths — the async tick daemon and the sync
`DaemonController` loop — an unreadable or below-threshold market **blocks the
cycle on the actual seam**, with an explicit, audited reason — no silent drops,
no fabricated edge. Seeded history and tick aggregates persist through the
durable candle store, so a restarted Brain replays the same state.

Slices A–D were built in order; each layer lands on the previous one.

---

## Slice A — domain chart watcher + async real-path gate (committed)

- `domain/services/market_brain_service.py` — `MarketBrainService`:
  - `seed_candles(market_id, candles)` — idempotent history ingestion (bar
    identity = timestamp + full OHLCV + timeframe, index-ordered).
  - `update_tick(market_id, tick)` — live-tick ring buffer (liquidity) +
    interval candle aggregation into the read series.
  - `snapshot(market_id)` — `StateSnapshot` from `AnalysisService` indicators
    (EMA20/50, ATR14, RSI14, Bollinger 20); trend stage from EMA alignment;
    momentum over the configured window; ATR percentile vs its own history;
    regime derived from stage (volatility names the regime only when the stage
    is unreadable — a flat tape is never "high volatility").
  - `advise(market_id)` — ranked `Advice`. **Fail closed**: insufficient data ->
    "brain warming up"; range-bound/unknown stage -> "no directional edge";
    confident trend below `action_threshold` -> explicit refusal. Every allowed
    `Move` carries `direction`, clamped `confidence`, and
    `risk_fraction <= max_risk_fraction` (volatility only ever **reduces** size).
- `application/async_daemon.py` — `AsyncDaemonController(brain=...)`: every fresh
  tick is read by the Brain *before* the real cycle; a blocked read audits
  `async.brain.blocked`, publishes the `brain.advice` event (allowed=False +
  reason), and returns — the real `CycleExecutor.run` is never invoked. An
  allowed read audits `async.brain.advice`, meters `brain_advised`, publishes
  the event with direction/confidence/risk, then runs the real cycle.
- `tests/test_market_brain_service.py` — seam proofs + real-signal reads
  (bull/bear/accumulation/distribution/oscillating/flat/high-vol) + the hard
  risk cap under extremes + event flow.

---

## Slice B — sync gate on the `DaemonController` loop + production config

The sync `DaemonController` — the loop `TradingOrchestrator.run_forever` drives —
now runs the **same** fail-closed Brain gate in front of its `_cycle_executor.run`:

- `application/daemon_controller.py` — `DaemonController(brain=...,
  brain_history_bars=...)`; `_brain_gate(brain, market_id)` warms the market
  (durable replay first, live-source seed fallback), then reads `advise`; an
  allowed read meters `sync_daemon.brain_advised` and audits `sync.brain.advice`;
  a refused read meters `sync_daemon.brain_blocks`, audits `sync.brain.blocked`,
  and publishes `brain.advice` (allowed=False) — the loop `continue`s before the
  real cycle seam. `get_status()` surfaces `brain.advised` when a brain is wired;
  no brain wired -> behaviour unchanged (parity).
- `application/factory.py` — `_build_market_brain(cfg, store=...)` reads
  `market_brain.*` (opt-in via `enabled`; a malformed or disabled section builds
  NO brain — fail closed). `build_orchestrator` wires the brain + `history_bars`
  into the `TradingOrchestrator`; `build_async_daemon` reuses the same brain for
  the async controller.
- `application/orchestrator.py` — `brain` + `brain_history_bars` fields passed
  through to the daemon controller.
- `tests/test_market_brain_sync_gate.py` — seam proof on the sync loop
  (unreadable brain -> `executor.run` never called, blocks+event counted;
  readable brain -> real cycle runs), no-brain parity, no-data-source fail
  closed, and factory config-knob wiring.

---

## Slice C — durable persistence / restart-safe replay

- `domain/services/market_brain_service.py` — `CandleStorePort` protocol
  (dependency-direction clean); `store` field; `warm_from_store(market_id,
  limit)` replays durable bars into a fresh Brain (False when no store/history);
  `seed_candles` and `update_tick` persist through the store when wired.
- `infrastructure/repositories/brain_candle_store.py` — durable adapter over
  the existing provider candle store, keyed `source="market_brain"` +
  `symbol=str(market_id)` + bar timeframe, upsert-idempotent by
  (timeframe, ts); `load_candles` reads across timeframes in timestamp order so
  the index-based indicators replay exactly.
- `infrastructure/repositories/sqlite/historical_candles.py` — `load` now
  accepts `timeframe=None` for cross-timeframe reads (existing callers
  unaffected).
- Both daemons warm **once per market** before their first read
  (`_brain_gate` / `_warm_brain_from_store`) so a restarted loop never reads an
  UNKNOWN market it has durable history for.
- `tests/test_market_brain_persistence.py` — restart identity (fresh brain reads
  identical state), idempotent seeding, aggregate-candle durability, the
  LAST-WINS honest boundary for same-timestamp tapes, and daemon warm-from-store
  before read/tick.

---

## Slice D — production live-wiring + end-to-end evidence

- `application/async_daemon.py` — `AsyncDaemonController(data_ingestion=...)`;
  `_warm_brain_from_store` now falls back to seeding the Brain from the live
  data source when the durable store is empty, so a fresh async deployment can
  actually read its chart (not silently UNKNOWN forever). With neither store nor
  live history the Brain stays UNKNOWN and blocks (fail closed).
- `application/factory.py` — `build_async_daemon` wires the orchestrator's real
  `data_ingestion` into the async controller.
- `scripts/evidence/run_market_brain_drill.py` — credential-free, network-free
  end-to-end drill over the **real** services (real sqlite, real observability,
  real event bus, real `CycleExecutor` seam): (1) sync fail-closed on the loop,
  (2) sync fail-closed with no data source at all, (3) restart-safe durable
  replay driving the real cycle, (4) async live-seed on first tick + warm-once,
  (5) async fail-closed with empty live source, (6) config wiring
  (enabled/disabled/malformed). Verdict PASS -> `2026-08-17_market_brain_drill.log`.
- Registered in the WP13 credential-free CI drill job
  (`scripts/evidence/run_ci_drills.py`, now **17 drills**) so a regression that
  silently weakens any of the six rails stops the build.
- `tests/test_market_brain_persistence.py` — async live-seed and empty-source
  fail-closed coverage.

---

## The real constraints discovered (enforced, not assumed)

- **Dependency direction**: the domain must not import infrastructure — the
  Brain consumes `_PriceTick` and `CandleStorePort` structural `Protocol`s; the
  daemons hand it the real `Tick` / durable adapter (structurally compatible).
- **Same-timestamp tapes**: `synthetic_candles` emits 220 bars at one timestamp.
  In-memory reads are strict index-based (the whole tape is read); the **durable
  projection is per-bar-timestamp and collapses such a tape deterministically
  LAST-WINS** — real exchange streams are timestamp-unique, so restart-safe
  proofs use timestamp-unique history (documented honest boundary, pinned in the
  tests and the drill).

## Quality gates (measured, not declared)

- Full suite: **2238 passed, 9 skipped**.
- Coverage: **100.00%** — 0 missing of 12,919 statements; gate remains
  `fail_under = 100`.
- `pyright` on the new/changed modules: **0 errors, 0 warnings** (strict).
- `ruff check src/ tests/`: **clean**; `black` and `isort`: **clean**.
- Evidence drill: `run_market_brain_drill.py` **6/6 PASS**, enforced in the CI
  drill job (17 credential-free drills).

## Honesty notes

- The Brain's advice is a directional (long/short) + risk-fraction *read*, not
  an order instruction. Order sizing, entry/exit rules, and live execution
  remain the EA's/strategy's decision and go through the same broker chain as
  before.
- Durable replay is restart-safe for timestamp-unique history; a same-timestamp
  synthetic tape collapses LAST-WINS in the durable seat (in-memory reads keep
  every bar).
- "Closing the Brain gap" means both execution paths are now fronted by a real
  market read with durable replay; it does **not** mean all execution risk is
  complete. No live exchange websocket feed has been exercised (the async
  pipeline still requires an operator-gated streaming feed; the drill drives the
  same decision point with the mock/live-source seams).
