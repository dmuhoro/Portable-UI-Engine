# TraderOS v1.3.2 — G-02 Soak Position Close-Out Release Notes

**Date:** 2026-10-01 · **Status:** patch on v1.3.1 (software-complete; GO
conditions operator-gated) · **Signed artifact:**
`docs/evidence/releases/RELEASE_1.3.2_manifest.json` (+ `.sig`)

## Why this release exists

v1.3.1 made the G-02 unattended soak *finishable*. Redeploying it to prove that
showed it was still unfinnable, and worse — **actively damaging the paper
account**. The first batch reported:

```
batch 001 FAIL   mismatches=1   orders_filled=0   n=0 latency probes
  broker_only_position  AAPL
```

The account told the story: **712.50489538 AAPL** held, ~$234,000 of exposure,
cash **−122,422.75**, buying power **0**.

The harness bought ten shares every hour and closed out resting **orders** —
never the **fills**. Share count compounded until nothing could be bought at
all, which is also why not one of the five latency probes was accepted. Three
defects, all invisible to a suite whose mocks echoed the broker's own
vocabulary:

1. **Positions were never closed out.** A buy-only soak with no position
   close-out is an account-draining process wearing a soak's clothes.
2. **Reconcile compared broker truth against the run's throwaway in-memory
   book**, so any position the run had not created looked like a phantom
   broker-only mismatch. The assertion is now "broker truth ends where this run
   found it".
3. **Close-out scored the order response instead of the outcome.** An order that
   fills between the snapshot and the cancel cannot be cancelled — and an order
   that *cannot* be cancelled is one that *already filled*. A fractional close
   acks `pending` and settles moments later. Both were recorded as leaked
   residue, failing batches that had in fact left the account exactly as found.

And a fourth, found only because the fix was deployed and re-measured: **the
position book lags fill settlement.** Correcting 1–3 produced a batch that
reported `after_qty=0.000000` and `VERDICT: PASS` while **132.05154639 shares of
its own buying were still in flight**. The next run read
`baseline_qty=132.051546` and — correctly, under strict ownership — declined to
touch it. **Own residue had become an "operator position":** the leak was now
permanent and self-legitimising. Judging the position read instead of the cancel
response only moved the eventual-consistency problem one level down; any mock
that returns positions instantly cannot see it.

## What ships

- **Position close-out.** Every batch captures a pre-run baseline and closes
  its own **net delta** back to it — in the normal path and in the crash
  path's `finally`. A pre-existing holding is never touched, matching the
  existing order-ownership rule.
- **Baseline reconciliation.** The run's book is compared against the baseline
  it inherited, so a run that leaves the account as it arrived reconciles
  clean, while a position the run cannot explain is still surfaced.
- **Outcome-based close-out.** `_cancel_residue` asserts *demonstrably not
  resting*; `_flatten_own_delta` asserts *demonstrably back at baseline*.
  Retries are bounded and only against a broker that **definitively refuses**,
  so a settling close is never mistaken for a leaking one — and a refusing
  broker is never spammed. Every attempt is recorded as a note.
- **The position book must be at REST before it declares anything.**
  `_await_position_quiescence` polls until two consecutive reads agree; both the
  flatten decision and the reported final position go through it. Once
  `_cancel_residue` has shown none of the run's orders is still open, no further
  fill can originate from them, so *all orders terminal* + *book at rest* makes
  the delta final. A book that never settles, or cannot be read, fails closed.
- **A flaky gate made deterministic.** The resync suite anchored a tick pair up
  to ~60s in the *future* against a 60s tolerance, failing ~1 run in 60 for a
  reason unrelated to its assertions. No threshold raised, no assertion
  loosened, nothing skipped.

## Verification

- **2361 tests pass (7 skipped)**; ruff, black, isort, pyright (strict) clean.
- **15 new tests** in `tests/test_soak_position_flat.py`. The end-to-end one
  reproduces the production symptom against the pre-fix harness (`mismatches=1`,
  `VERDICT: FAIL`), and a negative control proves a refused close-out fails
  closed rather than passing quietly.
- **Live paper broker: `VERDICT: PASS`** — 10 cycles, 0 lost intents,
  `still_resting=0`, `positions_back_at_baseline=True`, `mismatches=0`,
  submit→ack median 307.3 ms. Evidence:
  `docs/evidence/2026-10-01_soak_position_flatten_live.log`.
- Account reclaimed: 712.5 AAPL liquidated, buying power 0 → **447,486.44**,
  account flat with no open orders. Evidence:
  `docs/evidence/2026-10-01_soak_account_reset.log`.

## Honest residuals (operator-run, unchanged)

- **The 72h window is still operator-run and still wall-clock.** What this
  release changes is that it is now *safe to leave unattended*: exposure is
  closed out every batch, an empty account is a starting state rather than an
  accident, and every batch is confirmed flat by a check the harness does not
  control. Several real batches are proven end-to-end; three days are not
  compressible, and nothing here observes 72h of accumulated drift.
- The window whose batch 001 failed contains a **failed batch in its aggregate**.
  Start a fresh checkpoint before treating any final verdict as meaningful — an
  honest window, not a laundered one.
- **G-01** (a genuine cost-adjusted edge on out-of-sample data) remains open.
  The pilot is **DATA-VALIDATION ONLY**; no PnL claim.

## Release provenance

Cut as `v1.3.2`, aligned to `pyproject.toml` / `configs/settings.yaml` /
`configs/settings.production.example.yaml`. Signed artifact in
`docs/evidence/releases/`, produced by the reproducible manifest generator
(`scripts/governance/release_manifest.py`) rather than transcribed by hand, and
signed with the deterministic paper key — the operator re-signs with the real
`RELEASE_SIGNING_KEY` for GO, which is the documented step.
