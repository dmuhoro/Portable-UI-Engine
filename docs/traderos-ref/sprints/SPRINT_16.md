# Sprint 16 — Programme C Delivery: Auth, Observability, Dashboard, Live-Verification, Ops Polish

**Period:** 2026-08-01
**Objective:** Deliver the remaining Programme C work packages in sequential layers — Layer 1 WP-3 Auth/RBAC, Layer 2 WP-4 Observability, Layer 3 WP-1 Dashboard, Layer 4 WP-2 Live-trading verification/dry-run, Layer 5 WP-5 Ops polish — each gated by the full suite before the next, ending with docs, CHANGELOG, and a clean push.

**Reference docs:** `docs/engineering/STRATEGIC_COMPLETION_BLUEPRINT.md` (Programme C work packages), `docs/engineering/FINISH_LINE_DASHBOARD.md` (operator surface), `docs/engineering/CONSTITUTION.md`.

---

## Layer Register

| Layer | WP | Deliverable | Gate |
|-------|----|-------------|------|
| 1 | WP-3 | API-key Auth/RBAC: `require_read`/`require_operate`/`require_admin`, `/v1/auth/me`, open-by-default with configured keys | `tests/test_auth.py` (16) green |
| 2 | WP-4 | EventBroker + `/v1/events` SSE, kill-switch alerting, Binance gating | `tests/test_observability_events.py` (11) + `tests/test_factory_ingestion.py` (4) green |
| 3 | WP-1 | Static SPA dashboard mounted at `/dashboard/` with root 307 | `tests/test_dashboard.py` (6) green |
| 4 | WP-2 | Live-readiness service + `GET /v1/live/check` + workflow dry-run | `tests/test_live_readiness.py` (8) + dry-run suites green |
| 5 | WP-5 | Deterministic full suite (rate-limiter reset), lint/typecheck clean, sprint record + CHANGELOG, push | **1031 passed, 1 skipped**; ruff/pyright clean |

## Work Completed

### Layer 1 — WP-3 Auth / RBAC
- **Open-by-default** security posture: with no API keys configured, all endpoints stay open (dev parity). Setting any of `TRADEROS_ADMIN_API_KEY`/`TRADEROS_OPERATOR_API_KEY`/`TRADEROS_VIEWER_API_KEY` (legacy `TRADEROS_API_KEY` → admin) enables enforcement.
- **`infrastructure/auth.py`** — `APIKeyAuthenticator`: key → role resolution, constant-time-ish comparison, header/query-key lookup.
- **`interfaces/api/security.py`** — FastAPI dependencies `require_read`/`require_operate`/`require_admin` wired as `Depends(...)` on every protected route; `security.set_authenticator(...)` for tests; auth-info helper.
- **`GET /v1/auth/me`** — returns authenticated principal (role, key name) or 401 when enforcement is active.
- **Open paths preserved by design:** `/v1/healthz`, `/v1/health`, `/metrics`, and the `/dashboard` static mount remain unauthenticated.

### Layer 2 — WP-4 Observability
- **`interfaces/api/events.py`** — `EventBroker`: thread-safe bounded buffer (maxlen 50, drops oldest on overflow) with blocking `get(timeout)`; `get_broker`/`reset_broker`/`publish_event`.
- **`/v1/events`** — SSE endpoint (snapshot-first, keepalive every 15 s via `asyncio.to_thread`, unsubscribe in `finally`).
- **Fixed a real stream-blocking bug:** `asyncio.to_thread(sub.get, timeout=15)` was passing `timeout` as a positional arg to `BlockingQueue.get` (i.e. `sub.get(15, None)`); corrected to the positional `sub.get(True, 15)` in `event_stream(...)`.
- **`operator.event_stream(broker, orch_provider, wait_timeout=15.0)`** — reusable async generator factored out of the route so it is testable without HTTP buffering (TestClient buffers `stream()` responses, so SSE tests drive the generator directly with `@pytest.mark.anyio` and introspect the route via `APIRouter.routes` + `StreamingResponse` type checks).
- **Kill-switch alerting** — engage/disengage handlers emit `NotificationLevel.CRITICAL`/`WARNING` notifications with `metadata={"source": "operator_api"}`.
- **Binance gating** — real crypto feed only when `data_collection.binance.enabled` **and** the collector is installed; `configs/settings.yaml` ships `binance: enabled: false`.
- **`server.reset_rate_limiter()`** added to clear per-IP buckets for tests / hot-reload tooling; fixed a `NameError: name 'publish_event'` by routing through `events.publish_event(...)` (also repaired 3 previously-failing full-suite tests).

### Layer 3 — WP-1 Dashboard
- **Static SPA** at `src/traderos/interfaces/api/dashboard/`: `index.html`, `style.css`, `app.js`.
- **Capabilities:** API-key sign-in via `/v1/auth/me`, live SSE event log, workflow advance, kill-switch, strategy catalog (create/enable/disable/promote/archive), position/order/trade tables, equity-curve canvas.
- **Mounting:** `server.py` builds a dedicated `APIRouter`, registers operator endpoints, then `app.mount("/dashboard", StaticFiles(directory=_dashboard_dir, html=True), name="dashboard")`; landing page at `GET /dashboard/`; root `GET /` 307-redirects to `/dashboard/`.
- **Packaging:** files ship under `Path(__file__).parent / "dashboard"`; `pyproject.toml` adds `[tool.setuptools.package-data]` → `"traderos.interfaces.api.dashboard" = ["*.html", "*.js", "*.css"]` so wheels carry the assets (`pip install -e` in Docker already includes them via `PYTHONPATH=/app/src`).

### Layer 4 — WP-2 Live-trading verification / dry-run
- **`domain/services/live_readiness.py`** — `LiveReadinessService.check()` → `LiveReadinessVerdict` (`ready`, `dry_run`, `live_execution_enabled`, `checks`, `reasons`, `timestamp`; `to_dict()`). Checks broker connectivity/balance, market-data sources, kill-switch state, live preflight, operator-session state.
- **`GET /v1/live/check`** — read-gated endpoint returning `orch.live_readiness.check().to_dict()`.
- **Workflow dry-run** — `WorkflowAdvanceRequest.dry_run: bool = False`; `OperatorSessionService._gate_controlled_live` accepts `dry_run` in context with detail fields `dry_run`/`live_execution_enabled` and a distinct "dry-run — live execution disabled" result message, letting operators rehearse the `controlled_live` transition without enabling real execution.
- **Factory wiring** — `TradingOrchestrator` gains `live_readiness: LiveReadinessService | None`; `factory.py` builds it with broker/ingestion/preflight/kill-switch/operator-session and `live_execution_enabled=(mode==LIVE)`.

### Layer 5 — WP-5 Ops polish
- **`tests/conftest.py` (new)** — autouse fixture calls `server.reset_rate_limiter()` before every test, making the randomized-order full suite deterministic (eliminates transient order-dependent 429s).
- **Cleanup on review:** removed duplicated fields in `WorkflowAdvanceRequest` (PIE794) and unused imports in `tests/test_live_readiness.py` (F401); simplified a redundant `is not None` comparison in `live_readiness.py` (reportUnnecessaryComparison).

## Key Files Created/Modified

### Source
| File | Change |
|------|--------|
| `src/traderos/infrastructure/auth.py` (new) | `APIKeyAuthenticator`, key→role resolution |
| `src/traderos/interfaces/api/security.py` (new) | `require_read`/`require_operate`/`require_admin`, `set_authenticator`, `auth_info` |
| `src/traderos/interfaces/api/events.py` (new) | `EventBroker`, `publish_event`, broker lifecycle |
| `src/traderos/interfaces/api/operator.py` | `/v1/events` SSE, `event_stream(...)`, `/v1/live/check`, workflow `dry_run`, kill-switch alerting, RBAC deps, duplicate-field fix |
| `src/traderos/interfaces/api/server.py` | dashboard mount, root 307, `reset_rate_limiter()`, `events.publish_event(...)`, RBAC deps |
| `src/traderos/interfaces/api/dashboard/` (new) | Static SPA: `index.html`, `style.css`, `app.js` |
| `src/traderos/domain/services/live_readiness.py` (new) | `LiveReadinessService` + `LiveReadinessVerdict` |
| `src/traderos/domain/services/operator_session.py` | `dry_run` support in `controlled_live` gating |
| `src/traderos/application/factory.py` | Binance gating, `live_readiness` wiring, `live_execution_enabled` |
| `src/traderos/application/orchestrator.py` | `live_readiness` field |
| `configs/settings.yaml` | `data_collection.binance.enabled: false` |
| `pyproject.toml` | `[tool.setuptools.package-data]` for dashboard assets |

### Tests
| File | Tests |
|------|-------|
| `tests/test_auth.py` (new) | 16 — key auth, roles, /auth/me, open-by-default |
| `tests/test_observability_events.py` (new) | 11 — EventBroker semantics, kill-switch alerting, `event_stream`/route |
| `tests/test_factory_ingestion.py` (new) | 4 — Binance gating default/disable/process-enable |
| `tests/test_dashboard.py` (new) | 6 — index/assets served, panel presence |
| `tests/test_live_readiness.py` (new) | 8 — readiness verdicts, checks, dry-run mode |
| `tests/conftest.py` (new) | autouse rate-limiter reset (deterministic suite) |
| `tests/test_operator_api.py` | dry-run workflow + `/v1/live/check` (21 total) |
| `tests/test_operator_session.py` | 3 dry-run tests (16 total) |

### Docs
| File | Purpose |
|------|---------|
| `docs/sprints/SPRINT_16.md` (new) | This sprint record |
| `CHANGELOG.md` | New `[Unreleased] — Sprint 16` section |

## Machine Truth

| Metric | Value |
|--------|-------|
| Total tests | **1031 passing, 1 skipped** (full suite, two consecutive randomized runs) |
| Coverage | **86.80%** (threshold 70% exceeded) |
| Ruff | 0 errors on all changed `src/traderos` files + new/updated tests (8 pre-existing baseline findings untouched) |
| Pyright | 0 errors on all changed `src/traderos` files |
| Suite determinism | `tests/conftest.py` autouse `reset_rate_limiter()` removes order-dependent 429s |

**Known open items (carried forward, not blockers):**
- Live Binance/Alpaca execution still requires real credentials; the `/v1/live/check` verdict and workflow dry-run provide the pre-flight verification path without them.
