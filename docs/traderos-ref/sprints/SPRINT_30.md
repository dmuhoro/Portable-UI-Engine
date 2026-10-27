# Sprint 30 — Real Alpaca paper soak + latency + WP7 re-arm runway (WP5–WP7)

Everything this sprint is account-gated and operator-supervised per
`LIVE_RUN_POLICY.md`. The work: take the G-02 paper-soak harness from
"ready, needs keys" to **proven against the real Alpaca paper endpoint**,
attach WP6 latency calibration, and put WP7 on a documented, authority-gated
re-arm path. No real capital and no un-attempted code — nothing here moves the
GO state by itself.

## Ground truth (verified, not assumed)

- The G-02 harness drives the **real production chain** `CycleExecutor ->
  JournaledBroker -> AlpacaBrokerAdapter` and, on the first real-paper run,
  exposed a genuine production defect: Alpaca returns `qty`/`filled_qty` as
  strings and the adapter did arithmetic on raw broker strings
  (`TypeError` on the live path) and reported `filled=True`/`status=filled`
  unconditionally. Both fixed in `infrastructure/alpaca_broker.py`; unit
  suite stays green and the fix is verified against the real paper endpoint.
- The harness had no `symbol_map`, so market orders carried a random UUID as
  the symbol and the real account answered `asset "...uuid..." not found`.
  Bound the soak to a stable `market_id -> AAPL` (tradable + fractionable in
  the paper account) so the soak exercises the real path, not a literal error.
- The harness also reconciled a snapshot taken before the broker settled its
  cancels (its own residue) — it now **closes out only orders it created**
  (client-order-id prefix + not-in-baseline for the soak symbol), waits for
  entitlements to settle (bounded), and only PASSes from a clean closed state.

## SOAK_WINDOW evidence (bounded — full 24-72h is an operator-run gate)

- `docs/evidence/2026-08-09_final_smoke.log` — real-paper soak, 3 cycles,
  VERDICT PASS, reconcile clean, 0 lost, residue closed out.
- `docs/evidence/2026-08-09_oncall_transport_drill.log` — A7 6/6 PASS
  (severity routing, CRITICAL delivered on the wire, audited)
- `docs/evidence/2026-08-09_smoke5.log` — 5 cycles PASS
- `docs/evidence/2026-08-09_smoke3.log` — 5 cycles PASS
- Aggregated unattended runner: `2026-08-09_uattest2_aggregate.log` — 5/5
  batches PASS over a 60s supervised window, 0 reconcile/dup/lost.

## Work Completed

### WP5 — Real Alpaca paper soak (bounded proof under keysets)
- `scripts/evidence/run_real_paper_soak.py` — client-orders owned close-out,
  settle-wait before reconcile, honest `filled`/`pending` status, dated OUT
  path (`backend evidence file per day, no clobber`), latency line.
- `scripts/evidence/run_unattended_paper_soak.py` — new supervised 24-72h
  window runner: per-batch real-path soaks, close-out, per-batch audited rows,
  aggregate PASS only if every batch passes; stderr captured (no silent
  drops). Proven 5/5 on a 60s window; the real 24h window is an operator
  deliverable (command in the runbook).

### WP6 — Latency calibration (rides the soak)
- Same-path one-cent probes (SOAK_LATENCY_PROBES, ~10 per batch) report
  submit→ack ms through `place_market_order`. Observed (Alpaca paper,
  2026-08-09): min ≈ 244–306 ms, median ≈ 306–308 ms, max ≈ 308–356 ms.

### WP7 — Live-pilot runbook (re-arm = Operator, daily check-in)
- New `docs/runbooks/WP5_WP7_PAPER_TO_LIVE.md` — authority-restricted GO
  flow. Only the named Operator may re-arm; a daily check-in cadence is a
  hard stop (a day with no check-in pauses new live orders); none of the
  paper-soak evidence is a PnL claim.

### Repository hygiene (found while running evidence)
- `scripts/evidence/run_oncall_drill.py` had a hard-coded 2026-08-06 OUT path
  that a re-run overwrote; now day-aware (like the soak). The remaining
  evidence drills still use hard-coded dated OUT paths — every one of them
  must be made day-aware before it is re-run so no evidence is ever re-dated.

## Belt-and-suspenders checks
- Full suite WITHOUT PG: 1494 passed / 79 skipped (matches the last green
  base). Drill suite-locked tests + secret hygiene green
  (`test_integration/test_factory.py::TestOnCallTransportDrill`,
  `test_soak_disconnect_drill.py::...::harness fails-closed`,
  `test_secret_hygiene.py` — 9 passed).
- `ruff` clean on changed files; `pyright` 0 errors on the adapter.

## Not done (honest)
- A continuous 24-72h unattended window (operator deliverable, `--hours 24`).
- Live mode still NO-GO until every §8.4 gate and the Operator's signed
  acknowledgment happens — this sprint builds the evidence list and the
  authority boundary only.
