# Sprint 17 — Pilot Readiness: Order Surface, Service Wiring, Security Hardening, Pilot CLI

**Period:** 2026-08-01
**Objective:** Close the remaining Programme C product gaps ahead of the controlled live pilot — WP-2 the full broker order surface (stop/trailing/modify), WP-3 backtest + regime/breakout analysis + trade evidence wiring, WP-4 order-size guardrails and CORS hardening, WP-5 the pilot readiness CLI and dry-run rehearsal — each gated by the full suite, then the merge cascade feature → develop → main.

**Reference docs:** `docs/runbooks/CONTROLLED_PILOT.md`, `docs/runbooks/PILOT_READINESS.md`, `docs/engineering/STRATEGIC_COMPLETION_BLUEPRINT.md`.

---

## Work Package Register

| WP | Deliverable | Gate |
|----|-------------|------|
| WP-2 | Order surface: `place_stop_order`/`place_trailing_stop_order`/`modify_order` on the broker ABC, Alpaca + paper + rate-limiter adapters | `tests/test_paper_trading_service.py` + `tests/test_alpaca_broker.py` green |
| WP-3 | BACKTEST mode runs real backtests, regime/breakout analysis per cycle, trade-evidence knowledge-graph + research hooks | `tests/test_cycle_executor.py` + `tests/test_orchestrator.py` green |
| WP-4 | `GuardrailedBroker` order-size guardrails + deny-all CORS default | `tests/test_order_guardrails.py` (9) green |
| WP-5 | `traderos pilot readiness` / `pilot dry-run` + readiness runbook | `tests/test_cli.py` (4 new) green |
| Final | Full suite, lint/typecheck, sprint record + CHANGELOG, merge cascade + push | **1060 passed, 1 skipped**; ruff/pyright clean |

## Work Completed

### WP-2 — Order surface
- **`domain/adapters/broker_adapter.py`** — ABC extended with `place_stop_order` (market-stop), `place_trailing_stop_order` (trailing percent), and `modify_order` (qty replacement). Domain-facing contract for the missing broker capabilities.
- **`infrastructure/alpaca_broker.py`** — all three implemented via Alpaca `replace_order_by_id`: qty coerced to `int`, prices rounded to broker tick precision. Uses a local `client` var + local `req_cls = _ReplaceOrderRequest` so pyright is satisfied that the client is non-`None` at call time.
- **`domain/services/paper_trading_service.py`** — `PaperBrokerAdapter` upgraded to a stateful adapter (`_positions`, `_open_orders`, `_order_seq`, `_apply_fill`, `_record_order`): stop/trailing stop orders become real limit orders with trigger guards `market_price is not None and (...)`, fills update positions and record order lifecycle. Previously paper stops were near no-ops.
- **`domain/services/execution_service.py`** — `OrderStatus.MODIFIED = "modified"` for replace flows.
- **`infrastructure/broker_rate_limiter.py`** — rate-checked pass-throughs for the three new broker methods so the limiter stays in front of every order path.

### WP-3 — Service wiring
- **BACKTEST mode** — enabled strategies now run through `BacktestingService.run` on `data_ingestion.fetch_candles(limit=200)` (fallback `synthetic_candles(count=50)`); per-strategy `run_manifest` records plus `backtest.complete` events; a missing service records `ServiceError("BacktestingService is not available in BACKTEST mode")` in `errors` instead of crashing the cycle.
- **`RegimeDetectionService.detect`** + **`BreakoutDetectionService.analyze`** run each cycle; results published as `cycle.analysis` events (`payload: {market_id, regime, breakout_events}` — the Event attribute is `payload`, not `data`).
- **Trade evidence** — `_record_trade_evidence` post-fill hook creates knowledge-graph nodes (market `label=market:{id}`/`type=market`, strategy `type=strategy`) with `trades_in`/`has_strategy` edges and `research.create_observation(symbol=str(market_id), tags=[strategy_name, "trade"])`.
- **Orchestrator/factory** — `knowledge_graph`/`research` dataclass fields; orchestrator passes `backtest`, `knowledge_graph`, `research` into `CycleExecutor`; factory builds in-memory `KnowledgeGraphService` + `ResearchService` (all five research repos) and wraps the broker as `GuardrailedBroker(RateLimitedBroker(broker))`.

### WP-4 — Security hardening
- **`infrastructure/order_guardrail.py`** — `GuardrailedBroker`: enabled by default (`TRADEROS_ORDER_GUARDRAIL_ENABLED`, default true); rejects `qty < TRADEROS_MIN_ORDER_QTY` (default 1.0) or `notional > TRADEROS_MAX_ORDER_NOTIONAL` (default 500.0, `0` disables). A rejection returns `FillResult(False, 0.0, 0.0, quantity, "rejected", reason)` so it counts against the kill-switch failure counter like any broker failure. All order methods guarded (market/limit/stop/trailing/modify-qty); reads and cancel pass through.
- **CORS hardening** (`interfaces/api/server.py`) — default `CORS_ORIGINS=""` → no allowed origins (deny-all browser CORS); explicit `*` or a comma-separated list re-enables.
- **`docs/runbooks/CONTROLLED_PILOT.md`** — new **Order-Size Guardrails** section with pilot values and rationale.
- **`tests/test_order_guardrails.py`** (new, 9 tests) — min qty, max notional, passthrough, no-price skip, limit/stop/trailing, modify-qty, reads/cancel, disabled toggle, env-var load.

### WP-5 — Pilot readiness
- **`interfaces/cli/main.py`** — `pilot` subcommand: `traderos pilot readiness` runs `orch.live_readiness.check()` (human table or `--json`), exits 0 only when ready; `traderos pilot dry-run` rehearses the operator workflow end to end with `dry_run=True`, driving the state machine from its current step, auto-skipping `strategy_promotion` (operator decision), and stopping at the first failing gate. Exits non-zero on any failure. `--mode {paper,live,backtest}` accepted on each subcommand.
- **`tests/test_cli.py`** — 4 new tests: readiness text/JSON, dry-run text/JSON.
- **`docs/runbooks/PILOT_READINESS.md`** (new) — readiness gate table, workflow dry-run rehearsal flow, six go/no-go gates, controlled-live procedure, exit criteria, troubleshooting.

## Key Files Created/Modified

### Source
| File | Change |
|------|--------|
| `src/traderos/infrastructure/order_guardrail.py` (new) | `GuardrailedBroker` order-size guardrails |
| `src/traderos/domain/adapters/broker_adapter.py` | ABC: `place_stop_order`, `place_trailing_stop_order`, `modify_order` |
| `src/traderos/infrastructure/alpaca_broker.py` | stop/trailing/modify via `replace_order_by_id` |
| `src/traderos/domain/services/paper_trading_service.py` | stateful paper adapter, real stop/trailing behavior |
| `src/traderos/infrastructure/broker_rate_limiter.py` | rate-checked pass-throughs for the new order methods |
| `src/traderos/domain/services/execution_service.py` | `OrderStatus.MODIFIED` |
| `src/traderos/application/cycle_executor.py` | BACKTEST mode, `cycle.analysis` events, `_record_trade_evidence` |
| `src/traderos/application/orchestrator.py` | `knowledge_graph`/`research` fields, backtest pass-through |
| `src/traderos/application/factory.py` | `GuardrailedBroker(RateLimitedBroker(broker))`, KG + research services |
| `src/traderos/interfaces/api/server.py` | deny-all CORS default |
| `src/traderos/interfaces/cli/main.py` | `pilot` subcommand (`readiness` / `dry-run`) |

### Tests
| File | Tests |
|------|-------|
| `tests/test_order_guardrails.py` (new) | 9 — guardrail semantics |
| `tests/test_cli.py` | +4 — pilot readiness/dry-run text + JSON |

### Docs
| File | Purpose |
|------|---------|
| `docs/runbooks/PILOT_READINESS.md` (new) | Pilot readiness gate + dry-run rehearsal runbook |
| `docs/runbooks/CONTROLLED_PILOT.md` | Order-Size Guardrails section |
| `docs/sprints/SPRINT_17.md` (new) | This sprint record |
| `CHANGELOG.md` | New `[Unreleased] — Sprint 17` section |

## Machine Truth

| Metric | Value |
|--------|-------|
| Total tests | **1060 passing, 1 skipped** (full suite) |
| Coverage | **86.80%** (threshold 70% exceeded) |
| Ruff | 0 errors on all changed files |
| Pyright | 0 errors on all changed files |

**Known open items (carried forward, not blockers):**
- Live Binance/Alpaca execution still requires real credentials; `pilot readiness` / `pilot dry-run` / `/v1/live/check` provide the pre-flight verification path without them.
