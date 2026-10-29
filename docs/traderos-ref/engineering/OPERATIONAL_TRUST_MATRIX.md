# TraderOS — Operational Trust Matrix

**Version:** 1.0
**Date:** 2026-07-31
**Programme:** B — Operational Trust closure pass
**Scope:** All 11 findings (OT-001 … OT-011) from `docs/engineering/OPERATIONAL_TRUST_REPORT.md`, each with root cause → fix → regression test → evidence.

> **Purpose.** This matrix is the working record of Programme B. For every OT finding it states the confirmed root cause, the code change that addresses it (pinned to `file:line`), the regression tests that protect it, and the evidence produced. It is the basis for the Programme B delivery claim: **all 11 findings closed as code + test + evidence** unless explicitly marked a *remaining risk*.

---

## Closure summary

| Finding | Severity | Status | Root-cause fix | Regression tests | Evidence |
|---|---:|---|---|---|---|
| OT-001 | Critical | **Closed (structural), live connectivity = remaining risk** | `BinanceStreamTransport` + pure frame functions in `market_stream.py` | 7 new tests in `tests/test_programme_b_operational_trust.py` | Pure-frame + fake-WS transport tests |
| OT-002 | Critical | **Closed** | Durable `OrderEventJournal`; durable `DurableRunManifest` + daemon crash detection | 6 new tests | Restart/replay/outbox tests |
| OT-003 | Critical | **Closed** | Journal record *before* persist/publish (outbox); publish after success | `test_publish_failure_is_retained_and_replayed` | Outbox replay test |
| OT-004 | High | **Closed** | `validate_tick`/`normalize_timestamp` + malformed counter | 8 new tests | Tick validation tests |
| OT-005 | High | **Closed** | `OPEN_TRADE_STATUSES` across repos; backend-aware migrations (H7) | 10 new tests | PG fake-conn + repo parity tests |
| OT-006 | High | **Closed** | Per-trade locks in `OrderEventEngine` | 2 concurrency tests | 64/32-thread tests |
| OT-007 | High | **Closed** | `CandleAggregator` flush/late-tick/watermark | 4 new tests | Aggregator tests |
| OT-008 | High | **Closed** | Bounded `ReplayRecorder` + latency trim | 2 new tests | Retention tests |
| OT-009 | High | **Closed** | `_validate_fill` bounds guards | 3 new tests | Fill-guard tests |
| OT-010 | High | **Closed** | `run_with_timeout` + `/healthz` + `/health` readiness | 4 new tests | Timeout/endpoint tests |
| OT-011 | Medium | **Closed** | `ThreadSafeSQLiteConnection`; ruff gate | 2 new tests + B8 static gate | Thread-safety tests |

**Programme B test file:** `tests/test_programme_b_operational_trust.py` — **51 tests, all passing**.

---

## OT-001 — No production Binance WebSocket adapter

- **Root cause:** `BinanceCollector` was historical HTTP-only; `StreamTransport` was only an injected protocol with no Binance implementation.
- **Fix:** `src/traderos/infrastructure/market_stream.py`:
  - `BinanceStreamTransport` — thin connector that subscribes to `<symbol>@aggTrade`, parses frames, and yields normalized raw ticks.
  - `build_subscription_frame(symbols)` — pure SUBSCRIBE frame builder.
  - `parse_trade_frame(text)` — pure parser handling combined-stream envelopes (`{"stream":…, "data":…}`) and raw `aggTrade`/`trade` events; non-trade frames (acks, klines) return `None`.
  - `binance_stream_symbol(symbol)` — Binance stream-name normalization.
- **Regression tests:** `test_binance_stream_symbol_normalizes`, `test_build_subscription_frame_uses_agg_trade_streams`, `test_parse_trade_frame_raw_event`, `test_parse_trade_frame_combined_envelope`, `test_parse_trade_frame_ignores_non_trade_frames`, `test_binance_transport_subscribes_and_yields_trades`, `test_streaming_service_run_with_binance_transport`, `test_binance_default_connector_requires_websockets`.
- **Evidence:** all 8 pass; transport unit-tested against a fake WebSocket with zero network access.
- **Remaining risk (declared, not fabricated):** this sandbox has no outbound network and no `websockets` package, so **live** Binance connectivity is not evidenced. The transport's connector is injected; the default lazily imports `websockets` at connect time. Live validation requires authenticated network access and is a deployment-time step.

## OT-002 — Replay and idempotency state are not durable

- **Root cause:** `ReplayRecorder.records` and `OrderEventEngine._seen_events` were in-memory only; no durable event store or restart recovery existed.
- **Fix:**
  - `src/traderos/infrastructure/journal.py` — `OrderEventJournal` (durable `order_events` table, `v005_order_event_journal.py` migration), preloads processed event IDs at startup, `replay()` republishes un-`mark_published` events.
  - `src/traderos/infrastructure/run_manifest.py` — `DurableRunManifest` (durable `run_manifest` table) + `detect_unclean_shutdown()`.
  - `src/traderos/application/daemon_controller.py` — `_detect_crash()`/`_recover_from_crash()` run post-crash reconciliation only when the previous process never recorded a clean `stop`.
- **Regression tests:** `test_durable_idempotency_survives_restart`, `test_journal_preloads_seen_keys`, `test_durable_manifest_survives_process_restart`, `test_durable_manifest_clean_shutdown_not_a_crash`, `test_daemon_controller_recovers_after_crash`, `test_daemon_controller_skips_recovery_on_clean_shutdown`.
- **Evidence:** all pass; a second process instance sees the first instance's events/manifest.

## OT-003 — Order-event side effects are non-atomic

- **Root cause:** `apply()` mutated the domain and published events *before* persistence; failures could leave state, event stream, and audit inconsistent.
- **Fix:** `src/traderos/application/order_event_engine.py` — journal record is committed **before** persist/publish (outbox ordering); `mark_published` happens only after a successful publish; a publish failure leaves the event `pending` so `replay()` republishes it exactly once.
- **Regression tests:** `test_publish_failure_is_retained_and_replayed`, `test_duplicate_after_publish_failure_not_reapplied`.
- **Evidence:** both pass; after a failing bus the pending event is replayed once and never reapplied.

## OT-004 — Tick validation and timestamp normalization are absent

- **Root cause:** `ingest()` converted raw values without bounds/finite checks, symbol validation, or explicit timestamp-unit handling.
- **Fix:** `market_stream.py` — `validate_tick()` (symbol, finite positive price, non-negative finite quantity, stale/future rejection) and `normalize_timestamp()` (auto-detects milliseconds > 1e10 vs seconds); `ingest()` counts `malformed_ticks` and re-raises `InvalidTickError`; `run()` skips malformed frames without treating them as transport outages.
- **Regression tests:** ms normalization (year preserved), NaN/Inf/zero/negative price, negative quantity, empty symbol, future/stale rejection, malformed-skip in `run(max_messages=1)`.
- **Evidence:** all pass.

## OT-005 — `ACKNOWLEDGED` missing from open-order queries + broken Postgres migration path

- **Root cause (a):** `_OPEN_STATUSES` omitted `ACKNOWLEDGED` in the in-memory repo. **Fix:** `src/traderos/domain/entities/trade.py` — single `OPEN_TRADE_STATUSES` used by in-memory/sqlite/postgres `get_open()`.
- **Root cause (b / H7):** migrations used `conn.execute()` directly, breaking the PostgreSQL cursor-based path. **Fix:** `src/traderos/infrastructure/database/migration_utils.py` — `detect_backend()`/`execute()` routing; `migration_manager.py` routes every statement through `execute()` and deletes the version marker **before** `down()` runs (no phantom version rows); `v002`–`v005` rewritten backend-aware; `v004` guards missing `trades` table on fresh PG; all `down()` implementations idempotent.
- **Regression tests:** `test_pg_migration_runs_without_conn_execute`, `test_pg_migration_down_path`, `test_pg_v004_guards_missing_trades_table`, `test_pg_v004_alters_when_trades_table_exists`, `test_sqlite_down_removes_version_marker_before_down_runs`, acknowledged-open parity tests.
- **Evidence:** all pass; fake PG connection (no `.execute` on the connection) runs full migration + down.

## OT-006 — Concurrent order events are not serialized

- **Root cause:** `_seen_events` check and domain mutation were separate unsynchronized operations.
- **Fix:** `order_event_engine.py` — per-trade `threading.Lock` via `_lock_for(trade_id)` serializes dedupe + transition; journal is the durable single source of truth.
- **Regression tests:** `test_concurrent_identical_events_exactly_once` (64 threads → exactly one accepted), `test_concurrent_distinct_events_serialized` (32 threads → `accepted_fills == 1`, final status `FILLED`, no `InvalidTradeTransitionError`).
- **Evidence:** both pass.

## OT-007 — Candle aggregation is not robust to out-of-order data or shutdown

- **Root cause:** arrival-ordered aggregation with no flush/late-data policy.
- **Fix:** `market_stream.py` — `CandleAggregator` rewritten: epoch-bucket start, `flush(symbol)`, `flush_all()`, `flush_stale(now)`, `late_ticks` counter for already-closed buckets, bounded `closed_bucket_limit` deque; `_make` builds candles with correct UTC start (previously raised `TypeError` on int + timedelta).
- **Regression tests:** `test_aggregator_emits_closed_candle`, `test_aggregator_flush_partial_candle`, `test_aggregator_flush_all`, `test_aggregator_late_tick_for_closed_bucket_counted`, `test_aggregator_flush_stale`.
- **Evidence:** all pass.

## OT-008 — In-memory buffers create unbounded retention

- **Root cause:** `ReplayRecorder.records` and `_latencies` grew without bound.
- **Fix:** `market_stream.py` — `ReplayRecorder` uses a `maxlen` deque (default 100_000) + `dropped_records` counter; `_latencies` trimmed to ≤1500 and health uses the last ≤100.
- **Regression tests:** `test_recorder_bounded_and_counts_drops`, `test_latency_buffer_bounded_after_ingest`.
- **Evidence:** both pass (100-record cap with 50 drops; 2500 ingests → ≤1500 latencies).

## OT-009 — Duplicate/overflow fill acceptance

- **Root cause:** fills were accepted without bounds checks against the order quantity.
- **Fix:** `order_event_engine.py` — `_validate_fill()` rejects non-finite/≤0 quantity, quantity > order quantity, and non-finite/≤0 price for both `PARTIALLY_FILLED` and `FILLED`.
- **Regression tests:** `test_fill_quantity_above_order_rejected`, `test_fill_quantity_non_positive_rejected`, `test_fill_price_non_positive_rejected`.
- **Evidence:** all pass.

## OT-010 — API health endpoint is not operationally bounded

- **Root cause:** `GET /v1/health` synchronously called `create_orchestrator()` with no timeout; cold-start initialization stalled requests.
- **Fix:**
  - `src/traderos/infrastructure/health.py` — `run_with_timeout(check_fn, timeout)` (daemon worker + join(timeout), raises `TimeoutError`); `HealthService.check_timeout`/`summary()`/`history()`.
  - `src/traderos/infrastructure/observability.py` — SQLite health check timeout-bound.
  - `src/traderos/interfaces/api/server.py` — `GET /v1/healthz` (liveness, no dependency build, can never stall) and `GET /v1/health` (readiness via `create_orchestrator(timeout=ORCHESTRATOR_READY_TIMEOUT)`, returns 503 "degraded" on timeout).
- **Regression tests:** `test_health_check_times_out_instead_of_stalling`, `test_sqlite_health_check_times_out`, `test_healthz_liveness_never_builds_orchestrator`, `test_health_readiness_degraded_on_timeout`.
- **Evidence:** all pass; `test_get_health` in `tests/integration/test_api.py` (the OT-010 reproduction) now passes.

## OT-011 — Concurrency safety of shared sqlite connections + static gate

- **Root cause:** one shared `sqlite3.Connection` was used across API/orchestrator threads; Python's sqlite3 module does not serialize concurrent use even with `check_same_thread=False` (intermittent "SQLite objects created in a thread…" and "bad parameter or other API misuse").
- **Fix:** `src/traderos/infrastructure/database/connection.py` — `ThreadSafeSQLiteConnection` serializes every statement (execute/cursor/commit/rollback) under a reentrant lock and returns lock-bound cursor proxies; `_connect_sqlite` now honors an explicitly-passed `Config.db_path` (the env var must not shadow an explicit config — this also fixes cross-test DB contamination). `detect_backend()` recognizes the wrapper.
- **Regression tests:** `test_sqlite_connection_usable_across_threads` (8 threads × 50 inserts + cursor reads, zero errors), `test_thread_safe_connection_backend_detected_as_sqlite`.
- **Static gate:** `ruff check src/traderos` and `pyright src/traderos` run clean in Programme B delivery (B8).

---

## Remaining unknowns (unchanged from OT report, minus closures)

- Authenticated live Binance connectivity (OT-001 remaining risk — needs network + `websockets` package).
- Alpaca live `cancel_replace` semantics, real broker partial-fill ordering, and account field absence in production (OT-009 is a *duplicate/overflow* closure; live provider contract still requires authenticated testing).
- PostgreSQL behavior under failover and disk-full conditions in a real deployment.
- Live latency distributions and clock synchronization in deployment.
