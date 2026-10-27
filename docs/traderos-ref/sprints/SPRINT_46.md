# Sprint 46 — Verification-and-close: backup/restore vs current Postgres, rate-limiter load-shedding, SIGTERM flake, README

**Period:** 2026-08-22
**Objective:** Verify-and-close the genuine gaps below. Do NOT touch G-01/G-02
(operator-gated, already running) and do NOT start any new capability.

1. Re-verify backup/restore against the CURRENT Postgres instance (the last
   drill predates the Amsterdam migration).
2. Write an adversarial rate-limiter burst / load-shedding drill matching the
   rigor of the reconciliation/kill-switch drills.
3. Resolve the HA SIGTERM flake's open status definitively.
4. Refresh the README to current reality (sourced from GAP_READINESS + sprints).

---

## T1 — Backup/restore vs current Postgres (DONE, VERDICT PASS)

- Wrote `scripts/evidence/run_postgres_backup_restore_drill.py` — timed
  `pg_dump -Fc` snapshot of the LIVE production DB (via Railway SSH tunnel to
  `postgres-gkbz.railway.internal`), restored into a throwaway scratch DB on
  the same server, per-table row counts compared against the backup-time
  fingerprint, scratch DB dropped. No production data ever written.
- Result: schema v9, 35 tables, live counts (metrics_history 617+ rows, audit
  log, run_manifest) round-tripped exactly; backup 77 KB / ~32s, restore ~78s.
- **Two real findings surfaced (not during an incident):**
  1. **Orphaned volume confirmed real.** `railway volume list` shows
     `postgres-volume-tZfp` (attached, 120 MB, active) AND `postgres-volume`
     (detached, 84 MB) — the Sprint 43 "volume detached" warning is NOT purely
     cosmetic; a leftover volume sits unused. Data survives on the attached
     volume (drill proves it); operator should delete the orphan.
  2. **Production image had NO `postgresql-client`** — `traderos db backup`
     was impossible in production. Worse, Debian trixie ships client 17 which
     refuses PG 18.6 (`aborting because of server version mismatch`). The
     Dockerfile now installs `postgresql-client-18` from PGDG (deb822
     `.sources` format) to match the managed server major version.
- Evidence: `docs/evidence/2026-08-22_postgres_backup_restore_drill.log`.

## T2 — Rate-limiter burst / load-shedding drill (DONE, 13/13 PASS)

- Wrote `scripts/evidence/run_rate_limiter_burst_drill.py` — three phases:
  - **Phase 1 (broker path):** burst of 20 `place_market_order` calls through
    the REAL composed stack (`CircuitBreakeredBroker(GuardrailedBroker(
    RateLimitedBroker(inner)))`, same order as factory.py:398-408) with a
    budget of 3. Asserts: exactly budget admitted, rest rejected with a clear
    `RateLimitExceededError`, inner broker untouched beyond budget, breaker
    NOT tripped, other methods still admitted, traffic resumes after the
    window.
  - **Phase 2 (HTTP path):** burst through the real FastAPI app. Asserts HTTP
    429s, `Retry-After` + `X-RateLimit-Limit` + `X-RateLimit-Remaining`
    headers, app stays healthy (healthz 200 while over budget), traffic
    resumes after the window.
  - **Phase 3 (regression pins):** breaker ignores load-shedding rejections
    but still trips on genuine broker failures.
- **Two real defects found and fixed on the live path:**
  1. `RateLimitExceededError` was NOT in `_CYCLE_EXCEPTIONS` (cycle_executor,
     daemon_controller, async_daemon) — a burst crashed the cycle/daemon. Now
     contained: rejections are explicit (reason + event + health), never a
     process death.
  2. Every rate-limit rejection counted as a broker failure → after 5 the
     breaker opened for 30s, blocking legitimate traffic. Added
     `non_failure_exception` to `CircuitBreakerConfig` and wired
     `RateLimitExceededError` into `BROKER_CB` — load-shedding never opens the
     circuit; genuine failures still do.
  3. HTTP 429 lacked standard headers. Added `Retry-After`,
     `X-RateLimit-Limit`, `X-RateLimit-Remaining` to the rate-limit response
     (RFC 6585/9110).
- Tests: `test_resilience.py` (config + integration through `BROKER_CB` +
  `RateLimitedBroker`), `test_server_edges.py` (headers). Registered the drill
  in the CI credential-free set (`run_ci_drills.py` DRILLS).
- Evidence: `docs/evidence/2026-08-22_rate_limiter_burst_drill.log`.

## T3 — HA SIGTERM flake: root-caused and CLOSED (DONE)

- **Sprint 29 status:** `test_ha_failover` SIGTERM-under-load case "not
  reproduced in 7 runs, no marker added."
- **Investigation:** 24 consecutive green runs under 4× CPU load before any
  change (10× targeted SIGTERM tests, 8× full ha/failover+fatal suite, 6× full
  daemon_controller file) — consistent with Sprint 29's "not reproduced".
- **Root cause found (real defect, timing-hidden):** `DaemonController.
  run_forever` installed SIGTERM/SIGINT handlers at the TOP of
  `_run_forever_loop`, but ran crash-recovery → local-state fetch → startup
  broker reconciliation → `start()` → fatal-handler install BEFORE that. A
  SIGTERM arriving in that window hit the DEFAULT handler and terminated the
  process. Mocked tests never hit it because their startup path is near-
  instant; under real load (broker + DB round-trips) the window widens.
- **Fix:** handlers now install at the FIRST statement of `run_forever`; if a
  stop signal arrives during startup, startup work is skipped entirely and the
  loop exits immediately. Regression test
  `test_stop_signal_during_startup_reconciliation_is_handled` proves (a)
  handler install precedes recover/fetch, and (b) a real SIGTERM during startup
  survives + drains (process not killed).
- **Post-fix verification:** 10 consecutive full-file runs under 4× CPU load,
  44/44 each, 0 failures.
- **Answer to the open question:** the flake was genuinely unreproducible in
  the mocked suite, but the underlying defect was REAL (late handler install =
  default-kill window during slow startup). Now closed by ordering the install
  first, with a deterministic regression test.
- Evidence: `docs/evidence/2026-08-22_sigterm_startup_drain.log`.

## T4 — README refresh (DONE)

- Status table updated 2026-08-17/v1.2.0 → 2026-08-22/Sprints 41–45: test
  count (2293/7/100%), EU region migration, live Binance feed activation,
  WS-resync reconciliation, running G-02 cloud soak (batches 001–004 PASS),
  gated auto-deploy, durable stores, live backup/restore drill, rate-limiter
  drill.
- Honest headline corrected: now ingesting real Binance data; still NO-GO for
  real capital (never placed a real order; G-02/G-01 remain).
- "Known gaps" section rewritten: Sprint 41's four software gaps are closed
  (honest backtest, durable research store, pagination, real-feed switch);
  operator-run list now leads with the RUNNING soak; orphaned-volume item added.
- Data + risk-rails sections reflect live feed and explicit load-shedding.

## Verification

| Check | Result |
|---|---|
| Postgres backup→restore drill (live) | **VERDICT PASS** (schema v9, 35 tables round-trip) |
| Rate-limiter burst drill | **VERDICT PASS** (13/13 checks) |
| SIGTERM startup drain (regression test) | PASS (deterministic ordering + real-signal survival) |
| daemon_controller suite ×10 under 4× CPU load | 44/44 each, 0 failures |
| `test_resilience.py` / `test_broker_rate_limiter.py` / `test_server_edges.py` | all green |
| ruff / black / isort / pyright | clean |

## Honest residuals

- The orphaned `postgres-volume` is **surfaced, not deleted** — removing a
  volume is an operator action; the drill records it so it is handled before
  an incident.
- The Dockerfile's PGDG install (`postgresql-client-18`) is validated by the
  CI `deploy-check` job (this sandbox cannot reach apt.postgresql.org); the
  build must pass there before the image is trusted.
- G-02's 72h soak window and G-01's real-edge proof remain open on their own
  timeline — untouched by this sprint by directive.
