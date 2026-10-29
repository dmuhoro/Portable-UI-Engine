# Sprint 39 — Railway shipping path: deploy config consolidation, proxy-TLS posture, deploy runbook

**Period:** 2026-08-17
**Objective:** Close the last distance to a real-world deployment. Make the
exact artifact that will ship to Railway healthy under the production security
posture, remove config drift that would have split deploy behavior between
build systems, and give an operator a written deploy/verify/on-call/rollback
runbook they can follow without guessing env names. Ship-gate evidence is
re-run at 10x scale and the production boot path is proven in the built image.

---

## 1. Deploy config consolidation (railway.json / nixpacks.toml removed)

There were three deploy descriptors with **different** behavior:

- `railway.toml` (canonical): Dockerfile builder, `/app/data` + `/app/exports`
  volumes, health check on `/v1/healthz`.
- `railway.json`: same builder but health check on `/v1/health` and a
  duplicate restart policy — a second source of truth that could drift.
- `nixpacks.toml`: a **Nixpacks** build path that bypasses the Dockerfile
  entirely (`pip install -e ...` in Nixpacks instead of the hardened image).

- `railway.json` and `nixpacks.toml` are deleted (git-removed). `railway.toml`
  is the single source of deploy truth.
- `Dockerfile` hardened:
  - `ENV PYTHONUNBUFFERED=1` — a crashed/failed container writes its traceback
    to the platform log stream instead of buffering it away until process exit
    (on-call needs the real error).
  - HEALTHCHECK now probes the real HTTP liveness route
    `curl -fsS http://127.0.0.1:8000/v1/healthz`, matching what Railway polls —
    the container health state and the platform health check read the same wire.

## 2. Proxy-TLS production posture (`TLS_TERMINATED_BY_PROXY`)

Railway (and Fly, and any PaaS behind an HTTPS edge) **terminates TLS at the
platform** and forwards plaintext HTTP to the app container. The production
security policy previously required app-level SSL certs — so a `TRADEROS_ENV=production`
boot on such a platform could never pass (the container has no certs to
configure).

- `infrastructure/security_policy.py`:
  - New `_tls_terminated_by_proxy(...)` — explicit opt-in via
    `TLS_TERMINATED_BY_PROXY=true` (also accepts `1`/`yes`).
  - `check_security_posture(..., tls_terminated_by_proxy=None)` accepts the
    flag; TLS is satisfied by **either** self-terminated certs **or** the
    trusted-edge flag. Production never assumes the edge — it must be declared.
  - The TLS finding detail now distinguishes the mechanism
    (`"TLS configured"` vs `"TLS terminated at trusted platform edge"` vs
    `"TLS not configured (plaintext HTTP)"`) so a report is honest about *how*
    TLS is held.
  - `assert_production_policy()` passes the flag through; the API entrypoint
    therefore picks it up from the env automatically.
- `tests/test_security_policy.py` +3: proxy-flagged TLS passes in production;
  the flag is honored from the env var; the detail string names the platform
  edge. Security-policy suite: 18/18.

**Verified both directions in the built image** (this is the Railway boot path):

1. `TRADEROS_ENV=production` + `TLS_TERMINATED_BY_PROXY=true` + API keys
   + `TRADING_MODE=paper` → container boots, healthy, `/v1/healthz` alive,
   protected `/v1/workflow` returns 401 unauthenticated / 200 authenticated /
   401 wrong key, `/metrics` served.
2. `TRADEROS_ENV=production` **without** the proxy flag → refuses to boot with
   `SecurityPolicyError: tls: TLS not configured (plaintext HTTP)` (fail-closed
   intact).

## 3. G-03 production config template

- `configs/settings.production.example.yaml` — armed, conservative risk rails
  with `require_allowlist: true` and a non-empty `allowed_markets`, favoring
  the persistent `/app/data` DB path and an explicit `risk:` section for any
  process that loads config (daemon, CLI, governance gate `risk_config`).
  Documents that secrets never belong in YAML (platform variable store only).

## 4. G-04 Railway deploy / on-call runbook

- `docs/runbooks/RAILWAY_DEPLOY.md` — operator checklist: production env
  matrix (including `TRADEROS_ENV=production`, `TLS_TERMINATED_BY_PROXY=true`,
  all three API-key roles, on-call/webhook/vault knobs), deploy steps,
  a `curl` verification block (liveness, auth-boundary 401, authenticated 200,
  metrics), honest "what the smoke test does NOT cover" (DB backup/restore
  drill, LIVE execution, Vault unseal), on-call basics, secret rotation, and
  rollback.

## 5. Ship-gate evidence re-run

- **Paper soak ×10** (`run_paper_soak.py 2500`): 2500 cycles, 500 forced
  ack-drops through the real submission chain (CycleExecutor → JournaledBroker →
  AlpacaBrokerAdapter) → `PASS`. 0 duplicate orders (broker==journal==trades
  == 2500), 0 lost, restart re-submits nothing, reconcile 0 errors /
  0 mismatches, ack-loss recovered idempotently. Evidence:
  `docs/evidence/2026-08-17_sprint39_paper_soak_10x.log`.
- **Walk-forward re-run**: frozen oracle dataset, withheld 35% OOS window,
  full costs incl. latency — honest outcome unchanged: no strategy shows
  positive expectancy after costs on OOS → pilot remains **DATA-VALIDATION
  ONLY**, no PnL claim (LIVE_RUN_POLICY). Evidence recorded with the fresh run
  date.
- **CI drill suite**: 17/17 credential-free drills PASS at the time of this
  sprint (incl. full pytest at 100% coverage, ruff clean, pyright strict
  clean). SPRINT_40 later promoted the real-market walk-forward into the
  deterministic set — final count **18/18**.

## 6. Governance / honesty notes

- The npm-style `version = "0.2.12"` bump referenced in an earlier task note
  was a stale transcription; the repo's real version scheme is the package
  version (`pyproject.toml version = "1.1.0"` at the time, stable since
  Sprint 31) plus sprint-scoped changelog entries. No spurious release version
  was invented then; the plan is to fold the sprint sections into a single
  aligned release cut (`1.2.0`) when shipping, closing the G17/VB6
  version/tag drift (a `v1.1.0` tag never existed for the released changelog
  version).
- Pre-existing working-tree drift in `docs/evidence/` (regenerated drill logs
  and the frozen Binance CSV touched by an earlier local run) was left unstaged
  and is reported in the commit, not silently swept the other way. The
  frozen-dataset re-fetch/overwrite behavior itself is fixed separately (see
  SPRINT_40): the drill now reuses the committed dataset instead of mutating it.

## Verification closure

| Check | Result |
|---|---|
| `pytest -q` (full suite) | 2245 passed, 7 skipped, **100.00%** coverage (gate 100) |
| `ruff check src/ scripts/ tests/` | All checks passed |
| `pyright` (strict) | 0 errors, 0 warnings |
| CI drill suite | 17/17 PASS (18/18 after SPRINT_40 drill promotion) |
| Docker build `traderos-api` | builds clean |
| Container boot (production posture, proxy-TLS) | healthy; auth boundary 401/200/401; metrics ok |
| Container boot fail-closed (no proxy flag, production) | refuses to boot (`SecurityPolicyError`) |
