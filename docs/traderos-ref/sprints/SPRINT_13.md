# Sprint 13 — Programme B: Operational Trust

**Period:** 2026-07-31
**Objective:** Close every finding (OT-001…OT-011) from `docs/engineering/OPERATIONAL_TRUST_REPORT.md` with a root-cause fix, a regression test, and evidence — raising the Production Readiness Index from 22 toward the ≥70 controlled-pilot gate. This is a **survivability-only** Code Freeze sprint: no features, dashboards, or UI.

**Reference docs:** `docs/engineering/OPERATIONAL_TRUST_MATRIX.md` (the closure matrix), `docs/engineering/RECOVERY_TRUTH.md` (what recovers), `docs/engineering/FAILURE_INJECTION_REPORT.md` (injected faults → observed behavior).

---

## Findings Register

| Finding | Severity | Root cause | Resolution | Tests |
|---------|----------|------------|------------|-------|
| OT-001 | Critical | `StreamTransport` had no Binance implementation | `BinanceStreamTransport` + pure `parse_trade_frame`/`build_subscription_frame`/`binance_stream_symbol` (`market_stream.py`); connector injectable for offline tests | 8 (frame parsing, envelopes, acks, fake-WS transport, service `run()`, missing-package error) |
| OT-002 | Critical | Replay + idempotency state in memory | Durable `OrderEventJournal` (`journal.py` + `v005` migration); durable `DurableRunManifest` + daemon `_detect_crash`/`_recover_from_crash` | 6 (restart idempotency, preload, manifest restart, clean vs crash, controller recovery) |
| OT-003 | Critical | Domain mutated / published before persistence | Journal record committed **before** persist/publish (outbox); `mark_published` after success; `replay()` republishes pending events | 2 (publish-failure retained + replayed; never reapplied) |
| OT-004 | High | Raw values ingested without validation | `validate_tick`/`normalize_timestamp`/`InvalidTickError`; malformed counter; malformed frames skipped (not treated as outage) | 8 (ms vs s normalization, NaN/Inf/0/neg price, neg qty, missing symbol, future/stale, run-skip) |
| OT-005 | High | `ACKNOWLEDGED` omitted from open queries; PG migrations broken (H7) | Single `OPEN_TRADE_STATUSES` across repos; `migration_utils.execute` cursor routing; marker deleted before `down()`; `v002–v005` backend-aware + idempotent | 10 (PG fake-conn up/down, v004 guards, sqlite down ordering, repo parity) |
| OT-006 | High | Dedupe + transition race | Per-trade `threading.Lock` in `OrderEventEngine` | 2 (64-thread identical, 32-thread distinct) |
| OT-007 | High | Arrival-ordered, no flush/late policy | `CandleAggregator` epoch buckets + `flush`/`flush_all`/`flush_stale` + `late_ticks` + bounded closed-bucket deque | 5 |
| OT-008 | High | Unbounded in-memory buffers | Bounded `ReplayRecorder` (maxlen deque + drop counter); latency trim ≤1500, health uses last 100 | 2 |
| OT-009 | High | Fills accepted without bounds | `_validate_fill` rejects non-finite/≤0 qty, qty > order qty, non-finite/≤0 price | 3 |
| OT-010 | High | Health endpoint stalls (reproduced 45s+) | `run_with_timeout`; `/healthz` (liveness, no build) + `/health` (bounded readiness, 503 degraded); `ORCHESTRATOR_READY_TIMEOUT` | 4 (hung check, sqlite check, liveness, readiness 503) |
| OT-011 | Medium | Shared sqlite connection unsafe across threads | `ThreadSafeSQLiteConnection` serializes every statement/cursor; explicit config wins over env | 2 (8-thread stress, backend detection) |

**Result: 11/11 findings closed** (OT-001 live connectivity and OT-009/OT-005 live behavior remain *declared risks* R-01/R-02 — structural/contract closures only, not fabricated live claims).

## Key Files Created/Modified

### Source
| File | Change |
|------|--------|
| `src/traderos/infrastructure/journal.py` | **New.** Durable `order_events` journal: preload, `record`, `mark_published`, `pending_events`, `replay`, Event encode/decode |
| `src/traderos/application/order_event_engine.py` | **OT-002/003/006/009:** journal preload, outbox ordering, per-trade locks, `_validate_fill` guards, `replay()` |
| `src/traderos/infrastructure/market_stream.py` | **OT-001/004/007/008:** Binance transport + frame functions; `validate_tick`/`normalize_timestamp`; `CandleAggregator` flush/late-tick; bounded recorder/latency |
| `src/traderos/infrastructure/health.py` | **OT-010:** `run_with_timeout`, `HealthService.check_timeout`/`summary`/`history` |
| `src/traderos/infrastructure/observability.py` | **OT-010:** SQLite health check timeout-bound |
| `src/traderos/interfaces/api/server.py` | **OT-010:** `/healthz` liveness; `/health` bounded readiness with 503 degraded |
| `src/traderos/infrastructure/database/connection.py` | **OT-011:** `ThreadSafeSQLiteConnection` + cursor proxies; explicit config wins |
| `src/traderos/infrastructure/database/migration_utils.py` | **OT-005/H7:** `detect_backend`/`execute` cursor routing |
| `src/traderos/infrastructure/database/migration_manager.py` | **OT-005:** execute-routed statements; marker deleted before `down()` |
| `src/traderos/infrastructure/database/migrations/v002/v003/v004/v005` | **OT-005:** backend-aware, idempotent, `v005` journal table (new) |
| `src/traderos/infrastructure/run_manifest.py` | **OT-002:** `DurableRunManifest` + `detect_unclean_shutdown` |
| `src/traderos/application/daemon_controller.py` | **OT-002:** `_detect_crash`/`_recover_from_crash` on `run_forever` |
| `src/traderos/domain/entities/trade.py` + 3 trade repos | **OT-005:** `OPEN_TRADE_STATUSES` parity |

### Tests
| File | Tests |
|------|-------|
| `tests/test_programme_b_operational_trust.py` (new) | **51 regression tests** covering all 11 findings |

### Docs
| File | Purpose |
|------|---------|
| `docs/engineering/OPERATIONAL_TRUST_MATRIX.md` | Closure matrix: root cause → fix → test → evidence for OT-001…OT-011 |
| `docs/engineering/RECOVERY_TRUTH.md` | What recovers after Programme B; declared non-fabricated remaining gaps |
| `docs/engineering/FAILURE_INJECTION_REPORT.md` | 20 injected faults (F1–F20) with expected/observed behavior |
| `docs/engineering/MASTER_EXECUTION_PROGRAMME.md` §26 | SPRINT 13 dashboard + monthly update |
| `docs/engineering/STRATEGIC_COMPLETION_BLUEPRINT.md` §13/§14/§Programme B | Post-B PRI matrix, trust posture, in-progress status |

## Machine Truth

| Metric | Value |
|--------|-------|
| Total tests | **864 passing, 0 failures** (`python3 -m pytest -q -p no:randomly`, excluding 2 pre-existing environment-dependent flakes) |
| New tests added (Programme B) | **51** in `tests/test_programme_b_operational_trust.py` |
| Coverage | **83.77%** (baseline 84.63% pre-B) — threshold 70% exceeded |
| Ruff | 0 errors on `src/traderos` |
| Pyright | 0 errors |
| Regressions | 0; 2 env-dependent pre-existing flakes confirmed on baseline `0012d73` (psycopg2 no-server; API/benchmark load-timing) |

**Declared remaining risks (not fabricated as closed):**
- **R-01 — live Binance WebSocket connectivity:** no outbound network / `websockets` package in this sandbox. Transport is structurally implemented and pure-frame-tested; live connect/authenticated validation is a deployment-time step.
- **R-02 — live Alpaca + Postgres behavior:** no credentials / no Postgres server. Fill guards and PG migration path are contract/structure-tested; real broker partial-fill ordering, `cancel_replace` semantics, and PG failover remain unverified.
