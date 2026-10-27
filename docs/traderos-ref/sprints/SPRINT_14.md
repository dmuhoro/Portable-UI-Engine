# Sprint 14 — Programme C: Commercial Surface

**Period:** 2026-08-01
**Objective:** Turn TraderOS into something a human being can sign in to and operate — the operator workflow (C2), the operator REST surface (C1), the strategy catalog (C3), session reports (C4), the Finish Line Dashboard design doc (C5), and repo productization (C6). Sequential layers, each gated by the full quality gate before the next.

**Reference docs:** `docs/engineering/FINISH_LINE_DASHBOARD.md` (authoritative C5 doc), `docs/engineering/STRATEGIC_COMPLETION_BLUEPRINT.md` §Programme C, `docs/engineering/MASTER_EXECUTION_PROGRAMME.md` §26.

---

## Layer Register

| Layer | WP | Deliverable | Gate |
|-------|----|------------|------|
| 1 | C2 | Pure `OperatorWorkflow` state machine (10 canonical steps, strict ordering, re-run of current step, `WorkflowError`) + strategy params/template framework | 911 tests / 84.49% cov / pyright 0 / ruff clean |
| 2 | C3 | `v006` migration (workflow tables + legacy strategy reconcile), SQLite/in-memory workflow repos, strategy repo with template, factory wiring, execution gate consuming only enabled strategies | same gate |
| 3 | C2 | `OperatorSessionService`: every step gated on a real check (preflight, broker + reconciliation, feeds, paper sessions, catalog ranking, promotion, live confirmation, shutdown); transitions persisted | 924 tests / 84.67% cov |
| 4 | C1 | Operator REST endpoints (positions, orders, trades, portfolio, equity-curve, pnl, kill-switch, preflight, readiness, workflow, strategies, lifecycle actions) | 943 tests / 85.0% cov |
| 5 | C4 | `SessionReportService` (JSON + Markdown exports) + `/reports/session` endpoints | 948 tests / 85.12% cov |
| 6 | C5 | `docs/engineering/FINISH_LINE_DASHBOARD.md` | n/a (doc) |
| 7 | C6 | README productization (features, dashboard curl examples, docs table) | n/a (doc) |

## Work Completed

### C2 — Enforced operator workflow
- **`OperatorWorkflow`** (`domain/services/operator_workflow.py`): 10-step canonical order; `can_advance_to()` allows only the immediate next step or a re-run of the current one; `advance()` raises `WorkflowError` on any out-of-order attempt; `start` and `session_report` are non-repeatable; reaching `session_report` completes the workflow.
- **`OperatorSessionService`** (`domain/services/operator_session.py`): `perform(step, actor, **context)` runs a `_gate_*` check and only advances on a passing gate. Failing gates return `ok=False` (operator re-runs the step). Every successful transition is persisted via `OperatorWorkflowRepository`.

### C3 — Strategy catalog
- **`StrategyCatalogService`** (`domain/services/strategy_management.py`): seeded built-ins, versioned `Strategy` rows, lifecycle (`draft → active → disabled/archived`, single `promoted`), `clone`, `compare(names)` backtest ranking, `review(name)`.
- The execution loop consumes only enabled strategies via the `enabled_strategies` callable bound in the orchestrator; cycle execution is source-gated in `cycle_executor.py`.

### C1 — Operator API
- **`register_operator_endpoints`** (`interfaces/api/operator.py`), registered from `interfaces/api/server.py` under `/v1`: read panels (positions/orders/trades/portfolio/equity-curve/pnl/kill-switch/preflight/readiness/workflow/strategies/review) and write actions (kill-switch engage/disengage, workflow advance, strategy create/compare/lifecycle/clone).
- Error semantics: 400 (unknown step / lifecycle rule), 404 (unknown strategy), 409 (out-of-order workflow), 501 (capability not configured).
- Removed the superseded registry-based `GET /strategies` endpoints from the server.

### C4 — Session reports
- **`SessionReportService`** (`domain/services/session_report.py`): immutable `SessionReport` snapshot (session id, workflow state, transition log, portfolio, positions, trades, catalog + promoted strategy, risk, duration) with `to_dict`/`to_json`/`to_markdown`.
- Endpoints: `GET /v1/reports/session` (JSON) and `?fmt=markdown`.

### C5 / C6 — Documentation and productization
- **`docs/engineering/FINISH_LINE_DASHBOARD.md`** (new): authoritative design of the operator surface — workflow semantics table, endpoint/panel mapping, error semantics, catalog lifecycle, report contract, Definition of Done.
- **`README.md`**: features (catalog, workflow, dashboard API, session reports), operator curl examples, documentation table.

## Key Files Created/Modified

### Source
| File | Change |
|------|--------|
| `src/traderos/domain/services/operator_workflow.py` | New: state machine + `WorkflowTransition`/`WorkflowError` |
| `src/traderos/domain/services/operator_session.py` | New: gated session lifecycle |
| `src/traderos/domain/services/strategy_management.py` | New: catalog (seeding, lifecycle, compare, review) |
| `src/traderos/domain/services/session_report.py` | New: C4 report generation + exports |
| `src/traderos/domain/services/risk_service.py` | `KillSwitch.engage`/`disengage` |
| `src/traderos/domain/services/strategy_framework.py` | `StrategyRegistry.unregister` |
| `src/traderos/infrastructure/database/migrations/v006_operator_surface.py` | New: workflow tables + legacy strategy reconcile |
| `src/traderos/infrastructure/repositories/sqlite/workflows.py` | New: SQLite workflow repo (`WorkflowTransition` round-trip) |
| `src/traderos/application/factory.py` + `orchestrator.py` | `operator_session` wiring; `enabled_strategies` binding fix |
| `src/traderos/application/cycle_executor.py` | Source-gated `enabled_strategies` callable |
| `src/traderos/interfaces/api/operator.py` | New: all C1 operator/strategy/report endpoints |
| `src/traderos/interfaces/api/server.py` | Register operator router; removed superseded `/strategies` |

### Tests
| File | Tests |
|------|-------|
| `tests/test_operator_workflow.py` (new) | state machine, in-memory + SQLite repos, v006 migration |
| `tests/test_strategy_management.py` (new) | seeding, lifecycle, compare/ranking, review |
| `tests/test_cycle_gate.py` (new) | source gating, empty source, unknown template |
| `tests/test_operator_session.py` (new) | 13 gated-step tests incl. full session |
| `tests/test_operator_api.py` (new) | 19 endpoint tests (panels, workflow, strategies, kill switch) |
| `tests/test_session_report.py` (new) | 5 service + endpoint tests |
| `tests/test_preflight_execution_integration.py` | `_DummyStrategy` register/unregister hygiene |

### Docs
| File | Purpose |
|------|---------|
| `docs/engineering/FINISH_LINE_DASHBOARD.md` (new) | Authoritative C5 operator-surface doc |
| `README.md` | Productized entry point (features, examples, docs table) |
| `docs/sprints/SPRINT_14.md` | This sprint record |

## Machine Truth

| Metric | Value |
|--------|-------|
| Total tests | **948 passing, 0 failures** (`python3 -m pytest -q -p no:randomly`, excluding integration/DB/performance suites) |
| New tests added | **~120** across the six Programme C test files |
| Coverage | **85.12%** (threshold 70% exceeded) |
| Ruff | 0 errors on `src/traderos` + new tests |
| Pyright | 0 errors on `src/traderos` |
| Regressions | 0 (Programme B suite untouched and green) |

**Known open items (carried forward, not blockers):**
- `_sync_strategy_registry` in `application/factory.py` re-inserts registry names as `active` on rebuild, which can re-activate a disabled catalog strategy — revisit when persistence of disabled state is wired.
- WebSocket/SSE live feed for the dashboard is deferred (rest endpoints are the source of truth for now).
