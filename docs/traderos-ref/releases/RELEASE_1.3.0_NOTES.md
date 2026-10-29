# TraderOS v1.3.0 — Launch Candidate Release Notes

**Date:** 2026-08-23 · **Status:** launch candidate (software complete; GO
conditions operator-gated) · **Signed artifact:**
`docs/evidence/releases/RELEASE_1.3.0_manifest.json` (+ `.sig`)

## What ships in this release

TraderOS v1.3.0 is the launch candidate: every software gap on the road to the
controlled pilot is closed. The remaining GO conditions in
`docs/engineering/GAP_READINESS.md` are **operator-run** (the G-02 soak
window finishing ~2026-08-25T16:48Z, managed Vault/KMS rotation, live
PagerDuty/Slack delivery, orphaned-volume deletion, and the written GO
review).

### Capabilities (verified, not aspirational)

- **Real market data, end-to-end:** EU (Amsterdam) deployment, live Binance
  REST + WebSocket feed, WS-resync reconciliation proven on the wire
  (outage → gapless, kline-matching convergence).
- **G-02 cloud soak running:** dedicated `traderos-soak` Railway service in
  **EU West**, hourly batches through the real Alpaca paper chain;
  transient broker 503/429 now fail closed instead of crashing.
- **Order-path safety:** load-shedding is explicit (429 + headers, breaker
  stays closed, traffic resumes); kill-flatten + cap drills proven; SIGTERM
  startup drain fixed; intent-idempotent journal + restart replay proven.
- **Durability:** durable knowledge graph / research store / backtest history;
  live Postgres backup→restore proven; **automatic backup scheduler** (hourly,
  fail-closed, surfaced in orchestrator status).
- **Firm ops:** lease-based HA failover, Vault KV-v2 secret manager on the
  live boot path, rotation cadence proven, on-call transports proven on the
  real HTTP wire, gated auto-deploy from CI.
- **Pilot charter:** `LIVE_RUN_POLICY.md` §6 — DATA-VALIDATION-ONLY posture,
  fixed symbol set (BTCUSDT/ETHUSDT), hard stops, supervision cadence.

### Verification

- 2312+ tests / 100% line coverage (gate `fail_under = 100`).
- ruff, black, isort, pyright strict-clean; pre-commit 10 hooks.
- 20 credential-free evidence drills green in CI; `deploy-check` + `docker`
  green (image carries `postgresql-client-18`).
- Live evidence logs: `docs/evidence/` (backup/restore, rate-limiter burst,
  transient-broker-error, vault rotation, SIGTERM, WS-resync, soak launch).

## Release provenance

- Version is single-sourced: `pyproject.toml`, `configs/settings.yaml`, and
  `configs/settings.production.example.yaml` are all pinned to `1.3.0`; CI
  `version-check` gate re-verified.
- Signed release manifest in `docs/evidence/releases/` — the committed
  signature uses the deterministic **paper** key (drill only). For GO, the
  operator re-signs with `RELEASE_SIGNING_KEY`:
  `python3 scripts/governance/sign_release.py sign --artifact docs/evidence/releases/RELEASE_1.3.0_manifest.json`
- This release cut is aligned to `pyproject.toml` at its commit.

## What is intentionally NOT in this release

- Real order execution (tested last, per directive — the G-02 paper soak is
  the final proof before real capital).
- A PnL/edge claim (G-01 verdict remains DATA-VALIDATION-ONLY).
- The operator-run GO gates (managed Vault/KMS, live on-call delivery,
  orphaned-volume deletion, written GO review).

See `docs/engineering/GAP_READINESS.md` for the six GO conditions and
`docs/engineering/LIVE_RUN_POLICY.md` for the pilot charter.
