# Sprint 15 — Deployment, Railway, and Maintenance/Release

**Period:** 2026-08-01
**Objective:** Close the Deployment (5 items) and Maintenance/Release (4 items) gaps in a 12-hour block: compose stack, PostgreSQL migrations-on-boot, live Railway deployment, CI deploy gate, single version source, release workflow, secret rotation + retention, and documentation. Sequential layers, each gated before the next.

**Reference docs:** `docs/engineering/STRATEGIC_COMPLETION_BLUEPRINT.md` (Deployment / Maintenance & Release), `docs/architecture/ADR-005` (SQLite dev / PostgreSQL prod).

---

## Layer Register

| Layer | Item | Deliverable | Gate |
|-------|------|------------|------|
| 1a | DEP-1 | Rewritten `docker-compose.yml` (postgres + api + daemon + test PG) | `docker compose config -q` |
| 1b | DEP-2 | Fresh-PostgreSQL migrations E2E (v001–v006) | fresh PG → Schema version 6, `db check` OK |
| 1c | DEP-3 | Compose stack boots: API healthy, daemon running paper cycles | healthz 200, daemon `run_manifest` start row |
| 1d | DEP-4 | CI `deploy-check` job (compose validation + fresh-PG migration smoke + API container health) | CI green |
| 1e | DEP-5 | Railway deploy: Dockerfile + `railway.toml` (volumes, healthcheck), `$PORT` binding, PG service + `DATABASE_URL` | `traderos-production.up.railway.app` Online |
| 2a | M/R-1 | Single version source (`pyproject.toml`); `VERSION` file removed; `settings.yaml` synced; CI version drift check | CI green |
| 2b | M/R-2 | `release.yml`: tag-triggered gate + wheel + GHCR image + GitHub Release from CHANGELOG | YAML valid |
| 2c | M/R-3 | SecretRotator wired into orchestrator lifecycle + surfaced in status; `order_events` retention; rotating log files | 981 tests green |
| 3 | M/R-4 | `docs/sprints/SPRINT_15.md` + `CHANGELOG.md` | committed |

## Work Completed

### DEP — Deployment gaps
- **`docker-compose.yml`** (rewritten): `postgres` (16-alpine, `pg_isready` healthcheck), `traderos-api` (DATABASE_URL→postgres, `curl /v1/healthz` healthcheck), `traderos-daemon` (`entrypoint: traderos`, `command: daemon --interval 60 --mode paper`), `postgres-test` (test profile, port 5433); named volumes `postgres_data`/`traderos_data`/`traderos_exports`.
- **PostgreSQL migrations fixed** (fresh-PG path was previously un-runnable):
  - v001 `_serial()` now emits `SERIAL PRIMARY KEY` (bare `SERIAL` broke FK to `observations(id)` on PG).
  - v001 `is_active BOOLEAN DEFAULT 1` → `DEFAULT TRUE` (PG datatype mismatch).
  - Removed obsolete legacy `strategies`/`backtest_results` tables from v001 (repo-owned schema is authoritative since v003/v006).
  - v006 added `_serial(backend)`; unified legacy-rebuild path for both backends (drop `backtest_results` FK-first, rename to `strategies_legacy`, copy into repo DDL, drop; else ensure repo DDL).
  - CLI `db check` now uses `with conn.cursor()` (was `conn.execute`, broken on psycopg2).
  - Verified on fresh Postgres 16: migrate → Schema version 6; `strategies` columns = id/name/params/version/status/template/created_at.
- **Compose stack boot**: `docker compose up -d --build` → postgres/api/daemon all healthy; `GET /v1/healthz` 200, `GET /v1/health` 200 (mode paper); daemon process confirmed as `traderos daemon --interval 60 --mode paper` writing `run_manifest` to prod PG.
- **CI `deploy-check` job**: `docker compose config -q`; `docker build`; `db migrate` + `db check` (asserts Schema version 6) against a fresh CI Postgres via `--network host`; API container health smoke (`/v1/healthz` 200).
- **Railway** (https://traderos-production.up.railway.app, currently **Online**):
  - Removed `VOLUME` from the Dockerfile (Railway rejects it) and declared `/app/data` + `/app/exports` volumes in a new `railway.toml` with `healthcheckPath: /v1/healthz` and `startCommand: traderos-api`.
  - API binds `$PORT` (env) with `8000` fallback — Railway healthchecks the app on `$PORT`.
  - Added `Postgres-gKbz` (PostgreSQL 18.4) service, set `DATABASE_URL` to the internal URL on the app service, redeployed → all DB-backed endpoints return 200 on the fresh DB.
  - Deleted the duplicate auto-created `Postgres` service.

### M/R — Maintenance/Release gaps
- **Single version source**: `pyproject.toml` is now the sole version source (`1.1.0`); the dead root `VERSION` file removed; `configs/settings.yaml` `version` synced to `1.1.0`; new CI `version-check` job fails on drift.
- **`release.yml`**: on `v*` tag — asserts tag == `pyproject.toml` version, runs the full test gate against a CI Postgres, builds sdist/wheel, pushes the GHCR image (`ghcr.io/dmuhoro/traderos`, semver tags), creates a GitHub Release with the matching CHANGELOG section as notes.
- **SecretRotator wiring**: `SecretRotator` (env provider) now built in `build_orchestrator`, attached to `TradingOrchestrator`, started/stopped with the orchestrator lifecycle, and surfaced in `get_status()` as `secret_rotation` stats.
- **Journal/log retention**: `archiver.purge_old_entries` now purges the `order_events` journal (via `applied_at`) alongside the existing tables; file logging switched to `RotatingFileHandler` with `LOG_MAX_BYTES` (default 10 MB) and `LOG_BACKUP_COUNT` (default 5).

## Key Files Created/Modified

### Source
| File | Change |
|------|--------|
| `docker-compose.yml` | Rewritten full stack (postgres, api, daemon, postgres-test) |
| `Dockerfile` | Removed `VOLUME`; added `curl`; `/app/data` + `/app/exports` mkdir/chown |
| `railway.toml` (new) | Dockerfile builder, healthcheck, startCommand, volumes |
| `src/traderos/interfaces/api/main.py` | Bind `$PORT` (Railway) with 8000 fallback |
| `src/traderos/infrastructure/database/migrations/v001_initial.py` | PG: `SERIAL PRIMARY KEY`, `DEFAULT TRUE`, legacy tables removed |
| `src/traderos/infrastructure/database/migrations/v006_operator_surface.py` | `_serial(backend)`, unified legacy strategy rebuild |
| `src/traderos/interfaces/cli/main.py` | `db check` uses `conn.cursor()` |
| `src/traderos/application/factory.py` | SecretRotator wiring; `_build_secret_rotator()` |
| `src/traderos/application/orchestrator.py` | SecretRotator lifecycle + `secret_rotation` status |
| `src/traderos/infrastructure/archiver.py` | `order_events` retention via `applied_at` |
| `src/traderos/infrastructure/logging/__init__.py` | `RotatingFileHandler` retention (`LOG_MAX_BYTES`, `LOG_BACKUP_COUNT`) |

### CI / Release
| File | Change |
|------|--------|
| `.github/workflows/ci.yml` | New `version-check` and `deploy-check` jobs |
| `.github/workflows/release.yml` (new) | Tag-triggered release pipeline |

### Tests
| File | Tests |
|------|-------|
| `tests/test_archiver.py` (new) | `order_events` + audit retention (expired purged, recent kept) |
| `tests/integration/test_factory.py` | SecretRotator wired + lifecycle |

### Docs
| File | Purpose |
|------|---------|
| `docs/sprints/SPRINT_15.md` (new) | This sprint record |
| `CHANGELOG.md` | New `[Unreleased] — Sprint 15` section |

## Machine Truth

| Metric | Value |
|--------|-------|
| Total tests | **981 passing, 1 skipped** (full suite incl. PG-backed observability) |
| Coverage | **86.53%** (threshold 70% exceeded) |
| Ruff / Pyright | 0 errors on `src/traderos` + new tests |
| Pre-commit | All hooks pass (black, isort, ruff, pyright, trailing whitespace, EOF, YAML, merge-conflict, private-key) |
| Docker | `docker compose config -q` valid; stack boots healthy |
| Railway | `traderos-production.up.railway.app` **Online**, Postgres-gKbz Online |

**Known open items (carried forward, not blockers):**
- Live Binance/Alpaca verification needs real API credentials (not present in this environment) — runbook path documented; paper mode is the deployed default.
- The Railway public TCP proxy for Postgres (`postgres-gkbz-production.up.railway.app`) had not finished syncing at close; internal `DATABASE_URL` is authoritative for the app.
- A second `Postgres` service was auto-created during Railway project setup and was deleted; only `Postgres-gKbz` remains.
