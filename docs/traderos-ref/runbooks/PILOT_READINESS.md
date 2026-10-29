# Pilot Readiness Runbook — TraderOS

## Purpose

Gate the transition from paper trading to a controlled live pilot. This
runbook defines how to verify readiness, rehearse the operator workflow without
placing live orders, and how to make the go/no-go decision for the
`controlled_live` transition. It complements the risk envelope in
`CONTROLLED_PILOT.md`.

---

## When to Use

- Before every live-trading session (a full readiness pass must succeed).
- Before any upgrade to the order pipeline, strategy stack, or broker adapter.
- As the daily rehearsal during the pilot (paper mode, `dry-run`).

---

## Preconditions

1. Environment is configured per `CONTROLLED_PILOT.md` (guardrails, rate
   limits, risk parameters).
2. Config mode is `paper` for rehearsal, `live` for the go/no-go gate.
3. No in-flight manual orders on the broker.

---

## Step 1 — Readiness Gate

Run the live-readiness verification. It never places an order.

```bash
# Human-readable verdict
traderos pilot readiness --mode paper

# Machine-readable verdict (also available as GET /v1/live/check)
traderos pilot readiness --mode paper --json
```

The command exits `0` only when every check passes:

| Check | Meaning |
|-------|---------|
| `broker_connected` | Broker API reachable and authenticated |
| `data_feeds` | Data ingestion is producing usable candles |
| `kill_switch_closed` | Kill switch is not tripped and `can_trade()` is true |
| `live_preflight` | Preflight service passes (audit chain, reconciliation, `LIVE_TRADING_CONFIRMED=true`) |
| `operator_session` | Operator workflow is idle or at an expected step |

In `paper` mode, `live_preflight` and `operator_session` are expected to FAIL
unless live confirmation is explicitly set; that is correct rehearsal behavior,
not an incident.

**Rule:** do not proceed to Step 2 on a `NOT READY` verdict until the failing
checks are understood and corrected.

---

## Step 2 — Workflow Dry-Run Rehearsal

Rehearse the full operator workflow with `dry_run=True` so live execution stays
disabled. Strategy promotion is skipped (operator decision); every other step is
executed and its gate evaluated.

```bash
traderos pilot dry-run --mode paper
traderos pilot dry-run --mode paper --json
```

The rehearsal drives the workflow from its current state forward, stopping at
the first failing gate:

```
[PASS] start: operator session started
[FAIL] preflight: failed: Broker state reconciliation incomplete — order acceptance blocked
```

The command exits non-zero if any gate fails. A rehearsal that completes every
step (through `session_report`) is a strong readiness signal but does **not**
by itself enable live trading.

---

## Step 3 — Go / No-Go Gates

| # | Gate | Requirement |
|---|------|-------------|
| 1 | Readiness | `traderos pilot readiness --mode live` exits `0` |
| 2 | Rehearsal | `traderos pilot dry-run --mode live` exits `0` |
| 3 | Reconciliation | Broker reconciliation passes within tolerance (< 0.1%) |
| 4 | Guardrails | Order-size guardrail + rate limiter confirmed in the kill-switch path |
| 5 | Paper record | ≥ 5 consecutive profitable or flat paper sessions with no kill-switch trip |
| 6 | Operator review | Performance review + strategy promotion approved by an operator (human) |

Only when all six gates pass may the operator advance the workflow to
`controlled_live` via the operator API or dashboard. The workflow enforces
ordering — `controlled_live` is unreachable until `strategy_promotion` records a
promotion.

---

## Step 4 — Controlled Live

1. Set `LIVE_TRADING_CONFIRMED=true` and `TRADEROS_RISK_MODE=live` (or the
   configured equivalent), then restart.
2. Confirm `traderos pilot readiness --mode live` exits `0`.
3. Advance the workflow: `start → preflight → broker_check → market_data_check →
   paper_trading → performance_review → strategy_promotion → controlled_live`.
4. Monitor kill switch, reconciliation, and guardrail rejections for the first
   hour at 5-minute cadence.

---

## Exit Criteria (end of pilot)

As defined in `CONTROLLED_PILOT.md`: 30 consecutive days without a kill-switch
trip, all reconciliation runs within tolerance, preflight passes on 100% of
startups, no SEV-1 incidents, and a daily verified audit chain with zero breaks.

---

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| `live_preflight` FAIL in live mode | `LIVE_TRADING_CONFIRMED` unset or reconciliation blocked | Verify env var; run `traderos db check` / broker reconciliation |
| `operator_session` FAIL | Workflow out of order or completed | Inspect workflow state via `/v1/operator/workflow` |
| Dry-run blocks at `preflight` | Reconciliation incomplete | Confirm the broker account matches recorded state before continuing |
| Dry-run exits 0 but no output | Workflow already completed | Start a new operator session for the pilot |
