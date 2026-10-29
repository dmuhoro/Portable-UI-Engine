# Sprint 26 — Evidence-backed live-ops hardening (supervision, causal replay, disconnect soak, governance)

**Period:** 2026-08-04
**Objective:** Turn the remaining G-04/G-05/G-07 readiness gaps into *measured,
committed evidence*, and find/close a real correctness bug in the idempotent
submission path under forced disconnects. Four one-hour blocks: supervision +
alerting, causal trade replay, forced-disconnect paper soak, live-run
governance.

**Reference docs:** `docs/engineering/LIVE_RUN_POLICY.md`,
`docs/evidence/2026-08-04_sprint25_causal_replay.log`,
`docs/evidence/2026-08-04_sprint25_paper_soak.log`,
`docs/engineering/GAP_READINESS.md`.

---

## Work Package Register

| ID | Work package | Gate |
|----|--------------|------|
| WP-S1 | Supervision: heartbeat + unclean-shutdown detection wired into daemon & orchestrator | CRITICAL alert delivered on a forced process kill; clean shutdown stays silent |
| WP-S2 | Secret hygiene: no key literals committed; LIVE requires credentials; observability never persists secrets | 5 test proofs through the real config/audit path |
| WP-R1 | Causal chain: signal → decision → order → fill recorded per `signal_id` | Replay reconstructs *why* each fill happened, FIFO-realized PnL bit-matches recorded events |
| WP-S3 | Forced-disconnect soak through the real submission path | 300 cycles, 0 duplicates / 0 lost / 0 reconcile mismatches, journal restart replays without re-submit |
| WP-S4 | Caller-owned `client_order_id` threaded end-to-end (the bug the soak found) | One decision = one order even when the broker drops the ack; restart recovery preserves intent |
| WP-G1 | `LIVE_RUN_POLICY.md`: red-lines, kill authority, env separation, pilot terms | Document committed; operator acknowledges in writing before real capital |
| WP-G2 | Release signing + fail-closed live gate (`scripts/governance/`) | Sign/verify round-trip proven; live gate blocks unless every GO condition holds |

## Ground truth (verified, not assumed)
- Live chain (`application/factory.py`): `CycleExecutor → JournaledBroker →
  GuardrailedBroker → RateLimitedBroker → AlpacaBrokerAdapter`. Order call site
  `cycle_executor.py`.
- **L4 survey found:** `journal_entries` table is dead (no `JournalService`),
  `OrderEventEngine` never wired, and `trades` has no PnL column — realized PnL
  only exists on `positions` at close. Causal recording was therefore built on
  the live audit chain, not on those dead structures.
- **L6 soak found a real bug:** `JournaledBroker._submit` keyed its journal by a
  request-shape key `_client_key(market, side, qty, method)`, so *repeating*
  requests for the same shape collided and produced **phantom duplicate trades**
  (60 trades vs 50 broker orders in the first soak run). Fix: a caller-owned
  `client_order_id` generated once per decision is now the authoritative
  idempotency key, threaded through `CycleExecutor → ports → BrokerAdapter →
  AlpacaBrokerAdapter → JournaledBroker → BrokerRateLimiter → OrderGuardrail →
  PaperTradingService`.
- Credentials live only in env vars; `test_secret_hygiene` scans *tracked*
  files for `PK...` literals.

## Work Completed

### WP-S1 — Supervision & unclean-shutdown alerting
- `SupervisionService` (heartbeat store + check) wired into `DaemonController`
  (heartbeat each loop iteration; `check_unclean_shutdown` on start;
  `mark_clean_shutdown` on stop) and `Orchestrator`/`factory.py`
  (`JsonlHeartbeatStore(Path(cfg.data_dir)/"supervision.jsonl")`).
- Data-gap crossing now also emits a CRITICAL notification.
- `tests/test_supervision.py`: forced-kill subprocess drill delivers CRITICAL
  "Unclean Process Death"; clean shutdown and fresh-heartbeat cases stay silent.

### WP-S2 — Secret hygiene proofs
- `tests/test_secret_hygiene.py`: no Alpaca key literals in tracked files;
  `TRADING_MODE=live` without credentials raises `ConfigError` (fail-closed);
  live validation passes only with real credentials; observability tables
  (`audit_log`, `metrics_history`) never persist secret values; secret-rotator
  read/cache behavior.

### WP-R1 — Causal replay
- `CycleExecutor._record_causal` records `signal.generated`, `decision.made`
  (blocked or allowed), `order.placed`, `trade.fill` — each signal_id-keyed into
  the SQLite audit hash-chain (`json.dumps(..., default=str)`).
- New `domain/services/replay_service.py`: `ReplayService.replay_day(start,
  end)` reconstructs `signal → decision → order → fill` chains and computes
  FIFO realized PnL (`_fifo_realized_pnl`, long/short lot deques).
- `tests/test_replay_service.py` + `scripts/evidence/run_causal_replay.py`:
  real-CycleExecutor day replay — 6 chains, `total_realized_pnl=208.74`, audit
  chain integrity verified.

### WP-S3 — Forced-disconnect soak (found the bug)
- `tests/test_soak_disconnect_drill.py`: ack-loss masked by idempotent retry
  (zero duplicates); journal restart replays without resubmission;
  unconfirmed-intent fail-closed (`can_accept_orders` False on
  `UNCONFIRMED_INTENT` mismatch); soak cycles through the real submission path.
- `scripts/evidence/run_paper_soak.py` initial run **failed**: 60 trades vs 50
  broker orders — the phantom-duplicate bug below.

### WP-S4 — Caller-owned idempotency key (the fix)
- One `client_order_id` (`uuid4`) generated per decision, recorded in
  `decision.made` and `order.placed` audit detail, threaded through the whole
  submission chain (signatures now `(market_id, side, quantity,
  close_price=None, client_order_id=None)`).
- `JournaledBroker` uses the caller id as the authoritative journal key,
  preserving restart replay and intent dedupe.
- Post-fix soak (300 cycles): PASS — `broker_orders=300=journal_confirmed=300=
  trades`, `pending=0`, restart adds exactly 1 new order with no re-submits,
  reconcile 0 errors/0 mismatches, ack-loss recovered.
- Unrelated pre-existing fix: `interfaces/cli/main.py` E501.

### WP-G1 — Live-run policy
- `docs/engineering/LIVE_RUN_POLICY.md` (adopted 2026-08-04): six red-lines,
  kill-authority table, research/paper/live env separation, credential policy,
  release signing, pilot terms, GO/NO-GO (§8: six empirically demonstrated
  conditions, NO-GO default).

### WP-G2 — Release signing + live gate
- `scripts/governance/sign_release.py`: HMAC-SHA256 sign/verify; env key never
  printed/written; paper-key warning in drills; fail-closed verify.
- `scripts/governance/live_gate.py`: TRADING_MODE=live requires secrets
  conformance, credentials, `LIVE_TRADING_CONFIRMED`, allowlist gate, valid
  release signature, and `GO_CONDITIONS_MET` — any failure exits non-zero.
- `tests/test_live_gate_governance.py` (9 tests): sign/verify round-trip,
  tamper rejection, fail-closed without signature/key, paper mode not blocked,
  live blocked without GO, live passes with all conditions, unsigned artifact
  blocked, allowlist enforced.

### Evidence & gates
- Suite `1328 passed, 1 skipped`; ruff clean; pyright 0 errors; black/isort
  clean.

## Gates
- [x] CRITICAL alert delivered on forced process kill; clean shutdown silent
- [x] No key literals committed; LIVE fail-closed without credentials
- [x] Causal replay reconstructs fills with FIFO realized PnL; chain integrity
- [x] 300-cycle soak: 0 duplicates / 0 lost / 0 reconcile mismatches
- [x] One decision = one order under dropped-ack; restart replays without re-submit
- [x] `LIVE_RUN_POLICY.md` committed (red-lines, kill authority, pilot terms)
- [x] Sign/verify round-trip proven; live gate fail-closed and tested

## Not in scope / still open
- Real Alpaca paper endpoint soak (G-02 exit test: 24–72h unattended).
- HA failover for the daemon and a secret-manager + rotation (G-04 exit test).
- Portfolio caps / kill-flatten drill and allowlist blocking drill (G-03).
- Withheld-data conformance run + reference-PnL oracle (G-06).
- Live gate not yet wired into CI.
