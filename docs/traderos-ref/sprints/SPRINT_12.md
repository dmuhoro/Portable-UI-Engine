# Sprint 12 — Programme A: Core Loop Integrity

**Period:** 2026-07-31
**Objective:** Make the single trading cycle *correct* — close every verified core-loop defect (D1–D9) and pin the loop's invariants with regression tests. This is a **correctness-only** Code Freeze sprint: no features, dashboards, or UI.

**Reference docs:** `docs/engineering/CORE_LOOP_TRUTH.md` (execution graph, invariants I1–I10, defect register), `docs/engineering/CORE_LOOP_EVIDENCE.md` (per-defect proofs and machine truth).

---

## Core-Loop Defect Register

| Defect | Severity | Root cause | Resolution |
|--------|----------|------------|------------|
| D1 | P0 | `CycleExecutor.run()` filled trades directly and never created `Position` rows | Route every accepted fill through `PortfolioService.fill_trade` (`cycle_executor.py:221-237`), the only method that creates/updates positions |
| D2 | P0 | `PaperBrokerAdapter` returns `order_id=""`, leaving trades PENDING; unconditional `trade.fill()` then raised `InvalidTradeTransitionError` | `fill_trade` auto-submits a PENDING trade without an external id as `auto-{trade.id}` before filling (`portfolio_service.py`) |
| D3 | P0 | `size_position` returned dollars, used as share quantity | Returns shares: `round(cash * alloc / price, 8)`; `price <= 0 → 0.0` (`portfolio_service.py:46-57`); both callers pass `price=close_price` |
| D4 | P1 | Realized PnL never reached the kill switch | `PortfolioService.risk_service` field; `close_position` → `risk_service.record_realized_pnl`; `RiskService` forwards to `KillSwitch` + `PersistentKillSwitch`; wired in `factory.py` |
| D5 | P1 | 2/3 registered strategies could never fire (indicator set incomplete) | Cycle supplies real `sma_20/50`, `bb_upper_20/lower_20`, `atr_14`, high/low/volume to every strategy's `MarketState` |
| D6 | P2 | Cycle metrics lied (per-strategy increment, `duration_ms` ≈ 0) | `cycles.completed` counted once per cycle; `cycle.duration_ms` records measured `perf_counter` duration |
| D7 | P2 | Double preflight | **By design** (TOCTOU re-check required by `test_preflight_execution_integration.py`); reclassified in truth doc §5, no code change |
| D8 | P2 | Fabricated market data in `MarketState` | Real `candles[-1]` high/low/volume when candles exist; fallbacks only when empty |
| D9 | P2 | ATR recomputed ad hoc (`close_price * 0.01`) | `assess_trade` receives the real computed `atr_14` |

**Result: 8/9 defects closed (D7 by-design).**

## Invariant Regression Suite

`tests/test_core_loop_invariants.py` (11 tests) pins invariants I1/I2/I3/I5/I6/I8/I9 plus the D1–D6/D8/D9 closes:

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

## Key Files Created/Modified

### Bug fixes
| File | Change |
|------|--------|
| `src/traderos/application/cycle_executor.py` | **D1/D2**: fills via `fill_trade` incl. no-order-id; **D3**: `size_position(..., price=close_price)`; **D5/D8/D9**: real indicators + candle data in `MarketState`; **D6**: single `cycles.completed`, duration gauge |
| `src/traderos/domain/services/portfolio_service.py` | **D3**: share semantics in `size_position`; **D4**: `risk_service` field + realized-PnL reporting on close; **D1/D2**: `fill_trade` auto-submit path |
| `src/traderos/domain/services/risk_service.py` | **D4**: `record_realized_pnl` forwards to KillSwitch + PersistentKillSwitch |
| `src/traderos/domain/services/paper_trading_service.py` | **D3**: sizing caller passes `price=close_price` |
| `src/traderos/application/factory.py` | **D4**: wires `portfolio_service.risk_service = risk_service` after construction |

### New test files
| File | Tests |
|------|-------|
| `tests/test_core_loop_invariants.py` | **11 invariant regression tests** (I1/I2/I3/I5/I6/I8/I9 + D1–D6/D8/D9 closes) |

### Modified test files
| File | Change |
|------|--------|
| `tests/test_cycle_executor.py` | Realistic mocks for `test_candles_processed_with_data_ingestion`; E501 wrapped |
| `tests/test_portfolio_service.py` | Aligned with share-semantics sizing |

### New docs
| File | Purpose |
|------|---------|
| `docs/engineering/CORE_LOOP_TRUTH.md` | Execution graph, backtest path, `Trade._VALID_TRANSITIONS`, portfolio accounting model, invariants I1–I10, D1–D9 register, D7 by-design |
| `docs/engineering/CORE_LOOP_EVIDENCE.md` | Per-defect close proofs, regression table, post-fix machine truth, repro commands |
| `docs/AUDIT_GROUND_TRUTH.md` | Audit-chain ground truth (untracked prior; committed with this sprint) |

## Machine Truth

| Metric | Value |
|--------|-------|
| Total tests | **843 passing, 0 failures** (`python3 -m pytest -q -p no:randomly`) |
| New tests added (Programme A) | 11 |
| Coverage | **84.63%** (baseline 84.42%) — threshold 70% exceeded |
| Ruff | 0 errors on `src/traderos` + touched test files (11 pre-existing errors confined to untouched test files) |
| Pyright | 0 errors |
| Regressions | 0 (all touched diffs verified green over multiple consecutive runs) |

**Known environmental flake (unrelated to diff):** `tests/integration/test_api.py::test_orchestrator_start_stop` and `tests/performance/` benchmarks are load/timing-sensitive (incl. an intermittent `sqlite3.ProgrammingError` threading race under Starlette TestClient). They pass in isolation and in clean full-suite runs; the files and dependencies are untouched by this sprint. See `CORE_LOOP_EVIDENCE.md` §4.4.
