# Live Market Infrastructure Report

## Architecture Overview

Application code consumes `MarketDataPort`, `BrokerPort`, `EventBusPort`, and repositories. `StreamingMarketDataService` converts provider payloads into immutable ticks, applies bounded buffering and records replay events. `OrderEventEngine` applies broker events to the domain `Trade` and coordinates side effects through injected ports/callbacks.

## Execution Flow

Tick → clock/latency observation → replay record → bounded queue → application handler. Order event → idempotency key → domain transition guard → persistence → event emission → portfolio/audit/metrics callbacks.

## Latency Metrics

Each tick exposes `latency_ms`; service health reports the rolling mean of its last 100 observations. The local benchmark ingests 10,000 ticks under two seconds. No external exchange-to-process latency is claimed.

## Failure Modes and Recovery

Heartbeat timeout reports unhealthy. Full queues increment `dropped_ticks`. Transport exceptions reconnect up to the configured limit. Clock drift is observable via `ClockMonitor`. Duplicate broker event IDs are ignored; invalid late transitions are rejected by the domain state machine. Restart replay is supported from recorder records, while durable production storage remains an operational requirement.

## Test Evidence and Benchmarks

Sprint-specific unit/failure tests are in `tests/test_sprint9_infrastructure.py`; the ingestion benchmark is in `tests/performance/test_sprint9_benchmarks.py`. Existing Alpaca tests cover fills, rejection, cancellation, account and positions. The verification command is `PYTHONPATH=src pytest -q`.

## Remaining Risks

Live WebSocket provider authentication, provider failover configuration, durable event-stream deployment, broker streaming event consumer, PostgreSQL event schema/migrations, end-to-end restart drills, and production network latency measurements remain unverified in this workspace.

## Operational Readiness Assessment

The deterministic local components are testable and bounded, but the required production evidence for live provider connectivity and restart/reconciliation is absent.

## Recommendation

ADDITIONAL ENGINEERING REQUIRED
