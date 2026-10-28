# Sprint 35 — Test coverage to 100% (0 missing statements) + real graceful shutdown

**Period:** 2026-08-11
**Objective:** Finish the coverage grind to a measured **100%** (0 missing of
12,139 statements) with the `pyproject.toml` gate raised to 100, and — while
closing the last defensive branches — fix a real production defect found in the
daemon's forced-shutdown path that claimed a safety net it could not deliver.

## Work Completed

### Layer 4 bucket 3 — server / cli / config / logging / SSE (all 100%)
- `interfaces/api/sse_tokens.py` (76) — wrong-parts/scope 3-part token, empty
  nonce, non-integer expiry (`peek` + `validate`) in `tests/test_sse_token.py`.
- `infrastructure/config/config_loader.py` (108) — secret-in-yaml ignored via a
  real temp YAML file, string-bool coercion (`"true"`/`"1"`), `default_cash`
  int cast, `database_url` skip-validation, missing `db_path` directory
  creation, non-list `forex_symbols`, empty `db_path`, invalid `log_level`.
- `infrastructure/logging/__init__.py` (59) — `setup_json_logging` file
  (RotatingFileHandler) and stream paths, `JsonFormatter` exception + `extra`,
  `StructuredLogger` file-handler warning/critical (note: record `extra` data
  is injected via `extra={"extra": {...}}`).
- `interfaces/api/server.py` (280) — single-mode `reset_orchestrator`, CORS
  wildcard, rate-limit 429, metrics 501 with prometheus absent, login 501 with
  no account service, paper-session no-symbols/ids branch, session resolver 401,
  health 503 timeout — new `tests/test_server_edges.py`; 100% requires the
  broad API set (single-file runs misreport because endpoints share fixtures).
- `interfaces/cli/main.py` (538) — removed 3 unreachable `return` statements
  after `sys.exit` (dead code, −3 stmts) and covered the module `__main__`
  guard with `runpy.run_path(run_name="__main__")`.

### Domain / infrastructure offenders (all 100%)
- `application/order_event_engine.py` (93) + `domain/entities/trade.py` (79):
  CANCELLED/REJECTED/EXPIRED lifecycle + sidecars, unsupported transition
  ValueError, replay without journal no-op (EXPIRED requires ACKNOWLEDGED
  first). `trade.py` 134-136 closed via `expire()`.
- `application/account_service.py` (113): foreign password scheme → denied,
  empty username/password, DISABLED user fails closed (session + API key),
  empty token/session expiry/revoke no-op.
- `domain/services/research_engine.py` (52): backtest-id create, unknown-lesson
  empty result, lastrowid-None raise for all 5 create methods — new
  `tests/test_research_engine_edges.py`. (Pitfall: the engine uses
  `self.db.conn.cursor()`, so the mock must be `conn.conn.cursor.return_value`.)
- `domain/services/risk_config.py` (116): non-numeric/non-integer/non-list
  rail values rejected, `"false"` allowlist string returns False.

### Batch — remaining defensive branches (all 100%)
- `__main__.py` guard, `archiver.py` PG rollback-failure swallow, `events.py`
  handler-exception log-and-continue, `liquidity_zone_service.py` duplicate
  price skip, `auth.py` `role_grants` hierarchy + `configured_roles`,
  `observability.py` broken-chain-link with a *valid* hash + `timing` context
  manager, `observability_postgres.py` broken-link (valid-row) + timing
  `stop()` without start (verified against a live Postgres this run).
- Eleven single-line stragglers closed: `analysis_service` (high==low),
  `breakout_detection` (`_std` n<2), `correlation_service` (2-overlap return),
  `market_hours_engine` (24h session), `portfolio_service` (close audit/pnl +
  negligible-rebalance skip), `replay_service` (`_parse_detail` empty/non-json),
  `session_report` (`to_json`), `alpaca_broker` (`get_open_orders` missing-lib),
  `audit` (broken-link with internally-valid row), `yfinance_collector` stub,
  `attribution` (`_fill_dict(None)`).

### Real defect fixed — daemon forced shutdown was dead code
`application/daemon_controller.py` claimed a "Forced shutdown after timeout"
safety net that could never fire: `handle_stop` called `stop()` (setting
`_running = False`) before the loop could re-evaluate its deadline check, so
`while self._running` exited first. The branch was unreachable. Fixed to a real
graceful drain — the stop signal now stops scheduling new cycles while the
in-flight iteration finishes, and the deadline check force-breaks when a cycle
exceeds `shutdown_timeout`. Two new tests cover drain-then-exit and
force-after-timeout. (Residual, documented: a cycle blocked inside a C-level
call cannot be preempted by pure-Python loop code; that is a watchdog-thread
design decision, not silently papered over.)

## Belt-and-suspenders checks
- Full suite on the final state: **2139 passed / 7 skipped**, coverage
  **100.00% (0 missing of 12,139 statements)** — every module at 100%,
  including the Postgres-backed and live-broker modules exercised against a
  reachable Postgres this run.
- Gate raised in `pyproject.toml`: `fail_under = 100` (was 97).

## Not done (honest)
- The 100% is measured over the suite as-run (Postgres reachable; Alpaca
  paper/Binance testnet in-process drills excluded from deterministic CI).
  It does not claim 100% of every possible runtime state — `# pragma: no cover`
  lines (e.g. `_CYCLE_EXCEPTIONS` catch) and any future code path remain the
  suite's honest boundary.
- `yfinance_collector.fetch_historical` remains a `return []` stub — it fails
  toward "no data" (safe direction), but it is not real yfinance integration.
  Recorded, not claimed.
- Account qualification (see below): **NO-GO for real capital** stands.

## Account qualification (Layer 6) — go / no-go
| Venue | Status | Keys | Verdict for real capital |
|---|---|---|---|
| Alpaca | **Paper only** (`https://paper-api.alpaca.markets/v2`) | Provisioned, held in-process for drills only (never committed) | NO-GO for live; qualified for the G-02 paper soak |
| Binance | **Testnet only** | Provisioned, in-process only (never committed) | NO-GO for live; qualified for testnet drills |
| MetaTrader5 | Not connected yet (operator: "We'll connect to MT5 later") | — | NOT qualified; deferred |

Recommendation: since these paper/testnet keys were shared in plaintext chat,
rotate them before the live pilot. No funded live account exists, so the GO/NO-GO
definition in `GAP_READINESS.md` remains **NO-GO by default** — which is the
correct, honest state.
