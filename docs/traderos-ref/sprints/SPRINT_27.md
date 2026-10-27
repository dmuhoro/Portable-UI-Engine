# Sprint 27 — Every gap to 80+ (HA failover, cost realism, risk rails, oracle, replay, governance)

**Period:** 2026-08-04
**Objective:** Move every `GAP_READINESS` gap to 80+ with measured, committed
evidence — HA failover + secret rotation audit (G-04), cost-adjusted
walk-forward + latency (G-01), portfolio risk rails (G-03), partial-fill/
reconnect drills + a real-paper soak harness (G-02), reference-PnL oracle
conformance (G-06), multi-restart replay (G-05), and operator acknowledgment +
live gate in CI (G-07). The only thing not run is anything requiring real
broker credentials — those exit tests stay open, honestly.

**Reference docs:** `docs/engineering/GAP_READINESS.md`,
`docs/engineering/LIVE_RUN_POLICY.md`, `docs/evidence/2026-08-04_sprint27_*.log`.

---

## Work Package Register

| ID | Work package | Gate |
|----|--------------|------|
| WP-F | Firm ops: lease-based HA failover + secrets rotation with access audit (G-04) | Standby daemon fails closed and a healthy peer takes over; secret access/rotation audited with redacted values |
| WP-C | Cost realism: `latency_bps` in the execution cost model + keyless walk-forward evidence (G-01) | OOS walk-forward with full costs recorded; honest DATA-VALIDATION-ONLY verdict |
| WP-RR | Portfolio risk rails drill through the real loop (G-03) | Exposure cap, allowlist, kill-switch flatten, data-gap all provably stop the loop |
| WP-PF | Partial-fill + reconnect drill; real-paper soak harness (G-02) | Partial fills reconciled, 0 dup/lost, restart re-submits nothing; soak harness fails closed without keys |
| WP-O | Oracle conformance: frozen reference PnL lock (G-06) | Engine reproduces committed reference PnL on full + withheld windows |
| WP-MR | Multi-restart replay (G-05) | Full day replayed bit-complete after simulated restarts |
| WP-G | Operator acknowledgment + live gate in CI + governance drill (G-07) | Operator red-line ack signed+verified; CI asserts fail-closed live posture |

## Ground truth (verified, not assumed)
- Live chain (`application/factory.py`): `CycleExecutor → JournaledBroker →
  GuardrailedBroker → RateLimitedBroker → AlpacaBrokerAdapter`. Order call
  site `cycle_executor.py`.
- `DaemonController.leading` is a property backed by the failover manager; the
  drills drive `FailoverManager.try_acquire_leadership()` directly (there is no
  public failover accessor on the controller).
- No real Alpaca keys are available in this environment — every drill uses a
  simulated broker through the **real submission path**, and the real-paper
  soak harness **fails closed** (exit 2, NO-GO) without credentials.

## Work Completed

### WP-F — HA failover + secret rotation audit (G-04)
- `src/traderos/infrastructure/ha_failover.py`: `LeaseStore` (SQLite, owner
  lease, stale-after-90s) + `FailoverManager` (`leading`, `try_acquire_
  leadership`, `stop` releasing the lease). Fail-closed: no lease → no
  leadership, never a silent double-primary.
- Wired into `DaemonController` (failover gating per cycle) and
  `Orchestrator`/`factory.py` (`_build_failover` gated on `ha.enabled`; fixed
  stray imports that broke the module).
- `SecretsRotator` now records `secret.accessed` and `secret.rotated` audit
  entries with `value_redacted: True` — observability never persists secret
  values.
- `tests/test_ha_failover.py` (5 tests): lease semantics, stale-lease
  takeover (a third manager sees the dead primary's lease expire), and a
  real-`CycleExecutor` daemon drill where the standby blocks the live loop.
- `tests/test_secret_hygiene.py`: access + rotation are audited, values
  redacted; audit chain is verifiable.
- `scripts/evidence/run_firm_ops_drill.py`: **3/3 PASS** — standby fails
  closed and a healthy peer takes over; alert transport reaches the notifier
  (needs `NotificationChannel.WEBHOOK`); secret access audited + redacted
  (`2026-08-04_sprint27_firm_ops_drill.log`). Suite-locked by
  `test_firm_ops_drill_evidence_passes`.

### WP-C — Cost realism + walk-forward evidence (G-01)
- `ExecutionService` gained `latency_bps: float = 0.0`, folded into the
  side-aware `apply_slippage` (widens buys, lowers sells — conservative).
- `tests/test_cost_adjusted_backtest.py` `TestLatency` (5 tests): next-bar
  fills, last-bar dropped, latency widens buys/lowers sells, latency more
  conservative.
- `scripts/evidence/run_walk_forward_evidence.py`: **keyless** cost-adjusted
  walk-forward on the **frozen G-06 oracle candles** (reproducible on any
  machine), 35% withheld out-of-sample window, 5 folds, full costs (fee 10bps
  + slippage 5bps + latency 10bps).
- **Honest outcome recorded:** no strategy shows positive expectancy after
  full costs on OOS data → `VERDICT: PASS` with the explicit callout **PILOT =
  DATA-VALIDATION ONLY, no PnL claim** (`2026-08-04_sprint27_walk_forward_
  evidence.log`). Suite-locked by `test_walk_forward_evidence_drill_passes`.
- `run_cost_adjusted_backtest.py` updated to `latency_bps=10`.

### WP-RR — Portfolio risk rails drill (G-03)
- `scripts/evidence/run_risk_rails_drill.py`: **6/6 PASS** through the real
  loop — gross-exposure cap blocks (broker untouched), allowlist blocks an
  unlisted symbol and passes an allowlisted one, kill-switch flatten fires
  exactly once (1 sell close, 0 buys), data-gap (stale candles) blocks live,
  in-limit order still reaches the broker
  (`2026-08-04_sprint27_risk_rails_drill.log`). Suite-locked by
  `test_risk_rails_drill_evidence_passes`.

### WP-PF — Partial-fill/reconnect + real-paper soak harness (G-02)
- `scripts/evidence/run_partial_fill_reconnect.py`: `PartialFillAlpacaClient`
  fills 50% of every order and drops acks every 3rd order, through the real
  cycle → journal → adapter path. **7/7 PASS** — partial fills recorded with
  actual qty, local book == broker, reconcile clean, 0 duplicates
  (broker==journal==trades), 0 pending, restart re-submits nothing, forced
  disconnects exercised (`2026-08-04_sprint27_partial_fill_reconnect.log`).
- `scripts/evidence/run_real_paper_soak.py`: operator harness for the
  unattended Alpaca paper soak (G-02 exit test). **Fails closed** (exit 2,
  NO-GO) without `ALPACA_API_KEY`/`ALPACA_SECRET_KEY`; never fabricates broker
  truth (`2026-08-04_sprint27_real_paper_soak.log`). Suite-locked by
  `test_partial_fill_reconnect_drill_passes` and
  `test_real_paper_soak_harness_fails_closed_without_keys`.

### WP-O — Oracle conformance (G-06)
- `scripts/evidence/run_oracle_conformance.py`: reproduces the **committed
  reference PnL** on both the full frozen dataset and the withheld window to
  tolerance 1e-4 — **PASS 2/2** (`2026-08-04_sprint27_oracle_conformance.log`).
- Suite-locked by `test_oracle_conformance_drill_passes`.

### WP-MR — Multi-restart replay (G-05)
- `scripts/evidence/run_multirestart_replay.py`: real `CycleExecutor` cycles on
  a durable DB with **2 simulated process restarts** (close conn, fresh
  executor on the same DB), then `ReplayService.replay_day` verifies the audit
  chain is valid, every cycle is reconstructed, and the replay matches the
  recorded events — 9 cycles, chain complete, `total_realized_pnl=123.15`
  (`2026-08-04_sprint27_multirestart_replay.log`). Suite-locked by
  `test_multirestart_replay_drill_passes`.

### WP-G — Operator acknowledgment + live gate in CI (G-07)
- `scripts/governance/operator_ack.py`: records the operator's written
  acceptance of the seven red-lines, HMAC-SHA256 signed with
  `RELEASE_SIGNING_KEY`, stored under `docs/evidence/operator/` (or
  `OPERATOR_ACK_DIR`); `verify` fails closed on missing/tampered/invalid ack.
  Acknowledgment body excludes the `"signature"` key (round-trip bug fixed).
- `verify_ack` wired into `live_gate.py` as a required check in live posture.
- `tests/test_live_gate_governance.py`: `TestOperatorAck` (4 tests), live gate
  requires operator acknowledgment, live mode passes with all GO conditions +
  ack (14 tests).
- `.github/workflows/ci.yml`: new **governance** job — runs the live gate in
  paper mode (pass-through), then in live mode asserts it **fails** (blocks
  live posture with no GO conditions).
- `scripts/evidence/run_governance_drill.py`: **6/6 PASS** — release signing,
  release verify, operator ack, ack verify, live gate fails closed without GO,
  live gate passes with GO + ack (`2026-08-04_sprint27_governance_drill.log`).
  Suite-locked by `test_governance_drill_passes`.

### Evidence & gates
- Suite **1351 passed, 1 skipped**; whole-tree pyright **0 errors**; ruff
  clean; black clean; all seven sprint-27 drills suite-locked.

## Gates
- [x] Standby daemon fails closed; healthy peer takes over (lease semantics)
- [x] Secret access + rotation audited, values redacted
- [x] OOS walk-forward with full costs (fee + slippage + latency) recorded;
      honest DATA-VALIDATION-ONLY verdict
- [x] Portfolio risk rails 6/6 fail-closed against the real loop
- [x] Partial-fill + reconnect drill: 0 dup/lost, restart re-submits nothing
- [x] Real-paper soak harness fails closed without credentials
- [x] Engine reproduces committed reference PnL 2/2 (full + withheld)
- [x] Full day replayed bit-complete after 2 simulated restarts
- [x] Operator acknowledgment HMAC-signed + verified; live gate in CI
- [x] `GAP_READINESS.md` rescored 80+ (G-07 85); SPRINT_27 + CHANGELOG updated

## Not in scope / still open
- Real Alpaca paper endpoint soak (G-02 exit test: 24–72h unattended) — harness
  ready, needs paper keys.
- Real-market edge proof for G-01 — until then the pilot is **DATA-VALIDATION
  ONLY**; latency model to be tuned from live fills.
- Secret-manager integration (Vault/KMS) + on-call alerting transport (G-04).
- Production config defaults for caps/allowlists + operational kill surface
  (G-03).
- UI/regulator surfacing of replay attribution (G-05).
