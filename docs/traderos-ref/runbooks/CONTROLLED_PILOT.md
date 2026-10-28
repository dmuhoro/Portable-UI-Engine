# Controlled Pilot Parameters — TraderOS Live Trading

## Purpose

Define the operational envelope within which live trading is permitted during the controlled pilot phase.  These parameters are enforced by `PreflightService` at startup and monitored continuously.

---

## Preflight Gate (Mandatory)

All checks must pass before a live trading session begins:

| Check | Mechanism | Failure Action |
|-------|-----------|----------------|
| Audit chain integrity | `AuditPort.verify_chain()` | Block startup |
| Broker reconciliation | `BrokerStateReconciliationService.can_accept_orders` | Block startup |
| Kill-switch state | `KillSwitch.can_trade()` | Block startup |
| Live-mode confirmation | `LIVE_TRADING_CONFIRMED=true` env var | Block startup |

---

## Risk Parameters

| Parameter | Pilot Value | Rationale |
|-----------|-------------|-----------|
| `MAX_POSITION_SIZE` | 0.10 (10% of portfolio) | Conservative — half of standard 0.25 |
| `MAX_LEVERAGE` | 1.0 (no leverage) | Cash-only during pilot |
| `MAX_DRAWDOWN_LIMIT` | 0.10 (10%) | Tight — 50% of standard 0.20 |
| `MAX_POSITIONS_TOTAL` | 3 | Limit surface area |
| `DAILY_LOSS_LIMIT` | 5% of account equity | Hard stop on daily loss |
| `MAX_CONSECUTIVE_FAILURES` | 3 | Trip kill switch early |

---

## Rate Limiting (Flagged — Disabled by Default)

| Parameter | Default | Pilot Value | Env Var |
|-----------|---------|-------------|---------|
| Broker calls/second | 10 | 5 | `BROKER_RATE_LIMIT_MAX` |
| Rate limit window | 1s | 1s | `BROKER_RATE_LIMIT_WINDOW` |
| Rate limit enabled | false | true | `BROKER_RATE_LIMIT_ENABLED` |

---

## Order-Size Guardrails (Enforced in Front of the Broker)

The broker is wrapped in a `GuardrailedBroker` that rejects any order whose
size breaches the configured envelope before it reaches the exchange. A
rejected order returns `status="rejected"` and counts toward the kill-switch
failure counter like any other broker failure.

| Parameter | Pilot Value | Env Var |
|-----------|-------------|---------|
| Guardrail enabled | true | `TRADEROS_ORDER_GUARDRAIL_ENABLED` |
| Minimum order quantity | 1.0 shares | `TRADEROS_MIN_ORDER_QTY` |
| Maximum order notional | 500 USD | `TRADEROS_MAX_ORDER_NOTIONAL` |

Rationale for pilot values:

- **Minimum quantity 1.0** — the pilot trades whole-share US equities via
  Alpaca, which rejects fractional/dust quantities. Any signal that sizes to
  less than one share is refused instead of being silently rounded to 0.
- **Maximum notional 500 USD** — caps the blast radius of a single order while
  the strategy stack is still being validated live.

---

## Reconciliation

| Parameter | Value | Notes |
|-----------|-------|-------|
| Startup reconciliation | Required | Blocks order acceptance until first pass |
| Periodic reconciliation | Every cycle | Runs after each trading cycle |
| Kill-switch on recon failure | Yes | `record_failure()` per error |

---

## Exit Criteria for Pilot

The controlled pilot ends when:

1. 30 consecutive days without a kill-switch trip
2. All reconciliation runs pass within tolerance (< 0.1% discrepancy)
3. Preflight gate passes 100% of startup attempts
4. No SEV-1 incidents
5. Audit chain verified daily with zero breaks
