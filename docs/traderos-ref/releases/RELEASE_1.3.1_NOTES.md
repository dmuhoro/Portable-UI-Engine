# TraderOS v1.3.1 — G-02 Soak Viability Release Notes

**Date:** 2026-10-01 · **Status:** patch on the v1.3.0 launch candidate
(software-complete; GO conditions operator-gated) · **Signed artifact:**
`docs/evidence/releases/RELEASE_1.3.1_manifest.json` (+ `.sig`)

## Why this release exists

The v1.3.0 launch candidate shipped while the G-02 unattended paper soak — the
CRITICAL GO gate and the Layer 8 / CAP-14 exit test — was still running. That
window (started 2026-08-22T07:56Z, dedicated `traderos-soak` Railway service)
ended **CRASHED with no verdict**. In the evidence that is indistinguishable
from a run that produced nothing, so the gate could not be closed and the GO
review had nothing to review.

Three defects, all in the "unattended" premise, made the window unfinishable:

1. **A transient 503 crashed a batch.** Sprint 47 hardened the *submission*
   paths, but the *read/cancel* paths still had no retry, so one Alpaca blip
   aborted the batch and triggered a restart.
2. **Every restart reset the 72h clock.** The runner measured its window from
   `time.monotonic()` at process start, so a restart silently began a *fresh*
   72h window. `restartPolicyMaxRetries=3` then exhausted, and the service went
   CRASHED. **This is the defect that made the gate unfinishable.**
3. **A latent LIVE bug: reconcile spoke two vocabularies.** Local
   reconciliation state was keyed by `str(market_id)` while a real broker
   reports `"AAPL"`. Every held position appeared twice (phantom local-only +
   phantom broker-only). In LIVE this fails closed and blocks order acceptance
   for as long as any position is open — exactly when trading matters most.

## What ships

- **Broker read/cancel retry:** 429/5xx retry with backoff, `ServiceError` only
  after exhaustion (fail closed, never a bare `APIError`), permanent 4xx fails
  fast, `cancel_order` retries and returns a clean rejected `FillResult`.
- **Resumable soak window:** checkpointed atomically to the persistent volume;
  a restart continues from accumulated elapsed time instead of resetting.
  Fail-closed guards: completed windows are not re-run, different-geometry
  checkpoints are `superseded` not spliced, corrupt checkpoints start a fresh
  flagged window.
- **Broker-symbol reconciliation:** the correct vocabulary on both sides of the
  LIVE reconcile, so the GO gate stays open while a position is held.
- **No silent drops in the harness:** fsync'd evidence written before stdout,
  unverifiable broker reads fail closed, crash-safe close-out in `finally`.
- **`railway.soak.toml`:** `restartPolicyMaxRetries` 3 → 50.

## Verification

- **2346 tests pass (7 skipped)**; ruff, black, isort, pyright (strict) clean.
- 12 new adapter retry tests, **9 proven to fail without the fix**; 3 new
  orchestrator tests with an in-test negative control; 4 resume-drill tests.
- Measured resume behaviour: pre-fix a restart consumed a second full window
  (**40.2s of a 30s window**, 84 aggregate rows); post-fix **30.4s** (67 rows).
  Evidence: `docs/evidence/2026-10-01_soak_resume_drill.log`.

## Honest residuals (operator-run, unchanged)

- **The 72h window itself.** Redeploy `traderos-soak` and confirm every batch
  green before treating G-02 as closed. This release makes that achievable; it
  does not perform it.
- **G-01** (a genuine cost-adjusted edge on out-of-sample data) remains open.
  The pilot is **DATA-VALIDATION ONLY**; no PnL claim.
- `restartPolicyMaxRetries = 50` is a bound, not a guarantee — exhausting it is
  a real fault to diagnose, not something to paper over with a bigger number.

## Release provenance

Cut as `v1.3.1`, aligned to `pyproject.toml` / `configs/settings.yaml` /
`configs/settings.production.example.yaml`. Signed artifact in
`docs/evidence/releases/`; signed with the deterministic paper key (the operator
re-signs with the real `RELEASE_SIGNING_KEY` for GO — the documented step).
