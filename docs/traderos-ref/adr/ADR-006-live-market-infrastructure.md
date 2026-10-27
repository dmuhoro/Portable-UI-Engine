# ADR-006: Provider-neutral live market infrastructure

## Status

Accepted for staged implementation; live pilot remains gated.

## Decision

Keep market data and broker integrations behind application ports. Streaming transports emit immutable ticks into a bounded pipeline; broker events are applied through a deterministic, idempotent lifecycle coordinator. Provider SDKs remain infrastructure-only and failures are normalized at the adapter boundary.

## Consequences

Binance and Alpaca can be replaced without application changes. Replay, audit, metrics and portfolio effects are explicit seams for durable implementations. Production deployment still requires authenticated provider integration tests, durable event storage, and restart drills.
