# Sprint 24 — Order-level risk enforcement at the live submission boundary

**Period:** 2026-08-04
**Objective:** Make it impossible for an order to reach the live broker that
violates `max_position_size` or an already-breached `daily_loss_limit`, and
eliminate the fail-open (unlimited-loss) defaults. One-hour, tightly-scoped
fix. **This closes exactly one gap** (order-level risk enforcement at the real
submission seam); everything else in the OpenCode audit stays open.

**Scope (per directive):** the risk gate at the live order path + fail-closed
defaults + two proof tests + evidence + governance. No UI, no backtest engine,
no HA, no new risk features.

**Reference docs:** `docs/evidence/2026-08-02_sprint24_risk_gate_submission_boundary.log`,
`docs/engineering/NEXT_STEPS_TO_COMPLETION.md`,
`docs/engineering/GAP_READINESS.md` (scored readiness register + GO/NO-GO gate).

---

## Work Package Register

| ID | Work package | Gate |
|----|--------------|------|
| WP-O1 | Per-order gate before `broker.place_market_order` (live seam) | broker `place_market_order` never called when refused |
| WP-O2 | Fail-closed daily-loss default (2%-of-equity when unset) | no `float("inf")` daily-loss sentinel remains |
| WP-O3 | Proof through the real `CycleExecutor` path | 2 tests: notional cap + daily-loss breach |

## Ground truth (verified, not assumed)
- Live submission path: `application/cycle_executor.py:268`
  `self._broker.place_market_order(...)` (journaled broker →
  `AlpacaBrokerAdapter.submit_order`). **Not** `ExecutionService` — that is the
  order factory + paper-fill simulator used by backtest/paper, not the live
  submission path, so the gate was deliberately **not** placed there.
- `RiskService` was already consulted at cycle level
  (`cycle_executor.py:236-242` `can_trade`/`assess_trade`); the new gate adds
  per-order notional + daily-loss enforcement immediately before submission.
- `daily_loss_limit` was `float("inf")` (unlimited) on both kill switches:
  `KillSwitch` (`risk_service.py`) and `PersistentKillSwitch`
  (`reconciliation_service.py`).

## Work Completed

### WP-O1 — Per-order gate at the real submission seam
- New `RiskService.authorize_order(market_id, side, quantity, price, equity) ->
  TradeVerdict`, called in `cycle_executor` immediately before
  `broker.place_market_order`. Refuses when:
  - order notional (`qty × price`) exceeds `max_position_size` of equity, or
  - realized daily loss already reaches the effective daily-loss cap.
- Rejections are **explicit, never silent**: the caller gets a reason
  (recorded in `errors`), an audit entry (`risk.order_blocked`), and a metric
  (`risk.order_blocked`). `AuditPort` was additionally wired into `RiskService`
  in the factory (it was previously unset in production).

### WP-O2 — Fail-closed daily-loss default
- `KillSwitch.daily_loss_limit` default changed from `float("inf")` to `None`
  ("not configured"); `authorize_order` then applies a **conservative hard cap
  of 2% of current equity** (`DEFAULT_DAILY_LOSS_PCT = 0.02`,
  `RiskService.daily_loss_pct`). Never unlimited.
- `PersistentKillSwitch.daily_loss_limit` default likewise `float("inf")` →
  `None`; `can_trade()` treats `None` as no fixed dollar cap (the equity-relative
  cap is enforced at the order boundary where equity exists).
- Explicit dollar limits still override the default when configured.

### WP-O3 — Proof through the real path (`tests/test_cycle_risk_gate.py`)
Both tests drive a **real** `RiskService` through a **real** `CycleExecutor`
with a spy `BrokerAdapter` and assert `place_market_order` was **never** called:
1. `test_order_above_max_position_size_is_refused_broker_never_called` —
   notional 10 000 > 0.25 × 10 000 equity.
2. `test_order_after_daily_loss_breached_is_refused_broker_never_called` —
   realized −250 ≥ 2% × 10 000 equity.
3. Sanity: `test_order_within_limits_reaches_broker` — an in-limits order
   **does** reach the broker (gate is not a blanket block).

### Evidence (`docs/evidence/2026-08-02_sprint24_risk_gate_submission_boundary.log`)
- `grep` before (`3c80c4f`): `authorize_order` references in the submission
  path = **0**. After: wired at `cycle_executor.py:268`.
- Both proof tests PASS (order refused, broker never called); sanity test PASS.
- `grep 'daily_loss_limit.*float("inf")' src/` → **NONE** (fail-open default
  eliminated).
- Full suite: `1282 passed, 1 skipped`; coverage 92.54%;
  black/isort/ruff/pyright clean; pre-commit hooks pass.

### Gate
- [x] Broker `place_market_order` provably never called when a check refuses
- [x] No unlimited-loss default remains on either kill switch
- [x] Proof tests exercise the real `CycleExecutor` → `BrokerAdapter` path
- [x] Backtest/paper path unaffected (full suite green)

## Not in scope / still open
- Daily loss **beyond the guard** (realized PnL accounting robustness), position
  sizing strategy, backtest realism (fees/slippage), live-ops maturity
  (reconciliation, HA, alerting, live-run policy) — all scheduled for larger
  work blocks.
