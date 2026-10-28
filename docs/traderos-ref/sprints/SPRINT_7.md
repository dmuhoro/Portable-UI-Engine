# Sprint 7 — Production Readiness Programme

**Period:** 2026-07-28
**Objective:** Transform paper-trading platform into secure, deployable, operational quantitative research system.

---

## Phase 1 — Production Blockers ✅
| Item | Status |
|------|--------|
| **HTTPS support** | `SSL_KEYFILE`/`SSL_CERTFILE` env vars → uvicorn in `main.py` |
| **Secure CORS** | `CORS_ORIGINS` env var (comma-separated); default `*` for local dev |
| **CI security gates** | Removed `|| true` from `pip-audit` and `bandit` steps |
| **Domain exception adoption** | `ServiceError`/`InfrastructureError`/`ConfigError` in `retry.py`, `alpaca_broker.py`, `config_loader.py`, `notification_service.py` |
| **Startup validation** | `validate` CLI command; daemon calls `Config.validate()` before run loop |
| **Dependency hygiene** | Stale `requirements.txt` deleted; `pyproject.toml` sole source of truth |

## Phase 2 — PostgreSQL Support ✅
| Item | Files |
|------|-------|
| `DATABASE_URL` config + `psycopg2-binary` dep | `config_loader.py`, `pyproject.toml` |
| Connection factory | `infrastructure/database/connection.py` |
| DB-agnostic migrations | `migration_manager.py`, `v001_initial.py`, `v002_observability.py`, `v003_strategies.py` |
| PostgresRepository base class | `infrastructure/repositories/postgres/base.py` |
| PostgresSignalRepository | `infrastructure/repositories/postgres/signals.py` |
| PostgresTradeRepository/PostgresPositionRepository | `infrastructure/repositories/postgres/trades.py` |
| PostgresAuditService/PostgresMetricsService/PostgresHealthService/PostgresManifestService | `infrastructure/observability_postgres.py` |
| Factory runtime backend selection | `application/factory.py` |
| Archiver PostgreSQL compat | `infrastructure/archiver.py` |

## Phase 3 — Observability ✅
| Item | Files |
|------|-------|
| Prometheus client dep | `pyproject.toml` (`monitoring` extra) |
| PrometheusMetricsService | `infrastructure/monitoring.py` |
| Prometheus `/metrics` scrape endpoint | `interfaces/api/server.py` |
| Structured JSON logging | `infrastructure/logging/__init__.py` (`setup_json_logging`, `JsonFormatter`) |
| Request metrics middleware | `interfaces/api/server.py` (`_request_metrics`) |

## Phase 4 — API Hardening ✅
| Item | Files |
|------|-------|
| Rate limiter | `infrastructure/rate_limiter.py` |
| Rate limiting middleware | `interfaces/api/server.py` (`_rate_limit_middleware`) |
| `/metrics` exempt from auth | `interfaces/api/server.py` |
| `RATE_LIMIT_MAX` env var | `interfaces/api/server.py` |

## Phase 5 — Deployment ✅
| Item | Files |
|------|-------|
| Dockerfile (Python 3.14, all extras) | `Dockerfile` |
| Railway deploy config | `railway.json` |
| Nixpacks config | `nixpacks.toml` |
| CI upgraded to Python 3.14 | `.github/workflows/ci.yml` |

## Phase 6 — Verification ✅
| Item | Tests |
|------|-------|
| PrometheusMetricsService unit tests | `tests/test_monitoring.py` (7 tests) |
| RateLimiter unit tests | `tests/test_rate_limiter.py` (4 tests) |
| Database connection tests | `tests/test_database_connection.py` (3 tests) |
| Prometheus endpoint test | `tests/integration/test_api.py` |
| Rate limit headers test | `tests/integration/test_api.py` |
| **Total: 666 tests passing at 86% coverage** | |

---

## Key Files Created/Modified

### New files
- `src/traderos/infrastructure/database/connection.py`
- `src/traderos/infrastructure/monitoring.py`
- `src/traderos/infrastructure/rate_limiter.py`
- `src/traderos/infrastructure/observability_postgres.py`
- `src/traderos/infrastructure/repositories/postgres/__init__.py`
- `src/traderos/infrastructure/repositories/postgres/base.py`
- `src/traderos/infrastructure/repositories/postgres/signals.py`
- `src/traderos/infrastructure/repositories/postgres/trades.py`
- `railway.json`
- `nixpacks.toml`
- `tests/test_monitoring.py`
- `tests/test_rate_limiter.py`
- `tests/test_database_connection.py`

### Modified files
- `pyproject.toml` — postgres + monitoring extras
- `Dockerfile` — Python 3.14, all extras
- `.github/workflows/ci.yml` — Python 3.14, postgres+monitoring extras
- `src/traderos/infrastructure/config/config_loader.py` — `DATABASE_URL`
- `src/traderos/infrastructure/database/migration_manager.py` — backend detection
- `src/traderos/infrastructure/database/migrations/v001_initial.py` — pg compat
- `src/traderos/infrastructure/database/migrations/v002_observability.py` — pg compat
- `src/traderos/infrastructure/database/migrations/v003_strategies.py` — pg compat
- `src/traderos/infrastructure/archiver.py` — pg compat
- `src/traderos/infrastructure/logging/__init__.py` — `setup_json_logging()`
- `src/traderos/application/factory.py` — backend dispatch
- `src/traderos/interfaces/api/server.py` — metrics endpoint, rate limiter, structured logging
- `tests/integration/test_api.py` — new endpoint tests
