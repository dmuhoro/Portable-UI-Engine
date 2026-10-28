# Operational Trust Report — Sprint 9

## Verification posture

This review treated the implementation as untrusted. It used existing regression tests, focused Sprint 9 tests, repository checks, runtime protocol checks, timeout-bounded API execution, static analysis, source inspection, malformed-input probes, persistence probes, and concurrency analysis. No live credentials or production provider endpoints were available, so external connectivity is not inferred.

## Evidence summary

| Area | Evidence | Result |
|---|---|---|
| Sprint 9 tests/benchmark | 26 tests | Passed; focused coverage 87.59% |
| Repository/architecture regression | 192 tests | Passed |
| Runtime ports | `BrokerPort`/`MarketDataPort` structural checks | Passed for paper broker and stream service |
| API integration | `tests/integration/test_api.py::TestApiHealth::test_get_health` | Stalled; timeout-bounded run exited 124 after 45 seconds |
| Static analysis | Ruff on Sprint 9 files | Failed with 44 errors, including E701/E702/E501 and BLE001 |
| Live provider validation | Authenticated Binance/Alpaca | Not available |
| Restart/durability | Process restart with durable event store | Not implemented/evidenced |

## Findings

### OT-001 — No production Binance WebSocket adapter

- Severity: Critical
- Likelihood: Certain in the current deployment
- Impact: The platform cannot receive Binance live data; `StreamTransport` is only an injected protocol.
- Root cause: `BinanceCollector` remains historical HTTP-only and no WebSocket transport or provider failover implementation exists.
- Suggested fix: Implement authenticated/provider-specific Binance WebSocket transport behind `MarketDataPort`, including protocol-level heartbeat, subscription lifecycle, and a tested failover provider.
- Regression tests: connect/authentication, subscription acknowledgement, malformed frames, disconnect/reconnect, heartbeat timeout, failover, and end-to-end tick delivery.
- Evidence: repository search found only `binance_collector.py` historical REST code and the generic `StreamTransport` protocol.

### OT-002 — Replay and idempotency state are not durable

- Severity: Critical
- Likelihood: Certain after process restart
- Impact: `ReplayRecorder.records` and `OrderEventEngine._seen_events` are in-memory lists/sets. Restart loses market replay and duplicate-fill protection.
- Root cause: No event journal schema, durable event repository, checkpoint, or restart recovery path is wired.
- Suggested fix: Persist immutable events and processed event IDs transactionally with trade state; recover checkpoints before consuming broker events.
- Regression tests: kill/restart during each lifecycle transition, replay the same fill twice, verify exactly-once portfolio/audit effects.
- Evidence: both state holders are initialized in constructors and no persistence callback is invoked for recorder/idempotency state.

### OT-003 — Order-event side effects are non-atomic

- Severity: Critical
- Likelihood: Possible whenever persistence/audit/portfolio callbacks fail
- Impact: The trade is mutated before persistence; the event is published before persistence; a failure can leave state, event stream, audit, metrics, and portfolio inconsistent.
- Root cause: `OrderEventEngine.apply()` has no transaction, outbox, rollback, or retry boundary.
- Suggested fix: Use a transactional state transition/outbox unit of work, persist first, then publish from the outbox, and make every side effect retryable/idempotent.
- Regression tests: inject failure at each side effect and assert restart/retry produces one consistent transition.
- Evidence: `apply()` mutates the domain, publishes, then invokes `persist`, `portfolio_update`, `audit`, and `metrics` sequentially.

### OT-004 — Tick validation and timestamp normalization are absent

- Severity: High
- Likelihood: High with malformed/provider-version payloads
- Impact: Negative, NaN, infinite, zero, or unit-mismatched prices/timestamps can enter market calculations; Binance millisecond timestamps are interpreted as seconds.
- Root cause: `ingest()` directly converts raw values without bounds, finite checks, symbol validation, or explicit timestamp-unit handling.
- Suggested fix: Validate finite positive price/quantity, normalize provider timestamps by schema, reject stale/future ticks, and classify malformed input metrics.
- Regression tests: NaN/Infinity, negative/zero values, missing fields, millisecond timestamps, future timestamps, duplicate sequence IDs, and stale ticks.
- Evidence: adversarial input inspection showed raw `Decimal` conversion and `datetime.fromtimestamp(float(...))` with no domain validation.

### OT-005 — `ACKNOWLEDGED` is missing from the in-memory open-order query

- Severity: High
- Likelihood: Certain when using the in-memory repository
- Impact: Reconciliation/restart logic can omit acknowledged live orders and treat them as closed.
- Root cause: `_OPEN_STATUSES` contains pending, submitted, and partially filled but not acknowledged.
- Suggested fix: Centralize open-status definitions in the domain and use them across all repository implementations.
- Regression tests: persist an acknowledged trade through every repository and assert `get_open()` returns it.
- Evidence: runtime probe returned `memory_ack_open 0` while SQLite returned `sqlite_ack_open 1`.

### OT-006 — Concurrent order events are not serialized

- Severity: High
- Likelihood: Medium to high under asynchronous broker callbacks
- Impact: Simultaneous duplicate/partial-fill callbacks can race through `_seen_events` and domain mutation, producing exceptions or duplicate side effects.
- Root cause: No lock, actor, queue, compare-and-swap, or database uniqueness constraint surrounds deduplication plus transition.
- Suggested fix: Serialize by external order/trade ID and enforce durable unique event IDs transactionally.
- Regression tests: hundreds of concurrent identical and out-of-order events with exactly one accepted transition and zero uncaught exceptions.
- Evidence: `_seen_events` check and mutation are separate unsynchronized operations.

### OT-007 — Candle aggregation is not robust to out-of-order data or shutdown

- Severity: High
- Likelihood: Medium with reconnects/replay
- Impact: OHLC ordering can be wrong; incomplete final candles are never flushed; buckets can retain data indefinitely when a symbol stops receiving ticks.
- Root cause: Aggregation is arrival-ordered and only emits when a later bucket arrives; no sequence ordering, watermark, late-tick policy, or `flush()` exists.
- Suggested fix: Define event-time watermarks, late-data policy, explicit flush/close behavior, and bounded retention.
- Regression tests: out-of-order ticks, duplicate ticks, gaps, provider reconnect, final candle flush, and long-running symbol churn.

### OT-008 — In-memory buffers create unbounded retention

- Severity: High
- Likelihood: Certain over long-running operation
- Impact: `ReplayRecorder.records` and `_latencies` grow without bound; memory use increases continuously even though the tick queue is bounded.
- Root cause: No retention policy, disk sink, ring buffer, or compaction.
- Suggested fix: Durable append-only recorder with rotation/retention and bounded latency histogram/rolling window.
- Regression tests: 24-hour soak simulation with memory ceiling and record rotation assertions.

### OT-009 — Alpaca modification/cancel-replace path is unverified and semantically unsafe

- Severity: High
- Likelihood: High when used
- Impact: `cancel_replace()` cancels an order and then calls `replace_order_by_id` with the same ID; provider semantics and SDK signature are not validated. `get_account()` assumes `buying_power` and `cash` attributes.
- Root cause: Adapter tests cover only original submit/cancel/positions paths, not new methods against the real SDK contract.
- Suggested fix: Use the exact Alpaca request object/API for replace, model replacement order IDs, and add contract tests against pinned SDK fakes and sandbox calls.
- Regression tests: modify success/failure, replacement IDs, race with fills, account field absence, timeout/retry classification.

### OT-010 — API health endpoint is not operationally bounded

- Severity: High
- Likelihood: Reproduced in this environment
- Impact: The first API health request did not complete within 45 seconds; the full suite therefore cannot complete reliably.
- Root cause: `GET /v1/health` synchronously calls `create_orchestrator()` and initialization has no request timeout or readiness boundary. Exact blocking sub-call requires production tracing.
- Suggested fix: Separate liveness from dependency readiness, initialize dependencies at startup with bounded timeouts, and expose degraded readiness diagnostics.
- Regression tests: cold-start health under locked DB, unavailable provider, migration delay, and repeated concurrent health calls.
- Evidence: `timeout 45s pytest ...test_get_health` exited 124; direct TestClient probe stalled after `request`.

## Production Readiness Index

**22 / 100 — Not approvable.**

Scoring: local deterministic tests and structural contracts earn credit; live connectivity, durable recovery, atomic lifecycle state, API operational behavior, concurrency safety, and static quality gates are either failed or unverified. A passing unit-test subset cannot offset critical unknowns in a trading system.

## Risk Register

| ID | Risk | Severity | Likelihood | Disposition |
|---|---|---:|---:|---|
| OT-001 | No live Binance transport | Critical | Certain | Release blocker |
| OT-002 | Restart loses replay/deduplication | Critical | Certain | Release blocker |
| OT-003 | Non-atomic order side effects | Critical | Possible | Release blocker |
| OT-004 | Invalid tick acceptance/time units | High | High | Release blocker |
| OT-005 | Acknowledged orders omitted in memory | High | Certain | Must fix |
| OT-006 | Concurrent event race | High | Medium/High | Must fix |
| OT-007 | Incorrect/incomplete candle closure | High | Medium | Must fix |
| OT-008 | Unbounded memory retention | High | Certain | Must fix |
| OT-009 | Alpaca replace contract unverified | High | High | Release blocker |
| OT-010 | API health stalls | High | Reproduced | Release blocker |
| OT-011 | Ruff quality gate failure | Medium | Certain | Must fix |

## Remaining unknowns

Authenticated exchange behavior, TLS/proxy behavior, provider rate limits, broker event ordering, real partial-fill semantics, clock synchronization in deployment, PostgreSQL transaction behavior under failover, process-kill recovery, disk-full behavior, event retention capacity, and live latency distributions remain unknown.

## Approval decision

Do not approve for controlled live pilot. The evidence demonstrates useful local components, but not operational reliability of the complete trading lifecycle.
