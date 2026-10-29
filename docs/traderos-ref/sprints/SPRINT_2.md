# Sprint 2 — Paper Trading & Decision Intelligence

Branch: `sprint-2-paper-trading`
Version Target: v0.3.0

## Objective

Build the full trading pipeline from strategy → signal → risk → portfolio → execution → backtesting → paper trading. Deliver a decision intelligence platform capable of simulated live trading.

## Work Packages

### WP-040-043: Strategy Framework — COMPLETED
- `StrategyBase` ABC with `evaluate(MarketState) → SignalResult | None`
- `StrategyRegistry` — singleton registry for strategy discovery
- 3 starter strategies: `MovingAverageTrend`, `VolatilityBreakout`, `MeanReversion`
- `StrategyEvaluationService` — evaluates a strategy against market state
- Direction logic: `sma_20 < close` → bearish → `"short"` signal
- 8 tests pass

### WP-044-046: Signal Engine — COMPLETED
- `SignalService` — converts `SignalResult` into persisted `Signal` with TTL
- `validate_signal` — checks direction/value/expiry validity
- `deduplicate` — configurable policy (highest_confidence / latest)
- `get_active_signals`, `get_signals_for_strategy` — filtered queries
- 6 tests pass

### WP-047-050: Portfolio Engine — COMPLETED
- `PortfolioService` — `get_summary`, `size_position` (confidence-based), `compute_pnl`
- `open_trade`, `fill_trade` — trade lifecycle with position creation/update
- `rebalance` — target allocation convergence
- Repository-backed (TradeRepository, PositionRepository)
- 8 tests pass

### WP-051-054: Risk Engine — COMPLETED
- `RiskService` — `assess_trade` (Kelly Criterion with stop-loss/take-profit)
- `compute_var` — parametric VaR at configurable confidence
- `compute_max_drawdown`, `check_concentration`, `enforce_limits`
- Edge cases: `win_rate=0` handled (max_risk_amount = 0)
- 8 tests pass

### WP-055-058: Execution Engine — COMPLETED
- `Order` dataclass with `OrderType` (MARKET/LIMIT/STOP) and `OrderStatus` (PENDING/FILLED/PARTIAL/CANCELLED/REJECTED)
- `ExecutionService` — `create_market_order`, `create_limit_order`, `create_stop_order`
- `process_market_order` — immediate fill with slippage model
- `process_limit_order` — price trigger check
- `process_stop_order` — stop trigger then slippage
- `cancel_order` — status transition
- 10 tests pass

### WP-059-062: Backtesting Engine — COMPLETED
- `BacktestingService` — time-series iteration over candles
- Strategy evaluation loop with indicator computation (SMA, ATR)
- Trade simulation via `ExecutionService`, equity curve tracking
- `compute_metrics` — Sharpe/Sortino/Calmar ratios, max drawdown, win rate, profit factor, recovery factor (all using sample std ddof=1)
- `BacktestStep` NamedTuple for per-bar granularity
- 5 tests pass

### Docker Compose + Entry Points + Debt Cleanup — COMPLETED
- `pyproject.toml`: `traderos` and `traderos-api` entry points
- `Dockerfile`: Rewritten for pyproject.toml-based install, default entry `traderos`
- `docker-compose.yml`: Dual-service (CLI daemon + API server on port 8000)
- Root scripts updated to delegate to unified CLI
- 507 tests pass, coverage 88.3%, lint/typecheck clean

### New: REST API + Data Ingestion Service — COMPLETED
- FastAPI REST server (`traderos.interfaces.api.server`) — 12 endpoints: health, strategies, backtest, orchestrator control, paper sessions, audit, metrics, manifest
- API entry point: `uvicorn traderos.interfaces.api.main:app --host 0.0.0.0 --port 8000`
- `DataIngestionService` — multi-source data fetching via CollectorRegistry, normalized OHLCV output
- Optional dependency groups: `traderos[api]`, `traderos[alpaca]`, `traderos[all]`
- 5 tests pass

### New: Application Orchestrator + Broker Adapters — COMPLETED
- `TradingOrchestrator` — central runtime with PAPER/LIVE/BACKTEST modes, signal-driven trading cycle, event emission, health/metrics/audit tracking
- `BrokerAdapter` ABC — polymorphic interface for real/paper trading
- `AlpacaBrokerAdapter` — Alpaca REST API integration (optional dep)
- 5 tests pass

### WP-079-091: Integration, Performance, Docs, Release — COMPLETED
- Integration tests: strategy→backtest→risk→execution→paper pipeline, audit trail, metrics
- Performance benchmarks: 1000-candle backtest < 1s, 1000-order execution < 100ms
- Sprint docs updated, CHANGELOG finalized
- 497 tests pass, coverage 88.7%, lint/typecheck clean

### WP-071-078: Observability & Visualization — COMPLETED
- `MetricsService` — Counter/gauge/timing metrics with snapshot and query
- `RunManifestService` — Run recording with metadata and filtered retrieval
- `VisualizationService` — Equity curve, returns distribution, drawdown, performance summary chart generators
- 24 tests pass

### WP-067-070: Platform Layers — COMPLETED
- `NotificationService` — Multi-channel (CONSOLE/FILE/WEBHOOK), 4 severity levels, metadata
- `HealthService` — Service registry, check function execution, history tracking
- `AuditService` — Append-only audit trail with hash chaining and chain verification
- `Unified CLI` — `traderos/interfaces/cli/main.py` with 6 command groups (strategies, backtest, papertrade, health, audit, notify)
- 26 tests pass

### WP-063-066: Paper Trading Engine — COMPLETED
- `PaperTradingService` — session lifecycle (CREATED→RUNNING→PAUSED→STOPPED)
- Signal-driven pipeline: signal → risk → portfolio → execution
- `PaperBrokerAdapter` — simulated broker with configurable slippage, fill probability, partial fills
- Supports market/limit/stop order types
- `PaperSession` entity — tracks state, orders, trades, positions, equity curve
- `DeviationAnalysisService` — compares paper vs backtest metrics, computes correlation/RMSE
- 26 tests pass

## Deliverables
- 18 domain services across 7 engines (Strategy, Signal, Portfolio, Risk, Execution, Backtest, Paper)
- Full trading pipeline: strategy → signal → risk → portfolio → execution → backtesting → paper trading
- 507 tests pass (376 baseline + 131 new across all layers)
- Test coverage: 87.7%

## Out of Scope
- Real Money Trading
- Broker APIs (live)
- Machine Learning
- AI Agents
- Platform interfaces (CLI/API/WS/Dashboard)

## Success Criteria
- Strategy can generate signals from market data
- Signals are validated, deduplicated, and time-boxed
- Portfolio opens/fills trades with position tracking
- Risk service computes Kelly sizing and VaR
- Orders flow through execution with slippage model
- Backtest produces meaningful metrics (Sharpe, max DD, etc.)
- Paper trading simulates live sessions with realistic broker behavior
- All 439 tests pass; lint/typecheck clean
