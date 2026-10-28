# TraderOS — Failure Injection Report

**Version:** 1.0
**Date:** 2026-07-31
**Programme:** B — Operational Trust closure pass
**Method:** Deterministic fault injection. Each injected failure targets one trust boundary; the assertion is that the system degrades, retains, or recovers exactly as designed — never silently corrupts the order/event ledger.

> **Purpose.** This report lists every fault injected during Programme B, the target, the injected failure, the observed behavior, and the test that pins it. It complements `RECOVERY_TRUTH.md` (what recovers) and `OPERATIONAL_TRUST_MATRIX.md` (what changed).

---

## Injection log

| # | Target | Injected failure | Expected | Observed | Test (all in `tests/test_programme_b_operational_trust.py`) |
|---|---|---|---|---|---|
| F1 | Event publish (outbox) | `FlakyBus` raises on publish | Event stays pending; replay republishes once; never reapplied | Exactly one published event after replay; trade not double-mutated | `test_publish_failure_is_retained_and_replayed`, `test_duplicate_after_publish_failure_not_reapplied` |
| F2 | Concurrency — duplicate events | 64 threads submit the identical event id | Exactly one accepted transition, zero uncaught exceptions | Exactly one accepted; status `FILLED` once | `test_concurrent_identical_events_exactly_once` |
| F3 | Concurrency — out-of-order events | 32 threads submit distinct events for one trade | Serialized; exactly one accepted fill; final `FILLED`; no `InvalidTradeTransitionError` | Passed; exactly one `accepted_fills` | `test_concurrent_distinct_events_apply_in_order` |
| F4 | Fill guards | Fill quantity > order quantity; non-positive quantity; non-positive price | `InvalidTradeTransitionError`, no mutation | All three rejected | `test_fill_quantity_exceeding_order_rejected`, `test_fill_quantity_non_positive_rejected`, `test_fill_price_non_positive_rejected` |
| F5 | Tick price | NaN; +Inf; 0; negative | `InvalidTickError`, counted malformed | All rejected | `test_tick_rejects_nan_price`, `test_tick_rejects_infinite_price`, `test_tick_rejects_zero_and_negative_price` |
| F6 | Tick quantity | Negative quantity | `InvalidTickError` | Rejected | `test_tick_rejects_negative_quantity` |
| F7 | Tick symbol | Missing symbol | `InvalidTickError` | Rejected | `test_tick_rejects_missing_symbol` |
| F8 | Tick time | Future timestamp; stale timestamp (>300s) | `InvalidTickError` | Both rejected | `test_tick_rejects_future_and_stale` |
| F9 | Transport stream | Malformed frames only | Frames skipped as malformed, **not** treated as transport outage/reconnect | `malformed_ticks` increments; no reconnect counted | `test_ingest_counts_malformed_and_skips_transport_reconnect` |
| F10 | Candle aggregation | Late tick for an already-closed bucket | Rejected and counted, no OHLC corruption | `late_ticks == 1`; candle unchanged | `test_aggregator_rejects_late_tick_for_closed_bucket` |
| F11 | Candle aggregation | Idle symbol (no ticks) | `flush_stale` closes the candle | Partial candle emitted, bucket cleared | `test_aggregator_flush_stale_closes_idle_symbols`, `test_aggregator_flush_emits_partial_candle`, `test_aggregator_flush_all` |
| F12 | Retention | 150 records into a 100-cap recorder; 2500 ingests | Ring-buffer bound; drops counted | 100 kept / 50 dropped; `_latencies` ≤ 1500 | `test_replay_recorder_bounded`, `test_latency_buffer_bounded_after_ingest` |
| F13 | Health check | Dependency blocks 1s against a 0.1s budget | `TimeoutError`, unhealthy status, no stall | Raised/flagged | `test_health_check_times_out_instead_of_stalling`, `test_sqlite_health_check_times_out` |
| F14 | Orchestrator build | `build_orchestrator` blocks 0.5s against 0.05s readiness budget | `GET /v1/health` → 503 degraded, no hang; `/healthz` never builds | 503 with "not ready"; liveness does not call `create_orchestrator` | `test_health_readiness_degraded_on_timeout`, `test_healthz_liveness_never_builds_orchestrator` |
| F15 | PG connection API | Fake PG conn has **no** `.execute` (cursor-only, like psycopg2) | Migration chain + down-path run via cursor routing | Full run + down passed | `test_pg_migration_runs_without_conn_execute`, `test_pg_migration_down_path` |
| F16 | Fresh PG schema | `trades` table absent during v004 | Migration no-ops instead of failing | No-op on missing table; alters when present | `test_pg_v004_guards_missing_trades_table`, `test_pg_v004_alters_when_trades_table_exists` |
| F17 | Migration down mid-failure | v005 `down` spy observes the version marker | Marker removed **before** `down()` runs | Confirmed | `test_sqlite_down_removes_version_marker_before_down_runs` |
| F18 | Restart | Second process instance opens the same journal/manifest DB | State (event ids / manifest) durable across restart | Preload works; manifest history intact | `test_durable_idempotency_survives_restart`, `test_durable_manifest_survives_process_restart` |
| F19 | Clean vs crash shutdown | Manifest records start+stop (clean) vs start only (crash) | Recovery only on crash | Recovery runs for crash; skipped for clean | `test_daemon_controller_recovers_after_crash`, `test_daemon_controller_skips_recovery_on_clean_shutdown` |
| F20 | Shared sqlite connection | 8 threads × 50 concurrent inserts + cursor reads | Zero `ProgrammingError`/`InterfaceError` | Zero errors, 400 rows | `test_sqlite_connection_usable_across_threads` |

---

## Pre-existing environment failures (not Programme B regressions)

- `tests/test_database_connection.py::TestResolveBackend::test_postgres_raises_without_psycopg2` fails in this environment because `psycopg2` **is** installed but no Postgres server is reachable (`OperationalError: Connection refused`). Verified identical on baseline commit `0012d73` — environment-dependent, not a regression.
- `tests/integration/test_api.py` was flake-prone before Programme B (OT-010 stalled for 45s+); after the OT-010 fix its health/rate-limit tests pass.

## Re-run command

```bash
python3 -m pytest -q -p no:randomly tests/test_programme_b_operational_trust.py
```
