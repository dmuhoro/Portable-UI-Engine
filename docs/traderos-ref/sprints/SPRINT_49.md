# Sprint 49 — Layer 8 closure: make the G-02 soak able to finish

**Period:** 2026-10-01
**Objective:** The G-02 unattended paper soak (the CRITICAL GO gate and the exit
test for Layer 8 / CAP-14) had been CRASHED with no verdict since ~2026-08-25.
Close the software defects that made it unfinishable, then cut the release so
the operator can redeploy and let the window actually run. No new capability —
only correctness, durability, and honest evidence.

---

## What was wrong (measured, not guessed)

The `traderos-soak` Railway service last ran a 72h window beginning
2026-08-22T07:56Z. It never produced a verdict. Three independent defects, all
in the "unattended" premise:

1. **A single transient 503 crashed the batch.** Batch 005 failed on
   `APIError: service temporary unavailable` from the open-orders reconcile.
   Sprint 47 hardened the *submission* paths, but the read/cancel paths still
   had no retry, so one blip aborted the batch and the supervisor restarted.
2. **Every restart reset the 72h clock.** The runner measured its window from
   `time.monotonic()` at process start, so a restart silently began a *fresh*
   72h window and discarded elapsed time. Combined with
   `restartPolicyMaxRetries = 3`, the service burned its retries and went
   CRASHED — indistinguishable, in the evidence, from a run that produced
   nothing. **This is the defect that made the gate unfinishable.**
3. **A latent LIVE bug: reconcile spoke two vocabularies.** Local
   reconciliation state was keyed by `str(market_id)` while a real broker
   reports `"AAPL"`. Every held position appeared twice (phantom local-only +
   phantom broker-only). In LIVE this fails closed and blocks order acceptance
   for as long as *any* position is open. The existing tests passed only
   because their broker mocks echoed the UUID back — the paper broker's own
   vocabulary — so the suite could not see it. The soak never held a position
   long enough to expose it either.

## L1 — Broker read/cancel paths retry transient failures (DONE)

- `AlpacaBrokerAdapter.get_open_orders` / `get_positions` /
  `get_account_balance` now retry 429/5xx with backoff (`should_retry=
  _is_transient_api_error`) and raise `ServiceError` only after retries are
  exhausted — fail closed, never a bare `APIError`. Permanent 4xx fails fast
  without burning backoff.
- `cancel_order` retries the same way and returns a clean rejected
  `FillResult`; a failed cancel during close-out leaks a resting order, so it
  must not crash the close-out either.
- Fixed a pyright narrowing bug (`_GetOrdersRequest`/`_QueryOrderStatus`
  Optional) by binding to locals before entering the retry closure.
- Tests: 12 new in `tests/test_alpaca_broker.py`. **9 proven to fail without
  the fix**; the 5 that pass pre-fix are the permanent-4xx fail-fast and
  no-retry cases, which already held.

## L2 — Harness: durable evidence, no silent empty-read, crash-safe close-out (DONE)

`scripts/evidence/run_real_paper_soak.py`:

- Evidence is written **before** stdout, `fsync`'d, then echoed; a dead log
  drain or SIGKILL can no longer cost the evidence row.
- A failed open-orders read returns `None` instead of `[]`: "could not ask the
  broker" must never masquerade as "the account is clean" (which would *skip*
  close-out of orders actually resting). The no-residue check requires a
  verified snapshot and baseline; unverifiable broker truth fails closed.
- Close-out and crash recording moved into `finally`, so a crash still cancels
  this run's own residue and writes a CRASH record carrying the partial run.
- Ownership stays strict: only orders this run created (plus `latprobe-`
  orphans) are cancelled; a user's pre-baseline orders are never touched.
- Local positions are keyed by the broker symbol (see L3).

## L3 — Reconcile on the broker's symbol, not the internal market id (DONE)

- `TradingOrchestrator` gains `_broker_symbol()` and a `symbol_resolver` field;
  the factory wires it from the same `symbol_map` the adapter submits with.
  With no mapping it falls back to `str(market_id)` — correct for the paper
  broker, fail-closed rather than guessing a real ticker.
- Tests: `tests/test_orchestrator.py` drives the **real**
  `BrokerStateReconciliationService` with **real** broker payloads and asserts
  the GO gate stays open, with an **in-test negative control** proving the
  defect (resolver removed → both phantom mismatches → `can_accept_orders`
  False).

## L4 — Checkpoint the 72h window: restart resumes, never resets (DONE)

`scripts/evidence/run_unattended_paper_soak.py`:

- Window checkpointed to `docs/evidence/<label>_soak_state.json` on the
  persistent volume (survives the container restart), written atomically
  (temp + `os.replace`, `fsync`'d).
- On start it **continues** from accumulated elapsed time; batches, pass/fail
  counts, original `started_at` and restart count carry forward. Sleep between
  batches is checkpointed in slices so waiting time is not lost.
- Fail-closed guards: a completed window is not re-run (would overwrite a real
  verdict); a different-geometry checkpoint is set aside as `.superseded`,
  never spliced; a corrupt checkpoint starts a fresh, flagged window.
- `railway.soak.toml`: `restartPolicyMaxRetries` 3 → 50. With resume, retries
  are productive; the bound still fails closed against a tight crash loop.
- Tests: `tests/test_soak_resume_drill.py` (4 tests).

### Measured proof (the negative result)

30s window, killed after 10s, then restarted, run against both revisions:

| Revision | Wall-clock consumed | Resumed | Aggregate rows |
|---|---:|---|---:|
| pre-fix | **40.2s** (a second full window) | no | 84 |
| post-fix | **30.4s** | yes | 67 |

Full measurement + command in
`docs/evidence/2026-10-01_soak_resume_drill.log`.

## Verification

| Check | Result |
|---|---|
| Full suite (`pytest`) | **2346 passed / 7 skipped** |
| ruff / black / isort / pyright | clean |
| Adapter retry tests | 12 new; 9 fail without the fix |
| Orchestrator symbol tests | 3 new; in-test negative control |
| Resume drill | 4 tests, 126s |
| Version gate | pyproject == settings.yaml == 1.3.1 |

## Honest residuals

- The 72h window itself is **wall-clock and operator-run**: redeploy
  `traderos-soak`, watch the aggregate log, and confirm every batch green
  before treating G-02 as closed. This sprint makes that possible; it does not
  perform it.
- G-01 (a genuine cost-adjusted edge on out-of-sample data) is unchanged and
  remains open. The pilot is **DATA-VALIDATION ONLY**; no PnL claim.
- `restartPolicyMaxRetries = 50` is a bound, not a guarantee. If the soak
  exhausts it, that is a real fault to diagnose, not something to paper over
  with a higher number.
