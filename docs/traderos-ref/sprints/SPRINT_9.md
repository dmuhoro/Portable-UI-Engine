# Sprint 9 — Live Market Infrastructure

## Scope

Sprint 9 introduces the provider-neutral live market data pipeline and the deterministic broker-event lifecycle. `MarketDataPort` and `BrokerPort` remain the application boundaries; Binance and Alpaca are infrastructure concerns.

## Delivered

- bounded tick ingestion with explicit backpressure/drop accounting;
- heartbeat health, exchange-to-receive latency, clock-drift observation, reconnect loop and transport injection;
- candle aggregation and JSON replay recording;
- enriched events with correlation, trace, market, strategy and execution context;
- `ACKNOWLEDGED` lifecycle state with monotonic fill guards;
- idempotent `OrderEventEngine` coordinating persistence, event bus, portfolio callback, audit and metrics;
- Alpaca health, error classification, account/buying-power synchronization and order modification APIs;
- repositories treat acknowledged orders as open.

## Evidence

`tests/test_sprint9_infrastructure.py` covers bounded buffering, replay, candle closure, clock drift and duplicate/late order events. `tests/performance/test_sprint9_benchmarks.py` verifies 10,000 local tick ingestions in under two seconds on the CI runner. Existing Alpaca adapter tests remain green.

## Explicit limits

The repository has no live Alpaca credentials, exchange WebSocket integration environment, durable event-stream backend, or production latency sample. Therefore this sprint does not claim live-pilot readiness. Network behavior is tested through injected transports and SDK fakes.
