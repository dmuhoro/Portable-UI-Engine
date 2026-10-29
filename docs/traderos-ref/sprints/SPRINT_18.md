# Sprint 18 — Coverage to 91.8% + Production Security Hardening

**Period:** 2026-08-01
**Objective:** Close the remaining coverage gap across the flagged low-coverage modules (86.80% → 91.82%) and harden the production security posture so the deployment fails closed — authentication and TLS become mandatory under `TRADEROS_ENV=production`, with a `traderos security audit` CLI as verifiable evidence. Built in layers (1a unit → 1b PostgreSQL → 1c mop-up → Layer 2 security), each gated by the full suite, then the sprint record + CHANGELOG + push.

**Reference docs:** `docs/AUDIT_GROUND_TRUTH.md`, `docs/engineering/STRATEGIC_COMPLETION_BLUEPRINT.md`, `docs/runbooks/PILOT_READINESS.md`, `docs/runbooks/CONTROLLED_PILOT.md`.

---

## Work Package Register

| Layer | Deliverable | Gate |
|-------|-------------|------|
| 1a | Unit coverage for `market_hours_engine`, `webhook_notifier`, `leader_election`, `message_queue`, `interfaces/api/main.py` | 5 new/extended test files green |
| 1b | PostgreSQL-backed tests for `observability_postgres` + postgres `base/signals/trades` repos (against `traderos-pg-test`) | `test_observability_postgres_services.py` (18) + `test_postgres_repositories.py` (25) green |
| 1c | Mop-up: `sqlite/knowledge` (`get_neighbors` BFS), `in_memory/indicators`, `v004` migration | `test_sqlite_repos.py` + `test_in_memory_repos.py` + `test_migration_v004.py` green |
| Layer 2 | Production fail-closed posture + `traderos security audit` | `test_security_policy.py` (15) + CLI/API-main tests green |
| Final | Full suite, lint/typecheck, sprint record + CHANGELOG, push | **1201 passed, 1 skipped**; **91.82%**; ruff/pyright clean |

## Work Completed

### Layer 1a — Unit coverage for flagged modules
- **`domain/services/market_hours_engine.py`** — bug fixes surfaced by tests: `MarketSession.contains` now returns True for 24h sessions (`open == close`); `is_open` special-cases `CRYPTO_24_7` (always open) and `FOREX_24_5` (weekdays only); sentinel sessions are compared by **identity** (`is`) instead of structural `==`, which conflated `FOREX_24_5`/`CRYPTO_24_7` (both `time(0,0)`/`time(0,0)`/`UTC`); `next_open` now advances to the next valid session open when called after close or on a weekend. Coverage 38% → **98%**.
- **`infrastructure/notifiers/webhook_notifier.py`** — real latent bug: `retry_with_backoff` raises `ServiceError`, which the except clause `(_URLError, OSError)` never caught, leaking webhook failures; `ServiceError` added to the catch. Coverage 43% → **84%** (remaining lines are unreachable defensive branches).
- **`infrastructure/leader_election.py`** — PG `LeaderElection` exercised via fake connection (acquire/release, no-duplicate-callback, heartbeat thread). Coverage 58% → **97%**.
- **`infrastructure/message_queue.py`** — `RedisMessageQueue` exercised via a fake `redis` module (from_url/pubsub/subscribe/publish/close, `create_message_queue` routing). Coverage 67% → **100%**.
- **`interfaces/api/main.py`** — uvicorn runner tests (host/port env, SSL wiring, built-app passthrough). Coverage 33% → **94%**.

### Layer 1b — PostgreSQL-backed coverage
- **`infrastructure/observability_postgres.py`** — `PostgresAuditService` (linked hash chain, verify, find/get_entries), `PostgresMetricsService` (counters/gauges/timing/query/clear), `PostgresHealthService` (register/report/check with exception mapping/history), `PostgresManifestService` (record/get_runs/summary/clear) against the live `traderos-pg-test` container on `localhost:5433` (`POSTGRES_TEST_DSN`). Coverage 35% → **99%**.
- **Postgres repos** — `PostgresRepository` CRUD helpers + `PostgresSignalRepository` (get_active/get_by_strategy/get_range), `PostgresTradeRepository` (get_open honours `OPEN_TRADE_STATUSES`, fill round-trip, submit), `PostgresPositionRepository` (get_by_market/list_open/update). Coverage: base 39% → **94%**, signals 51% → **100%**, trades 41% → **100%**.

### Layer 1c — Mop-up
- **`repositories/sqlite/knowledge.py`** — `get_by_label`, `get_by_type`, `search`, embedding round-trip, edge `get_by_source`/`get_by_target`, and the `get_neighbors` BFS (depth 1, depth 2, no-neighbors, missing-node). Coverage 55% → **100%**.
- **`repositories/in_memory/indicators.py`** — `get_by_name` and `get_latest` (ordering + empty). Coverage 67% → **100%**.
- **`database/migrations/v004_external_order_id.py`** — `up`/`down` guarded paths for both sqlite and postgres backends (table missing, column present/absent, idempotent ALTERs). Coverage 69% → **100%** (+ `migration_utils` 27% → 100%).

### Layer 2 — Production security hardening (fail-closed posture)
- **`infrastructure/security_policy.py`** (new) — `TRADEROS_ENV=production` requires API keys and TLS and forbids CORS allow-all (`SecurityPolicyError` on violation); development/CI stay open-by-default (matching `APIKeyAuthenticator`). `check_security_posture()` returns a `SecurityReport` (environment, findings, verdict, `to_dict()` for JSON output). Secret rotation interval is reported as a finding.
- **`interfaces/api/main.py`** — calls `assert_production_policy` before serving; in production the API refuses to start until hardened (fails closed), verified by tests (no keys → `ConfigError`; hardened → server starts on `PORT` with TLS kwargs).
- **`interfaces/cli/main.py`** — new `traderos security audit` subcommand: human table or `--json` report, exits non-zero on insufficient posture (evidence for the pilot go/no-go gate).
- RBAC enforcement was already pervasive (every protected route depends on `require_read`/`require_operate`/`require_admin`; `tests/test_auth.py` covers 401/403 + role hierarchy); CORS deny-all default landed in Sprint 17.

## Key Files Created/Modified

### Source
| File | Change |
|------|--------|
| `src/traderos/infrastructure/security_policy.py` (new) | Environment-aware security posture + fail-closed production policy |
| `src/traderos/domain/services/market_hours_engine.py` | contains/is_open/next_open fixes; sentinel identity comparisons |
| `src/traderos/infrastructure/notifiers/webhook_notifier.py` | `ServiceError` caught after retry exhaustion |
| `src/traderos/interfaces/api/main.py` | `assert_production_policy` guard before serving |
| `src/traderos/interfaces/cli/main.py` | `security audit` subcommand |

### Tests
| File | Tests |
|------|-------|
| `tests/test_market_hours_engine.py` (new) | 26 — sessions, is_open, next_open, time_to_close |
| `tests/test_webhook_notifier.py` (new) | 7 — send/retry/backoff/error swallowing |
| `tests/test_leader_election.py` | +13 — PG `LeaderElection` with fake conn |
| `tests/test_message_queue.py` | +19 — `RedisMessageQueue` with fake redis |
| `tests/test_api_main.py` | +8 — runner + production fail-closed guard |
| `tests/test_observability_postgres_services.py` (new) | 18 — PG audit/metrics/health/manifest services |
| `tests/test_postgres_repositories.py` (new) | 25 — PG base/signals/trades/positions repos |
| `tests/test_migration_v004.py` (new) | 10 — v004 up/down sqlite + postgres |
| `tests/test_sqlite_repos.py` | +14 — knowledge node/edge functional + neighbors |
| `tests/test_in_memory_repos.py` | +3 — indicator get_by_name/get_latest |
| `tests/test_security_policy.py` (new) | 15 — posture checks + fail-closed assertions |
| `tests/test_cli.py` | +4 — security audit text/JSON/dispatch/fail |

### Docs
| File | Purpose |
|------|---------|
| `docs/sprints/SPRINT_18.md` (new) | This sprint record |
| `CHANGELOG.md` | New `[Unreleased] — Sprint 18` section |

## Machine Truth

| Metric | Value |
|--------|-------|
| Total tests | **1201 passing, 1 skipped** (full suite; skip = network-dependent Binance wss check) |
| Coverage | **91.82%** (up from 86.80%; threshold 70% exceeded) |
| Ruff | 0 errors on all changed files |
| Pyright | 0 errors on all changed files |

**Known open items (carried forward, not blockers):**
- Live Binance/Alpaca execution still requires real credentials; `pilot readiness` / `pilot dry-run` / `traderos security audit` provide the pre-flight verification path without them.
