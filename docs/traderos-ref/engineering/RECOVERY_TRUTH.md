# TraderOS — Recovery Truth

**Version:** 1.0
**Date:** 2026-07-31
**Programme:** B — Operational Trust closure pass
**Basis:** Source read against the working tree plus re-runnable tests in `tests/test_programme_b_operational_trust.py`. Every claim is pinned to a test or `file:line`.

> **Purpose.** This document states, without spin, what TraderOS can and cannot recover from after the Programme B changes. Recovery means: a process restart, a hung dependency, a failed side effect, or concurrent duplicate input does **not** lose money-relevant state or corrupt the event/order ledger.

---

## 1. What recovery is now evidenced

### 1.1 Order-event idempotency survives process restart — CLOSED

- A restart loses **nothing** about processed order events: `OrderEventJournal` (`src/traderos/infrastructure/journal.py`) persists event IDs, preloads them at construction, and rejects already-seen events.
- Evidence: `test_durable_idempotency_survives_restart`, `test_journal_preloads_seen_keys`.
- Mechanism: `OrderEventEngine.__post_init__` preloads `_seen_events` from `journal.load_event_ids()`; duplicate processing of the same trade ID after "restart" is rejected (`test_durable_idempotency_survives_restart`).

### 1.2 Failed publish is retained and replayed — CLOSED

- If the event bus raises while publishing, the event stays **pending** in the journal; a later `replay()` republishes it exactly once, and it is never reapplied to the trade.
- Evidence: `test_publish_failure_is_retained_and_replayed`, `test_duplicate_after_publish_failure_not_reapplied`.

### 1.3 Daemon restart recovery is decision-driven, not blind — CLOSED

- The daemon records `orchestrator/start` on boot and `orchestrator/stop` on clean shutdown in the durable `run_manifest` table (`DurableRunManifest`). On the next boot, `_detect_crash()` inspects the manifest: a last action of `start` with no `stop` means the previous process died mid-run, and only then does `_recover_from_crash()` run post-crash reconciliation.
- Evidence: `test_durable_manifest_survives_process_restart`, `test_durable_manifest_clean_shutdown_not_a_crash`, `test_daemon_controller_recovers_after_crash`, `test_daemon_controller_skips_recovery_on_clean_shutdown`.
- Source: `src/traderos/application/daemon_controller.py` (`_detect_crash`, `_recover_from_crash`, `recover_from_crash`).

### 1.4 Migration down-path cannot strand a phantom version — CLOSED

- On downgrade the version marker is deleted **before** `down()` runs; a partial failure leaves the DB without a false "current version" row rather than at a version whose schema is absent.
- Evidence: `test_sqlite_down_removes_version_marker_before_down_runs`; all `down()` implementations are idempotent (`DROP TABLE IF EXISTS`).
- Source: `src/traderos/infrastructure/database/migration_manager.py`, migrations `v002`–`v005`.

### 1.5 Hung dependency cannot stall a health/readiness path — CLOSED

- `run_with_timeout(check_fn, timeout)` runs the check on a daemon worker and raises `TimeoutError` after the budget, so a stuck database/provider never hangs the process or the API.
- Evidence: `test_health_check_times_out_instead_of_stalling`, `test_sqlite_health_check_times_out`, `test_health_readiness_degraded_on_timeout`.
- Source: `src/traderos/infrastructure/health.py`, `src/traderos/interfaces/api/server.py` (`/healthz` liveness, `/health` readiness with `ORCHESTRATOR_READY_TIMEOUT`).

### 1.6 Concurrent duplicate/out-of-order order events recover to a consistent state — CLOSED

- Per-trade locks serialize dedupe + transition. 64 concurrent identical events yield exactly one accepted transition; 32 concurrent distinct events yield exactly one accepted fill and final status `FILLED` with no uncaught transition errors.
- Evidence: `test_concurrent_identical_events_exactly_once`, `test_concurrent_distinct_events_apply_in_order`.
- Source: `src/traderos/application/order_event_engine.py` (`_lock_for`, `_seen_events`).

### 1.7 Shared sqlite connection recovers from thread misuse — CLOSED

- The previous intermittent failures ("SQLite objects created in a thread…", "bad parameter or other API misuse") are structurally removed: `ThreadSafeSQLiteConnection` serializes every statement and cursor call.
- Evidence: `test_sqlite_connection_usable_across_threads` (8 threads × 50 inserts + cursor reads, zero errors).

### 1.8 PostgreSQL migration path recovers to a consistent schema — CLOSED (structure)

- Migrations route through `migration_utils.execute()` (cursor-based for psycopg2), so a PG connection that only exposes `cursor().execute()` runs the full chain and its down-path.
- Evidence: `test_pg_migration_runs_without_conn_execute`, `test_pg_migration_down_path`, `test_pg_v004_guards_missing_trades_table`, `test_pg_v004_alters_when_trades_table_exists`.

---

## 2. What recovery is NOT evidenced (declared remaining risks)

These are **not** fabricated as closed. They require infrastructure this sandbox cannot provide:

| Gap | Why it remains unverified | Required to close |
|---|---|---|
| Live Binance WS reconnect/failover under real network faults | No outbound network; `websockets` package absent | Authenticated live connect, drop/restore test, provider failover test |
| PostgreSQL behavior under failover and disk-full | No Postgres server available (`psycopg2` connect refused in this env) | Live PG cluster fault-injection drill |
| Alpaca live `cancel_replace` semantics, real partial-fill ordering, account field absence | No live/paper Alpaca credentials | Contract tests against pinned SDK fakes + sandbox calls |
| Real market data latency distributions and clock drift in deployment | No production deployment | Soak run with latency histograms |

These gaps were already recorded as *remaining unknowns* in `docs/engineering/OPERATIONAL_TRUST_REPORT.md` and remain so here; none of them regress the closures above.

---

## 3. How to re-run the recovery evidence

```bash
# Full Programme B evidence file (51 tests, all must pass):
python3 -m pytest -q -p no:randomly tests/test_programme_b_operational_trust.py
```
