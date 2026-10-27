# Sprint 23 — Real-data backtesting: unified Alpaca + Binance data foundation

**Period:** 2026-08-02
**Objective:** Make backtesting run on **real** market data from both Alpaca and
Binance through a single, durable, provider-neutral data model — so the backtest
engine produces truthful fills/metrics instead of synthetic steps, grounding
future automated trading on stored history.

**Scope (per directive):** production data layer (collectors, store, service),
the backtest engine + CLI wiring, tests, evidence, governance. No UI, HA, or
live-risk features.

**Reference docs:** `docs/architecture/`, `docs/reading/` (existing ADRs),
`docs/evidence/2026-08-02_sprint23_real_backtest_alpaca_binance.log`.

---

## Work Package Register

| ID | Work package | Gate |
|----|--------------|------|
| L1 | Provider-neutral historical model (`HistoricalDataService`) | live fetch + cache-recall identical for both providers |
| L2 | Durable candle store (`SQLiteHistoricalCandleRepository` + v007) | idempotent upsert; keyed `(source, symbol, timeframe, ts)` |
| L3 | Alpaca + Binance collectors behind one contract | live 1h bars fetched from both |
| L4 | Backtest engine fills + real indicators | strategies signal; fills counted |
| L5 | CLI `backtest --source/--symbol/--timeframe/--candles` | real-data backtest runnable from CLI |
| L6 | Tests + evidence (both providers) | full suite green; evidence log attached |

## Work Completed

### L1/L2 — Unified data model + durable store
- New `HistoricalDataService` (domain): normalizes `CollectorOHLCV` → domain
  `Candle`, `market_id = uuid5("traderos://{source}/{symbol}")`, cache-aware
  `get_candles(source, timeframe, symbol, ...)` with fetch → store → reuse.
- `SQLiteHistoricalCandleRepository` + migration `v007_historical_candles`
  (`UNIQUE(source, symbol, timeframe, ts)` + lookup index), so a trusted bar is
  reused instead of refetched.
- Fixed cache-read bug surfaced by the drill: cached rows key `ts` (epoch), not
  `timestamp` — normalization now handles both live `CollectorOHLCV` and cached
  dict rows. Fixed a raw-sqlite iterable-cursor bug in the repo (fetchall).

### L3 — Collectors
- `AlpacaCollector` via the crypto feed (`CryptoHistoricalDataClient`, e.g.
  `BTC/USD`) — any key grants read access, no per-symbol licensing constraints;
  `BarSet.df` normalised defensively.
- `CollectorType.ALPACA` added; Binance collector used for `BTCUSDT` (public).
- Architecture: collectors are **composed at the CLI layer**, not imported from
  domain — domain remains infrastructure-import-free (enforced by
  `tests/architecture/test_dependency_direction.py`).

### L4 — Backtest engine reality fixes
- Indicator set enriched to what the registered strategies actually consume
  (`sma_20`, `sma_50`, `bb_upper/mid/lower_20`, `atr_14`) — previously only
  `sma_20`/`atr_14` existed, so strategies could never signal → 0 fills.
- `run()` now counts fills into `metrics.total_trades` (was hard-coded 0).
- Guarded `mean_reversion` division-by-zero during band warm-up.
- Verified honesty: flat ±2% BTC hourly data yields 0 `moving_average_trend`
  signals (threshold never met) while `volatility_breakout`/`mean_reversion`
  fill 100s of trades — the engine reports the data, not a fake edge.

### L5 — CLI
- `backtest` accepts `--source {synthetic,binance,alpaca}`, `--symbol`,
  `--timeframe`, `--candles`, `--no-cache`; prints period + full metrics
  (total return, Sharpe/Sortino, max DD, win rate, profit factor, total trades).

### L6 — Tests + evidence
- New `tests/test_historical_data_service.py` (fetch→cache-recall identical,
  idempotent upsert, unknown-source rejection, v007 present); migration-count
  expectations updated for v7.
- Evidence (`docs/evidence/2026-08-02_sprint23_real_backtest_alpaca_binance.log`):
  - Alpaca `BTC/USD` + Binance `BTCUSDT`: 60 live 1h bars fetched; cached recall
    identical (timestamps + OHLC); 60 stored each.
  - CLI backtests on both providers fill trades (`volatility_breakout`: 146
    Alpaca, 138 Binance on 600 bars).
- Full suite: `1279 passed, 1 skipped`; coverage 92.56%;
  black/isort/ruff/pyright clean.

### Gate
- [x] Live fetch + identical cache-recall on **both** providers
- [x] Real-candle backtests produce fills and metrics on **both** providers
- [x] Full suite green, coverage ≥ 70%, all lint/type gates pass
- [x] Evidence log committed

## Not in scope / still open
- Fees, slippage, and execution-latency realism in the engine (scheduled).
- Live-order maturity, HA, alerting, live-run policy (scheduled separately).
