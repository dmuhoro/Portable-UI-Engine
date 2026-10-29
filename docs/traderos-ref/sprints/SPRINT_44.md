# Sprint 44 — Operator gates closed: cloud soak live, auto-deploy activated

**Period:** 2026-08-22
**Objective:** Close the two operator-bound gates left open by Sprint 43:
wire the Alpaca paper credentials and the Railway deploy token, launch the
G-02 24–72h **cloud** paper-broker soak, and exercise the gated auto-deploy
path end-to-end. Zero changes to the execution / order path.

---

## L1 — Credential wiring (operator inputs landed)

- **Alpaca paper keys** (`ALPACA_API_KEY` / `ALPACA_SECRET_KEY`) were set via
  Railway CLI on both services — values passed directly from the operator,
  never echoed to logs, never committed to the repo (presence verified by
  key-name lookup, not by printing secrets).
- **RAILWAY_TOKEN** was stored as a GitHub Actions secret on
  `dmuhoro/TraderOS` (`gh secret set`). The token is *project-scoped*: it
  authenticates against the TraderOS project only (verified with
  `railway status --project … --environment production`; account-level APIs
  correctly refuse it). This is the least-privilege shape for CI deploys.

## L2 — Dedicated cloud soak service

The soak must survive laptop sleep, sandbox restarts, and my own session
boundaries, so it runs as a dedicated Railway service rather than locally:

- New service `traderos-soak` created via Railway's GraphQL API.
- `railway.soak.toml` (config-as-code, bound via the service's
  `railwayConfigFile` setting so it cannot collide with production's
  `railway.toml`):
  - start command: `run_unattended_paper_soak.py --hours 72 --batch-cycles 10 --interval-minutes 60`
  - restart policy `ON_FAILURE` (3 retries)
  - evidence volume mounted at `/app/docs/evidence` (aggregate log survives
    container restarts; every batch row is also printed to stdout for
    `railway logs` monitoring).
- The runner is self-supervised: each hourly batch runs the verified real-path
  harness (CycleExecutor -> JournaledBroker -> AlpacaBrokerAdapter -> real
  Alpaca paper endpoint), requires clean reconcile + close-out at baseline,
  writes its own dated evidence file, and a crashed/absent batch is recorded
  FAIL — never silently dropped. Final verdict is PASS only if **every**
  batch in the window passed.

## L3 — Soak launch proof (real evidence)

First deployment of the soak service; container logs show:

```
UNATTENDED REAL-PAPER SOAK RUNNER (real Alpaca paper)
started 2026-08-22T07:56:44Z  window=259200s  batch_cycles=10  interval=60.0m
WP6 latency (submit->ack ms): n=10 min=73.5 median=75.0 max=75.6
VERDICT: PASS
[2026-08-22T07:56:44Z] batch=001 PASS
runner closed out, broker at baseline:    True
reconcile clean vs real paper broker:    True
```

- Window = 259200 s = exactly 72 h (ends ~2026-08-25T07:56Z).
- Batch 001 PASS: 10 real market orders through the full production chain;
  submit->ack median 75 ms (EU ams -> Alpaca US paper endpoint); zero leaked
  orders; reconcile clean.
- Monitoring cadence during the window: check `batch=NNN PASS` rows in the
  service logs; any FAIL row or missing hour is investigated immediately.

## L4 — Auto-deploy activation (exercised for real)

- Sprint 43's deploy job previously skipped loudly because the token secret
  did not exist. With `RAILWAY_TOKEN` set, this sprint's pushes exercised the
  real path end-to-end — twice:
  1. First run (`14e1fcd`): all nine quality gates passed, then the deploy
     step failed with `railway: command not found` — the Railway install
     script drops the binary in `$HOME/.railway/bin`, which is not on the
     runner's PATH. **Real-path finding fixed in the workflow**
     (`export PATH="$HOME/.railway/bin:$PATH"`, commit `502b335`).
  2. Second run: **CI success including the deploy job** — production was
     actually deployed from `main` by CI (job duration 2m46s).
- Post-CI-deploy health re-proven on the deployed instance: orchestrator
  restarted (`{"status":"started","mode":"paper"}`), live-feed freshness
  delta (close 77314.01 → 77316.69, volume advancing between reads) —
  `FEED_LIVE_AFTER_CI_DEPLOY`.
- Main service also picked up its Alpaca vars via an automatic redeploy
  triggered by the variable set (deployment SUCCESS 07:55Z); feed health was
  re-proven at that boundary as well.

---

## Verification summary

| Check | Result |
|---|---|
| RAILWAY_TOKEN authenticates project-scoped | PASS |
| `gh secret set RAILWAY_TOKEN` | PASS |
| Soak service deployed with soak config-as-code | PASS |
| ALPACA keys present on traderos-soak + TraderOS | PASS |
| Soak batch 001 PASS (10 cycles, reconcile clean) | PASS |
| Soak window exactly 72 h, self-supervised | PASS |
| Main service redeployed with keys (SUCCESS) | PASS |
| Orchestrator restarted; feed live post-redeploy | PASS |
| CI deploy job: real-path finding found + fixed | PASS (`502b335`) |
| CI success **including deploy** — production deployed from `main` | PASS |
| Post-CI-deploy: orchestrator restarted; feed live re-proven | PASS |

## Honest residuals

- The G-02 gap closes when the **full 72-hour window completes with zero
  failed batches** (~2026-08-25T07:56Z) — running, not finished. Any FAIL row
  reopens it honestly.
- Paper-key rotation into a managed vault remains a later upgrade (keys sit
  in Railway env vars today).
- The account-level admin token used for one-off GraphQL ops (service
  creation) lives only in the local operator config (`~/.railway/config.json`);
  CI uses only the least-privilege project-scoped deploy token.
