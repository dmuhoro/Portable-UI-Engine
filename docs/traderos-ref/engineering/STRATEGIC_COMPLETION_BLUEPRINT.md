# TraderOS — Strategic Completion Blueprint

**Version:** 1.0
**Date:** 2026-07-31
**Author:** Strategic Codebase Audit (engineering intelligence mission)
**Basis:** Full repository audit of 136 source modules, 68 test files, 4 sprints, 4 ADRs, CI/CD, deployment configs, and two independent trust reports.

---

## 0. Executive Summary — The Single Question

> **"If TraderOS were to become a truly production-complete, operationally trusted, commercially valuable trading platform, what is the shortest execution path from today to that state?"**

**Answer:** TraderOS is an **engineering-complete, operationally-unproven, commercially-empty** codebase. The engineering core is genuinely strong — 84% coverage, 832 passing tests, SHA-256 tamper-evident audit chain, manual-reset circuit breaker, preflight go/no-go gate, dependency-direction enforcement, pyright-strict typing, and a clean CI with security jobs. But the operational trust report scores production readiness at **22/100** ("Do not approve for controlled live pilot"), and there is **no user-facing product at all**.

The shortest path is **three compressed programmes, not eleven sprints**:

1. **Programme A — Core Loop Integrity (~4 weeks).** Make the single trading cycle actually correct end-to-end: fix the position-bookkeeping bug, the position-sizing unit bug, the dead kill-switch loss tracking, the non-firing strategies, and the double-preflight. Wire the orphaned analysis layer (regime/breakout/liquidity detection) into the cycle. This is the highest-leverage work in the entire repository: every other programme depends on a correct core loop, and its defects silently violate the Constitution's risk principles today.

2. **Programme B — Operational Trust (~5 weeks).** Resolve all 11 OT findings: live Binance WebSocket transport, durable idempotency + replay, transactional order-event side effects, tick validation, the broken PostgreSQL migration path, API health boundedness, serialized order events, and concurrency safety. Deliverable: a verifiable controlled-pilot deployment that raises the Production Readiness Index from 22 to **70+**.

3. **Programme C — Commercial Surface (~3 weeks).** Build the minimum customer-usable surface: a real-time web dashboard (positions, P&L, orders, kill-switch), one-click paper→live mode with forced confirmation, and a documented user journey. Until this exists, the product has **zero commercial value** regardless of engineering quality.

**Total: ~12 weeks to a production-complete, operationally-trusted, commercially-usable trading platform.** Everything else in this document is decomposition of these three programmes.

---

## 1. Capability Classification — All Layers

Legend: **C** = COMPLETE, **V** = COMPLETE BUT NEEDS VERIFICATION, **P** = PARTIALLY IMPLEMENTED, **M** = MISSING, **O** = OBSOLETE, **D** = DUPLICATED

| # | Layer | Capability | State | Evidence |
|---|-------|-----------|-------|----------|
| 1 | Domain | Entity model (Trade, Position, Signal, Market, Candle, Strategy) | **C** | 25 entity modules, rigorous `Trade` state machine |
| 2 | Domain | Port protocols (Audit, Health, Metrics, Manifest, Broker, Notifier, EventBus) | **C** | `ports.py` fully protocolized; dependency-direction test enforced |
| 3 | Domain | Broker abstraction | **D** | `BrokerAdapter` ABC + `BrokerPort` Protocol, identical 6 methods, never formally linked |
| 4 | Application | Trading orchestration (start/stop/cycle/daemon) | **V** | Fully wired; BACKTEST mode is a stub, market-hours check dead |
| 5 | Application | Order execution (market/limit/fill/idempotency) | **P** | Market orders work; limit/stop have no production call path; idempotency exists only in unwired `OrderEventEngine` |
| 6 | Application | Preflight go/no-go gate | **V** | Wired per-signal; daemon pre-cycle hook is warn-only; executed twice per signal |
| 7 | Application | Broker state reconciliation | **C** | 10 mismatch types, `can_accept_orders` gate, crash recovery, effect-matrix tested |
| 8 | Application | Factory / composition root | **P** | God module; wires only Signal/Trade/Position repos (14 of 17 dead); hand-written SQL dialect forks |
| 9 | Infrastructure | Alpaca live broker | **V** | 6 ABC methods implemented + tests; **no `modify_order`**, no stop/trailing/bracket; OT-009 unverified |
| 10 | Infrastructure | Paper broker | **P** | `get_positions()/get_open_orders()/cancel_order()` are stubs; state not tracked |
| 11 | Infrastructure | Binance historical collection | **V** | Parsing tested; no pagination/retry; registered but always registered as MOCK |
| 12 | Infrastructure | Live market streaming | **P** | `StreamingMarketDataService` complete; **no production `StreamTransport` exists** (OT-001) |
| 13 | Infrastructure | Candle aggregation | **P** | `CandleAggregator` exists; not robust to out-of-order/shutdown (OT-007) |
| 14 | Infrastructure | Risk management | **P** | Kill-switch + circuit breaker wired; sizing unit bug, daily-loss dead, VaR/concentration un-wired |
| 15 | Infrastructure | Portfolio management | **P** | Service exists; **cycle never calls `fill_trade()`** → no positions, cash never decremented |
| 16 | Infrastructure | Strategy framework | **V** | Registry + 3 strategies wired; **params unsupported**, 2 of 3 strategies can never fire |
| 17 | Infrastructure | Signal generation pipeline | **P** | Pipeline exists; cycle fabricates high/low/volume; only 1 strategy can signal |
| 18 | Infrastructure | Backtesting engine | **V** | Complete engine + metrics; orchestrator backtest mode is a stub; synthetic candles |
| 19 | Infrastructure | Paper trading session engine | **P** | `PaperTradingService.process_candle` never invoked; sessions inert |
| 20 | Infrastructure | Knowledge graph | **M** | Service + repos implemented and tested; **never wired** into factory/API/CLI |
| 21 | Infrastructure | Research engine | **D** | `ResearchService` (repo-based) + `ResearchEngine` (raw-SQL), both unwired |
| 22 | Infrastructure | Session analysis / regime / breakout / sweep / swing detection | **M** | All 5 services implemented + tested in isolation; **none wired** into production |
| 23 | Persistence | SQLite | **C** | All 17 repos + observability tables; only 3 repos wired at runtime |
| 24 | Persistence | PostgreSQL | **P** | Only 3 of 17 repos; **migration path broken** (conn.execute on psycopg2); v004 fails on fresh PG |
| 25 | Persistence | Migrations | **P** | 4 migrations, up/down, backend-aware; PG path broken; 6 table-name collisions |
| 26 | Persistence | In-memory repositories | **C** | All 17 implemented; used as fallback + tests |
| 27 | Observability | Audit chain (3 backends) | **C** | SHA-256 content-integrity verification, tested against real PG |
| 28 | Observability | Health service (3 backends) | **C** | Complete, tested |
| 29 | Observability | Metrics | **D** | 4 implementations; `TimingContext` copy-pasted 4×; bogus cycle.duration metric |
| 30 | Observability | Run manifest | **C** | 3 backends, complete |
| 31 | Observability | Structured logging | **C** | JSON formatter wired in API; `StructuredLogger` test-only |
| 32 | Operations | Backup/restore (SQLite + PG) | **C** | gzip + pg_dump/restore, rotation, CLI, timed tests |
| 33 | Operations | Archival/purge | **P** | Hard-DELETE at startup, no archive, silent failures, hardcoded table list |
| 34 | Operations | Runbooks | **P** | 5 runbooks exist; **reference CLI commands that do not exist** — not executable |
| 35 | Security | API auth | **P** | X-API-Key; **optional by default** (open API if unset); non-constant-time compare |
| 36 | Security | Secrets management | **P** | `SecretRotator` + `EnvSecretProvider` implemented; **never wired** |
| 37 | Security | Dependency audit + bandit | **C** | pip-audit + bandit -ll in CI |
| 38 | Security | TLS/CORS | **P** | SSL only if keyfiles provided; CORS `*` default |
| 39 | Governance | Constitution, MEP, ADRs | **C** | 4 ADRs + Constitution + MEP; version/tag drift (1.0.0/1.1.0/0.3.0) |
| 40 | Governance | Version/release management | **P** | VERSION + CHANGELOG + tag v1.0.0; pyproject says 1.1.0 untagged; no release workflow |
| 41 | API | REST surface | **P** | 10 endpoint groups; no trade placement endpoint, no pagination, no SDK/WebSocket |
| 42 | API | Rate limiting | **P** | In-memory sliding window; single-process only; `/metrics` vs `/v1/metrics` inconsistent |
| 43 | CLI | Command tooling | **P** | 10 command groups; docs/runbooks reference commands that don't exist; no `__main__.py` |
| 44 | CI/CD | Pipeline | **V** | 5 jobs all run; missing black/isort checks, release job, perf regression gate |
| 45 | CI/CD | Docker deployment | **P** | Solid Dockerfile; **docker-compose runs two API containers, no daemon**; no prod PG |
| 46 | CI/CD | Railway/nixpacks | **V** | Configs valid; never verified deployed; `/v1/health` stalls (OT-010) |
| 47 | Testing | Unit/integration/architecture/perf | **C** | 832 passing, 84% coverage, architecture + integration + 3 benchmarks |
| 48 | Recovery | Crash recovery / drills | **C** | `recover_from_crash()`, reconciliation drills, operational-recovery tests |
| 49 | Live Trading | Live data transport | **M** | **No Binance WebSocket transport** (OT-001) — release blocker |
| 50 | Live Trading | Durable idempotency/replay | **M** | In-memory `_seen_events`/`ReplayRecorder` lost on restart (OT-002) — release blocker |
| 51 | Live Trading | Atomic order-event side effects | **M** | No transaction/outbox/rollback (OT-003) — release blocker |
| 52 | Commercial UX | Web dashboard / UI | **M** | Design contract only (`.ai/context/12_ui-context.md`); **nothing to click** |
| 53 | Commercial UX | Onboarding / user accounts | **M** | None |
| 54 | Commercial UX | SDK / hosted service | **M** | None |

---

## 2. Everything Already Finished

These are durable assets. **Do not rebuild them. Do not refactor them for their own sake.**

- **Audit integrity (all 3 backends)** — SHA-256 canonical serialization, content-integrity `verify_chain()`, 6-field mutation tests, multi-seed PYTHONHASHSEED determinism.
- **Broker state reconciliation** — 10-mismatch detection engine, KillSwitch wiring, 10×6 effect matrix (~63 assertions), TOCTOU-protected preflight.
- **Preflight go/no-go gate** — audit-chain + reconciliation freshness + kill-switch + live-confirmation, wired into factory and cycle.
- **Risk primitives** — manual-reset circuit breaker (ADR-007), consecutive-failure kill switch, WP-7.1 verification suite.
- **Domain entity model** — rigorous `Trade` state machine, value objects, position/signal/market/candle entities.
- **Architecture enforcement** — AST dependency-direction checker with committed breaking fixture.
- **SQLite persistence** — 17 repositories, 4 migrations, backup/restore with rotation, WAL + busy_timeout.
- **Observability services** — audit/health/metrics/manifest across InMemory/SQLite/Postgres; Prometheus `/metrics`; JSON structured logging.
- **Backup/restore** — SQLite gzip + `pg_dump`/`pg_restore`, CLI commands, timed SLO tests, operational-recovery drills.
- **CI/CD** — 5-job pipeline (lint, typecheck, test+coverage, pip-audit+bandit, docker push to GHCR).
- **Test infrastructure** — 832 passing tests at 84% coverage; architecture + integration + performance suites; 10-hook pre-commit.
- **Detection service logic** — regime/breakout/sweep/swing/liquidity/session-analysis algorithms all implemented and unit-tested (they just aren't wired).
- **Governance** — Constitution, MEP, 4 ADRs, operations runbooks, controlled-pilot parameters.

**Bottom line:** ~80% of the *engineering intellectual capital* is done and solid. The remaining work is **wiring, correctness, operational proof, and commercial surface** — not invention.

---

## 3. Everything Duplicated

| # | Duplication | Locations | Cost / Risk |
|---|-------------|-----------|-------------|
| D1 | Kill-switch | `RiskService` (risk_service.py) + `PersistentKillSwitch` (reconciliation_service.py) | Two sources of truth for circuit-open state |
| D2 | Research engine | `ResearchService` (repo-based) + `ResearchEngine` (raw-SQL in domain/research/) | Same workflow twice; both unwired |
| D3 | Broker contract | `BrokerAdapter` ABC + `BrokerPort` Protocol | Dead protocol; two contracts to keep in sync |
| D4 | Metrics implementation | 4 × (`MetricsService`, SQLite, Postgres, Prometheus) | Same `TimingContext` copy-pasted 4× |
| D5 | Market-data store | legacy `market_data` table (pandas) vs `candles` table (repo) | Two stores never reconciled |
| D6 | Pub/sub | `InMemoryEventBus` (events.py) + `InMemoryMessageQueue` (message_queue.py) | Two event systems |
| D7 | Strategy storage | `strategies` table + `strategy_registry` table + in-memory registry | Triplicated; split-brain |
| D8 | Notifications | `NotifierPort`→`WebhookNotifier` vs `NotificationService` built-in channels | Two delivery paths |
| D9 | Correlation | `CorrelationService.compute_correlation` + `DeviationAnalysisService.compute_corridor` | Same math twice |
| D10 | Max-drawdown | `BacktestingService.compute_metrics` + `RiskService.compute_max_drawdown` | Same math twice |
| D11 | Inline SMA/ATR | `BacktestingService.run` re-implements `AnalysisService` | Indicator drift risk |
| D12 | Trade pipeline | `CycleExecutor.run` + `PaperTradingService.process_candle` | Signal→risk→size→place duplicated |
| D13 | Doc trees | `docs/adr/` vs `docs/decisions/`, `docs/sprints/` vs `sprints/`, `runbooks/` vs `docs/runbooks/` | Confusion; stale copies |

**Consolidation rule:** do NOT build "one true implementation" by abstraction surgery. Kill the dead side (the one with zero production references) and keep the live side. Only D1, D4, and D7 are worth active consolidation (they touch production paths).

---

## 4. Everything Obsolete

| # | Module | Why obsolete |
|---|--------|--------------|
| O1 | `infrastructure/collectors/yfinance_collector.py` | `fetch_historical()` always returns `[]`; never registered |
| O2 | `infrastructure/database/db_manager.py` (`DatabaseManager`) | Legacy pandas persistence; only test consumers; superseded by repos |
| O3 | `domain/research/research_engine.py` | Superseded by repo-based `ResearchService`; test-only |
| O4 | `infrastructure/data/` | Empty package (dead directory) |
| O5 | `infrastructure/visualization.py` | Test-only; matplotlib exports are not a product surface |
| O6 | `BrokerPort` Protocol | Dead duplicate of `BrokerAdapter` ABC |
| O7 | `EventBus = EventBusPort` alias | Backward-compat cruft |
| O8 | `MarketHoursEngine` | Dead stub; `_is_market_hours()` always True, never called |
| O9 | `DaemonController._drain_open_orders()` | Empty body, never called |
| O10 | `infrastructure/logging/StructuredLogger` | Test-only; JSON formatter is the real logger |
| O11 | `configs/settings.yaml` branding | "Market Intelligence Platform v0.1.0" — stale identity |

**Action:** O1–O5, O6–O10 should be deleted or explicitly marked `# DEPRECATED`. This is pure simplification with zero risk (all are test-isolated).

---

## 5. Architectural Hot Spots

| # | Hot spot | Location | Consequence |
|---|----------|----------|-------------|
| H1 | **God method** — one 275-line method does data-fetch, indicators, strategy, preflight, risk, sizing, order, bookkeeping, metrics, events, notifications | `CycleExecutor.run()` | Every bug below traces to this. Untestable as a unit. |
| H2 | **God composition root** — 50+ imports, hardcoded knowledge of every infrastructure class, hand-written SQL dialect forks | `factory.py` | Wiring drift: 14 repos + 8 services never injected. |
| H3 | **Orchestrator god-dataclass** — 15+ concrete dependencies, manually constructs CycleExecutor/DaemonController | `orchestrator.py` | Duplicates composition; cannot be constructed by tests without 15 mocks. |
| H4 | **Kill-switch in the wrong module** — risk concept lives in reconciliation service | `reconciliation_service.py` | D1 root cause. |
| H5 | **Broker adapter in wrong layer** — `PaperBrokerAdapter` in domain/service, `AlpacaBrokerAdapter` in infrastructure | paper_trading_service.py, alpaca_broker.py | Layer ambiguity; two broker contracts. |
| H6 | **Migration/repo schema collision** — v001 creates 6 tables with column sets that differ from repo `CREATE TABLE IF NOT EXISTS` | migrations/v001 vs sqlite repos | Latent runtime failure the moment repos are wired. |
| H7 | **PG migration path broken** — `conn.execute()` on psycopg2 connections (no such method); v004 ALTERs a table that doesn't exist yet | migration_manager.py | `DATABASE_URL` set → crash. Confirmed. |
| H8 | **Split-brain strategy storage** — 3 stores, 2 synced via raw SQL | factory._sync_strategy_registry | API/CLI/daemon can disagree on strategies. |
| H9 | **Startup purge without safety** — hard DELETE on 5 tables at every build, silent failures, no retention config | `_get_db` → `purge_old_entries` | Data loss risk in production. |

---

## 6. Production Blockers (verified)

Ordered by severity. **All of these must be resolved in Programme B.**

| # | Blocker | Evidence | Severity |
|---|---------|----------|----------|
| PB1 | **No live market transport** — `StreamTransport` is a protocol with zero implementations; no Binance WebSocket | OT-001 | Critical — release blocker |
| PB2 | **Durability of idempotency/replay** — `_seen_events` + `ReplayRecorder` in-memory; restart loses duplicate-fill protection | OT-002 | Critical — release blocker |
| PB3 | **Non-atomic order side effects** — trade mutated before persist; failure leaves state/stream/audit/portfolio inconsistent | OT-003 | Critical — release blocker |
| PB4 | **Invalid tick acceptance** — NaN/neg/zero/millisecond-vs-second timestamps accepted | OT-004 | Critical — release blocker |
| PB5 | **PostgreSQL migration path broken** — confirmed `conn.execute` AttributeError on psycopg2 | H7 (verified) | Critical — release blocker |
| PB6 | **API `/v1/health` stalls** — synchronous orchestrator build in request path, no timeout (reproduced 45s+) | OT-010 | High — release blocker |
| PB7 | **Concurrent order events race** — dedup + transition not serialized | OT-006 | High |
| PB8 | **Candle aggregation fragility** — out-of-order/shutdown; final candle never flushed | OT-007 | High |
| PB9 | **Unbounded memory** — `ReplayRecorder.records`, `_latencies` grow forever | OT-008 | High |
| PB10 | **`ACKNOWLEDGED` omitted from in-memory open-order query** — acked live orders treated as closed | OT-005 | High (already fixed in SQLite/domain? verify memory) |
| PB11 | **Alpaca modify path unverified** — `cancel_replace` semantic mismatch risk | OT-009 | High |
| PB12 | **docker-compose deploys two API instances, no daemon** — trading loop never deployed | Audit (verified) | High |
| PB13 | **Health endpoint + metrics timers bogus** — `cycle.duration` measures ~0ms; `cycles.completed` counts per-strategy | Audit (verified) | Medium |

---

## 7. Commercial Blockers

| # | Blocker | Impact | Effort to resolve |
|---|---------|--------|-------------------|
| CB1 | **No web UI / dashboard** | A customer has nothing to click; zero commercial surface | ~2-3 weeks (Programme C) |
| CB2 | **No onboarding / user accounts / multi-tenancy** | Cannot onboard any user safely | ~1 week (post-MVP) |
| CB3 | **No SDK / no programmatic consumer** | Cannot integrate into external tooling | ~1 week (post-MVP) |
| CB4 | **No paper→live upgrade path in UI** | Live mode gated only by env var; no product flow | Included in C |
| CB5 | **No reporting / performance analytics UI** | Backtest/equity results only via matplotlib PNGs | Included in C |
| CB6 | **No pricing / packaging / deployment story** | No SaaS model, no multi-tenant isolation | Deferred (post-trust) |

**Strategic truth:** the Commercial Readiness is 0% not because the product is far from done, but because **no product surface has been started**. It is the cheapest 3 weeks of value in the roadmap.

---

## 8. Verification Blockers

| # | Blocker | Effect |
|---|---------|--------|
| VB1 | **No live-credential verification** — no authenticated Binance/Alpaca test anywhere | Cannot claim live capability |
| VB2 | **PG repository tests absent** — 3 PG repos + migrations never tested | PG layer is speculative |
| VB3 | **No deployment verification** — Railway/nixpacks never deployed; health stalls | Deploy story unproven |
| VB4 | **Runbooks reference non-existent CLI commands** — cannot execute any drill | Operations docs are fiction |
| VB5 | **OT-010 health stall blocks full-suite CI runs** in some environments | CI reliability |
| VB6 | **Version/tag drift** — 1.0.0 vs 1.1.0 vs 0.3.0 | Release provenance unreliable |
| VB7 | **`black`/`isort` not enforced in CI** (only local `make ci`) | Formatting regressions slip through |

---

## 9. Operational Trust Blockers

| # | Blocker | Effect |
|---|---------|--------|
| TB1 | **No durable event journal** | Cannot reconstruct state after restart |
| TB2 | **No outbox/transaction boundary** | Cannot guarantee exactly-once portfolio effects |
| TB3 | **No production transport** | Cannot receive live data at all |
| TB4 | **No bounded health/readiness** | Cannot operate a reliable health-checked deployment |
| TB5 | **No concurrency serialization** | Cannot trust broker callbacks under load |
| TB6 | **No retention policy** | Memory/disk grow unboundedly |
| TB7 | **Secret rotation unwired** | Credentials cannot rotate without restart |
| TB8 | **Leader election unwired** | Multi-instance deployment is unsafe |

The Operational Trust Report's **22/100 PRI** is the single most important number in the repository. Programme B is a direct attack on it.

---

## 10. Unnecessary Abstractions

| # | Abstraction | Verdict |
|---|-------------|---------|
| A1 | `BrokerPort` Protocol (vs `BrokerAdapter` ABC) | Delete |
| A2 | `EventBus` alias | Delete |
| A3 | `DataNormalizer.normalize` (sort-only) | Inline/delete |
| A4 | Empty repo ABCs (`LiquidityZoneRepository: pass`, `StrategyEvaluationService`, `MarketDataPort` nominal) | Delete or wire |
| A5 | `StrategyEvaluationService` (never used; cycle uses global registry) | Delete or wire |
| A6 | 4× `TimingContext` | Consolidate to one |
| A7 | `InMemoryMessageQueue` (vs `InMemoryEventBus`) | Delete |
| A8 | `DatabaseManager` (legacy) | Delete |
| A9 | `RedisCache`/`RedisMessageQueue` (no Redis service exists anywhere) | Delete or wire |

**Rule of three:** if a thing has zero production references and only test references, it is dead weight. Delete it. The repo has ~40 modules in this state.

---

## 11. Opportunities to Simplify (highest-leverage first)

1. **Wire, don't abstract.** The detection/analysis/research layer is 90% implemented and 0% wired. The cheapest "new" feature in the repository is *connecting two existing components*.
2. **Delete the dead layer** (Section 4 + 10): removes ~40 modules, dozens of confusing tests, and lets coverage % rise mechanically.
3. **Make the runbooks true** (VB4): fix the CLI surface so documented commands exist — this turns "governance fiction" into "operational truth" with a weekend of work.
4. **One strategy store** (D7/H8): single source of truth for strategies.
5. **One broker contract** (D3/H5): delete `BrokerPort`, promote `BrokerAdapter`, move `PaperBrokerAdapter` into infrastructure.
6. **Unify market-data stores** (D5): `candles` table is the future; drop legacy `market_data` writes.

---

## 12. Completion Matrix — Per Subsystem

| Subsystem | Completion | Notes |
|-----------|-----------|-------|
| Domain entities | 100% | |
| Domain ports/protocols | 100% | One dead protocol |
| Broker state reconciliation | 95% | Fully proven |
| Audit chain | 100% | All 3 backends verified |
| Risk management | 55% | Primitives done; sizing/loss/VaR unwired |
| Portfolio management | 40% | **Position creation broken in cycle** |
| Execution | 55% | Market path works; limit/idempotency/atomicity missing |
| Strategy framework | 60% | Params unsupported; 2/3 strategies dead |
| Signal pipeline | 50% | Fabricated bars; 1 strategy fireable |
| Backtesting | 80% | Engine complete; mode stub; synthetic candles |
| Paper trading | 55% | Broker used; session engine inert |
| Knowledge graph | 50% | Implemented + tested; **unwired** |
| Research | 50% | Duplicated + unwired |
| Analytics (regime/breakout/swing/etc.) | 45% | Implemented + tested; **unwired** |
| Data ingestion (historical) | 60% | Collector exists; always MOCK; no persistence |
| Live market data | 20% | Service complete; **no transport** |
| SQLite persistence | 95% | 17 repos; 3 wired |
| PostgreSQL persistence | 30% | 3 repos; **migration path broken** |
| In-memory persistence | 100% | |
| Observability | 90% | Consolidated but duplicated |
| Operations (backup/restore) | 100% | |
| Security | 45% | Gates exist; auth optional; secrets unwired |
| API | 60% | Surface exists; no trade endpoint; health stalls |
| CLI | 55% | 10 groups; documented commands missing |
| CI/CD | 70% | 5 jobs; missing release/deploy/perf-gate |
| Deployment | 40% | Docker good; compose broken; no prod PG; never deployed |
| Testing | 95% | 832 passing @ 84% |
| Recovery | 90% | Drills proven |
| Live trading | 15% | Transport, durability, atomicity all missing |
| Commercial UX | 0% | Nothing user-facing |
| Governance/docs | 80% | Version drift; doc trees split |

**Blended engineering completion:** ~66%. **Blended product completion:** ~35%.

---

## 13. Production Readiness Matrix

| Pillar | Pre-B | Post-Programme B | Evidence (post-B) |
|--------|-------|-------|----------|
| Deterministic logic + unit tests | 90% | 92% | 864 tests, 83.77% coverage (+51 Programme B tests) |
| Static quality gates | 95% | 98% | ruff 0, pyright 0 on `src/traderos` incl. new modules |
| Security scanning | 80% | 80% | pip-audit, bandit, no committed secrets |
| Broker connectivity | 15% | 30% | Thin Binance transport + fill guards (OT-001/OT-009); **live unverified** |
| Live market data | 10% | 60% | Transport + tick validation + candle robustness tested; **live unverified** |
| Durability/recovery | 25% | 90% | Durable journal + manifest + daemon crash recovery (OT-002) |
| Atomicity | 15% | 80% | Outbox ordering, persist-before-publish (OT-003) |
| Input validation | 30% | 95% | Tick validation, fill guards (OT-004/OT-009) |
| Concurrency safety | 20% | 85% | Thread-safe sqlite + per-trade locks (OT-011/OT-006) |
| API operational behavior | 20% | 85% | `/healthz` + bounded readiness (OT-010) |
| Deployment correctness | 25% | 40% | Postgres migration path fixed (OT-005/H7); compose/deploy unverified |
| **Production Readiness Index** | **22/100** | **≥ 70 (est. 70–76)** | OT report baseline; Programme B matrix + evidence docs |

**Target after Programme B:** PRI ≥ 70. **Status: estimated met (70–76).** The estimate is capped by the two declared, non-fabricated gaps: live Binance connectivity (R-01) and live Alpaca/Postgres behavior (R-02) — both require authenticated network access this sandbox cannot provide. Baselines: 22/100 is the official `OPERATIONAL_TRUST_REPORT.md` score; Programme B closure evidence is `OPERATIONAL_TRUST_MATRIX.md`, `RECOVERY_TRUTH.md`, `FAILURE_INJECTION_REPORT.md`.

---

## 14. Operational Trust Matrix

| Dimension | Pre-B | Post-Programme B | Trust |
|-----------|-------|-------|-------|
| Can receive live data | No (no transport) | Structurally yes (thin transport tested); **live unverified** | Medium |
| Can survive restart | No (in-memory idempotency) | Yes (durable journal + manifest + crash recovery) | High |
| Can guarantee exactly-once effects | No (non-atomic) | Yes (outbox ordering + per-trade serialization) | High |
| Can reject malformed input | Partially | Yes (tick validation + fill guards + malformed counters) | High |
| Can run concurrent broker callbacks | No (unserialized) | Yes (per-trade locks; thread-safe sqlite) | High |
| Can deploy multi-instance safely | No (no leader election wiring) | No (unchanged — out of Programme B scope) | Untrusted |
| Can rotate secrets | No (unwired) | No (unchanged) | Untrusted |
| Can execute ops runbooks | No (commands don't exist) | No (unchanged) | Untrusted |
| Can be monitored in prod | Partially (no dashboards/tracing) | Partially (bounded health + readiness added) | Low |
| Can audit all state changes | Yes (audit chain) | Yes (audit chain) | High |
| Can reconcile broker truth | Yes (10-mismatch engine) | Yes + post-crash reconciliation trigger | High |
| Can back up/restore | Yes (proven) | Yes (proven) | High |

**Trust posture:** "High-trust core primitives + high-trust recovery, live-touch path structurally implemented but not yet live-verified." The audit/reconciliation/backup primitives remain genuinely trustworthy; Programme B raised durability, atomicity, input validation, concurrency, and API operation to trusted. The two remaining untrusted touchpoints are **live connectivity** and **deployment**, both declared in the risk register.

---

## 15. Commercial Readiness Matrix

| Dimension | State | Readiness |
|-----------|-------|-----------|
| User-facing product | None | 0% |
| Onboarding | None | 0% |
| Accounts/multi-tenancy | None | 0% |
| SDK/API for consumers | REST-only, no trade endpoint | 10% |
| Reporting/dashboards | matplotlib PNGs | 5% |
| Live→paper upgrade path | env-var only | 10% |
| Pricing/deployment model | None | 0% |
| **Commercial Readiness Index** | **0/100** | Pre-product |

**Commercial truth:** TraderOS is currently a *platform engine*, not a *product*. That is fine for a research-first thesis, but it must be named honestly: everything so far is the engine; the product is entirely Programme C.

---

## 16. Pareto Analysis — The 20/80 Cut

The repository's remaining value is dominated by a handful of items. Ranked by combined leverage:

| Rank | Work item | % of remaining value |
|------|-----------|---------------------|
| 1 | **Fix the core trading loop correctness** (positions, sizing, loss-tracking, strategies, double-preflight) | ~25% |
| 2 | **Resolve OT-001/002/003** (transport, durability, atomicity) — the three critical release blockers | ~25% |
| 3 | **Fix PostgreSQL path + API health** (PB5/PB6) — production claim blockers | ~10% |
| 4 | **Build the web dashboard** (positions/P&L/orders/kill-switch) | ~10% |
| 5 | **Wire the orphaned analysis layer** (regime/breakout/liquidity) into the cycle | ~8% |
| 6 | **Delete dead weight + consolidate duplicates** | ~5% |
| 7 | **Live-credential verification + controlled pilot** | ~7% |
| 8 | **Runbooks/CLI truth** (make documented commands exist) | ~4% |
| 9 | **Versioning/release workflow** | ~3% |
| 10 | **Everything else** (reporting, SDK, multi-tenancy, dashboards) | ~3% |

**Pareto rule:** items 1–4 ≈ 70% of remaining value for ~6 weeks of work. Items 5–8 add ~24% for ~3 more weeks. That is the 90/10 cut — 12 weeks to ~94% of the value.

---

## 17. Task Ranking — Full List

Scored 1–5 (5 = highest). **Leverage** = engineering×business×risk combined; **PRI** = production-readiness-index points.

| Task | Eng. | Bus. | Risk↓ | Time | Dep. weight | PRI | DoD |
|------|:---:|:---:|:---:|:---:|:---:|:---:|-----|
| Fix position bookkeeping in cycle (`fill_trade` path) | 5 | 4 | 5 | 1d | 0 | +8 | Position created, cash decremented; test proves |
| Fix position sizing unit bug (dollars→shares) | 5 | 4 | 5 | 0.5d | 0 | +4 | qty is shares; test proves |
| Wire daily-loss tracking (`record_realized_pnl` on close) | 4 | 4 | 5 | 1d | 0 | +5 | Kill-switch trips on daily limit; test |
| Make all 3 strategies fireable (compute sma_50, bb) | 4 | 3 | 3 | 1d | 0 | +3 | All 3 strategies produce signals; test |
| Remove double-preflight + fix cycle metrics | 3 | 2 | 3 | 0.5d | 0 | +2 | Preflight called once; timers correct |
| Wire regime/breakout/liquidity detection into cycle | 4 | 3 | 4 | 2d | cycle-fix | +3 | Signals gated on regime; tests |
| Refactor `CycleExecutor.run()` into phases | 4 | 3 | 4 | 3d | 0 | +2 | run() < 80 lines; phase functions unit-tested |
| **Live Binance WebSocket transport** (OT-001) | 5 | 5 | 5 | 5d | 0 | +10 | Authenticated transport behind `StreamTransport`; failover tested |
| **Durable idempotency + replay** (OT-002) | 5 | 5 | 5 | 4d | transport | +8 | Kill/restart loses nothing; exactly-once test |
| **Transactional/outbox order effects** (OT-003) | 5 | 5 | 5 | 4d | durable | +8 | Side-effect failure → consistent retry; test |
| Tick validation + timestamp normalization (OT-004) | 4 | 4 | 5 | 2d | 0 | +5 | NaN/neg/ms-ts rejected; tests |
| Serialize order events (OT-006) | 4 | 4 | 4 | 2d | durable | +3 | Concurrent identical events → one accepted; test |
| Candle aggregation robustness (OT-007) | 3 | 3 | 4 | 2d | 0 | +2 | Out-of-order + flush; tests |
| Memory retention policy (OT-008) | 3 | 2 | 4 | 1d | 0 | +2 | Bounded recorder; soak test |
| **Fix PostgreSQL migration path** (PB5/H7) | 5 | 4 | 5 | 2d | 0 | +6 | `DATABASE_URL` boots; migrations run on PG; tests |
| Fix v004 order on fresh PG + schema collisions (H6) | 4 | 3 | 4 | 2d | PG-fix | +4 | Fresh PG full schema correct |
| **API health boundedness** (OT-010/PB6) | 4 | 4 | 4 | 1d | 0 | +4 | /health < 1s cold; degraded readiness; test |
| PG repo tests (3 repos + observability) | 4 | 3 | 3 | 2d | PG-fix | +3 | PG contract tests pass |
| **Web dashboard MVP** (positions/P&L/orders/kill-switch) | 5 | 5 | 4 | 12d | live-trust | — | Live-updating dashboard; auth'd |
| Paper→live upgrade flow in UI | 4 | 5 | 4 | 2d | dashboard | — | Forced confirmation; audit trail |
| Onboarding/accounts (MVP scope) | 4 | 5 | 3 | 3d | dashboard | — | First-run flow; session auth |
| Make runbooks executable (CLI truth) | 4 | 3 | 4 | 2d | 0 | +2 | Every documented command exists; drill passes |
| Delete dead weight + consolidate duplicates | 3 | 1 | 3 | 2d | 0 | +1 | 40 modules removed; 832→≥780 tests green |
| Versioning + release workflow | 3 | 3 | 3 | 1d | 0 | +1 | Single version source; tagged release; CI gate |
| Live-credential verification + controlled pilot | 5 | 5 | 5 | 3d | transport | +6 | Sandbox order + live tick verified; pilot report |
| docker-compose fix (daemon service + prod PG) | 4 | 4 | 4 | 1d | PG-fix | +2 | daemon + api + postgres stack boots |
| black/isort CI + perf regression gate | 2 | 1 | 2 | 0.5d | 0 | +1 | CI fails on format/perf regression |

---

## 18. Compressed Execution Programmes

**Do NOT preserve sprint structure.** Merge aggressively. Three programmes, strictly sequential, each with a hard Definition of Done that gates the next.

### Programme A — Core Loop Integrity
**Goal:** the single trading cycle is *correct* — every subsystem it touches does what its tests claim.
**Duration:** ~4 weeks | **PRI delta:** 22 → ~35 | **Blocker:** none (pure correctness)
**Status: COMPLETED 2026-07-31** — all A1 correctness defects closed (D1–D6, D8, D9; D7 reclassified by-design). Evidence: `docs/engineering/CORE_LOOP_TRUTH.md`, `docs/engineering/CORE_LOOP_EVIDENCE.md`. Machine truth: **843 tests passed, 84.63% coverage, ruff/pyright clean.**

| Work package | Tasks |
|--------------|-------|
| A1 — Loop correctness | Position bookkeeping; sizing unit; daily-loss wiring; strategy params; double-preflight; cycle metrics |
| A2 — Analysis layer wired | Regime/breakout/liquidity/session detection into the cycle; signal gating |
| A3 — Refactor for testability | Decompose `CycleExecutor.run()` into phase functions with per-phase tests |
| A4 — Hygiene sweep | Delete dead weight (Section 4+10); consolidate D1/D4/D7; unify strategy store; fix version drift; make runbooks true |

**Why it matters:** Every downstream programme builds on a correct core loop. Today the loop has verified correctness defects (positions never created, sizing in dollars, 2/3 strategies dead) that would corrupt live accounts. Fixing these is the highest-risk-reduction work available.

**Programme A outcome (2026-07-31):** defects fixed and pinned by 11 new invariant regression tests in `tests/test_core_loop_invariants.py` (I1/I2/I3/I5/I6/I8/I9 + D1–D6/D8/D9). Suite 832 → **843 passed**, coverage 84.42% → **84.63%**, ruff/pyright clean. Remaining Programme A backlog — A2 (wire analysis layer into the cycle), A3 (decompose `run()` into phase functions), A4 (hygiene sweep) — carries forward; note the Code Freeze scoped Programme A to *correctness only*, which is complete.
**Dependencies:** none. **Expected leverage:** unlocks B and C; +25 PRI-equivalent trust.

### Programme B — Operational Trust
**Goal:** PRI ≥ 70; controlled pilot approvable; PostgreSQL and API claims are true.
**Duration:** ~5 weeks | **PRI delta:** ~35 → 70+ | **Depends on:** A
**Status (2026-07-31):** **IN PROGRESS — implementation complete.** 11/11 OT findings closed as code + regression tests + evidence; PRI ≥ 70 estimated. Remaining for full closure: authenticated live Binance connectivity, live Alpaca/Postgres drill, and deployment/compose verification (declared risks R-01/R-02, not fabricated).

| Work package | Tasks | Status |
|--------------|-------|--------|
| B1 — Live data path | Binance WebSocket transport (OT-001); tick validation (OT-004); candle robustness (OT-007); retention (OT-008) | ✅ Code+tests (OT-001 live connectivity = R-01) |
| B2 — Durable lifecycle | Durable idempotency + replay (OT-002); outbox/transactional side effects (OT-003); event serialization (OT-006); ACKNOWLEDGED open-order parity | ✅ Code+tests |
| B3 — Postgres + API truth | Fix migration path (PB5/H7); fresh-PG schema (H6); PG repo tests; API health boundedness (OT-010) | ✅ Code+tests (live PG = R-02) |
| B4 — Deployment + verification | docker-compose daemon/PG stack; live-credential sandbox verification; controlled pilot run; Alpaca modify contract tests (OT-009) | ⏳ Deployment + live verification remain (R-01/R-02) |

**Why it matters:** This is the entire difference between "22/100 — do not approve" and "production-complete, operationally trusted."
**Dependencies:** A (correct loop to operate), B1 before B2 (data first).
**Expected leverage:** +45 PRI; first credible live-mode claim. **Evidence:** `OPERATIONAL_TRUST_MATRIX.md`, `RECOVERY_TRUTH.md`, `FAILURE_INJECTION_REPORT.md`, `docs/sprints/SPRINT_13.md`.

### Programme C — Commercial Surface
**Goal:** a human being can sign in and run the platform.
**Duration:** ~3 weeks | **PRI delta:** 70 → 75 (ops) | **Depends on:** B
**Commercial Readiness delta:** 0 → ~60
**Status (2026-08-01):** **IN PROGRESS.** Restructured into enforced-workflow-first work packages (C1 operator API, C2 enforced workflow, C3 strategy catalog, C4 session reports, C5 dashboard design, C6 productization) — full record in `docs/sprints/SPRINT_14.md`, authoritative design in `docs/engineering/FINISH_LINE_DASHBOARD.md`.

| Work package | Tasks |
|--------------|-------|
| C1 — Dashboard MVP | Real-time positions/P&L/orders/kill-switch/health; WebSocket or SSE feed |
| C2 — Mode & onboarding | Paper→live flow with forced confirmation + audit trail; first-run onboarding |
| C3 — Reporting | Equity curve, drawdown, per-strategy performance from backtest/paper data |

**Why it matters:** without this the product has zero commercial value no matter how trustworthy the engine is.
**Dependencies:** B (won't demo a 22/100 engine).

### Post-MVP (not in the 12-week path)
SDK, multi-tenancy, RBAC, pricing/billing, alerting integrations, advanced reporting, hosted service.

---

## 19. Final Answer

> **Shortest execution path from today to production-complete, operationally-trusted, commercially-valuable TraderOS:**

1. **Programme A (4 weeks):** make the trading loop correct and wire the analysis layer. No external dependencies; highest risk-reduction per hour in the repo.
2. **Programme B (5 weeks):** defeat the 11 operational-trust findings — live transport, durable lifecycle, Postgres truth, bounded API, verifiable pilot. Raise PRI 22→70+.
3. **Programme C (3 weeks):** ship the dashboard, onboarding, and paper→live flow. Take Commercial Readiness from 0→60.

**~12 weeks total.** After that: an operating, trustworthy, demoable trading platform — and the entire long tail (SDK, tenants, billing, dashboards) becomes incremental work on a real product instead of finishing an incomplete one.

**One-line rule for the team:** *finish the loop, prove the loop, show the loop.* Nothing else moves the business needle.

---

## 20. Verification of Key Audit Claims

| Claim | Verified? |
|-------|-----------|
| PG migration path calls `conn.execute()` on psycopg2 (no such method) | ✅ `migration_manager.py:20,28,62,89,103` |
| Cycle executor never creates Position via `fill_trade()` | ✅ `cycle_executor.py:197-213` — `open_trade`/`update_trade` only |
| Sizing returns dollars used as qty | ✅ `portfolio_service.size_position` returns `cash*allocation` |
| docker-compose runs two API instances, no daemon | ✅ compose services `traderos` + `traderos-api` share entrypoint |
| 832 tests / 84% coverage | ✅ fixed by Programme A: **843 passed, 84.63%** (`python3 -m pytest -q -p no:randomly`); evidence in `CORE_LOOP_EVIDENCE.md` §4 |
| ruff clean | ✅ `ruff check src/traderos/` — All checks passed |
| OT-001…OT-011 | ✅ from OPERATIONAL_TRUST_REPORT (22/100) |
| No `modify_order` anywhere | ✅ grep across BrokerAdapter/Port/Alpaca/Paper/RateLimited |
| `StreamTransport` has no implementations | ✅ protocol-only in `market_stream.py` |

---

## 21. Engineering Closure Pass Delta (2026-08-02)

Since the §20 audit-claim table (Programme A baseline) the repository advanced materially. Updated reality:

| Claim (2026-08-02) | Value |
|---|---|
| Tests | **1266 passed / 1266** |
| Coverage | **93.62 %** |
| `ruff check .` (whole repo) | **0 errors** (was src-only) |
| `pip-audit` | 0 known vulnerabilities |
| `bandit -r src/traderos -lll` | 0 High |
| `/metrics` | 200 (prometheus-client added) |
| Architecture | ports & adapters clean, no violations, pyright strict-clean |

**Programme status:** A (core correctness) ✅ · B (operational trust, OT-001…OT-011) ✅ code+tests with declared live unknowns R-01/R-02 · C (commercial surface) ✅ shipped · D (release/closure) **in progress**.

**Forward view:** the next programme is **Live Pilot Enablement** (`CLOSURE-12 → 15/16 → 08` per `ENGINEERING_CLOSURE_AUDIT.md` §10). Remaining open items are the live-connectivity drills, replay wiring, runbook parity, and the controlled pilot — none are speculative; each is tracked with a priority in the closure backlog.
