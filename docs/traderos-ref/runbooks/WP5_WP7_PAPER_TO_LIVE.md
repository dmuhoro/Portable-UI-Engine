# WP5–WP7 Runbook — Real Paper Soak, Latency Calibration, Live Re-arm

**Date:** 2026-08-09 · **Scope:** the account-gated progression to a live pilot.
Supersedes nothing; complements `LIVE_RUN_POLICY.md` (§6 pilot terms, §8 GO
gate) and `run_real_paper_soak.py` / `run_unattended_paper_soak.py`.

This runbook is **authority-restricted**: it documents *how to prove the rails*
against real Alpaca paper, *how to measure real ack latency*, and *how a live
pilot may be proposed*. Nothing here creates a GO for real capital. Per the
Constitution, WP7's live deployment is only ever re-armed by the named Operator
(human), never by code, and never by an unattended process.

---

## 1. Guardrails (shared by everything below)

- Credentials are **env-only** paper keys, never written to a file, commit,
  DB, or log (`LIVE_RUN_POLICY` §4; `tests/test_secret_hygiene.py`).
- The real-paper harness **fails closed**: without keys it returns
  `NO-GO (credentials absent)` and exit code 2 — it refuses to fabricate
  broker truth.
- Every run closes out **its own** residue (orders the runner created, by
  client-order-id ownership / not-in-baseline for the soak symbol) and waits
  for the broker cancel to settle before reconciling. A user's own orders are
  never cancelled.
- No silent drops: any batch that crashes is recorded `FAIL` in the aggregate
  log, not skipped.

## 2. WP5 — real Alpaca paper soak

Exit test (committed in `GAP_READINESS.md` G-02): *unattended paper-broker
soak (Alpaca paper, 24–72h) with 0 reconcile errors, 0 duplicate/lost orders
across forced disconnects, and journal-recovery replaying correctly.*

### 2a. Bounded smoke (any operator, any time)

```bash
export ALPACA_API_KEY=...           # paper keys, in-process only
export ALPACA_SECRET_KEY=...
PYTHONPATH=src python3 scripts/evidence/run_real_paper_soak.py 5
```

Runs 5 real market orders through the **production chain**
(CycleExecutor → JournaledBroker → AlpacaBrokerAdapter → Alpaca paper),
measures WP6 submit→ack latency, closes out its residue, and reconciles.
Evidence: `docs/evidence/<date>_real_paper_soak.log`.

### 2b. Unattended window (24–72h)

```bash
export ALPACA_API_KEY=... ALPACA_SECRET_KEY=...   # paper, env-only
PYTHONPATH=src python3 scripts/evidence/run_unattended_paper_soak.py \
    --hours 24 --batch-cycles 10 --interval-minutes 60
```

The runner supervises the window: each batch is an independent real-path soak
with clean close-out and reconcile; each batch is one audited row in
`docs/evidence/<date>_unattended_paper_soak_aggregate.log`. Final verdict is
`PASS` only if **every** batch passed (`0 reconcile/dup/lost across all
batches`). If a batch crashes, the failure is recorded — never dropped.

Operator action during a soak window: check the aggregate log at least once a
day; any FAIL row means the run must be diagnosed before re-running, never
hidden.

## 3. WP6 — latency calibration

**No separate harness.** Latency rides the soak (same real path, same orders):
`place_market_order` returns after the broker ack, so the measured elapsed time
is the real submit→ack round-trip. The harness runs `SOAK_LATENCY_PROBES`
(⌐10) one-cent probes per batch and prints:

```
WP6 latency (submit->ack ms): n=10 min=… median=… max=…
```

Baseline observed on 2026-08-09 (paper): **min≈244–306 ms, median≈306–308 ms,
max≈308–356 ms**. These become the pilot's connectivity acceptance band when
the same probes run against the **live** endpoint.

## 4. WP7 — bounded live pilot (re-arm only by the Operator)

### 4.1 Authority

- **Living re-arm authority: the named Operator (human) — the repository
  owner.** Re-arm requires a documented acknowledgment *after* a clean
  reconcile and after a fresh `traderos pilot readiness --mode live` pass.
- **No unattended process may re-arm.** An automated kill stays killed
  (kill-zero per `LIVE_RUN_POLICY §1`); only the Operator can undo it.
- **Daily check-in cadence:** during the pilot the Operator is the sole
  re-arm/key authority and must review, at least once per trading day:
  the audit chain (`traderos audit`), the reconcile/soak evidence, and the
  kill/alert trail. A day with no check-in = the pilot is paused (no new
  live orders) until a check-in happens. This is a stop, not a suggestion.

### 4.2 Re-arm checklist (all must be true)

1. G-02 paper soak **passes** on the real paper account (this runbook §2),
   including a 24h+ unattended window.
2. G-03 kill-switch-flatten + portfolio-cap drill pass against the real loop.
3. G-04 alert on forced kill is delivered (on-call drill 6/6); live keys live
   in a secret manager with rotation + access audit.
4. G-01 edge claim is either cost-adjusted/out-of-sample **or** the pilot is
   explicitly capped to **data-validation only** (connectivity, latency,
   execution fidelity — no PnL claim).
5. `LIVE_RUN_POLICY` §8 life-cycle GO conditions reviewed + acknowledged in
   writing by the Operator; red-lines and kill authority agreed.
6. Pilot footprint is bounded per §6: single allowlisted symbol set, per-order
   notional cap, gross exposure cap, 2%-of-equity daily-loss cap, and a
   documented hard-stop dollar loss defined **before** launch.
7. A signed release artifact and a passing CI `live_gate` (§5).

### 4.3 Signing

For allowed technical closures of these components during the pilot, use the
signed-release mechanism (`scripts/governance/sign_release.py sign`) — an
unsigned artifact never touches live. Paper drills need no signature.

## 5. Honest accounting (what these runs do NOT prove)

The 24h aggregate log (`docs/evidence/2026-08-04_sprint27_multirestart_replay.log`)
records order-integrity outcomes and ack latency on real paper; the drills that
produce them are run by `python3 scripts/evidence/run_ci_drills.py`. It does
**not** prove: an edge, fill-price fidelity vs live,
extended-hours behavior, or any PnL. WP7 re-arm is evidence-gated on §4.2; a
paper-soak pass is necessary, never sufficient. If any of that is the state,
say so in the evidence rather than dressing it as GO.
