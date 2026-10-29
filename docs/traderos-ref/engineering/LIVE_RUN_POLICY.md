# TraderOS — Live Run Policy (G-07)

**Status:** adopted 2026-08-04 · supersedes ad-hoc "we'll watch it" as the sole
authority for moving real capital.
**Reference:** `docs/engineering/GAP_READINESS.md` (G-07: 20/MED before this
policy), `TRADEROS_RELEASE_CONSTITUTION.md`, `docs/runbooks/PILOT_READINESS.md`.

This policy is the G-07 exit test: **a documented live-run policy (red-lines,
kill authority, release signing) reviewed and committed before any real capital
moves.** Until the GO conditions in §8 are empirically met, real capital is
NO-GO by default. This document does not create a GO; it makes the NO-GO (and
any future GO) auditable.

---

## 1. Red-lines (kill conditions)

The following are absolute. If any red-line is observed, trading stops **now**,
not at the next cycle:

1. **Any unplanned order** — an order on the broker that the local journal
   (`order_events`) did not intent-record before submission. Reconciliation
   mismatch severity ≥ 2 (`BROKER_ONLY_ORDER`, `LOCAL_ONLY_ORDER`,
   `UNCONFIRMED_INTENT`, `DUPLICATE_BROKER_STATE`).
2. **Kill-switch trip** — `kill_switch.circuit_open` (5 consecutive
   submission failures) or daily-loss cap breached. Flatten-on-trip is
   automatic and exactly-once (G-03).
3. **Data-gap breaker** — the live loop is blocked on absent/stale market data
   (`risk.data_gap_blocked`, threshold `max_data_staleness_seconds`).
4. **Gross exposure breach** — total open gross exposure above
   `max_gross_exposure`; new orders are refused and the breach is alerted
   (G-03).
5. **Supervision unclean-death alert** — the previous process died without a
   clean shutdown marker (`supervision.unclean_death`). Trading must not resume
   until broker-side truth is reconciled.
6. **Unreconciled startup** — `BrokerStateReconciliationService` has not
   completed cleanly; order acceptance is blocked (fail-closed).

**Kill-zero policy:** when any red-line fires, the position is flattened
(kill-switch → `FlattenService`) and the system holds **zero net open
exposure** until a human operator re-arms after documented reconciliation. No
auto-re-arm.

## 2. Kill authority

| Authority | May | Must |
|-----------|-----|------|
| **Operator (human)** | Kill at any time, no justification required | Log the kill; trigger post-kill reconciliation |
| **Daemon (automated)** | Engages kill-switch on red-lines 2–6 | Alert CRITICAL; audit `risk.*`/`supervision.*`; flatten |
| **RiskService** | Refuse any order that breaches a cap | Explicit reason + audit + metric (no silent drops) |
| **On-call** | Verify state, reconcile, document | Never re-arm without a signed operator acknowledgment |

Only an Operator can re-arm a killed system, and only after a clean
reconciliation (G-02) and a fresh `pilot readiness --mode live` pass.

## 3. Environment separation (research vs live)

- **Research/backtest** runs on stored candles (`data/trader.db`,
  `historical_candles`), unit-test doubles, and never touches a broker. Its
  edge claims are cost-adjusted and oracle-locked before they are candidates
  for promotion (G-01/G-06).
- **Paper** exercises the **real** order path (CycleExecutor → JournaledBroker
  → broker) against paper accounts with paper keys, env-only.
- **Live** requires: `TRADING_MODE=live`, `LIVE_TRADING_CONFIRMED=true`,
  non-empty `risk.allowed_markets` allowlist when `risk.require_allowlist` is
  set, env-only credentials, a signed release artifact (§5), and a GO per §8.
- Crossing research → live without passing §8 is a policy violation.

## 4. Credential policy

- Credentials are **env-only**, never committed. `tests/test_secret_hygiene.py`
  is a conformance gate that fails the suite if a tracked file contains a key
  literal (fail-closed; it has no hardcoded keys itself).
- Live keys live in a secret manager with rotation + access audit; paper keys
  exist only in-process for drills. No key may ever be persisted to the
  database (observability conformance test).

## 5. Release signing

Every artifact proposed for live must be **signed and verified**:

- `scripts/governance/sign_release.py sign --artifact <path> [--key-var <env>]`
  writes a signature file (HMAC-SHA256 of the artifact digest with the env
  key) to `docs/evidence/releases/`; `verify` fails closed on a missing or
  invalid signature.
- Paper-key drills run in-process only; a real key is never printed.
- `scripts/governance/live_gate.py` (CI gate) blocks a `live` config unless:
  (a) secrets conformance passes, (b) the release artifact is signed,
  (c) `TRADING_MODE=live` requires `LIVE_TRADING_CONFIRMED=true` and a
  non-empty allowlist, (d) the GAP_READINESS GO conditions are met
  (`GO_CONDITIONS_MET=true` set only by the documented GO review, never by
  code).

## 6. Pilot terms (the only permitted real-capital footprint)

**Pilot posture: DATA-VALIDATION ONLY.** The G-01 verdict is fixed before
launch: after full costs (fee 10 bps + slippage 5 bps + latency 10 bps) on the
withheld 35% out-of-sample window, **no strategy shows positive expectancy**.
The pilot therefore makes **no PnL claim** and is not an edge-seeking launch;
it exists solely to validate, against a real broker with real capital, that
the order path, latency, fills, reconciliation, and kill rails behave as the
drills say they do.

- **Bounded footprint:**
  - **Symbol set (allowlist):** exactly the pilot markets that the deployed
    feed ingests and that are named in the LIVE risk config — `BTCUSDT` and
    `ETHUSDT` (the crypto pair streamed live on the EU instance). Forex pairs
    (`EURUSD`, `GBPUSD`) are **excluded**: they are not fed live and would trip
    the data-gap breaker. The allowlist may be **narrowed** at arming, never
    widened.
  - **Per-order notional cap:** `max_position_size` = 0.25 × equity, on a
    pilot account sized so a single order is a small fraction of the pilot
    envelope.
  - **Gross exposure cap:** `max_gross_exposure` = 1.0 × equity (never net
    long/short beyond the kill-zero default).
  - **Daily-loss cap:** 2% of equity realized, fail-closed at the submission
    seam.
  - **Max positions:** ≤ 10 concurrent (`max_positions_total`).
- **Hard stop defined before launch (immutable for the pilot window):**
  - A **dollar-loss hard stop** recorded at arming (operator-set, in the
    deployment notes, not in code) — when realized pilot loss reaches it, the
    operator engages the kill switch and the pilot ends.
  - **Kill-zero:** any red-line (§1) flattens to zero net open exposure and
    holds until a human operator re-arms after documented reconciliation. No
    auto-re-arm.
  - **Time-bounded window:** the pilot runs for a defined calendar window
    (operator-set, e.g. 1 week); it does not run indefinitely.
- **Supervised:** a human operator reviews `pilot readiness --mode live` and a
  fresh dry-run immediately before the first live order; the first hour is
  monitored at 5-minute cadence; on-call is live (§ ONCALL_LIVE_DELIVERY).
- **No edge claim:** absent a future G-01 edge proof, the pilot's sole output
  is the validation evidence (fills, latency, reconciliation, kill rails) —
  recorded in `docs/evidence/` like every other drill.
- **Escalation to an edge-seeking pilot** requires a NEW G-01 edge proof on
  out-of-sample real data AND a written GO review amending this §6; it is not
  implied by a successful data-validation pilot.

## 7. Auditability

Every red-line event, kill, flatten, refusal, unclean-death, and release
signature is written to the hash-chained audit log and surfaced by a metric and
a CRITICAL notification. The causal chain per fill (signal → decision → order →
fill → PnL) is reconstructible by replay (G-05). Nothing is silent.

## 8. GO / NO-GO (the only gate that matters)

GO requires all of the following, empirically demonstrated — not declared:

1. G-02 paper soak passes (0 reconcile errors, 0 duplicate/lost orders across
   forced disconnects; journal-recovery replays correctly).
2. G-03 kill-switch-flatten + portfolio-cap drill pass against the real loop.
3. G-01 cost-adjusted walk-forward shows a genuine edge — or the pilot is
   explicitly capped to data-validation only.
4. G-04 alert delivered on forced kill; HA failover proven; live keys in a
   secret manager.
5. This policy reviewed and acknowledged in writing by the operator; red-lines
   and kill authority agreed.
6. Pilot bounded per §6 with the hard stop defined before launch.

**NO-GO until then is the default, not a failure state.** This policy, the
release signing scripts (`scripts/governance/sign_release.py sign`), and the
CI live-gate (`scripts/governance/live_gate.py`, run as the `live-gate` job in
`.github/workflows/ci.yml`) are the mechanism by which that default is
enforced mechanically rather than by intention.
