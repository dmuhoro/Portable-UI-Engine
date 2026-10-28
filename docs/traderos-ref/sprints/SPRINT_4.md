# Sprint 4 — Real-Market Wiring: Data Feed, Broker, Price Integrity

Programme Reference: Master Execution Programme — Workstream 2 (Core Runtime)
Version Target: v0.4.0

## Objective

Close three critical gaps that prevent the trading platform from functioning with real market data and a live broker: wire the existing data ingestion pipeline into the orchestrator, wire Alpaca for LIVE mode, and fix the fill_price multiplier bug in PaperBrokerAdapter.

## Work Packages

### Gap 3 (WP-101): Fix fill_price Multiplier Bug — COMPLETED
- `BrokerAdapter.place_market_order()` now accepts optional `close_price: float | None` parameter
- `PaperBrokerAdapter.place_market_order()` returns absolute price (`close_price * slippage_multiplier`) instead of just the multiplier
- `PaperTradingService.process_candle()` updated to pass `close_price` and consume absolute price (removed double-multiply workaround)
- `AlpacaBrokerAdapter` signature updated (close_price accepted but unused — real broker provides fill price)
- `TradingOrchestrator.run_cycle()` passes `close_price` to `broker.place_market_order()` so trades record real prices
- `MockBroker` in tests updated with new signature

### Gap 1 (WP-102): Wire Market Data Feed — COMPLETED
- `DataIngestionService.get_latest_close(market_id)` method added — resolves the latest close price for a market by looking up its data source and fetching the most recent candle
- `factory.py` now builds a `CollectorRegistry` with `MockDataCollector` (always) + optional `BinanceCollector` (if alpaca-py installed)
- Symbols parsed from `settings.yaml` (`data_collection.forex_symbols` + `data_collection.crypto_symbols`) generate deterministic UUIDs via `uuid.uuid5()`
- `DataIngestionService` registered in factory and passed to `TradingOrchestrator`
- `TradingOrchestrator.run_forever()` uses `data_ingestion.get_latest_close(mid)` to resolve price instead of hardcoded `100.0`

### Gap 2 (WP-103): Wire Alpaca for LIVE Mode — COMPLETED
- `factory.py` broker selection branches on `TradingMode.LIVE` — uses `AlpacaBrokerAdapter` if `alpaca_api_key` and `alpaca_secret_key` are configured
- Falls back to `PaperBrokerAdapter` on ImportError (alpaca-py not installed) or runtime errors
- Config typed fields added: `alpaca_api_key`, `alpaca_secret_key`, `alpaca_paper`
- Environment variable support: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_PAPER`

### Hardening (WP-104): Config Typing & Daemon Recovery — COMPLETED
- `Config` gains typed fields `alpaca_api_key`, `alpaca_secret_key`, `alpaca_paper`
- `Config.load()` maps env vars `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_PAPER`
- `TradingOrchestrator.run_forever()` wraps `run_cycle()` in try/except for panic recovery — errors logged and reported to health service, daemon continues

## Deliverables
- fill_price returns absolute USD price (not ~1.0005 multiplier)
- Orchestrator reads real market data from data ingestion pipeline
- LIVE mode uses AlpacaBrokerAdapter when credentials are present
- Daemon recovers gracefully from per-cycle panics

## Out of Scope
- SQLAlchemy/async DB migration (future sprint)
- WebSocket-based real-time price updates
- Order status reconciliation / position sync from broker

## Success Criteria
- `test_place_market_order_slippage` passes with close_price-based absolute price
- `build_orchestrator(mode="live")` instantiates AlpacaBrokerAdapter when credentials set
- `run_forever()` falls back to last-known-price and continues on cycle error
- All 514+ tests pass with 88%+ coverage
