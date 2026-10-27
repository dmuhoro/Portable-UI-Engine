# TraderOS — Core Loop Evidence

**Version:** 1.0
**Date:** 2026-07-31
**Author:** Programme A — Core Loop Integrity pass
**Companion:** `docs/engineering/CORE_LOOP_TRUTH.md` (source-pinned defect register D1–D9 and invariants I1–I10)
**Basis:** Working tree post-fix, HEAD `66dfff1` + Programme A changes (uncommitted at time of writing). Every claim below is backed by a re-runnable command and/or a pinned `file:line`.

> **Purpose.** This file records *how* each verified defect (D1–D9) was closed, the exact code change, the regression test that proves it, and the post-fix machine truth. It is the evidence trail for Programme A — Core Loop Integrity.

---

## 1. Baseline (Pre-Fix Machine Truth)

Recorded at HEAD `66dfff1` before any Programme A change:

| Gate | Result | Command |
|------|--------|---------|
| Tests | **832 passed** | `python3 -m pytest -q` |
| Coverage | **84.42%** | same run (cov report) |
| Ruff | **11 pre-existing errors, all in tests** | `ruff check src/traderos` → clean; 11 errors confined to test files (`test_dependency_direction`, `test_audit_integrity`, `test_backup`, `test_cycle_executor`, `test_preflight_service`) |
| Pyright | **0 errors** | `pyright src/traderos` |

---

## 2. How Each Defect Was Closed

### D1 (P0) — Fills never created positions

**Change.** `CycleExecutor.run()` now routes every accepted fill through the only method that creates/updates a `Position` row — `PortfolioService.fill_trade` — instead of the `open_trade → submit → fill → update_trade` sequence that left the position repo untouched.

- Before: `cycle_executor.py` (baseline):197-213 — `open_trade`, conditional `submit`, direct `trade.fill`, `update_trade`; zero `fill_trade` calls in production (grep: only `portfolio_service.py:95`).
- After: `src/traderos/application/cycle_executor.py:221-237` — `open_trade(...)` then, for both the with-order-id (`fill.order_id` truthy → `submit` at :232-234) and no-order-id cases, `portfolio_service.fill_trade(trade, fill_price=fill.fill_price)` at :235-237. `fill_trade` auto-submits a PENDING trade without an external order id as `auto-{trade.id}` and fills it, then creates/updates the `Position` (`portfolio_service.py:100`).

**Proof.** `tests/test_core_loop_invariants.py::test_fill_without_order_id_completes_and_creates_position` and `test_fill_with_order_id_records_external_id_and_sizes_shares` — full cycle runs against in-memory `trade_repo`/`position_repo`, asserting exactly one FILLED trade and one open `Position` row with `quantity ==` the share-sized fill.

### D2 (P0) — Every paper-broker fill raised `InvalidTradeTransitionError`

**Change.** Same `fill_trade` routing (above). The root cause was `PaperBrokerAdapter._fill_result` returning `order_id=""` (`paper_trading_service.py:65`), leaving the trade PENDING after `open_trade`, so the unconditional `trade.fill()` was an illegal `PENDING→FILLED` transition (trade.py:30). `fill_trade` handles the no-order-id case by auto-submitting (`auto-{trade.id}`) before filling (`portfolio_service.py:100`).

**Proof.**
- `tests/test_core_loop_invariants.py::test_paper_broker_path_completes` — end-to-end path through `PaperBrokerAdapter` (which returns `order_id=""`), asserting the trade reaches FILLED and a position exists, with no error in `CycleResult.errors`.
- `tests/test_core_loop_invariants.py::test_pending_to_filled_transition_rejected` — asserts `trade.fill()` directly on a PENDING trade still raises `InvalidTradeTransitionError` (state machine preserved; the fix routes *through* it, not around it).

### D3 (P0) — `size_position` returned dollars, used as share quantity

**Change.** `PortfolioService.size_position(cash, confidence, price)` now returns **shares**: `round(cash * min(risk_per_trade * confidence * 10, max_allocation) / price, 8)`; `price <= 0` returns `0.0` (`portfolio_service.py:46-57`).

Callers updated to pass the price:
- `cycle_executor.py:199-203` → `size_position(cash=cash, confidence=signal.confidence, price=close_price)`.
- `paper_trading_service.py:216` → same `price=close_price` argument.

**Proof.** `tests/test_portfolio_service.py::test_size_position_returns_shares` — pins share semantics: at $10k cash, confidence 0.8, price 100 → `0.02·0.8·10/100 = 1600/100 = 16.0` shares (not `1600.0` dollars); `price=0` and `confidence=0` return `0.0`.

### D4 (P1) — Realized PnL never reached the kill switch

**Change.**
- `PortfolioService` gains a `risk_service: RiskService | None` field (`portfolio_service.py:31`); `close_position` reports realized PnL: `if self.risk_service is not None: self.risk_service.record_realized_pnl(realized)` (`portfolio_service.py:150-151`).
- `RiskService.record_realized_pnl` forwards to `kill_switch.record_realized_pnl` and, when present, `persistent_kill_switch.record_realized_pnl` (`risk_service.py:111-115`).
- Composition root wires the link: `factory.py` sets `portfolio_service.risk_service = risk_service` after constructing both.

**Proof.** `tests/test_core_loop_invariants.py::test_close_position_feeds_realized_pnl_to_kill_switches` — fills a BUY position through the cycle, closes it via `PortfolioService.close_position`, and asserts the kill switch's `daily_realized_pnl` reflects the realized gain; `test_daily_loss_limit_trips_after_realized_loss` — a large realized *loss* pushes `daily_realized_pnl` past `daily_loss_limit` and trips `can_trade`.

### D5 (P1) — Two of three registered strategies could never fire in the cycle

**Change.** `CycleExecutor.run()` now computes and supplies the full indicator set to every strategy's `MarketState` from real candle data:
- `sma_50` via `analysis.compute_sma(candles, 50)` (`cycle_executor.py:115-117`)
- `bb_upper_20` / `bb_lower_20` via `analysis.compute_bollinger_bands(candles, 20, 2.0)` (:121-125)
- real `high` / `low` / `volume` from the last candle (:109-111)
- real `atr_14` from `compute_atr(candles, 14)` (:118-120)
- fallbacks to `close_price` / `close*0.01` / fabricated values only when `candles` is empty (:99-106).

**Proof.**
- `tests/test_core_loop_invariants.py::test_all_builtin_strategies_can_fire_on_cycle_indicator_set` — asserts `MovingAverageTrend`, `VolatilityBreakout`, and `MeanReversion` each produce a non-None evaluation against the exact indicator dict the cycle builds.
- `tests/test_core_loop_invariants.py::test_cycle_uses_real_candle_data_in_market_state` (D8) — asserts `state.indicators["high"/"low"/"volume"]` equal the last candle's real values, not the fabricated `close*1.01/0.99/1000.0`.
- `tests/test_core_loop_invariants.py::test_no_signal_on_fallback_indicators` — with no candles the fabricated fallback set must produce no signal (nothing fires, nothing falsifies).

### D6 (P2) — Cycle metrics lied

**Change.**
- `cycles.completed` moved out of the per-strategy `finally` to exactly once per cycle: `cycle_executor.py:274`.
- `cycle.duration_ms` records the measured duration: `duration = (time.perf_counter() - start) * 1000` at :275, then `self._metrics.gauge("cycle.duration_ms", duration)` at :276 (the baseline called `timing(...).stop()` at the same instant, recording ≈0).

**Proof.** `tests/test_core_loop_invariants.py::test_cycle_metrics_are_per_cycle_and_duration_recorded` — a multi-strategy cycle increments `cycles.completed` exactly once and records a non-zero `cycle.duration_ms` gauge.

### D7 (P2) — Double preflight — **by design, retained**

The two checks are *not* duplicates in intent: the first (:176-183) is the per-signal go/no-go gate; the second (:208-215) is the TOCTOU re-check immediately before broker submission, required by `tests/test_preflight_execution_integration.py` (Programme Ω signature test, `test_preflight_execution_integration.py::test_toctou_race_detection`). An attempted removal was reverted; the re-check is a deliberate defensive re-validation at the last possible moment. Reclassified as **by-design** in `CORE_LOOP_TRUTH.md` §5. No code change.

### D8 (P2) — Fabricated market data in `MarketState` — closed (see D5)

**Change.** Real `high`/`low`/`volume` from `candles[-1]` when candles exist (`cycle_executor.py:109-111`).

**Proof.** `tests/test_core_loop_invariants.py::test_cycle_uses_real_candle_data_in_market_state` (above).

### D9 (P2) — ATR recomputed ad hoc in the cycle

**Change.** `assess_trade` now receives the real ATR: `atr=atr_14` computed at :118-120 and threaded through at :191-196 (baseline passed `close_price * 0.01`).

**Proof.** `tests/test_core_loop_invariants.py::test_cycle_passes_real_atr_to_risk` — a spy `RiskService` asserts `assess_trade` was called with `atr ==` the real computed ATR, not `close_price*0.01`.

---

## 3. New Regression Surface

`tests/test_core_loop_invariants.py` (11 tests) — invariant regressions I1/I2/I3/I5/I6/I8/I9 plus D1–D6/D8/D9 closes:

| Test | Guards |
|------|--------|
| `test_fill_without_order_id_completes_and_creates_position` | D1, I1 |
| `test_paper_broker_path_completes` | D2 |
| `test_pending_to_filled_transition_rejected` | D2 (state machine intact), I3 |
| `test_fill_with_order_id_records_external_id_and_sizes_shares` | D1, D3, I1, I5 |
| `test_close_position_feeds_realized_pnl_to_kill_switches` | D4, I2 |
| `test_daily_loss_limit_trips_after_realized_loss` | D4, kill-switch trip |
| `test_all_builtin_strategies_can_fire_on_cycle_indicator_set` | D5, I6 |
| `test_no_signal_on_fallback_indicators` | D8, I9 |
| `test_cycle_uses_real_candle_data_in_market_state` | D8, I9 |
| `test_cycle_passes_real_atr_to_risk` | D9 |
| `test_cycle_metrics_are_per_cycle_and_duration_recorded` | D6, I8 |
| `test_size_position_returns_shares` (in `test_portfolio_service.py`) | D3, I5 |

---

## 4. Post-Fix Machine Truth

Run on 2026-07-31 against the working tree. All commands from repo root. `python` does not exist in this environment; **`python3` is the interpreter.**

### 4.1 Full suite (authoritative, deterministic ordering)

```
$ python3 -m pytest -q -p no:randomly
======================= 843 passed, 19 warnings in 34.38s =======================
```

Coverage (same run, `--cov=.` in `pyproject.toml` addopts):

```
TOTAL   6942   1067    85%
Required test coverage of 70.0% reached. Total coverage: 84.63%
```

**843 passed** (baseline 832 → +11 invariant tests), **84.63%** coverage (baseline 84.42% → +0.21pt), threshold 70% exceeded. (Warning count varies by run/environment; unrelated to the diff.)

### 4.2 Lint — all touched files clean

```
$ ruff check src/traderos tests/test_core_loop_invariants.py tests/test_cycle_executor.py tests/test_portfolio_service.py
All checks passed!
```

### 4.3 Types

```
$ pyright src/traderos
0 errors, 0 warnings
```

### 4.4 Known environmental flakes (unrelated to this change)

`tests/integration/test_api.py::test_orchestrator_start_stop` and the `stress_tick_ingestion` / throughput benchmarks in `tests/performance/` are **load/timing sensitive**: they pass in isolation, pass in their own files, and passed in 7/7 consecutive full-suite runs taken for this evidence set (3 with `--tb=long`, 4 with coverage). One intermittent failure was also observed under load as `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread` inside the Starlette TestClient layer — same root class (orchestrator thread racing API shutdown), same file, not a regression. Neither file nor its dependencies (`daemon_controller.py`, `server.py`, `StreamingMarketDataService`) is touched by the Programme A diff (verified: `git diff --stat` shows only `cycle_executor.py`, `factory.py`, `paper_trading_service.py`, `portfolio_service.py`, `risk_service.py` + the three test files). Failures observed earlier were transient system-load artifacts, not regressions.

---

## 5. Scope Guard

Per the Code Freeze for Programme A: **correctness only.** No new features, dashboards, or UI. The backtest loop (`BacktestingService.run`) is a separate internally-consistent loop (`CORE_LOOP_TRUTH.md` §1.2) and was deliberately not modified. `CycleExecutor.run()` still short-circuits in `BACKTEST` mode (`cycle_executor.py:89-93`). The double-preflight remains by design (§2 D7).

## 6. Repro Commands (copy-paste)

```bash
python3 -m pytest -q -p no:randomly                        # full suite → 843 passed
python3 -m pytest tests/test_core_loop_invariants.py -q    # new invariant regressions → 11 passed
ruff check src/traderos tests/test_core_loop_invariants.py tests/test_cycle_executor.py tests/test_portfolio_service.py
pyright src/traderos
```
