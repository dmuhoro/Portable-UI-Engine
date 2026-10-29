# Sprint 34 — Test coverage 95.16% → 97.07% (flagged offenders to 100%)

**Period:** 2026-08-11
**Objective:** Close the remaining coverage gap from the 95.16% baseline
(588 missing statements) to ≥97%, and raise the `pyproject.toml` gate from 70%
to 97% so the achieved level is enforced. Every offender flagged by the
baseline measurement was taken to 100% (or its residual lines proven covered
by the full suite), so the new gate is backed by tests, not by a relaxed
measurement.

## Work Completed

### Baseline
- Full-suite measurement on the final Sprint 33 state: **12152 statements,
  588 missing, 95.16%** (threshold 70%). Offenders ranked by missing lines.

### Batch A — flagged infrastructure + domain offenders (all 100%)
- `application/factory.py` (28), `infrastructure/cache.py` (22),
  `repositories/sqlite/markets.py` (21), `domain/services/strategy_framework.py`
  (19), `domain/services/reconciliation_service.py` (18),
  `infrastructure/monitoring.py` (17) — each closed with functional edge tests
  (`tests/test_factory_coverage.py`, `tests/test_sqlite_markets_repo.py`,
  `tests/test_reconciliation_service_coverage.py`, extended
  `tests/test_cache.py`/`test_strategy_framework.py`/`test_monitoring.py`).

### Batch B — API layer (operator.py, security.py, market.py all 100%)
- `tests/test_market_api.py` (16) — market overview/candles/symbols/indicators,
  backtest success+failure, observations, ingest/research 503s, no-source 404;
  two tests were silently passing on the wrong 404 until the standalone apps
  called `app.include_router(router)` (FastAPI/Starlette 1.3.1 lazy
  `_IncludedRouter`).
- `tests/test_api_security_edges.py` (20) — session-token seam (valid/invalid/
  no-key-when-enabled → 401), `require_operate` 403s, `require_sse`
  open/accept/forbid, `auth_info`, auth boundary with `TRADING_MODE=live`.
- `tests/test_operator_api_edges.py` — LIVE cash branches, equity-curve loop,
  readiness broker-failure, workflow idle/advance, strategy lifecycle errors
  (compare/review/enable/disable/promote/archive/clone), probes, order
  normalization, session report json+markdown, SSE keepalive `continue` path
  (requires pulling a 3rd frame before the generator closes at the yield).

### Batch C — remaining offenders (all 100%)
- `infrastructure/collectors/alpaca_collector.py` (24) — new
  `tests/test_alpaca_collector.py`: `_frame_interval` mappings, env-key
  fallback, df-None, MultiIndex vs plain-index parsing, string-timestamp
  branch. Gotcha: `TimeFrame.Minute` is a `classproperty` returning a fresh
  object per access with identity `__eq__` — tests compare `amount`/`unit`.
- `repositories/sqlite/signals.py`, `indicators.py`, `historical_candles.py`
  (get_active/get_by_strategy/get_range, get_by_name/get_latest, load/count
  start/end/limit + dict-row branch) in `tests/test_sqlite_repos.py` /
  `tests/test_historical_data_service.py`.
- `repositories/in_memory/research.py` (get_by_symbol/get_by_observation/
  get_by_hypothesis/get_by_experiment/get_by_result/get_by_tags) in
  `tests/test_in_memory_repos.py`.
- `notifiers/webhook_notifier.py` — urllib ImportError fallback flags
  (re-import with `__import__` blocked), and the `urlopen is None` RuntimeError
  inside the retry closure (reached by making the retry seam null out `urlopen`
  after the guard passes).

## Belt-and-suspenders checks
- Full suite on the final state: **1907 passed / 7 skipped**, coverage
  **97.07%** (356 missing of 12152; `--cov-fail-under=97` passes).
- Gate raised in `pyproject.toml`: `fail_under = 97` (was 70) with
  `--cov=traderos` in addopts so the gate measures the package, not the tests.
- 110 of 121 files report 100% (`--skip-covered`); every file below 97% has a
  residual line count of ≤1-2 statements and is a defensive/`except` branch or
  an operator-only path (Postgres repos, live-broker failure branches).
- Removed a stray accidental file (`src/traderos/interfaces/api/market.py,cover`).

## Not done (honest)
- The residual 3% is dominated by defensive `except`/guard branches, Postgres-
  backed repos (need a live PG container), and live-broker/network failure
  paths (Alpaca crypto feed, yfinance) — deliberately not faked with mocks
  that would claim protection the real path does not provide.
- Evidence drills re-ran today (05:36 UTC) as part of the ongoing evidence
  cadence: the frozen Binance BTCUSDT 1h CSV was re-fetched (newest ~1y window,
  oldest 47 rows dropped); the G-06 oracle conformance lock is unaffected
  (2/2 PASS against the committed reference, trades=55 / withheld=18), and the
  real-market walk-forward still shows **no positive expectancy after full
  costs on OOS data** — the honest callout stands.
