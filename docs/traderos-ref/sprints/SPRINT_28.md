# Sprint 28 — Product track: user accounts + per-user risk rails + manufacturing meta

**Period:** 2026-08-07
**Objective:** Implement Track B's pilot-feeding rails and Track M's manufacturing
meta, per `PILOT_TO_PRODUCT.md` and `BUILD_PRINCIPLES.md`. Deliver the
user/account model (B1), then the per-user risk rails with `user_id` audit
attribution enforced **at the real live submission boundary** (B2), and forge
the FounderOS manufacturing loop on TraderOS itself (M1–M4).

**Reference docs:** `docs/engineering/PILOT_TO_PRODUCT.md`,
`docs/engineering/BUILD_PRINCIPLES.md`, `docs/engineering/FOUNDEROS_WORKFLOW_SPEC.md`,
`docs/evidence/2026-08-07_user_account_drill.log`.

---

## Ground truth (verified, not assumed)
- Live chain (`application/factory.py`): `CycleExecutor → JournaledBroker →
  GuardrailedBroker → RateLimitedBroker → AlpacaBrokerAdapter`. Order call
  sites in `cycle_executor.py` (`can_trade` + `authorize_order`).
- Per-user rails are enforced **at those two call sites** by threading
  `trading_user_id` from factory → orchestrator → executor, and each per-user
  profile is resolved from config (`risk.per_users`) by a `PerUserRiskResolver`
  installed on the `RiskService`.
- Unknown user + resolver configured → **denied fail-closed** (no silent open).
  A per-user `engaged` flag is an operator-scoped kill switch that halts that
  trader alone, never others, never the global path.

## Work Completed

### B1 — User/account model (committed earlier this sprint)
- `domain/entities/user.py`: `User`, `UserSession`, `UserApiKey` + roles/statuses.
- `domain/repositories/user_repository.py` port + SQLite impl
  (`infrastructure/repositories/sqlite/users.py`).
- `domain/services/account_service.py`: salted PBKDF2-HMAC-SHA256 + constant-time
  compare, expiring sessions (denied + evicted), one-time per-user API keys
  (only SHA-256 persisted, revoked keys deny), admin bootstrap from
  `TRADEROS_ADMIN_USERNAME`/`PASSWORD`.
- migration `v008_user_accounts.py` (schema version 8, SQLite + PG).
- Proof: `tests/test_account_service.py`, account drill
  (`docs/evidence/2026-08-07_user_account_drill.log`), integration in
  `tests/integration/test_factory.py`.

### B2 — Per-user risk rails + `user_id` attribution (this change)
- `PerUserRiskProfile` (user-scoped: gross exposure, position size, position
  count, daily loss pct, allowlist, plus a fail-closed `engaged` operator kill
  switch). All defaults bounded — no unlimited allowance.
- `PerUserRiskResolver`: unknown users fail closed (denied, not silently allowed).
- Enforcement at the real boundary — `cycle_executor.py` `can_trade` +
  `authorize_order` now take `user_id=`; `Orchestrator` threads
  `trading_user_id`; `factory.py` builds a resolver from `risk.per_users` and
  sets `trading_user_id` from `risk.operator_user_id`.
- Scoped kill switch: an engaged profile blocks only that trader; other traders
  and the global system path are unaffected.
- Proof:
  - `tests/test_per_user_rails.py` (attribution, caps, allowlist, fail-closed,
    scoped kill-switch).
  - `tests/test_cycle_risk_gate.py` **boundary proof**: an engaged per-user
    profile through the real `CycleExecutor` leaves `broker.place_market_order`
    NEVER called (`result.trades == 0`).
  - `tests/test_factory_ingestion.py`: config → resolver wiring on the real
    `build_orchestrator` path.

### Track M — manufacturing meta (FounderOS, bootstrapped on TraderOS)
- **M1** already present: `docs/engineering/BUILD_PRINCIPLES.md` (7 principles +
  5-step loop + instantiation recipe).
- **M2** `docs/engineering/FOUNDEROS_WORKFLOW_SPEC.md`: the one-page task
  template — scope / exit test / blast radius / reviewer / evidence path, with
  the define→gate→execute→verify→lock loop.
- **M3** wired into `.ai/context/13_playbook.md`: the five-field task template
  is mandatory before labour; specialized-agent roles exist under
  `.ai/agents/`.
- **M4** blast-radius tiering in the playbook: execution/risk paths
  human-gated (fail-closed real-submission proof required); CRUD/copy paths
  lightweight-gated. Default is Tier 1 when unknown.

## Work Completed

### A6 hardening — real HashiCorp Vault secret-manager integration
- `SecretProviderPort` in `domain/ports.py`; `EnvSecretProvider` (default) +
  `VaultSecretProvider` (KV-v2 via `requests`) in `infrastructure/secrets.py`.
- Factory `_build_secret_rotator` resolves `VaultSecretProvider` when
  `VAULT_ADDR`/`VAULT_TOKEN` are set; **never silently falls back to env** when
  a provider is required — the boot path fails closed (`factory.py`).
- `SecretRotator.get()` writes `secret.accessed` audit + metrics
  (`read.cached`/`read.provider`); values never leave the process (only key
  names + versions). Removed the built-in `os.getenv` bypass.
- Proof: `scripts/evidence/run_vault_secret_manager_drill.py` →
  `docs/evidence/2026-08-07_vault_secret_manager_drill.log` (5/5, against a
  real dev Vault at 127.0.0.1:8200); `tests/test_secret_provider_port.py`
  (11 tests: redaction, no-silent-fallback, fail-closed boundary seeding).

### A7 work — real trigger paths feeding the on-call transport
- Reconciliation failure wired at the **real detection seam**:
  `BrokerStateReconciliationService` now takes notifications/audit/metrics and
  delivers a CRITICAL alert when reconciliation fails; healthy reconciles stay
  silent.
- Proof: `scripts/evidence/run_trigger_alerting_drill.py` →
  `docs/evidence/2026-08-07_trigger_alerting_drill.log` (6/6: reconciliation
  failure, clean-silent, unclean shutdown, severity routing, live kill-switch
  trip — all on a real loopback HTTP transport); `tests/test_trigger_alerting.py`.

### WP3 — operational-health surfacing in the operator dashboard
- `FailoverManager.status()` reads the durable lease file + the live in-process
  signal (`leading`, `owner`, `lease_path`, `last_lease`).
- `TradingOrchestrator.get_status()` now carries `operational`:
  `ha` (configured / leading / last lease), `oncall` (`configured`,
  `min_severity`, `delivered`, `delivery_failed` from the router's own metrics
  counters), and `trading_user_id`. Unconfigured subsystems report
  `configured=False` — never claimed as protected.
- `trading_user_id` threaded into `/v1/positions`, `/v1/orders`, `/v1/trades`
  at the response seam; the dashboard renders it as a per-row column and in the
  new **Operational health** panel (`interfaces/api/dashboard/`).
- Proof: `scripts/evidence/run_operational_health_drill.py` →
  `docs/evidence/2026-08-08_operational_health_drill.log` (6/6: durable lease
  source truth, on-call counter moves 0→1→2 exactly with real kill-switch
  trips on the wire, `trading_user_id='trader-01'` on all three endpoints).
- API + unit tests in `test_operator_api.py`, `test_orchestrator.py`,
  `test_ha_failover.py`.

### B3 — Retail account seam + per-trader order entry (this change)
- The retail surface authenticates with **sessions**, not API keys:
  `POST /v1/retail/register`, `POST /v1/retail/login`, `POST /v1/retail/logout`
  (server-side revoke), `GET /v1/retail/me` (profile + per-trader risk rails).
  All backed by the real `AccountService` (PBKDF2 + constant-time compare,
  fail-closed) now wired into the orchestrator (`factory.py` builds a
  `SQLiteUserRepository` + `AccountService`; PG backend honestly reports the
  account service as not-configured).
- Order entry `POST /v1/retail/orders` runs through the **SAME real
  submission path as the live loop**: `CycleExecutor.submit_retail_order()`
  calls the per-user `RiskService.authorize_order(user_id=...)`, then
  `GuardrailedBroker.place_market_order`, then the same portfolio persistence +
  causal audit chain (`decision.made → order.placed → trade.fill`) so a refused
  order never reaches the broker and every outcome is replayable.
- **Fail-closed by default**: `authorize_order` denies before any broker call;
  retail order entry is **paper-mode only** (live/backtest refuse 403 rather
  than pretending a path exists); a missing/expired session token denies 401.
- Proof:
  - `tests/test_retail_api.py` — sessions, register/login/logout, order entry
    fail-closed, invalid-market 422.
  - `tests/test_retail_api.py::TestRetailOrderProofRealPath` **wire proof**:
    an engaged per-user profile through the real `CycleExecutor` leaves
    `broker.place_market_order` NEVER called while the same loop with an engaged
    profile calls it exactly once.

### B4 — Causal attribution / regulator replay endpoint (product change)
- `GET /v1/attribution/replay?start=…&end=…` (operator `require_read`) runs the
  real `ReplayService.replay_day()`: reconstructs each fill's causal chain from
  the durable audit trail and recomputes realized PnL via FIFO matching. Honest
  data source — the replay reads the same audit/trade repos the live loop
  writes; nothing is fabricated for this view.
- Proof: `tests/test_attribution_api.py` exercises the endpoint against a real
  orchestrator with an order submitted through the retail seam; asserts the
  causal chain is complete and `end < start` returns 422.

### C — 7-route frontend contract (product change)
Closes the production CORS gap and makes the CURRENT dashboard + friend beta a
typed, authenticated consumer of the operator surface. Scope is exactly the
7 in-scope routes; EVERYTHING else (pagination, `localStorage` XSS,
PG-backed operator login, Market Overview/Research Lab screens, Next.js) stays
explicitly out of scope.

- **CORS (TASK 1):** `CORS_ORIGINS` unset in production meant every browser
  cross-origin call was refused. Set
  `https://traderos-production.up.railway.app,http://localhost:3000` on
  Railway and verified live: pre-flight `OPTIONS` and cross-origin `GET` return
  `access-control-allow-origin`; a disallowed origin gets no header. No
  `CORS_ORIGINS=*`.
- **Orders contract (TASK 2):** `/v1/orders` returned raw broker dicts
  (`qty`/`type`, no `status`) that the dashboard could not render. Added
  `_normalize_order` at the response seam — stable `id`, `symbol`, `side`,
  `quantity` (float), `order_type`, `status` (default `open`), tolerating both
  paper and legacy (`order_id`/`market_id`) broker shapes.
- **Error envelope (TASK 3):** unified the 7 in-scope routes (and FastAPI 422
  validation failures via a `RequestValidationError` handler) on the single
  `{"error": {"code", "message"}}` envelope; shape documented in the OpenAPI
  `info.description`.
- **Typed response models (TASK 4):** pydantic v2 models in `schemas.py` wired
  via `response_model=` on positions/orders/trades/portfolio/kill-switch/
  readiness/strategies and exposed in `/openapi.json` — the real
  prerequisite for a generated frontend client.
- **Authenticated browser SSE (TASK 5):** `EventSource` cannot send
  `X-API-Key`, so previously SSE only worked with auth open. `sse_tokens.py`
  mints short-lived (TTL 60 s, `EVENT_TOKEN_TTL_SECONDS`), single-purpose,
  single-use, HMAC-signed tokens via authenticated `GET /v1/events/token`;
  `security.require_sse` + the boundary let a valid token open exactly the
  SSE route and nothing else; replay/expiry/bogus → 401. The dashboard now
  mints and subscribes with `?token=` when auth is required.
- Proof exercises the real paths: `tests/test_sse_token.py` (incl. a real
  uvicorn subprocess), `tests/test_order_contract.py` (real paper orchestrator
  with a real open limit order), envelope-consistency cases across all 7
  routes.

### AS-7 — Immune-system layer: broker circuit breaker + synthetic probes
The first concrete slice of the founder-approved operational-immune system.
Two gaps closed at the real boundary, with honest scoping.

- **Thread-safe circuit breaker (`infrastructure/resilience.py`):** closed /
  open / half-open states, per-dependency preconfigured instances
  (`BROKER_CB`, `VAULT_CB`, `PG_CB`), public config accessors
  (`threshold` / `recovery_seconds`) and a `get_breaker_status()` probe seam.
  The timeout wrapper uses a **thread-bounded worker** (mirrors the existing
  `run_with_timeout`), NOT `SIGALRM` — the earlier draft used
  `signal.setitimer`, which only works from the main thread and is
  process-global, and would be a production crash vector inside the FastAPI
  threadpool. Fixed before wiring.
- **Enforced at the real submission boundary (`infrastructure/broker_circuit_breaker.py`):**
  a `BrokerAdapter` decorator (same composition pattern as `RateLimitedBroker`
  / `GuardrailedBroker`) wrapped around the broker in `factory.py`, so
  **every** submit/cancel call from any caller (cycle executor, paper service,
  flatten, probe) is circuit-protected. The decorator lives in
  `infrastructure`, NOT on the domain `PaperBrokerAdapter`, so the
  domain-never-imports-infrastructure ADR stays intact — the initial draft that
  decorated the domain service was detected by the
  `architecture/test_dependency_direction.py` gate and moved to the correct
  boundary before landing.
- **Probes (`interfaces/api/operator.py`):** `GET /v1/probes/broker` +
  `GET /v1/probes` run a synthetic probe through the **public** broker API —
  `place_limit_order(..., close_price=None)` (PENDING) then `cancel_order` —
  never touching private broker fields (the prior draft called
  `_next_order_id` / `_record_order` and broke against the guard-railed
  wrapper). Round-trip latency > 1000 ms → `ok=false`. **In LIVE mode the
  probe is read-only** (balance + open-orders round-trip): a cyclic
  real-money order round-trip is unacceptable, so the probe degrades to
  connectivity only, fail-closed.
- Proof: `tests/test_resilience.py` (16 cases: 11 CB unit cases, decorator +
  thread-safety, the shared breaker registry, and end-to-end probe API cases
  incl. an open-circuit fail-fast test that asserts the wrapped production
  broker refuses a place order and leaves zero orders behind).

## Gates (delta on this change)
- Full suite: **1442 passed / 79 skipped / 89.84% coverage** (was 1431/73/
  89.96%). New: 11 cases (the 16 resilience cases less 5 counter-shared
  existing probe assertions; global coverage edged down because the
  breaker/registry modules add untraversed config branches).
- Lint (`ruff check`) clean on the whole `src`/`tests`/`scripts` tree;
  `black` and `isort` clean on all touched files; `pyright` 0 errors on the
  touched files and the full project.
- The `architecture/test_dependency_direction.py` ADR gate is respected:
  domain never imports infrastructure (the circuit-breaker draft that
  violated it was moved to the correct boundary).

## Not in scope / still open (honest)
- **Account-gated final phase (C1 real Alpaca paper soak, C2 live latency
  calibration, C3 bounded live pilot) stays blocked on real broker
  credentials** — never fabricated, never paper-over. The on-call/HA surface is
  proven only via local loopback; a managed on-call platform (PagerDuty-class)
  is not exercised here and remains open.
- Retail order entry is paper-only by design; live-mode retail orders refuse
  (403) rather than fabricate. A production retail surface on a real broker
  remains future work behind C1-C3.
- Full-suite runs may flash 2 environment-ordered flakes — a real-Postgres
  table name collision in `test_migration_v004` and a subprocess
  drill SIGTERM under full-suite load (`test_ha_failover`). Both pass
  deterministically in isolation and are unrelated to this change.
- Real Alpaca/Binance credentialed tests remain NO-GO without credentials.
- `VAULT_CB` / `PG_CB` are preconfigured but not yet wired at their
  submission boundaries, and the probe summarizes only the broker leg by
  design (`ProbesSummary.broker`); wiring the remaining breakers + a periodic
  probe scheduler (30 s) is tracked for the next shift.
