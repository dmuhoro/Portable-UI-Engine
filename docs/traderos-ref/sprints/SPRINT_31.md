# Sprint 31 — Operator auth (WP8), dashboard market/research panes (WP9), on-call providers (WP10)

This sprint closes three operator-facing gaps without touching the
account-gated WP5–WP7 path (still operator-run per `LIVE_RUN_POLICY.md`): the
operator dashboard moved off static roaming API keys onto a PG/HMAC-backed
username+password session (WP8), gained Market Overview + Research Lab panes
served from the real runtime services (WP9), and the on-call router gained
provider-native PagerDuty + Slack transports wired into the live boot path,
env-gated and fail-closed (WP10).

## Ground truth (verified, not assumed)

- The operator surface previously authenticated with a static `X-API-Key` that
  the dashboard persisted in `localStorage` — a roamable, XSS-readable
  credential. WP8 replaces the browser-held key with a short-lived server-side
  session token minted by `/v1/auth/login` (username+password, PBKDF2
  verification via `AccountService`) and held only in the closing page
  session; `/v1/auth/logout` revokes it, and the audit trail records
  `login`/`login_denied`. Confirmed by grep: no `localStorage` API-key
  persistence remains in the dashboard.
- The new session seam (`X-Session-Token` -> role via `security.set_session_resolver`) is RBAC-identical to the key seam: a viewer session
  reads the dashboard but cannot operate the workflow or trip the kill switch
  (`test_operator_login.py` proves it). An invalid session is an explicit 401,
  never a silent fall-through.
- WP9 endpoints read the **real** orchestrator services (DataIngestionService,
  AnalysisService, strategy registry, ResearchService) — the same objects the
  rest of the API uses — and tests assert the returned indicator values equal
  `AnalysisService` output to tolerance.
- WP10 transports implement the existing `OnCallTransport` protocol the
  severity router already fans out to; delivery is only success on a provider
  ack (PagerDuty `success`/`triggered`, Slack `"ok": true`) verified against a
  real loopback HTTP server. Both are env-gated (no key configured = not wired
  = `oncall is None`) and construct-time fail-closed when a key is absent.

## Work Completed

### WP8 — PG/HMAC-backed operator login (replaces static dashboard API key)
- `infrastructure/repositories/postgres/users.py`: `PostgresUserRepository`
  (users/user_sessions/user_api_keys) mirroring the SQLite repo; exported from
  the postgres package with the parity tests in `test_postgres_repositories.py`.
- `factory.py`: `account_service` now wired for Postgres too, and
  `bootstrap_admin_from_env()` runs at factory time so a PG-backed operator can
  log in.
- `infrastructure/auth.py`: public `role_grants(role, permission)` (RBAC bucket
  hierarchy), used by the session seam.
- `interfaces/api/security.py`: `X-Session-Token` accepted as an alternative
  credential alongside `X-API-Key`; boundary, `current_role`,
  `_permission_dependency`, `require_sse` and `/v1/auth/me` all session-aware;
  `/v1/auth/login` added to the public prefixes; `reset_authenticator()`
  clears the session resolver so test isolation stays deterministic.
- `interfaces/api/server.py`: `POST /v1/auth/login` + `POST /v1/auth/logout`,
  and `build_app` installs the session->role resolver.
- Dashboard `app.js`/`index.html`: username+password sign-in, session token in
  `sessionStorage`, `logout()` clears + revokes. Verified `node --check` clean
  and no `localStorage` API-key persistence.
- Tests: `test_operator_login.py` (12 — login success/wrong-password/unknown/
  malformed, guarded reads, unknown session 401, logout revokes, `/v1/auth/me`
  role, viewer 403 on operate and kill switch).

### WP9 — Market Overview + Research Lab
- `interfaces/api/market.py` (registered in `build_app`): `GET /v1/market/
  overview` (per-symbol last/change/volume/SMA20/SMA50/RSI/ATR/trend state),
  `GET /v1/market/candles`, `GET /v1/market/symbols`, `GET /v1/research/
  indicators` (SMA/EMA/RSI/ATR/Bollinger/Stochastic series), `POST /v1/
  research/backtest` (registered strategy against the symbol's real candles),
  `GET`/`POST /v1/research/observations` (the C2 journal, via `ResearchService`).
  All gate on the shared `require_read`/`require_operate` dependencies; unknown
  symbols 404; missing service 503.
- Dashboard: "Market Overview" and "Research Lab" panels (backtest chart of
  metrics, observation journal with log form).
- Tests: `test_market_research.py` (10 — boundary/session denial, symbol list,
  indicator/candle consistency vs `AnalysisService`, unknown-symbol fail-closed,
  backtest through the registry, viewer cannot write the journal but may run
  read-only research), plus `test_dashboard.py` assertions for the new panels
  and endpoints.

### WP10 — real on-call providers (PagerDuty + Slack)
- `infrastructure/notifiers/oncall_router.py`: `PagerDutyTransport` (Events API
  v2 envelope, `dedup_key` from metadata, severity map, env-gated on
  `PAGERDUTY_ROUTING_KEY`) and `SlackTransport` (webhook payload with channel
  override, env-gated on `SLACK_WEBHOOK_URL`). Both require 2xx + provider ack,
  retry with backoff, and raise `OnCallDeliveryError` on failure — no silent
  drop.
- `factory.py`: the on-call fan-out now builds **all** configured providers
  (PagerDuty/Slack/generic webhook); with none configured `oncall` stays `None`
  (no external alert is claimed).
- Tests: `test_oncall_providers.py` (11 — no-credential fail-closed, events/v2
  and Slack payload shapes on the real wire, non-2xx and ack-rejection raise,
  factory fan-out/no-provider wiring).

## Belt-and-suspenders checks
- Subset runs green after each work package (auth+dashboard 75, +core infra
  111, market/research+dashboard 17, oncall 18, trigger-alerting 7; combined
  final-state subset 54).
- `node --check` clean on the dashboard bundle; `test_dashboard.py` asserts
  "Finish Line Dashboard", login/me/advance/kill-switch/report endpoints and
  `EventSource` are unchanged.
- Full suite run three times on the **final committed state** (after the
  ruff/black/isort/pyright fixes), each green: **1528 passed / 82 skipped**
  (3/3 runs identical; an earlier 3x on the pre-format state matched).
- Static checks clean on all changed files: `ruff check`, `black --check`,
  `isort --check` pass; `pyright src tests` reports 0 errors.

## Not done (honest)
- WP5's continuous 24–72h unattended paper-soak window remains an operator-run
  gate (bounded real-paper runs PASS; the full window and the aggregate
  evidence are the operator's deliverable via `run_unattended_paper_soak.py`).
- WP7 live re-arm stays authority-gated: the named Operator (human) and the
  signed GO checklist in `WP5_WP7_PAPER_TO_LIVE.md` — nothing in this sprint
  moves the NO-GO default.
- WP10 deliveries are proven on the real wire against loopback receivers; a
  **live PagerDuty/Slack account with credentials** must still receive one real
  incident (operator step; keys are env-only and never committed).
