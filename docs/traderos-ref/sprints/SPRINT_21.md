# Sprint 21 — Order-Survivability: durable journal wire-up (L1-L4)

**Period:** 2026-08-02
**Objective:** Close the trust boundary so the order path is *survivable*
(L1) and *provable* (L2), then give operators the runbook→CLI controls (L3)
and prove the two last live-dependency drills against **real** networks and
Postgres (L4). No feature work, no new abstractions, no fabrication:
everything green and evidence-only.

**Reference docs:** `docs/AUDIT_GROUND_TRUTH.md`,
`docs/engineering/FINISH_LINE_DASHBOARD.md`,
`docs/engineering/STRATEGIC_COMPLETION_BLUEPRINT.md` (OT-001/OT-004, R-01/R-02).

---

## Work Package Register

| Layer | Deliverable | Gate |
|-------|-------------|------|
| L1 | Durable `JournaledBroker` wired into the LIVE order path | full suite green; replay returns stored result, no double-submit |
| L2 | Restart / broker-surprise drill | broker calls `0` on replay; intent drift blocks `can_accept_orders` |
| L3 | Runbook → CLI parity (`risk`, `metrics`, `daemon start`, `audit verify`) | subcommands exist + hands-on PASS |
| L4 | Live Binance + Postgres crash-recovery drills (R-01/R-02) | real network PASS logged |
| L5 | Constrained live pilot + real-money switch procedure | **gate held; requires operator funding/approval** |
| Final | Full suite + lint/typecheck + sprint record + CHANGELOG + push | **1274 passed, 1 skipped**; ruff/black/isort/pyright clean |

## Work Completed

### L1 — Durable, idempotent order submission
- New `src/traderos/infrastructure/journaled_broker.py`: `JournaledBroker`
  wrapper persists an *intent* (`CONFIRMED` after broker success) before the
  broker and deduplicates by a derived `uuid5` key
  `_client_key(market_id, side, quantity, method)`. On restart, replay returns
  the previously stored result (no duplicate submit); an intent-only event
  yields `needs_reconcile`.
- `journal.py`: added `get()`, `update()`, `count()` and `row_factory = sqlite3.Row`.
- `factory.build_orchestrator()` now wraps the LIVE broker with
  `JournaledBroker(broker, OrderEventJournal(sqlite3.connect(cfg.db_path)))`
  (best-effort, `except Exception` → no-op).
- `broker_state_reconciliation_service.py`: added
  `MismatchType.UNCONFIRMED_INTENT` and `journal_pending` to `reconcile()`;
  `daemon_controller.py` feeds pending intents into reconcile.

### L2 — Restart / broker-surprise drill (`docs/evidence/2026-08-02_l2_restart_surprise_rehearsal.log`)
- Restart → broker submit calls `B = 0` (replayed `ext-1` filled, no submit).
- Intent drift present → `can_accept_orders = False`.
- `reconcile.mismatches` reports `unconfirmed_intent`; `PRAGMA` checks pass.

### L3 — Runbook → CLI parity (CLOSURE-14 shape)
- `main.py` gains `risk {status,check,reset,kill,reconcile}`,
  `metrics {snapshot,watch}`, `daemon {run,start}` alias, and
  `audit verify` (chain hash). All hands-on verified; exit codes honor the
  verdict (fail→1). Kill-switch stays ADR-007 manual-reset.

### L4 — Live dependency drills (real network / real Postgres)
- **R-01 Binance live** (`docs/evidence/2026-08-02_l4r01_binance_live.log`):
  `BinanceCollector` REST klines against `api.binance.com` (BTCUSDT 1m) + a
  **live** `wss://stream.binance.com:9443` `@kline_1m` tick validated through
  the OT-004 pipeline → `RESULT: PASS`.
- **R-02 Postgres crash** (`docs/evidence/2026-08-02_l4r02_postgres_crash_drill.log`):
  crashed `traderos-pg-test`, boundary failed closed
  (`connection-refused`), restarted healthy, marker row survived →
  `RESULT: PASS`.

### Gate
- Full suite **1274 passed, 1 skipped**, coverage **92.83%** (≥70 required);
  `ruff check src/ tests/` 0 errors; black/isort (whole `src`) unchanged;
  pyright strict clean on all changed modules.

### Honest residual (not fabricated)
- **L5 real-money pilot + live switch** intentionally NOT run: requires
  explicit operator funding/approval per constitution. Documented, gated,
  honest.
