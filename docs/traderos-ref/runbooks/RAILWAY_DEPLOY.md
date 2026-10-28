# Railway Deploy & On-Call — Runbook (G-04)

Goal: ship the TraderOS API to Railway on a **live public HTTPS URL** with the
production security posture armed, and keep operators able to recover it.

> This runbook makes the G-04 "we can actually ship this" promise concrete.
> It is an operator checklist, not a substitute for the platform walkthrough.
> The exact account/project token steps are in Railway's own docs; this is the
> TraderOS-specific wiring so a fresh operator is not guessing env names.

## 0. What the deploy targets

* `Dockerfile` builds the `traderos-api` image (uvicorn on `0.0.0.0:PORT`).
* `railway.toml` is the single source of deploy truth: builder + volumes.
  `railway.json` / `nixpacks.toml` were drift and are deleted — do not recreate.
* Boot sequence in `src/traderos/interfaces/api/main.py`:
  1. `assert_production_policy(...)` — refuses to boot unless the production
     posture is met (auth keys + TLS via real certs **or** the trusted-edge
     flag).
  2. `run_migrations_on_boot()` — applies schema migrations, fails closed if
     the store is not migratable.
  3. UVicorn serves on `$PORT` (Railway sets `PORT` automatically).
* Health: Railway polls `/v1/healthz` (`railway.toml -> deploy.healthcheckPath`).
  The container HEALTHCHECK hits the same route. Both are public, so the probe
  works even with auth armed.

## 1. Prerequisites

* `railway` CLI installed and authenticated (`railway login`).
* `docker` available locally to smoke-test the exact image that ships.
* A Railway project, or permission to create one.

## 2. Production environment (Railway Variables)

Railway terminates TLS at its edge. The app is behind a trusted proxy, so it
must serve plaintext HTTP internally and declare that its TLS comes from the
platform edge. Without this the security policy refuses to boot.

| Variable | Required | Value / example |
| --- | --- | --- |
| `TRADEROS_ENV` | yes | `production` |
| `TLS_TERMINATED_BY_PROXY` | yes | `true` (Railway serves the public HTTPS URL) |
| `TRADEROS_ADMIN_API_KEY` | yes | generate a long random secret (password generator) |
| `TRADEROS_OPERATOR_API_KEY` | yes | separate long random secret |
| `TRADEROS_VIEWER_API_KEY` | no | separate viewer role secret |
| `PORT` | Railway manages | do not set manually |
| `TRADING_MODE` | yes | `paper` for the pilot; `live` only after the pilot gates |
| `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` | live only | real keys live here, never in `settings.yaml` |
| `DB_PATH` | no | default `data/trader.db` lands on the `/app/data` volume |
| `WEBHOOK_URL` / `SLACK_WEBHOOK_URL` / `ONCALL_WEBHOOK_URL` | no | notification / on-call fan-out |
| `PAGERDUTY_ROUTING_KEY` | no | PagerDuty integration |
| `VAULT_ADDR` + `VAULT_TOKEN` | live only | preferred provider for live keys (falls back to env, audited) |
| `PROBE_SCHEDULER_INTERVAL` | no | default `30`; page cadence for the readiness probes |
| `RISK_*` | live only | arm the real risk rails — see `configs/settings.production.example.yaml` |

Secrets go in Railway Variables / the platform secret store — never in
`settings.yaml`, never committed. The app refuses sealed-mode configuration
gaps loudly at boot (fail closed).

## 3. Deploy

```bash
railway login            # browser auth with the owning account
railway link             # pick the TraderOS project/environment
railway variables set TRADEROS_ENV=production \
    TLS_TERMINATED_BY_PROXY=true \
    TRADEROS_ADMIN_API_KEY='<long-secret>' \
    TRADEROS_OPERATOR_API_KEY='<long-secret>' \
    TRADING_MODE=paper
railway up               # builds the Dockerfile and starts the service
```

Railway then exposes the service at a public `https://<slug>.up.railway.app`
URL and begins polling `/v1/healthz`.

## 4. Verify the deployment

```bash
BASE=<public-url>   # e.g. https://traderos-production.up.railway.app

# 1. Liveness (public) — must return {"status":"alive"}
curl -fsS "$BASE/v1/healthz"

# 2. Health (public probe)
curl -fsS "$BASE/v1/health"

# 3. Auth boundary is armed: unauthenticated request to a protected route -> 401
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/v1/workflow"   # expect 401

# 4. Authenticated operator request -> 200 (not 401/500)
curl -fsS -H "X-API-Key: $TRADEROS_OPERATOR_API_KEY" "$BASE/v1/workflow"

# 5. Metrics endpoint (public, read-only)
curl -fsS "$BASE/metrics" | head -20
```

If step 3 returns `200` with keys armed, the fail-closed boundary is broken in
this deployment — stop and fix before proceeding (never ship an open boundary).

## 5. What your smoke test does NOT cover (honesty)

* Migration state on a **fresh persistent volume**: the health endpoint checks
  store reachability, but a production DB, its backup strategy and its restore
  drill are exercised in the DB runbook, not by this deploy smoke test.
* LIVE execution: this runbook deploys `TRADING_MODE=paper`. Going live is gated
  by the pilot checklist (`docs/runbooks/PILOT_READINESS.md`), not this doc.
* Vault unseal / rotation: see below.

## 6. On-call basics

* Watch `Deployments` in the Railway dashboard; failed health checks stop the
  service and trigger Railway's restart policy.
* Read metric trends via `/metrics`; probe/page behavior is wired when an
  on-call transport (`SLACK_WEBHOOK_URL`, `ONCALL_WEBHOOK_URL`,
  `PAGERDUTY_ROUTING_KEY`) is set.
* Recovery of a crashed instance is a redeploy of the same image; data lives on
  the persistent volume so history survives the recycle.

## 7. Rotating secrets

Rotation is done in the platform, not in a commit:

1. Generate a new value and set it in Railway Variables (instant, no redeploy
   required for runtime reads).
2. Revoke the old value at the source (Alpaca dashboard / secret store).
3. Verify with the authenticated request from step 4.

Immediate rotation is required whenever a key is suspected exposed. Live keys
should be read via Vault when configured (VAULT_ADDR/token) — never committed
to the repo.

## 7b. The soak service: `railway redeploy` will NOT pick up new code

`traderos-soak` has **no GitHub source connection**. Every deployment of it is
reported with `reason=redeploy`, i.e. Railway re-runs the **last built image**.
So this sequence silently deploys the old code:

```
git push origin main            # code is on GitHub
railway redeploy -s traderos-soak        # <-- re-runs the OLD image
railway redeploy -s traderos-soak --from-source   # <-- ALSO re-runs the old image
```

This was found the hard way during Sprint 50: two "redeploys" of the fixed soak
both ran the pre-fix harness and leaked a further 389 AAPL into the paper account
before it was noticed. The production `TraderOS` service *is* connected
(`reason=deploy` on push) — the difference is not obvious from the CLI.

**Deploy the soak from the working tree instead:**

```
railway up -s traderos-soak --detach --yes     # builds from the current checkout
```

**Always verify the running code, not the deploy's success.** The batch output
format is the tell — the fixed harness prints `still_resting=`,
`positions_back_at_baseline=` and a baseline reconcile line, and the pre-fix
harness printed `cancel_failures=` and `local_positions=0`:

```
railway logs -s traderos-soak -n 40
```

Then confirm the account directly rather than trusting the harness verdict
(it has lied before — see `docs/sprints/SPRINT_50.md`):

```
railway logs -s traderos-soak -n 40 | grep -E 'VERDICT|positions_back_at_baseline'
```

If a batch reports PASS, still read the Alpaca paper account's positions a
minute later. A green batch whose fills are still landing is the exact failure
mode Sprint 50 fixed, and only the broker can tell you about it.

## 8. Rollback

Railway keeps deployment history in the dashboard: select the previous healthy
deployment and redeploy it. Because data is on the persistent volume and the
image is immutable, a rollback is fast and loss-free for the DB.

## 9. Related

* `configs/settings.production.example.yaml` — the G-03 risk rails armed by any
  config-loaded process (daemon / governance gate).
* `docs/runbooks/OPERATIONS.md` — backups, restore, incident lifecycle.
* `docs/runbooks/PILOT_READINESS.md` — the gate for moving from paper to live.
