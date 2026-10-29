# TraderOS — Core Loop Truth

**Version:** 1.0
**Date:** 2026-07-31
**Author:** Programme A — Core Loop Integrity pass
**Basis:** Source read line-by-line and re-runnable commands against the working tree (HEAD `66dfff1`, plus `docs/AUDIT_GROUND_TRUTH.md` uncommitted). Every claim below is pinned to `file:line`.

> **Purpose.** This is the canonical, source-pinned description of the trading core loop (signal → risk → size → preflight → order → broker → ack/fill → portfolio → metrics → audit → persistence → recovery → next cycle), the Trade state machine, the portfolio accounting model, and every verified defect that prevents a true *closed* loop. It is the reference for the Programme A fixes and the basis for `CORE_LOOP_EVIDENCE.md`.

---

## 1. The Core Loop — As Built

The system has two independent "loops". They share the strategy/analysis/risk/execution primitives but do **not** share the same portfolio accounting path.

### 1.1 Live / Paper loop — `CycleExecutor.run()`

Source: `src/traderos/application/cycle_executor.py`

```
cycle.start (event)
   │
   ▼
fetch candles            data_ingestion.fetch_candles(mid, limit=100)   :96-97
   │
   ▼
compute indicators       analysis.compute_sma(20), compute_atr(14)      :98-106
   │                      defaults: sma_20=close_price, atr_14=close*0.01
   ▼
for each registered strategy                                               :109
   │
   ├─ build MarketState  indicators {close,high,low,volume,sma_20,atr_14} :115-126
   │                      high/low/volume are FABRICATED (close*1.01, close*0.99, 1000.0)
   │
   ├─ strategy.evaluate → SignalResult | None                             :127-129
   │
   ├─ signal_service.process_evaluation → persist Signal, provenance      :131-140
   │
   ├─ PREFLIGHT #1      preflight_service.check(live_mode)                :154-161
   │
   ├─ risk.can_trade(positions)                                           :162-166
   │                      positions = get_summary(0).open_positions
   │
   ├─ risk.assess_trade(price, confidence, atr, equity)                   :169-176
   │                      atr passed as close_price*0.01 (recomputed, not real ATR)
   │
   ├─ qty = portfolio.size_position(cash, confidence)                     :177-180   ← DOLLARS used as qty
   │
   ├─ PREFLIGHT #2      preflight_service.check(live_mode)                :185-192   ← duplicate of #1
   │
   ├─ fill = broker.place_market_order(mid, side, qty, close_price)       :194-196
   │
   ├─ if fill.filled:                                                       :197
   │    ├─ open_trade(signal_id, mid, side, qty, price)                    :198-208
   │    ├─ if fill.order_id: trade.submit(order_id); update_trade           :209-211
   │    ├─ trade.fill(fill_qty, fill_price); update_trade                  :212-213   ← RAISES if no order_id (PENDING→FILLED)
   │    ├─ kill_switch.record_success()                                    :228
   │    └─ metrics.counter("trades.executed")                              :229
   │    └─ ✗ positions NEVER created — fill_trade() is never called
   │
   └─ else: kill_switch.record_failure()                                   :231
   │
   ▼
finally: metrics.counter("cycles.completed")                                :244-246  ← per-STRATEGY, not per-cycle
   ▼
health.report_healthy / report_unhealthy                                   :247, 250
   ▼
duration = perf_counter diff; metrics.timing("cycle.duration_ms").stop()   :252-253  ← timing started+stopped at same instant
   ▼
cycle.complete (event) → CycleResult(mid, signals, trades, errors, duration, t) :256-270
```

### 1.2 Backtest loop — `BacktestingService.run()`

Source: `src/traderos/domain/services/backtesting_service.py`

Self-contained (no event bus, no audit, no kill switch). Owns its own cash/position accounting in local variables (`cash`, `position_qty`, `equity_curve`), computes indicators from the candle window directly (lines 102-123), and sizes by `qty = signal.confidence * 10` (line 137). **It is a separate, internally-consistent loop and is not affected by the live-loop defects — but it is also not evidence for them.**

`CycleExecutor.run()` short-circuits in `BACKTEST` mode (cycle_executor.py:89-93) and returns an empty result; backtests never run through the cycle.

---

## 2. The Trade State Machine — Source of Truth

Source: `src/traderos/domain/entities/trade.py` `_VALID_TRANSITIONS` (lines 29-55). Guarded by `_guard_transition` (65-67) → raises `InvalidTradeTransitionError`.

| From | → Allowed | Terminal? |
|------|-----------|-----------|
| PENDING | SUBMITTED, CANCELLED, REJECTED | no |
| SUBMITTED | ACKNOWLEDGED, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED | no |
| ACKNOWLEDGED | PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED, EXPIRED | no |
| PARTIALLY_FILLED | FILLED, CANCELLED, REJECTED, EXPIRED | no |
| FILLED | — | **yes** |
| CANCELLED | — | **yes** |
| REJECTED | — | **yes** |
| EXPIRED | — | **yes** |

`Trade.fill(fill_qty, fill_price)` requires a pre-state of SUBMITTED/ACKNOWLEDGED/PARTIALLY_FILLED. **`PENDING → FILLED` is invalid** (trade.py:30, 104-110).

The idempotent broker-event coordinator `OrderEventEngine.apply()` (application/order_event_engine.py:29-91) transitions via the same entity methods, deduplicates by `event_id` (or a composite key), and calls `persist(trade)` + `portfolio_update(trade)` callbacks. It is correctly built but **is not wired into `CycleExecutor`** (grep: zero production callers of `OrderEventEngine`).

---

## 3. Portfolio Accounting Model — As Built

Source: `src/traderos/domain/services/portfolio_service.py`

| Method | Behavior | Production callers |
|--------|----------|--------------------|
| `get_summary(cash)` :31-42 | equity = cash + Σ qty·current_price; open positions from `position_repo.list_open()` | cycle :162, :168 |
| `size_position(cash, confidence)` :44-52 | **returns `cash * min(0.02·confidence·10, 0.25)` — a dollar notional** | cycle :177, paper :216 |
| `open_trade(...)` :66-90 | persists `Trade(PENDING)` | cycle :198 |
| `fill_trade(trade, fill_price)` :95-136 | auto-submits (`auto-{id}`) if PENDING without order id, fills, and **creates/updates a `Position`** (BUY +qty, SELL −qty) | **NONE** |
| `close_position(position, close_price)` :138-152 | realizes PnL via `Position.close()`, records audit | **NONE** |
| `update_position` :57-64 | mark-to-market | NONE |

Position entity (`domain/entities/position.py`): `quantity` signed (long >0, short <0), `pnl = qty·(current−entry)`, `close()` zeroes qty and accumulates `realized_pnl`.

Kill switch (`domain/services/risk_service.py`): `KillSwitch.record_failure/success` wired in the cycle (:228, :231); `KillSwitch.record_realized_pnl` (:55) and `PersistentKillSwitch.record_realized_pnl` (reconciliation_service.py:132) have **zero callers**. `can_trade()` trips on `abs(daily_realized_pnl) >= daily_loss_limit` (:67) — unreachable because realized PnL is never fed in; default `daily_loss_limit = inf` (:42).

---

## 4. Invariants (Target Truth)

What must hold for a closed, correct loop:

1. **Every accepted broker fill produces exactly one FILLED `Trade` and exactly one `Position` record** (created or updated). `I1`.
2. **A position is only ever closed through `PortfolioService.close_position`**, and that close reports realized PnL to the kill switch (daily loss limit) and to audit/metrics. `I2`.
3. **A `Trade` only ever transitions along `_VALID_TRANSITIONS`.** No entity method may be called from an illegal state; the state machine is the single authority. `I3`.
4. **Trade accounting is single-path.** `CycleExecutor` must not reimplement what `fill_trade` does (open→submit→fill→persist). `I4`.
5. **Sizing yields a positive share quantity** = `round(min(risk·confidence·10, max_alloc) · equity / price, 8)`; a $ figure is never used where a quantity is expected. `I5`.
6. **Every strategy registered in the registry can, in principle, emit a signal in the live cycle** (its required indicators are always populated from real candle data). `I6`.
7. **Preflight runs once per cycle per signal decision**, immediately before broker submission. `I7`.
8. **Metrics are truthful:** `cycles.completed` increments once per cycle; `cycle.duration_ms` records the measured duration. `I8`.
9. **Indicators are real.** No fabricated high/low/volume in `MarketState`. `I9`.
10. **Backtest and live/paper agree on order semantics** (direction, quantity units, PnL sign). `I10`.

---

## 5. Verified Defect Register

Severity: **P0** = corrupts core accounting / breaks the loop; **P1** = feature path dead; **P2** = observability/duplication.

| # | Severity | Defect | Evidence | Impact |
|---|----------|--------|----------|--------|
| D1 | P0 | **Fills never create positions.** The cycle does `open_trade`→`submit`→`fill`→`update_trade` but never calls `fill_trade`, the only method that creates/updates `Position` rows. `fill_trade` and `close_position` have zero production callers (grep). | cycle_executor.py:197-213; grep `fill_trade` = portfolio_service.py:95 only; grep `close_position` = portfolio_service.py:138 only | Position records never exist; `get_summary().open_positions` always empty; `can_trade()` position limits never engage; `close_position` can never fire; the portfolio "loop" is open-ended. |
| D2 | P0 | **Every paper-broker fill raises `InvalidTradeTransitionError`.** `PaperBrokerAdapter._fill_result` always returns `order_id=""` (paper_trading_service.py:65); the cycle only calls `submit()` when `fill.order_id` is truthy (:209), then unconditionally calls `trade.fill()` (:212) on a still-PENDING trade → invalid `PENDING→FILLED` transition. Trade persists stuck as PENDING; error swallowed into `errors` list. | paper_trading_service.py:65, 67-93; trade.py:30; cycle_executor.py:209-213 | In the system the factory actually builds (PaperBrokerAdapter, fill_probability=1.0), **no live/paper trade can ever complete**. |
| D3 | P0 | **`size_position` returns dollars, used as share quantity.** Returns `cash·alloc` (portfolio_service.py:51); cycle (:177) and paper (:216) pass the result straight to `place_market_order(quantity=…)`. At price 100 and $10k cash → qty up to 2500 units instead of ~25. Position sizes are wrong by ~2-3 orders of magnitude and not price-relative. | portfolio_service.py:51; cycle_executor.py:177-196; paper_trading_service.py:216-224 | Position value/PnL/equity numbers are meaningless; risk per trade is not respected. |
| D4 | P1 | **Realized PnL is never fed to the kill switch.** `KillSwitch.record_realized_pnl` (risk_service.py:55) and `PersistentKillSwitch.record_realized_pnl` (reconciliation_service.py:132) have zero callers; `close_position` records audit only. | grep `record_realized_pnl` → definitions only | Daily loss limit can never trip; circuit protection incomplete. |
| D5 | P1 | **Two of three registered strategies cannot fire in the cycle.** `MovingAverageTrend` requires `sma_50` (strategy_framework.py:60) — never supplied; `MeanReversion` requires `bb_upper_20`/`bb_lower_20` (:93-94) — never computed. Only `VolatilityBreakout` is reachable (needs `atr_14`/`close`, default ratio 0.01 blocks unless real candles are volatile). The entire analysis layer (Regime/Breakout/LiquidityZone/Session/Swing) is unwired. | grep `sma_50`/`bb_upper_20`/`bb_lower_20` → strategy_framework.py only; cycle MarketState keys :117-124 | Registered strategy surface is mostly dead; strategy registry promises more than the loop delivers. |
| D6 | P2 | **Cycle metrics lie.** `metrics.timing("cycle.duration_ms").stop()` at :253 creates a fresh `TimingContext` and stops it immediately — the real `duration` (:252) is never recorded; `cycles.completed` increments inside the per-strategy `finally` (:244-246), so it counts strategies-per-cycle, not cycles. | cycle_executor.py:244-246, 252-253; metrics.py:68-77 | Dashboards show duration≈0 and N× inflated cycle counts. |
| D7 | P2 | **Double preflight.** Identical `preflight_service.check(live_mode)` calls at :154-161 and :185-192 (broker reconciliation runs twice per signal; second is 20 lines after the first). | cycle_executor.py:154-161 vs 185-192 | Duplicate work; risk of divergence between the two checks. |
| D8 | P2 | **Fabricated market data in `MarketState`.** `high=close·1.01`, `low=close·0.99`, `volume=1000.0` (:119-121) even when real candles exist. | cycle_executor.py:117-124 | Any strategy reading high/low/volume computes on synthetic data. |
| D9 | P2 | **ATR/equity recomputed ad hoc in cycle.** `atr` passed to `assess_trade` is `close_price·0.01` (:172) even when a real ATR was computed at :106. | cycle_executor.py:104-106, 169-174 | Risk assessment does not use the real ATR. |

---

## 6. How the Tests Mask These Defects

| Defect | Masking test behavior |
|--------|----------------------|
| D1 (no positions) | Tests assert on trades/`CycleResult.trades`, never on `position_repo` contents after a run. `_MockBroker` returns `order_id="ord1"` (non-empty) so the submit path is exercised and no exception escapes; position absence is never asserted. |
| D2 (empty order_id) | The only brokers in tests supply a non-empty `order_id`; `PaperBrokerAdapter` itself is not exercised through `CycleExecutor`. |
| D3 (dollar sizing) | `test_portfolio_service.test_size_position` asserts `size == 10000.0·min(0.02·0.8·10, 0.25)` — it pins the dollar-returning bug as expected behavior. `test_preflight_execution_integration` mocks `size_position.return_value = 0.5`. |
| D4 (realized PnL) | No test feeds a close through `KillSwitch`. |
| D5 (dead strategies) | Strategy unit tests call `evaluate` with hand-built indicator dicts; no test asserts that the **cycle** supplies those keys. |
| D6 (metrics) | No test asserts `cycles.completed` count or `cycle.duration_ms` gauge value after a multi-strategy cycle. |
| D7 (double preflight) | Preflight tests assert behavior, not call count. |
| D8 (fabricated data) | No test inspects the `MarketState.indicators` the cycle builds. |

---

## 7. Target State (Post-Programme A)

1. `CycleExecutor` fill path routes through `PortfolioService.fill_trade` (handles both the with-order-id and no-order-id cases) — closing D1+D2+D4-path (I1, I2, I3, I4).
2. `size_position(cash, confidence, price)` returns share quantity; all callers updated — D3 (I5).
3. Position close (e.g., a future `close_position` caller / exit logic) feeds `KillSwitch.record_realized_pnl` and `PersistentKillSwitch` — D4 (I2).
4. Cycle populates `sma_50`, `bb_upper_20`, `bb_lower_20` (and real high/low/volume) from `AnalysisService` on real candles; the regime/breakout/liquidity/session/swing layer is wired so all registered strategies can fire — D5, D8, D9 (I6, I9).
5. Single preflight immediately before broker submission; `cycles.completed` once per cycle; `cycle.duration_ms` records the measured duration — D6, D7 (I7, I8).
6. New tests assert: a filled cycle creates exactly one Position; an empty-order-id fill completes; `PENDING→FILLED` is rejected; `close_position` reports realized PnL; all registered strategies can emit via the cycle's indicator set; preflight called exactly once; metrics counts are exact.
