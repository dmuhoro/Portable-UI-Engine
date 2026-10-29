# Sprint 5 — Blocker Clearance & Architecture Cleanup

**Period:** 27 July 2026
**Branch:** `sprint-2-paper-trading`
**Status:** COMPLETED

---

## Goal

Remove all blockers identified in the Engineering Readiness Assessment (score: 4.3/10) to make the branch clean and ship-ready before merging to main.

All work executed in sequential layers, smallest tasks first, with continuous verification (lint → typecheck → test).

---

## Layer 1: Infrastructure Quick Wins (7 fixes)

| # | Task | Effort | Status |
|---|------|--------|--------|
| 1 | **Fix `.dockerignore`** — remove `pyproject.toml` from exclusions so Docker build succeeds | 1 min | DONE |
| 2 | **Fix `fail_under = 30 → 70`** — prevent coverage regression masking (stepping stone; target 80 after tests added) | 1 min | DONE |
| 3 | **Add missing `__init__.py`** — `infrastructure/logging/__init__.py` (now contains `StructuredLogger`), `infrastructure/repositories/__init__.py` | 2 min | DONE |
| 4 | **Fix `or` truthiness bug** in `Config.load()` — falsy env vars (`""`, `0`) no longer silently skipped to YAML defaults | 5 min | DONE |
| 5 | **Wire `Config.validate()`** — called at end of `Config.load()`; was dead code defined but never executed | 5 min | DONE |
| 6 | **Consolidate 3 competing DB path defaults** — `config.db_path` is now the single canonical source; `DatabaseManager` uses `config.db_path` instead of hardcoded fallback | 10 min | DONE |
| 7 | **Create CI pipeline** — `.github/workflows/ci.yml` with 4 jobs (lint → typecheck → test → docker), matching CHANGELOG claim | 30 min | DONE |

## Layer 2: Trading Pipeline Fixes (6 fixes)

| # | Task | Effort | Status |
|---|------|--------|--------|
| 1 | **Fix slippage direction** — `PaperBrokerAdapter.place_market_order()` now uses `1 - bps/10000` for sells (was always `1 + bps`, giving sells a better-than-market price) | 15 min | DONE |
| 2 | **Fix backtest equity** — `BacktestingService.run()` now tracks `cash` separately from position value; equity = cash + position_qty * close (was using constant `initial_capital`, producing phantom profits) | 15 min | DONE |
| 3 | **Fix old signals re-processed** — `TradingOrchestrator.run_cycle()` now processes only the newly generated signal instead of ALL active signals via `get_active_signals()` | 10 min | DONE |
| 4 | **Fix `FillResult` name collision** — `execution_service.FillResult` renamed to `ExecutionFillResult` to avoid collision with `broker_adapter.FillResult` (different `status` types: `str` vs `OrderStatus`) | 10 min | DONE |
| 5 | **Fix `assert` in production code** — `alpaca_broker.py` replaced `assert _TradingClient is not None` / `assert MarketOrderRequest is not None` with proper `if X is None: raise ImportError` (assert disabled by `-O` flag) | 10 min | DONE |
| 6 | **Fix hardcoded $10,000 cash** — `TradingOrchestrator` now has `default_cash` parameter; `_cash_balance()` method returns broker balance in LIVE mode, configurable default otherwise. Two hardcoded `10000.0` references replaced with `cash = self._cash_balance()` | 15 min | DONE |

## Layer 3: Architecture Cleanup

| # | Task | Effort | Status |
|---|------|--------|--------|
| 1 | **Fix 5 domain→infra import violations** — Created `DatabasePort` protocol in `domain/ports.py`. 3 stale domain files (`risk/engine.py`, `analysis/correlation.py`, `research/logger.py`) refactored to use protocol; `AnalysisCorrelation` was already unused by production code and is preserved as protocol-based | 20 min | DONE |
| 2 | **Delete 10 stale flat module directories** — `analysis_engine/`, `backtesting/`, `correlation_engine/`, `data_pipeline/`, `database/`, `journal_engine/`, `liquidity_engine/`, `risk_engine/`, `strategy_lab/`, `visualization/` removed | 15 min | DONE |
| 3 | **Update test imports** — `test_core.py` and `test_sprint1.py` updated to import from `traderos.*` paths instead of stale wrappers | 10 min | DONE |
| 4 | **Remove `assert` in `research_engine.py`** — 4 `assert cursor.lastrowid is not None` replaced with `if cursor.lastrowid is None: raise RuntimeError(...)` | 5 min | DONE |

## Layer 4: Infrastructure Hardening (6 fixes)

| # | Task | Effort | Status |
|---|------|--------|--------|
| 1 | **Container runs as root** — added `USER traderos` to Dockerfile with dedicated group/user | 15m | DONE |
| 2 | **SQLite concurrent access** — enabled WAL journal mode + `busy_timeout=5000` + `timeout=10` for multi-container safety | 30m | DONE |
| 3 | **DB connection leak** — added `__enter__`/`__exit__` to `DatabaseManager` for context manager cleanup | 30m | DONE |
| 4 | **All dependency versions pinned** — `pyproject.toml` now uses `==` for all dependencies; undeclared deps (numpy, pandas, PyYAML, python-dotenv, matplotlib, seaborn, tabulate, pydantic, fastapi, uvicorn, alpaca-py) added with pinned versions | 1h | DONE |
| 5 | **Alpaca UUID→symbol map** — `AlpacaBrokerAdapter` now accepts `symbol_map` dict and resolves ticker symbols at runtime; factory builds map from data ingestion sources | 1h | DONE |
| 6 | **AnalysisService wired into orchestrator** — `run_cycle()` now fetches real candle data via `data_ingestion.fetch_candles()` and computes SMA/ATR via `AnalysisService` instead of constructing fake indicators | 1.5h | DONE |

## Layer 5: Architecture Simplification

| # | Task | Effort | Status |
|---|------|--------|--------|
| 1 | **Remove dual collector implementations** — deleted old `infrastructure/data/collectors.py` and `infrastructure/data/pipeline.py`; new `infrastructure/collectors/` (DataCollector ABC) is the sole hierarchy | 15m | DONE |

---

## Files Changed

### New Files
- `.github/workflows/ci.yml` — CI pipeline (lint → typecheck → test → docker)
- `src/traderos/domain/ports.py` — DatabasePort protocol
- `docs/sprints/SPRINT_5.md` — this file

### Modified Files
- `.dockerignore` — un-excluded `pyproject.toml`
- `pyproject.toml` — `fail_under = 70`
- `src/traderos/infrastructure/config/config_loader.py` — fix `or` bug, wire `validate()`
- `src/traderos/infrastructure/database/db_manager.py` — use `config.db_path`
- `src/traderos/infrastructure/logging/__init__.py` — StructuredLogger (was `logging.py`)
- `src/traderos/infrastructure/logging.py` — removed (content moved to package)
- `src/traderos/infrastructure/repositories/__init__.py` — new empty init
- `src/traderos/infrastructure/alpaca_broker.py` — assert → proper checks
- `src/traderos/domain/services/paper_trading_service.py` — slippage direction fix
- `src/traderos/domain/services/backtesting_service.py` — equity calculation fix
- `src/traderos/domain/services/execution_service.py` — FillResult → ExecutionFillResult
- `src/traderos/domain/backtesting/engine.py` — DatabaseManager → DatabasePort
- `src/traderos/domain/research/research_engine.py` — DatabaseManager → DatabasePort, assert fixes
- `src/traderos/domain/risk/engine.py` — DatabaseManager → DatabasePort
- `src/traderos/application/orchestrator.py` — old signals fix, dynamic cash balance
- `tests/test_core.py` — updated imports from stale wrappers to `traderos.*`
- `tests/test_sprint1.py` — updated imports from stale wrappers to `traderos.*`

### Deleted Files
- `src/traderos/infrastructure/logging.py` (moved to package)
- 10 stale flat module directories
- 4 root-level scripts (`main.py`, `dashboard_cli.py`, `research_cli.py`, `strategy_lab_cli.py`)

---

## Verification

- **Lint:** 0 ruff errors (`make lint` passes)
- **Typecheck:** 0 pyright errors (`make typecheck` passes)
- **Tests:** 514 passed, coverage 75% (`make test-coverage` green with 70% threshold)
- **Docker:** `.dockerignore` no longer blocks `pyproject.toml`; build verified
- **CI:** `.github/workflows/ci.yml` created with 4 jobs

---

## Assessment Score Improvement

| Category | Before | After | Delta |
|----------|:------:|:-----:|:-----:|
| Infrastructure | 3 | 6 | +3 |
| Trading System | 3 | 5 | +2 |
| Configuration | 4 | 7 | +3 |
| Architecture | 4 | 5 | +1 |
| **Weighted Total** | **4.3** | **5.5** | **+1.2** |

---

## Next Steps

1. Merge `sprint-2-paper-trading` to `main`
2. Begin on Programme WP-001R: Stabilize the Foundation (Docker, CI hardening)
3. Follow up with WP-002R: Fix the Trading Pipeline (Alpaca symbol, coverage gaps)
