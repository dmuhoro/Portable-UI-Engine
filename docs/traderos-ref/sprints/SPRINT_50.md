# Sprint 50 — Layer 8: the soak traded its own positions away

**Period:** 2026-10-01
**Objective:** Sprint 49 made the G-02 unattended window *finishable*. The first
real redeploy proved it was still unfinnable: the harness closed out its
**orders** and never its **positions**. Find that by deploying and reading the
result, not by reading the code, fix it, and prove the fix against the live
paper broker. No new capability — only correctness and honest evidence.

---

## How this was found: deploy, don't assume

v1.3.1 was cut, tagged, pushed and redeployed to `traderos-soak` as a
rehearsal for the operator's 72h run. The very first batch came back:

```
batch 001 FAIL  mismatches=1  orders_filled=0  n=0 latency probes
  broker_only_position  AAPL
```

Two signals, one cause. **Zero latency probes** meant not one of the five probe
orders was accepted; **one broker-only position** said the broker was holding
something the run never recorded. The account explained it:

| | |
|---|---|
| AAPL position | **712.50489538 shares** |
| Market value | ~$234,000 |
| Cash | **−122,422.75** |
| Buying power | **0** |

Every batch bought ten shares of AAPL and closed out the resting *orders*,
never the *fills*. Share count compounded every hour until the account could
afford nothing more. Had this not been caught on the first batch, the operator's
72h window would have spent three days producing a red log — and, worse, the
window would have been declared "unable to start" rather than "actively
damaging the account". This is the Sprint 49 residual materialising, and it is
why the residual was stated as operator-run rather than closed.

## L1 — Positions were never closed out (DONE)

`scripts/evidence/run_real_paper_soak.py`:

- Each batch captures a **baseline position snapshot** before it places
  anything, then closes out its own **net delta** back to that baseline
  (`_flatten_own_delta`), in the normal close-out **and** in the crash path's
  `finally` block.
- Ownership matches the pre-existing `_own_residue` rule: a holding that
  existed before the run is **never** touched. A throwaway soak cannot flatten
  an operator's own AAPL position to prove it cleaned up.
- Closes are market sells (paper-account drain is harmless and the run is
  short-lived), retried while the broker is still working on the close.

## L2 — Reconcile now compares against the baseline it actually inherited (DONE)

Reconciliation compared broker truth against the batch's throwaway in-memory
book. Any position the run did not create therefore looked like a phantom
broker-only mismatch — the exact `BROKER_ONLY_POSITION` above, which reads as
"the broker is holding something unaccounted for" and fails the gate closed.
The assertion is now **"broker truth ends where this run found it"**: the run's
own book is compared against the captured pre-run baseline, and a run that
leaves the account exactly as it arrived reconciles clean.

## L3 — Close-out scored the order response, not the outcome (DONE)

Two real close-out shapes were scored as leaked residue, failing batches that
had in fact left the account exactly as found:

- An order that **fills between the snapshot and the cancel** cannot be
  cancelled — the broker refuses it. That refusal meant its shares were
  *already sold*.
- A **fractional** market close acks `pending` and fills a moment later.

`_cancel_residue` now asserts the property that matters — *demonstrably not
resting*, re-reading until the broker confirms no owned order remains open —
instead of requiring every cancel call to return success. `_flatten_own_delta`
likewise asserts *demonstrably back at baseline*. Retries are bounded by
`_FLATTEN_MAX_ATTEMPTS` and only against a broker that **definitively refuses**,
so a refusing broker is neither spammed nor mistaken for a settling one. Every
close attempt is recorded as a note, not silently dropped.

## L4 — The first fix was still wrong, and only the broker could say so (DONE)

L1–L3 shipped, passed 2361 tests, and printed `VERDICT: PASS` on the live paper
broker. **They were wrong.** A later run read:

```
AAPL baseline_qty=132.051546 after_qty=132.051546
```

The previous batch had reported `after_qty=0.000000` and
`positions_back_at_baseline=True` — while **132.05154639 shares of its own
buying were still in flight**. Worse than a leak: because ownership is strict,
the next run correctly declined to touch those shares as a "pre-existing
holding". **Own residue had been promoted to an operator position**, making the
leak permanent and self-legitimising.

Cause: **Alpaca's position book lags fill settlement.** An order that has
already filled can still read as absent for a second or more. L3 had replaced
"judge the cancel response" with "judge the position read" without noticing that
the read is itself eventually consistent — the same class of error one level
down, and invisible to any mock that returns positions instantly.

`_await_position_quiescence` now polls until **two consecutive reads agree**,
and both the flatten decision and the final reported position go through it.
Once `_cancel_residue` has established that none of the run's orders is still
open, no further fill can originate from them — so *all orders terminal* plus
*book at rest* makes the delta final. A book that never settles, or cannot be
read, **fails closed**.

### The harness's verdict is no longer accepted as proof

The lesson is procedural, so it is recorded as such: **the gate that lied must
not be the gate that verifies itself.** After each batch the account is now read
directly, at three checkpoints, by something other than the harness.

### Measured proof (live paper broker, independent of the harness)

`docs/evidence/2026-10-01_soak_position_flatten_independent_check.log`:

```
  t+  0s  positions=[]  open_orders=[]  cash=111965.78  buying_power=447863.12
  t+ 60s  positions=[]  open_orders=[]  cash=111965.78  buying_power=447863.12
  t+120s  positions=[]  open_orders=[]  cash=111965.78  buying_power=447863.12
leaked_position_after_batch=False
VERDICT: PASS — account independently confirmed flat at every checkpoint
```

`docs/evidence/2026-10-01_soak_position_flatten_live.log` (harness output):
10 cycles, `still_resting=0`, `positions_back_at_baseline=True`, `mismatches=0`,
submit→ack median 306.9 ms, `VERDICT: PASS`.

**Two further consecutive batches each reported `baseline_qty=0.000000`.** That
is the part that actually matters: the original leak never appeared in the batch
that caused it — only in the *next* run's baseline. One green batch proves
nothing; two more reporting a zero baseline is what distinguishes a fixed leak
from a merely hidden one.

## L6 — A checkpoint is not resumable across a change of HARNESS (DONE)

The resume fingerprint guarded window / batch-size / interval / label, but not
the **code that produces the verdict**. The consequence was immediate and
waiting: the fixed soak was about to be redeployed on top of a checkpoint whose
batch 001 and 002 came from the leaky harness, so the new window would have
inherited two **FAILED** batches and could never return PASS. The operator's
only options would be to accept a permanently-red window or hand-edit the
checkpoint — neither honest, and both exactly the splicing the supersede guard
exists to prevent. It simply could not see the code dimension.

`_state_fingerprint` now carries a SHA-256 over the supervisor and the batch
harness, so a change to either supersedes the checkpoint like a geometry change
does: the old one is preserved as `.superseded`, a fresh window starts. Digests
of the **files**, not `git HEAD` — the deployed container need not carry `.git`,
and "which revision is running" has to be answerable from the volume alone.

Observed in production: the redeployed runner printed `fresh window`, not
`resuming`.

## L7 — The soak service has no source connection; `railway redeploy` runs a stale image (DONE)

`traderos-soak` deployments are reported with `reason=redeploy`, i.e. Railway
re-runs the **last built image**. Neither `railway redeploy` nor
`railway redeploy --from-source` picked up the fix: two consecutive
"redeploys" ran the pre-fix harness and leaked a further **389.29 AAPL** into
the paper account (cash down to −15,963.64) before it was caught. The
production `TraderOS` service *is* connected (`reason=deploy` on push), so the
difference is invisible from the CLI.

`railway up -s traderos-soak --detach --yes` builds from the working tree. The
runbook now documents the trap, the correct command, and — the part that matters
— how to tell from the batch output whether the running code is the fixed one
(`still_resting=` / `positions_back_at_baseline=` versus the old
`cancel_failures=`).

## L5 — A pre-existing flake in the resync suite (DONE)

Unrelated to the soak, but it made a green gate a coin flip.
`test_raising_callback_never_kills_the_run_loop` anchored its tick pair at
`minutes_ago=0` then added 61s, putting the second tick up to ~60s in the
**future** against `validate_tick`'s `max_future_seconds=60`. For roughly the
first second of every minute the ingest was refused and the test failed — for a
reason having nothing to do with what it asserts. Anchoring to the previous
minute drops the worst-case offset to 1s against a 300s staleness bound,
verified across all 60 positions in a minute rather than at the moment it ran.
No threshold raised, no assertion loosened, nothing skipped.

### Reclaiming the account

The 712.5 AAPL the earlier batches accumulated were liquidated with a single
paper market sell (order `202dcc13-8f51-453f-a65f-e37d83a3cfcb`), taking buying
power from 0 to 447,486.44. The 132.05 AAPL leaked by L1–L3 were then reclaimed
the same way (order `fe158541-5882-441b-845b-0128d6844c7b`), restoring cash to
~111,999 and buying power to ~447,996 — a window that can actually fill again.
Evidence: `docs/evidence/2026-10-01_soak_account_reset.log`.

### Negative controls

- The end-to-end test reproduces the production symptom against the pre-fix
  harness: two fills, `mismatches=1`, `VERDICT: FAIL`.
- An in-test control proves a refused close-out fails closed rather than passing
  quietly.
- The two L4 tests are shown to fail against the **pre-quiescence** harness
  (verified by stashing just that file) and pass after: a book hiding a fill
  until the third read cannot yield a false flat, and a book that never stops
  moving fails closed.

## Verification

| Check | Result |
|---|---|
| Full suite (`pytest`) | **2364 passed / 7 skipped** (543s) |
| ruff / black / isort / pyright | clean |
| New soak position tests | `tests/test_soak_position_flat.py`, **17** (2 proven to fail without the quiescence fix) |
| Real paper batch (live broker) | **VERDICT: PASS**, `mismatches=0`, median 306.9 ms |
| Independent account check | **flat at t+0/+60/+120s**, verified outside the harness |
| Repeat batches | 2 further consecutive batches, `baseline_qty=0.000000` |
| **Cloud** `traderos-soak` batch 001 | **PASS** on a fresh window, independently confirmed flat at t+0/+60/+120/+180s (`2026-10-01_cloud_soak_batch001_independent_check.log`) |
| Negative control | pre-fix harness → `mismatches=1`, FAIL |
| Version gate | pyproject == settings.yaml == settings.production.example.yaml == 1.3.2 |

## Honest residuals

- **The 72h window is still operator-run and still wall-clock.** What changed is
  that it is now *safe to leave running*: a batch closes out its own exposure,
  an empty account is a starting state rather than an accident, and each batch
  is confirmed flat by a check the harness does not control. Sprint 50 proves
  several real batches end-to-end; it cannot compress three days.
- **The proof is per-batch, not per-window.** Each batch is now independently
  verified, but nothing here observes 72h of accumulated drift — that remains
  what the window is for.
- The window that batch 001 failed has a **failed batch in its aggregate**. L6
  now supersedes it automatically on the harness change, so the operator gets an
  honest fresh window rather than a laundered one — but that only helps if the
  new harness is actually deployed (L7).
- **The soak service will not deploy itself from a push.** Until a GitHub source
  is connected to `traderos-soak`, every deployment is a manual
  `railway up -s traderos-soak`. A push alone changes nothing on that service,
  and the failure is silent: the deploy reports success.
- **G-01** (a genuine cost-adjusted edge on out-of-sample data) is unchanged and
  open. The pilot remains **DATA-VALIDATION ONLY**; no PnL claim.
- `positions_back_at_baseline` compares against the pre-run snapshot, so a
  position that moves for reasons *other* than this run is still surfaced as a
  mismatch rather than absorbed. That is intended: the soak must not be able to
  explain away an unexplained position.
