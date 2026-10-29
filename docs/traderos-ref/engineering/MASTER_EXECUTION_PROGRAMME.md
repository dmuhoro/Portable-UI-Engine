# TraderOS v1 Master Execution Programme

> **Version**: 1.0
> **Status**: Active
> **Authority**: Operational — derived from the TraderOS v1 Engineering Constitution
> **Supersedes**: All prior sprint plans, roadmaps, and task lists
> **Horizon**: 12 months (Months 1–12)
> **Review Cadence**: Weekly (tactical), Monthly (architectural), Quarterly (strategic)

---

## Table of Contents

1. Executive Programme Summary
2. Current State vs Target State Analysis
3. Architecture Transition Strategy
4. Capability Map
5. Capability Dependency Graph
6. Programme Structure
7. Epics
8. Workstreams
9. Milestones
10. Sprint Plan
11. Work Package Templates
12. Work Breakdown Structure
13. Critical Path Analysis
14. Engineering Priority Matrix
15. Risk Register
16. ADR Implementation Schedule
17. Testing & Verification Strategy
18. Quality Gates
19. Code Review Workflow
20. Definition of Ready
21. Definition of Done
22. Documentation Workflow
23. Release Strategy
24. Portfolio Readiness Checklist
25. Hiring Readiness Checklist
26. Engineering Dashboard
27. Weekly Engineering Operating Rhythm
28. Monthly Architecture Review Process
29. Quarterly Technical Debt Review
30. Final 12-Month Execution Timeline

---

## 1 Executive Programme Summary

### Programme Mandate

This programme exists to transform the TraderOS repository from a v0.2 research prototype into a v1 production-grade Trading Intelligence Platform, as defined by the Engineering Constitution. Every task, epic, and milestone in this programme is traceable to the Constitution, the Engineering Audit findings, or both.

### Programme Scope

| Dimension | In Scope | Out of Scope |
|-----------|----------|--------------|
| Architecture | Full 4-layer architecture, event bus, repository pattern | Microservices extraction (deferred to v2) |
| Data | Crypto + Forex OHLCV | Equities, futures, options (deferred to v1.1) |
| Trading | Research → Backtest → Paper → Live pipeline | HFT, colocation, DMA |
| Intelligence | Knowledge graph, research workflow | ML model training (consume only) |
| Deployment | Docker, docker-compose, CI/CD | Kubernetes orchestration (deferred) |
| Users | Single-user (CLI-focused) | Multi-tenant, RBAC (deferred to v1.1) |

### Guiding Constraints

1. **Architecture before features** — No feature is built on a foundation that has not been stabilized.
2. **Test before trust** — No code merges without tests. Coverage target: 90%+.
3. **Research first** — No trading execution capability exists without research pipeline completeness.
4. **Debt budget** — 20% of every sprint is mandatory debt reduction.
5. **Evidence over opinion** — Every architectural decision requires an ADR.

### Key Numbers

| Metric | Current (v0.2) | Target (v1) |
|--------|----------------|-------------|
| Test count | 7 | 500+ |
| Test coverage | ~5% | 90%+ |
| Source lines | ~1,709 | 15,000–25,000 |
| CI/CD | None | Full pipeline |
| Docker | None | Multi-container |
| Architecture layers | Flat modules | 4-layer bounded contexts |
| Domain entities | 12 tables (flat) | 30+ entities with inheritance |
| ADRs | 1 | 12 |
| Commands | 3 CLIs | 1 unified CLI (20+ commands) |
| Integrations | 2 APIs | 4+ (incl. paper broker) |

### Constitutional Traceability Key

Every element in this programme is tagged with its source:

- `[C:n]` = Constitution Section n
- `[C:Pn]` = Constitution Principle n
- `[C:Sn.n]` = Constitution Subsystem n.n
- `[A:n]` = Audit Finding n
- `[CAP:n]` = Capability n (see Section 4)

---

## 2 Current State vs Target State Analysis

### 2.1 Architecture Layer Coverage

| Layer | Current State | Target State | Gap |
|-------|---------------|--------------|-----|
| Interface | 3 standalone CLIs, no API, no dashboard | Unified CLI + REST API + WebSocket + Dashboard | Complete rewrite required |
| Application | `main.py` orchestrator (procedural) | Orchestrator class + Scheduler + Event Bus + Workers | New subsystem |
| Domain | Flat modules, mixed concerns | 8 bounded contexts with interfaces | Restructuring + interface extraction |
| Infrastructure | SQLite (direct access from domain code) | SQLite/PostgreSQL via Repository pattern | Repository extraction, migration framework |

### 2.2 Architecture Violations (from Audit)

| Violation | Severity | Current Location | Target |
|-----------|----------|-----------------|--------|
| Domain code imports infrastructure | Critical | `analysis_engine/`, `liquidity_engine/`, `backtesting/`, `risk_engine/` import `database.db_manager` directly | Repository interfaces; domain code never imports DB |
| Single orchestrator with mixed concerns | High | `main.py` does data collection, analysis, visualization, logging | Separate Orchestrator + pipeline stages |
| No interface boundaries | High | CLIs import domain modules directly | CLI → Application Service → Domain |
| Module-level mutable state | Medium | `Config` singleton is mutable | Frozen config after init |
| No event system | Medium | Engines call each other directly | Event bus for all cross-engine communication |
| Visualization depends on domain knowledge | Low | `visualization/charts.py` knows OHLC structure | Visualization consumes standardized data contracts |

### 2.3 Testing Gap

| Metric | Current | Target | Work Required |
|--------|---------|--------|---------------|
| Test framework | `unittest` | `pytest` | Migration |
| Test count | 7 | 500+ | New tests for all modules |
| Coverage | ~5% | 90%+ | Comprehensive coverage |
| CI integration | None | PR gate | GitHub Actions workflow |
| Test isolation | Uses real SQLite | In-memory repositories | Fake/Mock infrastructure |
| Performance tests | None | Critical path benchmarks | New test suite |

### 2.4 Engineering Infrastructure Gap

| Capability | Current | Target |
|------------|---------|--------|
| Linting | None (code has mixed style) | `ruff` (strict) + pre-commit |
| Formatting | None | `black` + `isort` |
| Type checking | Manual | `pyright` (strict) |
| CI/CD | None | GitHub Actions (lint → typecheck → test → build) |
| Docker | None | `Dockerfile` + `docker-compose.yml` |
| Makefile | None | `test`, `lint`, `typecheck`, `build`, `clean` targets |
| Pre-commit | None | All checks automated |

### 2.5 Domain Model Gap

| Entity | Current State | Target State |
|--------|---------------|--------------|
| Market | Implicit (symbol strings) | First-class entity with lifecycle |
| Candle | Dict/list in code | Typed dataclass with validation |
| Indicator | Array in code | Typed entity with parameters |
| Signal | Implicit (dict) | First-class entity with provenance |
| Trade | Not modeled | Full trade lifecycle entity |
| Portfolio | Not modeled | Aggregate root |
| RiskProfile | Not modeled | Configurable entity |
| Hypothesis | DB table, no validation | Entity with lifecycle state machine |
| Experiment | Not modeled | First-class entity |
| Lesson | DB table, no validation | Entity with actionability tracking |
| KnowledgeNode | Not modeled | Graph entity with embeddings |

---

## 3 Architecture Transition Strategy

### 3.1 Migration Principles

1. **No big bang rewrites**. Every refactoring keeps the system runnable.
2. **Strangler pattern**. New architecture grows alongside old code; old code is deleted only when new code covers its functionality.
3. **Testable at every step**. After each migration step, tests pass.
4. **Backward compatibility preserved** during transition. CLI interfaces remain stable during internal rewrites.

### 3.2 Transition Phases

```
Phase 0: Foundation (Months 1–2)
  ┌─────────────────────────────────────────────────────────────┐
  │ Old: main.py + flat modules + direct DB access              │
  │ New (additive): Makefile, CI/CD, Docker, pre-commit,        │
  │                 pytest migration, in-memory repositories     │
  │ Status: Both coexist. Old runs via main.py. New infra       │
  │         validates on every CI run.                           │
  └─────────────────────────────────────────────────────────────┘

Phase 1: Package Restructure (Months 2–4)
  ┌─────────────────────────────────────────────────────────────┐
  │ Old: analysis_engine/, liquidity_engine/, etc. (flat)       │
  │ New: traderos/domain/, traderos/infrastructure/,            │
  │       traderos/application/, traderos/interfaces/            │
  │ Action: Create new package structure. Move modules one      │
  │         by one. Each move extracts interfaces.               │
  │ Status: Dual directory structure during migration.           │
  │         Old imports redirect to new package.                 │
  └─────────────────────────────────────────────────────────────┘

Phase 2: Interface Extraction (Months 3–6)
  ┌─────────────────────────────────────────────────────────────┐
  │ Action: Extract Repository interfaces. Extract Engine       │
  │         interfaces. Remove direct DB access from domain.    │
  │ Status: Old code still works, but health checks start       │
  │         flagging modules that still violate architecture.    │
  │         Architecture tests enforce new rules.               │
  └─────────────────────────────────────────────────────────────┘

Phase 3: Event Bus Integration (Months 5–8)
  ┌─────────────────────────────────────────────────────────────┐
  │ Action: Implement event bus. Wire engines to publish and    │
  │         subscribe to events. Replace direct engine calls.   │
  │ Status: Orchestrator can run in event-driven mode or        │
  │         direct mode. Direct mode is deprecated.             │
  └─────────────────────────────────────────────────────────────┘

Phase 4: Engine Modernization (Months 6–12)
  ┌─────────────────────────────────────────────────────────────┐
  │ Action: Rewire each engine to new interfaces. Add missing   │
  │         engines (Signal, Portfolio, Execution). Retire old  │
  │         flat modules as their replacements are verified.    │
  │ Status: Old modules deleted. All code in new architecture.  │
  └─────────────────────────────────────────────────────────────┘

Phase 5: Platform Completion (Months 9–12)
  ┌─────────────────────────────────────────────────────────────┐
  │ Action: API, Dashboard, SDK. Multi-user. Production infra.  │
  │ Status: v1 complete.                                        │
  └─────────────────────────────────────────────────────────────┘
```

### 3.3 File Migration Strategy

Each legacy file follows this lifecycle:

```
Step 1: Create interface in traderos/domain/
Step 2: Create implementation in traderos/infrastructure/
Step 3: Create adapter that wraps old module behind new interface
Step 4: Update tests to use new interface (with in-memory impl)
Step 5: Switch production code to new interface
Step 6: Archive old module after deprecation period
```

### 3.4 Data Migration Strategy

Database schema changes follow this pattern:

```
Step 1: Create new tables alongside old tables (new suffix)
Step 2: Dual-write to old and new tables
Step 3: Backfill new tables from old data
Step 4: Verify parity between old and new
Step 5: Switch reads to new tables
Step 6: Remove old tables
```

---

## 4 Capability Map

```
CAP-01: Engineering Infrastructure ──────── Foundation
  ├─ CAP-01.01: CI/CD Pipeline
  ├─ CAP-01.02: Developer Tooling (lint, typecheck, format)
  ├─ CAP-01.03: Docker Development Environment
  ├─ CAP-01.04: Test Framework & Coverage
  └─ CAP-01.05: Build Automation (Makefile)

CAP-02: Architecture Framework ──────────── Architecture
  ├─ CAP-02.01: Package Structure (4-layer)
  ├─ CAP-02.02: Repository Pattern
  ├─ CAP-02.03: Event Bus
  ├─ CAP-02.04: Configuration System v2
  ├─ CAP-02.05: Error Handling Framework
  ├─ CAP-02.06: Structured Logging
  └─ CAP-02.07: Domain Entity Model

CAP-03: Market Data Platform ────────────── Data
  ├─ CAP-03.01: Collector Interface & Implementations
  ├─ CAP-03.02: Data Normalization Pipeline
  ├─ CAP-03.03: Data Validation
  ├─ CAP-03.04: Time-Series Storage
  └─ CAP-03.05: Data Export/Import

CAP-04: Analysis Platform ───────────────── Analysis
  ├─ CAP-04.01: Indicator Computation Engine
  ├─ CAP-04.02: Regime Detection
  ├─ CAP-04.03: Feature Extraction
  ├─ CAP-04.04: Correlation Analysis
  └─ CAP-04.05: Analysis Pipeline Orchestration

CAP-05: Liquidity Platform ──────────────── Liquidity
  ├─ CAP-05.01: Swing Detection
  ├─ CAP-05.02: Liquidity Zone Mapping
  ├─ CAP-05.03: Sweep Detection
  ├─ CAP-05.04: Breakout Detection
  └─ CAP-05.05: Session Analysis

CAP-06: Research Platform ───────────────── Research
  ├─ CAP-06.01: O-H-T-R-L Workflow
  ├─ CAP-06.02: Hypothesis Management
  ├─ CAP-06.03: Experiment Configuration & Replay
  ├─ CAP-06.04: Research Search
  └─ CAP-06.05: Auto-Observation Generation

CAP-07: Knowledge Graph ─────────────────── Knowledge
  ├─ CAP-07.01: Graph Data Model
  ├─ CAP-07.02: Graph CRUD Operations
  ├─ CAP-07.03: Graph Traversal & Query
  └─ CAP-07.04: Graph Visualization

CAP-08: Strategy Platform ───────────────── Strategy
  ├─ CAP-08.01: Strategy Definition Framework
  ├─ CAP-08.02: Strategy Registry
  ├─ CAP-08.03: Strategy Versioning
  ├─ CAP-08.04: Strategy Parameter Management
  └─ CAP-08.05: 3+ Starter Strategies (Ported)

CAP-09: Signal Platform ─────────────────── Signal
  ├─ CAP-09.01: Signal Generation
  ├─ CAP-09.02: Signal Validation
  ├─ CAP-09.03: Signal Deduplication
  └─ CAP-09.04: Signal Provenance

CAP-10: Risk Platform ───────────────────── Risk
  ├─ CAP-10.01: Position Sizing (3+ methods)
  ├─ CAP-10.02: Exposure Validation
  ├─ CAP-10.03: Drawdown Monitoring
  ├─ CAP-10.04: Correlation Check
  ├─ CAP-10.05: Kill Switch
  └─ CAP-10.06: Risk Profile Management

CAP-11: Portfolio Platform ──────────────── Portfolio
  ├─ CAP-11.01: Portfolio State Management
  ├─ CAP-11.02: Trade Lifecycle
  ├─ CAP-11.03: Position Aggregation
  ├─ CAP-11.04: Mark-to-Market
  └─ CAP-11.05: Performance Analytics

CAP-12: Execution Platform ──────────────── Execution
  ├─ CAP-12.01: Order Lifecycle State Machine
  ├─ CAP-12.02: Order Management
  ├─ CAP-12.03: Broker Adapter Interface
  ├─ CAP-12.04: Paper Trading Adapter
  ├─ CAP-12.05: Live Broker Adapter
  └─ CAP-12.06: Execution Analytics

CAP-13: Backtesting Platform ────────────── Backtest
  ├─ CAP-13.01: Historical Simulation Engine
  ├─ CAP-13.02: Cost Modeling (commission, spread, slippage)
  ├─ CAP-13.03: Performance Metrics
  ├─ CAP-13.04: Walk-Forward Optimization
  └─ CAP-13.05: Results Comparison

CAP-14: Paper Trading Platform ──────────── Paper
  ├─ CAP-14.01: Session Management
  ├─ CAP-14.02: Live Data Integration
  ├─ CAP-14.03: Fill Simulation
  ├─ CAP-14.04: Backtest-Deviation Analysis
  └─ CAP-14.05: Paper Portfolio Tracking

CAP-15: Visualization Platform ──────────── Visuals
  ├─ CAP-15.01: Price Chart Generation
  ├─ CAP-15.02: Liquidity Map Visualization
  ├─ CAP-15.03: Correlation Heatmap
  ├─ CAP-15.04: Equity Curve & Performance Charts
  ├─ CAP-15.05: Knowledge Graph Visualization
  └─ CAP-15.06: Multi-Format Export

CAP-16: Interface Platform ──────────────── Interfaces
  ├─ CAP-16.01: Unified CLI
  ├─ CAP-16.02: REST API
  ├─ CAP-16.03: WebSocket Stream
  ├─ CAP-16.04: Dashboard (Web)
  └─ CAP-16.05: Python SDK

CAP-17: Notification Platform ───────────── Notifications
  ├─ CAP-17.01: Notification Framework
  ├─ CAP-17.02: Multi-Channel Delivery
  ├─ CAP-17.03: Rate Limiting & Aggregation
  └─ CAP-17.04: Alert Rules

CAP-18: Observability Platform ──────────── Observability
  ├─ CAP-18.01: Structured Logging Infrastructure
  ├─ CAP-18.02: Health Check Endpoint
  ├─ CAP-18.03: Metrics Collection
  ├─ CAP-18.04: Run Manifests
  └─ CAP-18.05: Audit Trail
```

---

## 5 Capability Dependency Graph

```
LAYER 1: FOUNDATION (no dependencies)
  CAP-01: Engineering Infrastructure
  CAP-02: Architecture Framework

LAYER 2: DATA (depends on Layer 1)
  CAP-03: Market Data Platform ──── depends on ──── CAP-01, CAP-02
  CAP-18: Observability Platform ── depends on ──── CAP-01, CAP-02

LAYER 3: ANALYSIS (depends on Layer 2)
  CAP-04: Analysis Platform ─────── depends on ──── CAP-03
  CAP-05: Liquidity Platform ────── depends on ──── CAP-03

LAYER 4: RESEARCH (depends on Layer 1, 2)
  CAP-06: Research Platform ─────── depends on ──── CAP-02, CAP-18
  CAP-07: Knowledge Graph ───────── depends on ──── CAP-06

LAYER 5: STRATEGY & SIGNAL (depends on Layers 3, 4)
  CAP-08: Strategy Platform ─────── depends on ──── CAP-04, CAP-05
  CAP-09: Signal Platform ───────── depends on ──── CAP-08, CAP-04, CAP-05

LAYER 6: RISK & PORTFOLIO (depends on Layer 5)
  CAP-10: Risk Platform ─────────── depends on ──── CAP-09, CAP-11
  CAP-11: Portfolio Platform ────── depends on ──── CAP-03

LAYER 7: EXECUTION (depends on Layer 6)
  CAP-12: Execution Platform ────── depends on ──── CAP-10, CAP-11, CAP-03

LAYER 8: BACKTEST & PAPER (depends on Layers 5, 6, 7)
  CAP-13: Backtesting Platform ──── depends on ──── CAP-08, CAP-10, CAP-11
  CAP-14: Paper Trading Platform ── depends on ──── CAP-12, CAP-13, CAP-03

LAYER 9: PRESENTATION (depends on all above)
  CAP-15: Visualization Platform ── depends on ──── CAP-03, CAP-04, CAP-05, CAP-07, CAP-11
  CAP-16: Interface Platform ────── depends on ──── All CAPs above
  CAP-17: Notification Platform ─── depends on ──── CAP-18, CAP-02

Visual representation:

Layer 1:  CAP-01  CAP-02
              \      /
Layer 2:    CAP-03  CAP-18
             /  \      |
Layer 3: CAP-04 CAP-05 |
            \    /     |
Layer 4:  CAP-06 CAP-07
              \    /
Layer 5:    CAP-08 CAP-09
              /    \
Layer 6: CAP-10 --- CAP-11
              \    /
Layer 7:    CAP-12
              |
Layer 8: CAP-13 --- CAP-14
              |
Layer 9: CAP-15 CAP-16 CAP-17
```

---

## 6 Programme Structure

### 6.1 Governance

```
Programme Sponsor:      CTO / Founding Engineer
Programme Manager:      Engineering Manager (rotating)
Architecture Authority: Architecture Review Board (all engineers)
Quality Authority:      QA Lead / Test Champion
```

### 6.2 Delivery Structure

```
Programme
  ├── Workstream 1: Foundation (CAP-01, CAP-02)
  │     ├── Epic 1.1: Engineering Infrastructure
  │     └── Epic 1.2: Architecture Framework
  │
  ├── Workstream 2: Data & Analysis (CAP-03, CAP-04, CAP-05)
  │     ├── Epic 2.1: Market Data Platform
  │     ├── Epic 2.2: Analysis Platform
  │     └── Epic 2.3: Liquidity Platform
  │
  ├── Workstream 3: Research & Knowledge (CAP-06, CAP-07)
  │     ├── Epic 3.1: Research Platform
  │     └── Epic 3.2: Knowledge Graph
  │
  ├── Workstream 4: Trading Core (CAP-08, CAP-09, CAP-10, CAP-11)
  │     ├── Epic 4.1: Strategy Platform
  │     ├── Epic 4.2: Signal Platform
  │     ├── Epic 4.3: Risk Platform
  │     └── Epic 4.4: Portfolio Platform
  │
  ├── Workstream 5: Execution & Simulation (CAP-12, CAP-13, CAP-14)
  │     ├── Epic 5.1: Execution Platform
  │     ├── Epic 5.2: Backtesting Platform
  │     └── Epic 5.3: Paper Trading Platform
  │
  └── Workstream 6: Platform (CAP-15, CAP-16, CAP-17, CAP-18)
        ├── Epic 6.1: Visualization Platform
        ├── Epic 6.2: Interface Platform
        ├── Epic 6.3: Notification Platform
        └── Epic 6.4: Observability Platform
```

### 6.3 Team Structure

```
Sprint Team (4–6 engineers):
  ┌──────────────────────────────────────────────────┐
  │  Workstream assignments per sprint               │
  │                                                  │
  │  Engineer 1-2: Workstream 1 (Foundation)         │
  │  Engineer 2-3: Workstream 2 (Data & Analysis)    │
  │  Engineer 1:   Workstream 3 (Research)           │
  │  All:          Integration & stabilization       │
  └──────────────────────────────────────────────────┘
```

---

## 7 Epics

### Epic 1.1: Engineering Infrastructure

| Field | Value |
|-------|-------|
| **Objective** | Establish the development toolchain, CI/CD pipeline, containerization, and test infrastructure required for all future engineering work. |
| **Business value** | Eliminates manual processes, reduces integration risk, enables rapid iteration. Every hour invested here saves 10+ hours during later epics. |
| **Engineering value** | Provides immediate feedback on code quality. Enforces standards mechanically. Creates developer environment that "just works." |
| **Architecture value** | Foundation layer. Without this, no architecture can be enforced. |
| **Dependencies** | None. This is the starting point. |
| **Deliverables** | Makefile, `.github/workflows/ci.yml`, `Dockerfile`, `docker-compose.yml`, `.pre-commit-config.yaml`, `pyproject.toml`, `pytest` configuration, coverage configuration, `ruff` configuration, `pyright` configuration |
| **Acceptance criteria** | `make test` passes in < 30s. `make lint` passes with 0 errors. `make typecheck` passes with 0 errors. `make docker-dev` starts the system. CI pipeline runs on every push. Pre-commit hooks block violations. |
| **Definition of success** | A new engineer can clone, run `make setup && make test`, and be productive in < 5 minutes. |
| **Risks** | Tool version conflicts (Python 3.11+ compatibility). CI minute costs. |
| **Estimated effort** | 2–3 sprints (3–4 engineer-weeks) |
| **Hiring impact** | None (foundational, done by existing team) |
| **Source** | [C:10], [C:8.18], [A:CI/CD gap], [A:Docker gap], [A:Testing gap], [CAP-01] |
| **Constitution principles** | P6 (Test Before Trust), P7 (Architecture Before Features), P8 (Automation over Manual) |

---

### Epic 1.2: Architecture Framework

| Field | Value |
|-------|-------|
| **Objective** | Implement the 4-layer architecture, repository pattern, event bus, configuration v2, and domain entity models that form the structural backbone of the platform. |
| **Business value** | Enables all future feature development to occur within a consistent, maintainable architecture. Prevents the architectural debt that plagued v0.2. |
| **Engineering value** | Clear boundaries make code easier to write, test, and reason about. Repository pattern enables in-memory testing without databases. |
| **Architecture value** | This is the architecture. Without this epic, v1 cannot exist. |
| **Dependencies** | Epic 1.1 (engineering infra must be in place to validate architecture) |
| **Deliverables** | `traderos/` namespace package, `traderos/domain/`, `traderos/infrastructure/`, `traderos/application/`, `traderos/interfaces/` packages, `Repository` base classes for all entities, `InMemoryRepository` implementations, `EventBus` class with typed events, `Config` v2 (validated, frozen, schema-based), domain entity dataclasses, exception hierarchy per context, architecture tests that enforce dependency direction |
| **Acceptance criteria** | Architecture tests verify no infrastructure imports in domain code. All domain entities have `InMemoryRepository` implementations. Event bus passes integration tests with 3+ event types. Config v2 validates on load and is immutable after init. Error hierarchy covers all bounded contexts. |
| **Definition of success** | A new bounded context can be added by creating `traderos/domain/new_context/` with zero infrastructure imports, and it is immediately testable with in-memory repositories. |
| **Risks** | Scope creep (trying to build perfect architecture instead of working architecture). Over-engineering before understanding actual requirements. |
| **Estimated effort** | 3–4 sprints (4–6 engineer-weeks) |
| **Hiring impact** | Low — establishes patterns that new hires will learn |
| **Source** | [C:4], [C:5], [C:6], [C:7], [C:8.18], [A:Architecture violations], [CAP-02] |
| **Constitution principles** | P1 (Research First — architecture enables research), P5 (Small Composable Systems), P7 (Architecture Before Features) |

---

### Epic 2.1: Market Data Platform

| Field | Value |
|-------|-------|
| **Objective** | Transform the ad-hoc data collection into a robust, tested, observable Market Data Engine. |
| **Business value** | Reliable market data is the foundation of all research and trading. Without this, nothing else works. |
| **Engineering value** | Establishes the collector interface pattern used by all future data sources. Validates the repository pattern with real data. |
| **Architecture value** | Data layer — feeds all upstream engines. |
| **Dependencies** | Epic 1.2 (repository pattern, domain entities) |
| **Deliverables** | `MarketDataRepository` interface + SQLite implementation + InMemory implementation, `DataCollector` ABC with `BinanceCollector`, `YFinanceCollector`, `MockDataCollector` implementations, `DataNormalizer` service, `DataValidator` service, `Market` domain entity, `Candle` domain entity, `MarketDataIngestionService` application service, data pipeline event types, collector registration mechanism |
| **Acceptance criteria** | All 3 collectors pass integration tests with mocked exchange responses. Normalization produces identical output regardless of source. Validation rejects: negative prices, zero volumes, gap > 5%, out-of-sequence timestamps. Repository CRUD operations verified with in-memory and SQLite implementations. 95%+ test coverage. 1 year of 1h data for 10 symbols collects and stores in < 30s. |
| **Definition of success** | A new exchange can be added by implementing `DataCollector` ABC and registering it — no other code changes needed. |
| **Risks** | Exchange API changes breaking collectors. Rate limiting during data collection. |
| **Estimated effort** | 2–3 sprints (3–4 engineer-weeks) |
| **Hiring impact** | Medium — this is a well-bounded module suitable for onboarding new engineers |
| **Source** | [C:8.1], [C:6 Market], [C:6 Candle], [A:Collector tight coupling], [CAP-03] |
| **Constitution principles** | P3 (Every Decision Traceable — data lineage), P4 (No Hidden State — all data persisted), P5 (Small Composable Systems — collector interchangeability) |

---

### Epic 2.2: Analysis Platform

| Field | Value |
|-------|-------|
| **Objective** | Extract, re-architect, and comprehensively test the Analysis Engine as a proper domain subsystem. |
| **Business value** | Analysis outputs (indicators, regimes, features) are the primary inputs to strategy development. Accuracy and reproducibility are critical. |
| **Engineering value** | Validates the model of stateless domain services consuming repository data. |
| **Architecture value** | Core analysis — feeds Signal Engine and Strategy Engine. |
| **Dependencies** | Epic 1.2 (domain entities, repositories), Epic 2.1 (market data) |
| **Deliverables** | `AnalysisService` with `compute_indicators()`, `detect_regime()`, `extract_features()` methods, `Indicator` domain entity, `Regime` enum (TRENDING_BULLISH, TRENDING_BEARISH, RANGING, VOLATILE, QUIET), `FeatureVector` dataclass, `CorrelationService` with `compute_correlations()`, `RegimeDetectionStrategy` interface (pluggable algorithms), indicator library (SMA, EMA, volatility, ATR, RSI, etc.), comprehensive test suite with hand-calculated expected values |
| **Acceptance criteria** | All indicators match hand-calculated expected values within floating-point tolerance. Regime detection correctly classifies synthetic trending, ranging, and volatile data with 90%+ accuracy. Feature vectors are deterministic (same input → same output). Correlation analysis matches numpy reference implementation. 95%+ test coverage. Indicators computed on 100,000 candles in < 1s. |
| **Definition of success** | A new indicator can be added by writing a pure function and registering it — no infrastructure code needed. |
| **Risks** | Numerical precision differences between platforms. Computational cost of high-resolution indicators. |
| **Estimated effort** | 2 sprints (2–3 engineer-weeks) |
| **Hiring impact** | Medium — good module for engineers with quantitative background |
| **Source** | [C:8.2], [C:6 Indicator], [C:6 Regime], [A:Analysis engine tightly coupled], [CAP-04] |
| **Constitution principles** | P2 (Evidence over Opinion — all indicators produce evidence), P5 (Small Composable Systems — pluggable indicators) |

---

### Epic 2.3: Liquidity Platform

| Field | Value |
|-------|-------|
| **Objective** | Re-architect the Liquidity Engine into a composable set of services with proper interfaces and comprehensive testing. |
| **Business value** | Liquidity analysis is a key differentiator of TraderOS. Reliable zone/sweep/breakout detection directly impacts strategy quality. |
| **Engineering value** | Demonstrates how composed services work together within the domain layer. |
| **Architecture value** | Market structure analysis — feeds Signal Engine. |
| **Dependencies** | Epic 1.2 (domain entities), Epic 2.1 (market data) |
| **Deliverables** | `SwingDetectionService`, `LiquidityZoneService`, `SweepDetectionService`, `BreakoutDetectionService`, `SessionAnalysisService`, `LiquidityZone` domain entity, `SwingPoint` domain entity, `SweepEvent` domain entity, `BreakoutEvent` domain entity, `SessionStats` dataclass, `LiquidityAnalysisOrchestrator` (composes the services), comprehensive test suite with synthetic and real chart patterns |
| **Acceptance criteria** | Swing detection correctly identifies known swing highs/lows on labeled chart data. Zone mapping clusters correctly with configurable threshold. Sweep detection identifies bullish and bearish sweeps. Breakout detection identifies consolidation → breakout sequences. Session analysis correctly assigns global timezone sessions. 90%+ test coverage. Full analysis on 100,000 candles in < 2s. |
| **Definition of success** | A new liquidity detection technique can be added by implementing a single service interface and registering it with the orchestrator. |
| **Risks** | Parameter sensitivity — swing detection thresholds may need calibration per asset class. |
| **Estimated effort** | 2 sprints (2–3 engineer-weeks) |
| **Hiring impact** | Medium — good module for engineers interested in market microstructure |
| **Source** | [C:8.3], [C:6 LiquidityZone], [A:Liquidity engine tightly coupled], [CAP-05] |
| **Constitution principles** | P5 (Small Composable Systems — each detection is independent), P10 (Performance — must be fast enough for real-time) |

---

### Epic 3.1: Research Platform

| Field | Value |
|-------|-------|
| **Objective** | Build the complete O-H-T-R-L research workflow as a proper domain subsystem with full validation, provenance, and query capabilities. |
| **Business value** | The research workflow is the core differentiator of TraderOS. This epic directly implements the platform's identity. |
| **Engineering value** | Defines the lifecycle state machine pattern used by other entities (trades, orders, experiments). |
| **Architecture value** | Research layer — feeds Knowledge Graph. All trading entities link back to research entities. |
| **Dependencies** | Epic 1.2 (domain entities, repositories, config) |
| **Deliverables** | `ResearchService` with full O-H-T-R-L lifecycle, `Observation` entity, `Hypothesis` entity (with status machine: proposed → testing → confirmed/rejected/inconclusive), `Experiment` entity (with configuration capture), `Result` entity, `Lesson` entity, `ResearchRepository` interface + implementations, `ExperimentConfig` validator (ensures reproducibility), `WorkflowTraceService` (traverses entity chain), `AutoObservationService` (generates observations from system events), `ResearchSearchService` (full-text search across all entities) |
| **Acceptance criteria** | Complete O-H-T-R-L workflow executes end-to-end. Hypothesis status transitions follow state machine rules. Experiment configuration captures ALL parameters needed for exact replay. Workflow trace correctly traverses from lesson → result → experiment → hypothesis → observation. Full-text search returns results in < 200ms on 1000 entities. Auto-observations generated from simulated system events. 95%+ test coverage. |
| **Definition of success** | A trader can observe a market pattern, formulate a hypothesis, design and execute a backtest, record the result, and extract a lesson — with full provenance — without leaving the CLI. |
| **Risks** | Over-engineering the state machine. Balancing flexibility (freeform content) with structure (enforceable schemas). |
| **Estimated effort** | 3 sprints (4–5 engineer-weeks) |
| **Hiring impact** | High — this is the module that most clearly demonstrates TraderOS's unique value. Great for interviews and demos. |
| **Source** | [C:8.9], [C:6 Hypothesis], [C:6 Experiment], [C:6 Lesson], [A:Research engine existing but basic], [CAP-06] |
| **Constitution principles** | P1 (Research First), P2 (Evidence over Opinion), P3 (Every Decision Traceable) |

---

### Epic 3.2: Knowledge Graph

| Field | Value |
|-------|-------|
| **Objective** | Implement the knowledge graph that connects all research entities into a traversable, queryable network with visualization support. |
| **Business value** | The knowledge graph is what makes TraderOS a learning platform rather than a trade logging system. Connections between insights compound over time. |
| **Engineering value** | Introduces graph data modeling to the team. Establishes patterns for semantic search and embedding support. |
| **Architecture value** | Knowledge layer — consumes from all research entities. |
| **Dependencies** | Epic 3.1 (research entities), Epic 1.2 (repositories, event bus) |
| **Deliverables** | `KnowledgeGraphService` with node/edge CRUD, `KnowledgeNode` entity, `KnowledgeEdge` entity, `GraphTraversalService` (depth-limited BFS/DFS), `GraphSearchService` (full-text + relationship), `GraphVisualizationService` (generates graph layouts), `embedding` field on nodes (vector storage interface, implementation deferred), `GraphEventSubscriber` (auto-indexes research entities), `InsightDiscoveryService` (finds non-obvious connections) |
| **Acceptance criteria** | Graph CRUD operations verified with in-memory and SQLite implementations. Depth-5 traversal on 1000 nodes completes in < 100ms. Path finding between connected nodes returns correct path. Auto-indexing creates KnowledgeNodes for all research entities on creation. Search finds entities by content and by relationship. 90%+ test coverage. |
| **Definition of success** | A trader can start from a lesson and traverse back through its entire research provenance chain in both directions, discovering related observations and experiments along the way. |
| **Risks** | Graph queries on SQLite may be slow at scale (mitigated: PostgreSQL + Graph extensions for production). |
| **Estimated effort** | 2 sprints (3–4 engineer-weeks) |
| **Hiring impact** | Medium — demonstrates data modeling sophistication |
| **Source** | [C:8.10], [C:6 KnowledgeNode], [A:Knowledge graph is basic SQL chains], [CAP-07] |
| **Constitution principles** | P1 (Research First — knowledge persistence), P3 (Every Decision Traceable — graph traversal for provenance) |

---

### Epic 4.1: Strategy Platform

| Field | Value |
|-------|-------|
| **Objective** | Build a production-quality strategy definition and management framework with versioning, parameter management, and comprehensive testing. |
| **Business value** | Strategies are the primary user-facing abstraction. A clean strategy framework directly impacts user productivity and confidence. |
| **Engineering value** | Establishes the plugin architecture pattern used by the future plugin system. |
| **Architecture value** | Strategy layer — connects analysis output to trading decisions. |
| **Dependencies** | Epic 2.2 (analysis outputs), Epic 2.3 (liquidity outputs), Epic 1.2 (domain entities) |
| **Deliverables** | `Strategy` ABC with `evaluate()`, `get_parameters()`, `set_parameters()`, `validate()` methods, `StrategyRegistry` with decorator registration, `StrategyMeta` entity, `StrategyVersion` value object (semver), `StrategyParameter` dataclass with type/range/default validation, `StrategyEvaluationService`, `MarketState` dataclass (consolidated input to strategies), ported versions of: `MovingAverageTrend`, `VolatilityBreakout`, `MeanReversion`, strategy serialization/deserialization for persistence |
| **Acceptance criteria** | Strategy ABC enforces interface contract. Registry successfully registers, lists, and retrieves strategies. Strategy versioning produces different evaluation for different versions. All 3 starter strategies produce expected signals on known market conditions. Parameters validate type and range. Strategy evaluation on 100 symbols in < 10ms. 95%+ test coverage. |
| **Definition of success** | A new strategy can be defined by subclassing `Strategy`, implementing `evaluate()`, and decorating with `@registry.register` — no other code changes. |
| **Risks** | Strategy interface may need evolution as more complex strategies are implemented (mitigated: ABC allows additive methods). |
| **Estimated effort** | 2 sprints (2–3 engineer-weeks) |
| **Hiring impact** | High — strategy development is how quants will use TraderOS. Must be polished. |
| **Source** | [C:8.4], [C:6 Strategy], [A:Strategy interface basic but correct pattern], [CAP-08] |
| **Constitution principles** | P5 (Small Composable Systems — strategy as plug-in), P3 (Every Decision Traceable — versioned) |

---

### Epic 4.2: Signal Platform

| Field | Value |
|-------|-------|
| **Objective** | Build the signal generation and validation pipeline that transforms strategy evaluations into risk-validated trading recommendations. |
| **Business value** | Signal quality directly impacts trading performance. Deduplication and validation prevent costly conflicting orders. |
| **Engineering value** | Demonstrates the event-driven pattern: strategies publish evaluations → signals are generated → risk engine validates. |
| **Architecture value** | Signal layer — the bridge between strategy and execution. |
| **Dependencies** | Epic 4.1 (strategy framework), Epic 2.2 (analysis), Epic 2.3 (liquidity), Epic 1.2 (event bus) |
| **Deliverables** | `SignalService` with `process_evaluations()`, `validate_signal()`, `deduplicate()` methods, `Signal` entity, `SignalValidator` strategy pattern, `SignalDeduplicator` (handles conflicting long/short, cooldown periods), `SignalEvent` types, `SignalProvenanceService` (links signal to indicators + strategy version), `SignalRepository` interface + implementations |
| **Acceptance criteria** | Signal generation correctly converts strategy evaluations to Signal entities. Deduplication resolves conflicting signals with configurable policy (latest wins, highest confidence wins, etc.). Stale price detection rejects signals > 1 bar old. Signal provenance correctly links to all inputs. 100 signals processed in < 5ms. 95%+ test coverage. |
| **Definition of success** | Adding a new signal source requires implementing a signal provider that publishes to the event bus — existing deduplication and validation logic applies automatically. |
| **Risks** | Signal conflicts at market open / high-volatility events need careful handling. |
| **Estimated effort** | 1–2 sprints (1–2 engineer-weeks) |
| **Hiring impact** | Low-medium — straightforward but critical module |
| **Source** | [C:8.5], [C:6 Signal], [A:No signal engine exists], [CAP-09] |
| **Constitution principles** | P3 (Every Decision Traceable), P9 (Observability by Default — signal decisions logged) |

---

### Epic 4.3: Risk Platform

| Field | Value |
|-------|-------|
| **Objective** | Build a comprehensive risk management framework that validates every signal against configurable limits before execution. |
| **Business value** | Risk management is non-negotiable for live trading. This epic directly protects capital. |
| **Engineering value** | Demonstrates fail-closed design and the strategy pattern for pluggable position sizing methods. |
| **Architecture value** | Risk layer — the gate between analysis and execution. |
| **Dependencies** | Epic 4.2 (signals to validate), Epic 4.4 (portfolio state), Epic 1.2 (domain entities) |
| **Deliverables** | `RiskService` with `assess_signal()`, `calculate_position_size()`, `check_exposure()`, `check_drawdown()`, `check_correlation()`, `evaluate_kill_switch()` methods, `RiskProfile` entity, `PositionSizingStrategy` interface with implementations (Kelly, fixed_fraction, volatility_adjusted, risk_parity), `ExposureLimits` value object, `DrawdownMonitor`, `CorrelationCheckService`, `KillSwitchService`, `RiskAssessment` result dataclass, `RiskEvent` types |
| **Acceptance criteria** | All position sizing methods produce correct results verified by hand calculation. Exposure limits correctly reject signals that exceed per-market and per-portfolio limits. Drawdown monitoring triggers kill switch at configured threshold. Correlation check prevents adding correlated positions. Kill switch immediately rejects all signals when active. Every rejection includes a human-readable reason. 95%+ test coverage. Assessment in < 5ms per signal. |
| **Definition of success** | A new position sizing method can be added by implementing `PositionSizingStrategy` and registering it with the risk service — all other logic (exposure, drawdown, kill switch) applies automatically. |
| **Risks** | Numerical edge cases in position sizing (zero capital, extremely high volatility) could cause division by zero. |
| **Estimated effort** | 2 sprints (2–3 engineer-weeks) |
| **Hiring impact** | High — risk management is a critical hiring signal for trading engineers |
| **Source** | [C:8.6], [C:6 RiskProfile], [A:Risk engine exists but limited], [CAP-10] |
| **Constitution principles** | P2 (Evidence over Opinion — limits derived from data), P4 (No Hidden State — all risk state persisted), P9 (Observability by Default — every validation logged) |

---

### Epic 4.4: Portfolio Platform

| Field | Value |
|-------|-------|
| **Objective** | Build the portfolio management system that tracks positions, trades, capital, and performance. |
| **Business value** | Portfolio tracking is essential for understanding strategy performance and making capital allocation decisions. |
| **Engineering value** | Demonstrates aggregate root pattern in domain-driven design. |
| **Architecture value** | Portfolio layer — the central state of the trading system. |
| **Dependencies** | Epic 2.1 (market data for mark-to-market), Epic 1.2 (domain entities, repositories) |
| **Deliverables** | `PortfolioService` with trade lifecycle management, `Portfolio` aggregate root, `Position` entity (computed from trades), `Trade` entity with full lifecycle, `PortfolioRepository`, `PositionRepository`, `TradeRepository`, `MarkToMarketService`, `PerformanceAnalyticsService` (Sharpe, Sortino, Calmar, max drawdown, win rate, profit factor), `PortfolioSnapshot` value object, `PortfolioEvent` types |
| **Acceptance criteria** | Trade lifecycle fully implemented (open → partial → closed). Portfolio correctly aggregates positions from trades. Mark-to-market correctly computes unrealized PnL. Performance metrics match reference implementations. 100+ concurrent positions supported. Portfolio computation in < 1ms. 95%+ test coverage. |
| **Definition of success** | After 1000 trades across 10 strategies, portfolio correctly reports per-strategy and aggregate PnL, exposure, and risk metrics — all traceable to individual trades. |
| **Risks** | Race conditions in trade ordering during high-frequency scenarios (mitigated: event-sourced position computation). |
| **Estimated effort** | 2 sprints (3–4 engineer-weeks) |
| **Hiring impact** | Medium — standard domain modeling challenge |
| **Source** | [C:8.7], [C:6 Trade], [C:6 Position], [C:6 Portfolio], [A:No portfolio tracking exists], [CAP-11] |
| **Constitution principles** | P3 (Every Decision Traceable), P4 (No Hidden State) |

---

### Epic 5.1: Execution Platform

| Field | Value |
|-------|-------|
| **Objective** | Build the execution engine that transforms risk-approved signals into broker-submitted orders with full lifecycle tracking. |
| **Business value** | Execution is the final step in the trading pipeline. Without it, research cannot be capitalized. |
| **Engineering value** | Demonstrates state machine design pattern and adapter pattern for external integrations. |
| **Architecture value** | Execution layer — the interface between TraderOS and the outside world. |
| **Dependencies** | Epic 4.3 (risk assessment), Epic 4.4 (portfolio for trade recording), Epic 2.1 (market data for execution prices) |
| **Deliverables** | `ExecutionService` with order lifecycle management, `Order` entity with state machine (created → submitted → partial → filled → cancelled → rejected), `OrderFactory` (creates market/limit/stop orders), `BrokerAdapter` ABC, `PaperBrokerAdapter` (simulated fills), `OrderRepository`, `ExecutionEvent` types, retry logic with exponential backoff, `ExecutionAnalyticsService` (fill rate, slippage, latency) |
| **Acceptance criteria** | Order state machine handles all transitions correctly. `PaperBrokerAdapter` produces statistically realistic fills. Retry logic correctly handles transient failures with configurable backoff. Order submission in < 100ms. Broker adapter can be swapped via configuration. 90%+ test coverage. |
| **Definition of success** | A new broker can be integrated by implementing `BrokerAdapter` — all order management, lifecycle tracking, and analytics apply automatically. |
| **Risks** | Broker API changes. Order state edge cases (partial fills at market close, etc.). |
| **Estimated effort** | 3 sprints (4–5 engineer-weeks) |
| **Hiring impact** | High — execution quality is a key hiring signal for trading systems engineers |
| **Source** | [C:8.8], [C:6 Trade], [C:6 Order], [A:No execution exists], [CAP-12] |
| **Constitution principles** | P3 (Every Decision Traceable), P4 (No Hidden State — order persistence), P9 (Observability by Default) |

---

### Epic 5.2: Backtesting Platform

| Field | Value |
|-------|-------|
| **Objective** | Build a production-quality backtesting engine that simulates strategy performance with realistic costs and produces comprehensive metrics. |
| **Business value** | Backtesting is the primary research tool. Speed and accuracy directly impact research velocity. |
| **Engineering value** | Demonstrates the reuse of strategy/risk/portfolio engines in simulation mode (same code, different data source). |
| **Architecture value** | Backtest layer — validates strategies before paper trading. |
| **Dependencies** | Epic 4.1 (strategies), Epic 4.3 (risk for simulated validation), Epic 4.4 (portfolio for simulated tracking), Epic 2.1 (market data), Epic 1.2 (event bus, repositories) |
| **Deliverables** | `BacktestingService` with `run()`, `compare()`, `walk_forward()` methods, `BacktestConfig` dataclass, `BacktestResult` entity (metrics + equity curve + trade log), `CostModel` (commission, spread, slippage), `PerformanceMetrics` calculator (Sharpe, Sortino, Calmar, max DD, win rate, profit factor, expectancy, recovery factor), `WalkForwardOptimizer`, `BacktestComparisonService`, `BacktestEvent` types |
| **Acceptance criteria** | Backtest results match expected values from known input data within 0.1%. Commission, spread, and slippage correctly impact PnL. Walk-forward optimization produces valid parameter ranges. Comparison report clearly shows differences between backtest runs. 1 year of 1h data backtest in < 5s. 95%+ test coverage. |
| **Definition of success** | A strategy backtested with the same parameters on the same data produces identical results every time (deterministic, reproducible). |
| **Risks** | Look-ahead bias in indicator computation. Survivorship bias in historical data. |
| **Estimated effort** | 3 sprints (4–5 engineer-weeks) |
| **Hiring impact** | High — backtesting accuracy is a fundamental trading engineering skill |
| **Source** | [C:8.11], [C:6 Experiment], [A:Backtesting exists but limited], [CAP-13] |
| **Constitution principles** | P2 (Evidence over Opinion), P3 (Every Decision Traceable), P10 (Performance — must be fast) |

---

### Epic 5.3: Paper Trading Platform

| Field | Value |
|-------|-------|
| **Objective** | Bridge backtesting and live trading with a paper trading system that executes strategies against live data in simulation mode. |
| **Business value** | Paper trading is the final validation step before live capital is at risk. Deviation analysis between backtest and paper is critical. |
| **Engineering value** | Demonstrates the live vs. simulation mode pattern that enables the same code to run in research, paper, and live modes. |
| **Architecture value** | Paper layer — the bridge between research and production. |
| **Dependencies** | Epic 5.1 (execution with paper adapter), Epic 5.2 (backtest results for comparison), Epic 2.1 (live market data), Epic 1.2 (scheduler) |
| **Deliverables** | `PaperTradingService` with session lifecycle, `PaperTradingConfig`, `PaperTradingSession` entity, `FillSimulator` (configurable fill model), `DeviationAnalysisService` (backtest vs paper comparison), `PaperPortfolioTracker`, `PaperTradingEvent` types, session persistence and recovery |
| **Acceptance criteria** | Paper trading session starts, runs, and stops cleanly. Fill simulation matches real exchange behavior within configurable tolerance. Deviation reports clearly show statistically significant differences between backtest and paper. Session recovers after restart with identical state. Runs 24/7 without memory leaks. Dashboard updates in < 1s per bar. 90%+ test coverage. |
| **Definition of success** | A strategy can be developed with backtesting, validated with paper trading, and the deviation report provides sufficient confidence for the trader to decide whether to go live. |
| **Risks** | Fill simulation accuracy depends on market data resolution. Slippage estimation during high volatility. |
| **Estimated effort** | 3 sprints (4–5 engineer-weeks) |
| **Hiring impact** | Medium-high — demonstrates understanding of simulation fidelity |
| **Source** | [C:8.12], [C:14 (Paper Trading)], [A:No paper trading exists], [CAP-14] |
| **Constitution principles** | P1 (Research First — paper is the final research step), P2 (Evidence over Opinion — deviation data) |

---

### Epic 6.1: Visualization Platform

| Field | Value |
|-------|-------|
| **Objective** | Re-architect the visualization system into a proper service with multiple export formats, knowledge graph visualization, and performance charts. |
| **Business value** | Visual output is how traders understand their research. Quality visualization directly impacts trust in the platform. |
| **Engineering value** | Demonstrates clean separation between data and presentation. |
| **Architecture value** | Presentation layer — consumes from all engines. |
| **Dependencies** | All data-producing engines (Epics 2.1–5.3), Epic 1.2 (data contracts) |
| **Deliverables** | `VisualizationService` with chart generation methods, `Chart` dataclass, `PriceChartGenerator`, `LiquidityMapGenerator`, `CorrelationHeatmapGenerator`, `EquityCurveGenerator`, `KnowledgeGraphRenderer`, `ChartExporter` (PNG, SVG, HTML), `ChartTheme` (configurable styling) |
| **Acceptance criteria** | All legacy chart types ported to new service. Knowledge graph visualization renders correctly for depth-3 graphs. Export produces valid PNG, SVG, and HTML. Single chart generation in < 2s. 85%+ test coverage. |
| **Definition of success** | A new chart type can be added by implementing a chart generator class — existing export and theming apply automatically. |
| **Risks** | matplotlib limitations for complex graph visualizations (mitigated: explore graphviz/plotly for knowledge graphs). |
| **Estimated effort** | 2 sprints (2–3 engineer-weeks) |
| **Hiring impact** | Low-medium — standard visualization work |
| **Source** | [C:8.13], [A:Visualization tightly coupled to domain], [CAP-15] |
| **Constitution principles** | P5 (Small Composable Systems), P9 (Observability by Default) |

---

### Epic 6.2: Interface Platform

| Field | Value |
|-------|-------|
| **Objective** | Build the unified CLI, REST API, WebSocket stream, and Web Dashboard that expose all platform capabilities to users and external systems. |
| **Business value** | Interfaces determine how users interact with TraderOS. Quality interfaces directly impact adoption and satisfaction. |
| **Engineering value** | Demonstrates clean interface layering — all interfaces are thin wrappers over application services. |
| **Architecture value** | Interface layer — the outermost layer of the architecture. |
| **Dependencies** | All domain epics (2.x–5.x), Epic 1.2 (event bus for WebSocket), CAP-18 (observability for API monitoring) |
| **Deliverables** | Unified CLI (`traderos` command with all subcommands), REST API (FastAPI or Flask), OpenAPI documentation, WebSocket endpoint for real-time data, Web Dashboard (minimal React/Vue or server-rendered), API authentication, request validation middleware, error response formatting |
| **Acceptance criteria** | CLI passes `--help` completeness review. All 20+ commands work with JSON output mode. REST API endpoints cover all domain operations. OpenAPI spec is valid and complete. WebSocket delivers < 10ms latency. Dashboard loads in < 2s. 90%+ test coverage for CLI and API. |
| **Definition of success** | Every platform capability is accessible through CLI and API. A user can perform their entire workflow (data → analysis → research → backtest → paper trade) without ever using the dashboard. |
| **Risks** | API design decisions may need breaking changes as capabilities evolve (mitigated: API versioning from day 1). |
| **Estimated effort** | 4–5 sprints for full interface suite (phased: CLI first, then API, then WS, then dashboard) |
| **Hiring impact** | High — interfaces are what external engineers evaluate first |
| **Source** | [C:8.15], [C:8.16], [C:8.17], [A:CLIs are separate scripts, no API/dashboard], [CAP-16] |
| **Constitution principles** | P7 (Architecture Before Features — interface isolation), P5 (Small Composable Systems) |

---

### Epic 6.3: Notification Platform

| Field | Value |
|-------|-------|
| **Objective** | Build a multi-channel notification system that delivers timely alerts without noise. |
| **Business value** | Notifications keep traders informed of critical events without requiring constant dashboard monitoring. |
| **Engineering value** | Demonstrates the observer/event-subscriber pattern in practice. |
| **Architecture value** | Cross-cutting — consumes events from all subsystems. |
| **Dependencies** | Epic 1.2 (event bus), CAP-18 (observability) |
| **Deliverables** | `NotificationService`, `Notification` entity, `NotificationChannel` ABC with implementations (CLI, terminal-notifier, webhook, email stub), `NotificationRule` entity (configure when to notify), `NotificationAggregator` (prevents spam), rate-limiting logic, notification history |
| **Acceptance criteria** | Multi-channel delivery works with at least 2 channel implementations. Rate limiting prevents > 1 notification per 5s per source. Aggregation correctly combines duplicate notifications. History queryable with filters. 90%+ test coverage. |
| **Definition of success** | Adding a new notification channel requires implementing `NotificationChannel` — all routing, rate limiting, and history apply automatically. |
| **Risks** | Notification fatigue if too many alerts. |
| **Estimated effort** | 1 sprint (1 engineer-week) |
| **Hiring impact** | Low |
| **Source** | [C:8.14], [A:No notification system], [CAP-17] |
| **Constitution principles** | P9 (Observability by Default) |

---

### Epic 6.4: Observability Platform

| Field | Value |
|-------|-------|
| **Objective** | Build the structured logging, metrics collection, health checking, and run manifest systems that make TraderOS observable and debuggable. |
| **Business value** | Without observability, production issues cannot be diagnosed. This is non-negotiable for live trading. |
| **Engineering value** | Structured logging and metrics are cross-cutting concerns that every engineer benefits from. |
| **Architecture value** | Cross-cutting — touches every subsystem. |
| **Dependencies** | Epic 1.1 (infrastructure for log shipping), Epic 1.2 (event bus for metrics events) |
| **Deliverables** | `StructuredLoggingService` (JSON format, correlation ID propagation), `MetricsService` (counters, timers, gauges), `HealthCheckService` (aggregates subsystem health), `RunManifestService` (records config + inputs + outputs per run), `AuditTrailService` (immutable event log for compliance), Prometheus metrics endpoint, health endpoint |
| **Acceptance criteria** | All subsystems emit structured logs with required fields. Metrics service correctly records counter, timer, and gauge values. Health endpoint reports status of all subsystems. Run manifest is produced for every pipeline run. Audit trail is append-only and tamper-evident. Correlation ID propagates through all subsystems. 90%+ test coverage. |
| **Definition of success** | A production incident can be fully diagnosed using structured logs, metrics, and run manifests — without requiring console access or ad-hoc queries. |
| **Risks** | Log volume could be high (mitigated: configurable log levels, sampling for high-frequency events). |
| **Estimated effort** | 2 sprints (2–3 engineer-weeks) |
| **Hiring impact** | Medium — demonstrates production engineering maturity |
| **Source** | [C:10.5], [C:10.9], [C:10.13], [C:10.14], [A:No observability infrastructure], [CAP-18] |
| **Constitution principles** | P9 (Observability by Default), P8 (Automation over Manual Work) |

---

## 8 Workstreams

| ID | Name | Epics | Duration | Dependencies | Lead |
|----|------|-------|----------|--------------|------|
| WS-1 | Foundation | Epic 1.1, Epic 1.2 | Months 1–4 | None | Engineering Lead |
| WS-2 | Data & Analysis | Epic 2.1, Epic 2.2, Epic 2.3 | Months 2–6 | WS-1 | Data Engineer |
| WS-3 | Research & Knowledge | Epic 3.1, Epic 3.2 | Months 3–7 | WS-1 | Research Engineer |
| WS-4 | Trading Core | Epic 4.1, Epic 4.2, Epic 4.3, Epic 4.4 | Months 4–9 | WS-2, WS-3 | Trading Engineer |
| WS-5 | Execution & Simulation | Epic 5.1, Epic 5.2, Epic 5.3 | Months 6–11 | WS-4 | Systems Engineer |
| WS-6 | Platform | Epic 6.1, Epic 6.2, Epic 6.3, Epic 6.4 | Months 5–12 | WS-2, WS-3, WS-4 | Full-Stack Engineer |

### Workstream Dependency Graph

```
Month:  1  2  3  4  5  6  7  8  9  10  11  12
        │  │  │  │  │  │  │  │  │  │   │   │
WS-1    ████████████████████████
WS-2       ████████████████████████████
WS-3          ████████████████████████████████
WS-4                ████████████████████████████████████
WS-5                      ████████████████████████████████████
WS-6                         ████████████████████████████████████
```

---

## 9 Milestones

| ID | Name | Date | Dependencies | Deliverables | Acceptance |
|----|------|------|--------------|--------------|------------|
| M0 | Engineering Foundation Complete | Month 2 | None | CI/CD, Docker, pre-commit, Makefile, lint/typecheck pass | `make test` passes in < 30s. CI green on every push. |
| M1 | Architecture Framework Complete | Month 4 | M0, WS-1 | 4-layer package structure, repositories, event bus, config v2, domain entities | Architecture tests pass. Event bus operational. Config validated. |
| M2 | Data Platform Complete | Month 5 | M1, WS-2 | Data collectors normalized + validated + stored. All 3 collector types passing. | 95% coverage on data pipeline. 10 symbols collectable. |
| M3 | Analysis & Liquidity Complete | Month 6 | M2, WS-2 | Analysis and Liquidity engines ported to new architecture with full test coverage. | Indicators match reference. Liquidity detection validated on labeled data. |
| M4 | Research Platform Complete | Month 7 | M1, WS-3 | O-H-T-R-L workflow complete. Research CLI functional. Auto-observation working. | Full workflow traceable from lesson to observation. |
| M5 | Trading Core Complete | Month 9 | M3, M4, WS-4 | Strategies, signals, risk, portfolio working in new architecture. Backtesting ported. | Strategy → Signal → Risk → Portfolio pipeline verified end-to-end. |
| M6 | Execution Complete | Month 10 | M5, WS-5 | Order lifecycle, paper broker adapter, execution analytics working. | Paper trading fills match expected distribution. |
| M7 | Backtesting & Paper Trading Complete | Month 11 | M6, WS-5 | Backtesting and paper trading fully functional. Deviation analysis working. | Backtest is deterministic. Paper trades trackable. Deviation reports generated. |
| M8 | Platform Complete | Month 12 | M5, M6, M7, WS-6 | CLI, API, dashboard, notifications, observability all operational. | All 20+ CLI commands work. OpenAPI spec complete. Dashboard loads. |
| M9 | v1 Release | Month 12 | M0–M8 | Repository meets all Hiring Readiness and Portfolio Readiness criteria. | All quality gates pass. v1 tagged. |

---

## 10 Sprint Plan

### Sprint Structure

- **Duration**: 2 weeks
- **Cadence**: Sprint planning Monday AM, Review Friday PM
- **Capacity**: 80% feature + 20% debt (per Constitution)
- **Team**: 4–6 engineers (scaling as hired)

### Sprint 1–2: Foundation Sprint

| Sprint | Focus | Work Packages | Debt Allocation |
|--------|-------|---------------|-----------------|
| 1 | Developer toolchain | WP-001, WP-002, WP-003 | Existing test migration (WP-004) |
| 2 | Docker + CI/CD | WP-005, WP-006, WP-007 | Logging standardization (WP-008) |

### Sprint 3–4: Architecture Sprint

| Sprint | Focus | Work Packages | Debt Allocation |
|--------|-------|---------------|-----------------|
| 3 | Package structure + domain entities | WP-009, WP-010, WP-011 | Config validation (WP-012) |
| 4 | Repository pattern + in-memory impl | WP-013, WP-014, WP-015 | Config v2 migration (WP-016) |

### Sprint 5–6: Architecture + Data

| Sprint | Focus | Work Packages | Debt Allocation |
|--------|-------|---------------|-----------------|
| 5 | Event bus + architecture tests | WP-017, WP-018 | Architecture violation fixes (WP-019) |
| 6 | Market data engine + collector port | WP-020, WP-021, WP-022 | Data validation tests (WP-023) |

### Sprint 7–8: Data + Analysis

| Sprint | Focus | Work Packages | Debt Allocation |
|--------|-------|---------------|-----------------|
| 7 | Analysis engine port | WP-024, WP-025, WP-026 | Indicator accuracy verification (WP-027) |
| 8 | Liquidity engine port | WP-028, WP-029, WP-030 | Zone mapping tests (WP-031) |

### Sprint 9–10: Research

| Sprint | Focus | Work Packages | Debt Allocation |
|--------|-------|---------------|-----------------|
| 9 | Research engine (O-H-T-R-L) | WP-032, WP-033, WP-034 | Research CLI migration (WP-035) |
| 10 | Knowledge graph | WP-036, WP-037, WP-038 | Search indexing (WP-039) |

### Sprint 11–14: Trading Core

| Sprint | Focus | Work Packages | Debt Allocation |
|--------|-------|---------------|-----------------|
| 11 | Strategy framework + port | WP-040, WP-041, WP-042 | Strategy test coverage (WP-043) |
| 12 | Signal engine | WP-044, WP-045 | Risk engine port (WP-046) |
| 13 | Portfolio engine | WP-047, WP-048, WP-049 | Trade lifecycle tests (WP-050) |
| 14 | Risk engine completion | WP-051, WP-052, WP-053 | Risk edge cases (WP-054) |

### Sprint 15–17: Execution & Backtest

| Sprint | Focus | Work Packages | Debt Allocation |
|--------|-------|---------------|-----------------|
| 15 | Execution engine + order lifecycle | WP-055, WP-056, WP-057 | Order state machine tests (WP-058) |
| 16 | Backtesting engine port | WP-059, WP-060, WP-061 | Backtest determinism tests (WP-062) |
| 17 | Paper trading | WP-063, WP-064, WP-065 | Fill simulation accuracy (WP-066) |

### Sprint 18–20: Platform

| Sprint | Focus | Work Packages | Debt Allocation |
|--------|-------|---------------|-----------------|
| 18 | Unified CLI + API | WP-067, WP-068, WP-069 | API test coverage (WP-070) |
| 19 | Observability + notifications | WP-071, WP-072, WP-073 | Log migration (WP-074) |
| 20 | Visualization + Dashboard | WP-075, WP-076, WP-077 | Visualization test coverage (WP-078) |

### Sprint 21–24: Stabilization & Release

| Sprint | Focus | Work Packages | Debt Allocation |
|--------|-------|---------------|-----------------|
| 21 | Integration testing + bug fix | WP-079, WP-080 | Cross-engine integration tests (WP-081) |
| 22 | Performance optimization | WP-082, WP-083 | Benchmarking suite (WP-084) |
| 23 | Documentation + release prep | WP-085, WP-086, WP-087 | ADR finalization (WP-088) |
| 24 | v1 Release | WP-089, WP-090 | Final debt sprint (WP-091) |

---

## 11 Work Package Templates

### Template: Architecture Work Package

```
WP-XXX: [Title]
Priority: [Critical/High/Medium/Low]
Epic: [Epic X.X]
Workstream: [WS-X]
Objective: [One sentence]
Background: [Context from Constitution and Audit]
Requirements:
  - [Requirement 1]
  - [Requirement 2]
Technical approach:
  - [Approach detail 1]
  - [Approach detail 2]
Dependencies:
  - WP-XXX ([dependency description])
Files likely affected:
  - [file path 1]
  - [file path 2]
Testing requirements:
  - [Test requirement 1]
  - [Test requirement 2]
Documentation updates:
  - [Doc update 1]
  - [Doc update 2]
ADR required: [Yes/No]
  - If Yes: ADR-XXX ([title])
Acceptance criteria:
  - [Criterion 1]
  - [Criterion 2]
Rollback strategy:
  - [How to revert this change safely]
Estimated effort: [X] engineer-days
Evidence required:
  - [Evidence 1]
  - [Evidence 2]
Source: [Constitution, Audit, Capability references]
```

---

## 12 Work Breakdown Structure

### Foundation Work Packages

```
WP-001: Makefile & Developer Tooling Setup
  Priority: Critical | Epic: 1.1 | Effort: 2d
  Files: Makefile, pyproject.toml, .pre-commit-config.yaml
  Testing: N/A (infra)
  ADR: No
  Source: [C:10], [C:10.1], [A:No build automation]

WP-002: pytest Migration & Configuration
  Priority: Critical | Epic: 1.1 | Effort: 2d
  Files: pyproject.toml, tests/, conftest.py
  Testing: All existing tests must pass under pytest
  ADR: No
  Source: [C:10.4], [A:unittest only, 7 tests]

WP-003: Linting & Formatting Configuration
  Priority: Critical | Epic: 1.1 | Effort: 1d
  Files: pyproject.toml, .pre-commit-config.yaml
  Testing: `make lint` passes on entire codebase
  ADR: No
  Source: [C:10.1], [A:No linting]

WP-004: Type Checking Configuration
  Priority: Critical | Epic: 1.1 | Effort: 1d
  Files: pyproject.toml
  Testing: `make typecheck` passes on entire codebase
  ADR: No
  Source: [C:10.7], [A:No type checking]

WP-005: Dockerfile & docker-compose.yml
  Priority: High | Epic: 1.1 | Effort: 2d
  Files: Dockerfile, docker-compose.yml, .dockerignore
  Testing: `docker-compose up` starts system
  ADR: No
  Source: [C:8.18], [A:No Docker]

WP-006: GitHub Actions CI Pipeline
  Priority: Critical | Epic: 1.1 | Effort: 2d
  Files: .github/workflows/ci.yml
  Testing: CI pipeline passes on PR
  ADR: No
  Source: [C:8.18], [A:No CI/CD]

WP-007: SQLite → PostgreSQL Migration Framework
  Priority: Medium | Epic: 1.2 | Effort: 3d
  Files: traderos/infrastructure/database/
  Testing: Migration tests verify schema parity
  ADR: Yes, ADR-005
  Source: [C:8.18], [C:5 (Key Decision 1)]
```

### Architecture Work Packages

```
WP-008: Namespace Package Restructuring
  Priority: Critical | Epic: 1.2 | Effort: 3d
  Files: New: traderos/domain/, traderos/infrastructure/, traderos/application/, traderos/interfaces/
  Testing: All imports work under new structure
  ADR: Yes, ADR-002
  Source: [C:4], [C:5]

WP-009: Domain Entity Dataclasses
  Priority: Critical | Epic: 1.2 | Effort: 4d
  Files: traderos/domain/entities/
  Testing: Entity validation tests for all 15+ entities
  ADR: No (entities are implementations of C:6)
  Source: [C:6]

WP-010: Repository Interfaces
  Priority: Critical | Epic: 1.2 | Effort: 3d
  Files: traderos/domain/repositories/
  Testing: Interface contract tests
  ADR: Yes, ADR-004
  Source: [C:8.18], [C:5 (Key Decision 4)]

WP-011: InMemory Repository Implementations
  Priority: Critical | Epic: 1.2 | Effort: 3d
  Files: traderos/infrastructure/repositories/in_memory/
  Testing: Same test suite as WP-010, running against in-memory impl
  ADR: No
  Source: [C:10.4 (test isolation)]

WP-012: SQLite Repository Implementations
  Priority: High | Epic: 1.2 | Effort: 3d
  Files: traderos/infrastructure/repositories/sqlite/
  Testing: Same test suite as WP-010, running against SQLite impl
  ADR: No
  Source: [C:8.18]

WP-013: Config v2 (Validated, Frozen, Schema-based)
  Priority: High | Epic: 1.2 | Effort: 2d
  Files: traderos/infrastructure/config/
  Testing: Config validation tests, immutability tests
  ADR: No
  Source: [C:10.8], [C:P4 (No Hidden State)]

WP-014: Error Handling Framework
  Priority: High | Epic: 1.2 | Effort: 2d
  Files: traderos/domain/exceptions/
  Testing: Exception hierarchy tests
  ADR: No
  Source: [C:10.10]

WP-015: Structured Logging Service
  Priority: High | Epic: 6.4 | Effort: 2d
  Files: traderos/infrastructure/logging/
  Testing: Log format validation tests
  ADR: Yes, ADR-007
  Source: [C:10.5], [C:P9 (Observability)]

WP-016: Event Bus Implementation
  Priority: High | Epic: 1.2 | Effort: 4d
  Files: traderos/infrastructure/events/
  Testing: Event publishing, subscription, delivery tests
  ADR: Yes, ADR-003
  Source: [C:5], [C:5 (Key Decision 2)]

WP-017: Architecture Enforcement Tests
  Priority: Critical | Epic: 1.2 | Effort: 2d
  Files: tests/architecture/
  Testing: Import tests verify dependency direction
  ADR: No
  Source: [C:4 (Dependency Rule)], [C:7 (Boundary Rules)]
```

### Data & Analysis Work Packages

```
WP-018: MarketDataRepository Implementation
  Priority: High | Epic: 2.1 | Effort: 2d
  Files: traderos/domain/repositories/market_data_repository.py, traderos/infrastructure/repositories/
  Testing: CRUD tests, time-series range query tests
  ADR: No
  Source: [C:8.1]

WP-019: DataCollector ABC & Registry
  Priority: High | Epic: 2.1 | Effort: 2d
  Files: traderos/domain/collectors/
  Testing: Collector registration and selection tests
  ADR: No
  Source: [C:8.1]

WP-020: BinanceCollector Port
  Priority: High | Epic: 2.1 | Effort: 2d
  Files: traderos/infrastructure/collectors/binance_collector.py
  Testing: Mocked exchange tests, normalization tests
  ADR: No
  Source: [C:8.1], [A:ccxt used directly]

WP-021: YFinanceCollector Port
  Priority: High | Epic: 2.1 | Effort: 1d
  Files: traderos/infrastructure/collectors/yfinance_collector.py
  Testing: Mocked exchange tests, normalization tests
  ADR: No
  Source: [C:8.1]

WP-022: MockDataCollector Port
  Priority: Medium | Epic: 2.1 | Effort: 1d
  Files: traderos/infrastructure/collectors/mock_collector.py
  Testing: Deterministic output verification
  ADR: No
  Source: [C:8.1]

WP-023: Data Normalization & Validation Service
  Priority: High | Epic: 2.1 | Effort: 3d
  Files: traderos/domain/services/data_normalizer.py, traderos/domain/services/data_validator.py
  Testing: Gap detection, outlier rejection, sequence validation tests
  ADR: No
  Source: [C:8.1]

WP-024: AnalysisService Implementation
  Priority: High | Epic: 2.2 | Effort: 4d
  Files: traderos/domain/services/analysis_service.py
  Testing: All indicators vs. hand-calculated values
  ADR: No
  Source: [C:8.2]

WP-025: Regime Detection Service
  Priority: High | Epic: 2.2 | Effort: 2d
  Files: traderos/domain/services/regime_detection.py
  Testing: Synthetic trending/ranging/volatile data classification
  ADR: No
  Source: [C:8.2]

WP-026: CorrelationService Port
  Priority: Medium | Epic: 2.2 | Effort: 1d
  Files: traderos/domain/services/correlation_service.py
  Testing: Correlation vs. numpy reference
  ADR: No
  Source: [C:8.2]

WP-027: SwingDetectionService Port
  Priority: High | Epic: 2.3 | Effort: 2d
  Files: traderos/domain/services/swing_detection.py
  Testing: Known swing points verification
  ADR: No
  Source: [C:8.3]

WP-028: LiquidityZoneService Port
  Priority: High | Epic: 2.3 | Effort: 2d
  Files: traderos/domain/services/liquidity_zone_service.py
  Testing: Zone clustering validation
  ADR: No
  Source: [C:8.3]

WP-029: SweepDetectionService Port
  Priority: Medium | Epic: 2.3 | Effort: 2d
  Files: traderos/domain/services/sweep_detection.py
  Testing: Sweep identification on known patterns
  ADR: No
  Source: [C:8.3]

WP-030: BreakoutDetectionService Port
  Priority: Medium | Epic: 2.3 | Effort: 2d
  Files: traderos/domain/services/breakout_detection.py
  Testing: Consolidation/breakout sequence detection
  ADR: No
  Source: [C:8.3]

WP-031: SessionAnalysisService Port
  Priority: Low | Epic: 2.3 | Effort: 1d
  Files: traderos/domain/services/session_analysis.py
  Testing: Session boundary correctness across timezones
  ADR: No
  Source: [C:8.3]
```

### Research Work Packages

```
WP-032: ResearchService Implementation
  Priority: High | Epic: 3.1 | Effort: 4d
  Files: traderos/domain/services/research_service.py
  Testing: Complete O-H-T-R-L workflow test
  ADR: No
  Source: [C:8.9]

WP-033: Hypothesis State Machine
  Priority: High | Epic: 3.1 | Effort: 2d
  Files: traderos/domain/entities/hypothesis.py
  Testing: All state transitions, invalid transitions rejected
  ADR: No
  Source: [C:6 Hypothesis]

WP-034: Experiment Configuration Capture
  Priority: High | Epic: 3.1 | Effort: 3d
  Files: traderos/domain/entities/experiment.py, traderos/domain/services/experiment_config.py
  Testing: Config serialization/deserialization roundtrip
  ADR: No
  Source: [C:6 Experiment], [C:P3 (Reproducibility)]

WP-035: AutoObservation Service
  Priority: Medium | Epic: 3.1 | Effort: 2d
  Files: traderos/domain/services/auto_observation.py
  Testing: Event→observation generation tests
  ADR: No
  Source: [C:8.9]

WP-036: KnowledgeGraphService Implementation
  Priority: High | Epic: 3.2 | Effort: 3d
  Files: traderos/domain/services/knowledge_graph_service.py
  Testing: Node/edge CRUD, traversal, path finding
  ADR: No
  Source: [C:8.10]

WP-037: Graph Traversal & Search Service
  Priority: High | Epic: 3.2 | Effort: 3d
  Files: traderos/domain/services/graph_traversal.py
  Testing: Depth-limited traversal, path finding, full-text search
  ADR: No
  Source: [C:8.10]

WP-038: Graph Visualization Service
  Priority: Medium | Epic: 3.2 | Effort: 2d
  Files: traderos/domain/services/graph_visualization.py
  Testing: Render correctness for known graphs
  ADR: No
  Source: [C:8.10]
```

### Trading Core Work Packages

```
WP-039: Strategy ABC & Registry
  Priority: High | Epic: 4.1 | Effort: 3d
  Files: traderos/domain/strategies/
  Testing: Registration, retrieval, evaluation dispatch
  ADR: No
  Source: [C:8.4]

WP-040: Strategy Versioning
  Priority: Medium | Epic: 4.1 | Effort: 2d
  Files: traderos/domain/strategies/versioning.py
  Testing: Version comparison, serialization, deterministic evaluation per version
  ADR: No
  Source: [C:8.4]

WP-041: Starter Strategy Ports (3 strategies)
  Priority: High | Epic: 4.1 | Effort: 3d
  Files: traderos/infrastructure/strategies/
  Testing: Each strategy evaluated against known market conditions
  ADR: No
  Source: [C:8.4], [C:6 Strategy]

WP-042: SignalService Implementation
  Priority: High | Epic: 4.2 | Effort: 3d
  Files: traderos/domain/services/signal_service.py
  Testing: Signal generation, validation, deduplication
  ADR: No
  Source: [C:8.5]

WP-043: RiskService Implementation
  Priority: Critical | Epic: 4.3 | Effort: 4d
  Files: traderos/domain/services/risk_service.py
  Testing: All position sizing, limit checks, kill switch scenarios
  ADR: No
  Source: [C:8.6]

WP-044: Position Sizing Methods (3+)
  Priority: High | Epic: 4.3 | Effort: 3d
  Files: traderos/domain/services/position_sizing/
  Testing: Kelly, fixed fraction, volatility-adjusted — hand-calculated verification
  ADR: No
  Source: [C:8.6]

WP-045: Kill Switch Implementation
  Priority: Critical | Epic: 4.3 | Effort: 2d
  Files: traderos/domain/services/kill_switch.py
  Testing: Activation, deactivation, edge cases
  ADR: No
  Source: [C:8.6]

WP-046: PortfolioService Implementation
  Priority: High | Epic: 4.4 | Effort: 4d
  Files: traderos/domain/services/portfolio_service.py
  Testing: Trade lifecycle, position aggregation, mark-to-market
  ADR: No
  Source: [C:8.7]

WP-047: Performance Analytics Service
  Priority: Medium | Epic: 4.4 | Effort: 3d
  Files: traderos/domain/services/performance_analytics.py
  Testing: All metrics vs. reference implementations
  ADR: No
  Source: [C:8.7]
```

### Execution & Simulation Work Packages

```
WP-048: ExecutionService & Order State Machine
  Priority: High | Epic: 5.1 | Effort: 4d
  Files: traderos/domain/services/execution_service.py, traderos/domain/entities/order.py
  Testing: All order state transitions, persistence, recovery
  ADR: No
  Source: [C:8.8]

WP-049: BrokerAdapter ABC
  Priority: High | Epic: 5.1 | Effort: 2d
  Files: traderos/domain/adapters/broker_adapter.py
  Testing: Interface contract tests
  ADR: No
  Source: [C:8.8]

WP-050: PaperBrokerAdapter
  Priority: High | Epic: 5.1 | Effort: 3d
  Files: traderos/infrastructure/adapters/paper_broker.py
  Testing: Fill simulation accuracy, edge cases
  ADR: No
  Source: [C:8.8], [C:8.12]

WP-051: BacktestingService Port & Extension
  Priority: High | Epic: 5.2 | Effort: 5d
  Files: traderos/domain/services/backtesting_service.py
  Testing: Deterministic results, cost model impact, metrics accuracy
  ADR: No
  Source: [C:8.11]

WP-052: Walk-Forward Optimization
  Priority: Medium | Epic: 5.2 | Effort: 3d
  Files: traderos/domain/services/walk_forward.py
  Testing: Validation on multiple windows
  ADR: No
  Source: [C:8.11]

WP-053: PaperTradingService
  Priority: High | Epic: 5.3 | Effort: 4d
  Files: traderos/domain/services/paper_trading_service.py
  Testing: Session lifecycle, fill simulation, recovery
  ADR: No
  Source: [C:8.12]

WP-054: Deviation Analysis Service
  Priority: Medium | Epic: 5.3 | Effort: 3d
  Files: traderos/domain/services/deviation_analysis.py
  Testing: Statistical significance detection
  ADR: No
  Source: [C:8.12]
```

### Platform Work Packages

```
WP-055: Unified CLI Framework
  Priority: High | Epic: 6.2 | Effort: 5d
  Files: traderos/interfaces/cli/
  Testing: All 20+ commands with valid/invalid inputs, JSON output parsing
  ADR: No
  Source: [C:8.17], [C:5 (Key Decision 3)]

WP-056: REST API Framework
  Priority: High | Epic: 6.2 | Effort: 5d
  Files: traderos/interfaces/api/
  Testing: All endpoints, error responses, auth, OpenAPI validation
  ADR: No
  Source: [C:8.15]

WP-057: WebSocket Stream
  Priority: Medium | Epic: 6.2 | Effort: 3d
  Files: traderos/interfaces/api/websocket.py
  Testing: Connection, message format, latency
  ADR: No
  Source: [C:8.15]

WP-058: Web Dashboard (Minimal)
  Priority: Medium | Epic: 6.2 | Effort: 5d
  Files: traderos/interfaces/dashboard/
  Testing: Component rendering, API integration
  ADR: No
  Source: [C:8.16]

WP-059: Health Check & Metrics Endpoints
  Priority: High | Epic: 6.4 | Effort: 3d
  Files: traderos/interfaces/api/health.py, traderos/infrastructure/metrics/
  Testing: Health aggregation, metric recording
  ADR: No
  Source: [C:8.18], [C:10.14]

WP-060: Run Manifest Service
  Priority: Medium | Epic: 6.4 | Effort: 2d
  Files: traderos/infrastructure/logging/run_manifest.py
  Testing: Manifest generation, completeness verification
  ADR: No
  Source: [C:P9 (Observability)]

WP-061: Audit Trail Service
  Priority: Medium | Epic: 6.4 | Effort: 2d
  Files: traderos/infrastructure/audit/
  Testing: Append-only verification, tamper detection
  ADR: No
  Source: [C:P3 (Traceable)]

WP-062: Notification Service
  Priority: Low | Epic: 6.3 | Effort: 3d
  Files: traderos/domain/services/notification_service.py
  Testing: Multi-channel delivery, rate limiting, aggregation
  ADR: No
  Source: [C:8.14]

WP-063: VisualizationService Port
  Priority: Medium | Epic: 6.1 | Effort: 4d
  Files: traderos/infrastructure/visualization/
  Testing: Chart generation, export format validation
  ADR: No
  Source: [C:8.13]
```

### Stabilization & Release Work Packages

```
WP-064: Integration Test Suite (Cross-Engine)
  Priority: High | Epic: All | Effort: 5d
  Files: tests/integration/
  Testing: End-to-end pipeline tests (data → analysis → signal → risk → portfolio)
  ADR: No
  Source: [C:10.4], [C:11 Definition of Done]

WP-065: Performance Benchmarking Suite
  Priority: Medium | Epic: All | Effort: 3d
  Files: tests/performance/
  Testing: Critical path benchmarks, regression detection
  ADR: No
  Source: [C:P10 (Performance is a Feature)]

WP-066: ADR Completion & Review
  Priority: High | Epic: All | Effort: 2d
  Files: docs/decisions/
  Testing: N/A (documentation review)
  ADR: All 12 ADRs
  Source: [C:16], [C:P7 (Architecture Before Features)]

WP-067: API OpenAPI Documentation
  Priority: High | Epic: 6.2 | Effort: 2d
  Files: traderos/interfaces/api/openapi/
  Testing: OpenAPI spec validation
  ADR: No
  Source: [C:8.15]

WP-068: Developer Documentation
  Priority: Medium | Epic: All | Effort: 3d
  Files: docs/
  Testing: N/A (documentation)
  ADR: No
  Source: [C:10.6]

WP-069: v1 Release Tag & Changelog
  Priority: High | Epic: All | Effort: 1d
  Files: CHANGELOG.md, VERSION
  Testing: N/A (release process)
  ADR: No
  Source: [C:10.11 (Git Standards)]
```

---

## 13 Critical Path Analysis

### Critical Path: Foundation → Architecture → Data → Analysis → Trading Core → Execution → Release

```
Month 1   ██ WP-001 (Makefile)          → WP-002 (pytest)           → WP-003 (lint)
Month 2   ██ WP-005 (Docker)            → WP-006 (CI/CD)             → WP-007 (DB migration)
Month 3   ██ WP-008 (Package structure)  → WP-009 (Entities)         → WP-010 (Repositories)
Month 4   ██ WP-013 (Config v2)          → WP-016 (Event bus)        → WP-017 (Arch tests)
Month 5   ██ WP-018 (MarketDataRepo)     → WP-019 (Collectors)       → WP-023 (Validation)
Month 6   ██ WP-024 (Analysis)           → WP-027 (Swing)            → WP-032 (Research)
Month 7   ██ WP-036 (Knowledge Graph)    → WP-039 (Strategy)         → WP-042 (Signals)
Month 8   ██ WP-043 (Risk)              → WP-046 (Portfolio)        → WP-048 (Execution)
Month 9   ██ WP-051 (Backtest)          → WP-053 (Paper Trading)    → WP-055 (CLI)
Month 10  ██ WP-056 (API)               → WP-059 (Health/Metrics)   → WP-062 (Notifications)
Month 11  ██ WP-064 (Integration Tests)  → WP-065 (Performance)      → WP-066 (ADRs)
Month 12  ██ WP-068 (Documentation)      → WP-069 (Release)
```

### Critical Path Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| WP-008 (Package restructure) causes import breakage | High | Incremental migration with compatibility layer |
| WP-016 (Event bus) design complexity | Medium | Start with simple pub/sub, add features later |
| WP-043 (Risk engine) numerical edge cases | Medium | Extensive edge case test suite |
| WP-048 (Execution) broker integration | High | Paper adapter first; live broker is lower priority |
| WP-055 (CLI) scope creep | Medium | Minimum viable CLI first, add commands iteratively |
| WP-064 (Integration tests) flakiness | Medium | Dedicated stabilization sprint |

---

## 14 Engineering Priority Matrix

### Priority Framework

Priority is determined by two dimensions:
- **Value**: Business impact + Architectural impact + Dependency value
- **Urgency**: Blocks other work + Risk of delay + Market timing

```
Priority 1 (Critical): Must do now. Blocks everything else.
Priority 2 (High): Must do this quarter. Unblocks major workstreams.
Priority 3 (Medium): Important but not blocking. Schedule within 2 quarters.
Priority 4 (Low): Nice to have. Schedule when capacity allows.
```

### Priority Matrix (Months 1–12)

| WP-ID | Description | Value | Urgency | Priority |
|-------|-------------|-------|---------|----------|
| WP-001 | Makefile & Tooling | 5 | 5 | **Critical** |
| WP-002 | pytest Migration | 5 | 5 | **Critical** |
| WP-003 | Linting/Formatting | 4 | 5 | **Critical** |
| WP-004 | Type Checking | 4 | 4 | **High** |
| WP-005 | Docker | 4 | 4 | **High** |
| WP-006 | CI/CD | 5 | 5 | **Critical** |
| WP-008 | Package Restructure | 5 | 4 | **Critical** |
| WP-009 | Domain Entities | 5 | 4 | **Critical** |
| WP-010 | Repository Interfaces | 5 | 4 | **Critical** |
| WP-011 | InMemory Repos | 4 | 4 | **High** |
| WP-013 | Config v2 | 3 | 3 | **High** |
| WP-016 | Event Bus | 4 | 3 | **High** |
| WP-017 | Architecture Tests | 5 | 4 | **Critical** |
| WP-018 | MarketDataRepo | 5 | 4 | **Critical** |
| WP-024 | Analysis Service | 4 | 3 | **High** |
| WP-032 | Research Service | 5 | 3 | **High** |
| WP-036 | Knowledge Graph | 4 | 3 | **High** |
| WP-039 | Strategy Framework | 5 | 3 | **High** |
| WP-042 | Signal Service | 4 | 3 | **High** |
| WP-043 | Risk Service | 5 | 3 | **High** |
| WP-046 | Portfolio Service | 4 | 3 | **High** |
| WP-048 | Execution Engine | 5 | 3 | **High** |
| WP-051 | Backtesting | 5 | 3 | **High** |
| WP-053 | Paper Trading | 4 | 2 | **Medium** |
| WP-055 | Unified CLI | 4 | 3 | **High** |
| WP-056 | REST API | 4 | 2 | **Medium** |
| WP-059 | Health/Metrics | 4 | 3 | **High** |
| WP-064 | Integration Tests | 5 | 3 | **High** |
| WP-065 | Performance Benchmarks | 3 | 2 | **Medium** |

---

## 15 Risk Register

| ID | Risk | Likelihood | Impact | Score | Mitigation | Owner | Status |
|----|------|------------|--------|-------|------------|-------|--------|
| R-01 | Team capacity insufficient to meet 12-month timeline | Medium | High | 12 | Phased delivery; prioritize critical path; defer low-priority features | PM | Active |
| R-02 | Architecture migration breaks existing functionality | High | High | 16 | Incremental strangler pattern; comprehensive test suite; parallel run validation | Tech Lead | Active |
| R-03 | Exchange API changes break data collectors | Medium | Medium | 9 | Collector interface isolates changes; monitoring for API changes | Data Eng | Active |
| R-04 | Backtest determinism failures due to floating-point | Medium | Medium | 9 | Tolerance-based assertions; fixed random seeds; reference implementations | Trading Eng | Active |
| R-05 | Performance targets not met (backtest > 5s, analysis > 1s) | Medium | High | 12 | Vectorized operations; profile early; optimize critical path | All | Active |
| R-06 | Event bus becomes single point of failure | Low | High | 8 | Fallback direct-call mode; circuit breaker pattern | Arch Eng | Active |
| R-07 | Knowledge graph queries too slow on SQLite | Medium | Medium | 9 | In-memory caching; PostgreSQL for production; query optimization | Research Eng | Active |
| R-08 | Fill simulation in paper trading not representative | Medium | High | 12 | Configurable fill model; compare against real broker fills | Trading Eng | Active |
| R-09 | ADR process creates documentation overhead | Low | Low | 3 | Lightweight ADR template; review as part of PR process | All | Active |
| R-10 | Dependency on external APIs (ccxt, yfinance) without fallback | Medium | High | 12 | MockCollector as permanent fallback; data caching | Data Eng | Active |
| R-11 | Team lacks trading domain expertise | Medium | Medium | 9 | Pair programming; trading books; domain modeling sessions | EM | Active |
| R-12 | Scope creep from research-first philosophy | Medium | Low | 6 | Strict Definition of Ready; architecture review gate | PM/Arch | Active |

### Risk Response Strategy

| Score | Response | Action |
|-------|----------|--------|
| 13–16 | Avoid | Restructure plan to eliminate or transfer risk |
| 9–12 | Mitigate | Active mitigation plan with owner and deadline |
| 5–8 | Accept | Monitor; contingency plan if triggered |
| 1–4 | Ignore | No action required |

---

## 16 ADR Implementation Schedule

| ADR | Title | Required By | Work Package | Status |
|-----|-------|-------------|--------------|--------|
| ADR-001 | Research-First over Execution-First | Completed | N/A | **Done** |
| ADR-002 | Modular Monolith with Extraction Path | Month 3 | WP-008 | Pending |
| ADR-003 | Event Bus as Nervous System | Month 4 | WP-016 | Pending |
| ADR-004 | Repository Pattern for Persistence | Month 3 | WP-010 | Pending |
| ADR-005 | SQLite Dev / PostgreSQL Prod | Month 2 | WP-007 | Pending |
| ADR-006 | CLI-First Interface Strategy | Month 9 | WP-055 | Pending |
| ADR-007 | Structured Logging as Default | Month 3 | WP-015 | Pending |
| ADR-008 | Backtest-to-Live Parity | Month 10 | WP-054 | Pending |
| ADR-009 | Knowledge Graph as Research Backbone | Month 6 | WP-036 | Pending |
| ADR-010 | Deprecation Strategy | Month 11 | WP-066 | Pending |
| ADR-011 | Plugin System Architecture | Month 12 | WP-066 | Deferred to v1.1 |
| ADR-012 | ML Model Integration Boundary | Month 12 | WP-066 | Deferred to v1.1 |

### ADR Template

```markdown
# ADR-NNN: [Title]

**Status**: [Proposed | Accepted | Deprecated | Superseded]
**Date**: YYYY-MM-DD
**Author**: [Name]

## Context
[What is the issue motivating this decision?]

## Decision
[What is the change being proposed?]

## Consequences
[What becomes easier or harder to do?]

## Alternatives Considered
[What other options were considered and why were they rejected?]
```

---

## 17 Testing & Verification Strategy

### Test Pyramid

```
        ╱╲
       ╱  ╲          E2E Tests (5%)
      ╱    ╲         Full pipeline, CLI, API
     ╱──────╲
    ╱        ╲      Integration Tests (15%)
   ╱          ╲     Cross-engine, repository, event bus
  ╱────────────╲
 ╱              ╲  Unit Tests (80%)
╱                ╲ Domain services, entities, validators
```

### Test Categories

| Category | Scope | Framework | Isolation | CI Stage |
|----------|-------|-----------|-----------|----------|
| Unit | Single class/function | pytest | Complete (mock all deps) | PR check |
| Integration | Multiple engines, repositories | pytest | In-memory repos, mock external APIs | PR check |
| E2E | Full pipeline | pytest + docker | Docker compose, mock exchanges | Nightly |
| Performance | Critical path benchmarks | pytest-benchmark | Isolated environment | Nightly |
| Architecture | Dependency rules | pytest-arch | N/A | PR check |
| Property | Invariant verification | hypothesis | Complete | Weekly |

### Test Naming Convention

```
test_<module>_<scenario>_<expected_behavior>

Examples:
test_risk_service_drawdown_breach_rejects_signal
test_backtesting_engine_deterministic_same_input_same_output
test_signal_service_duplicate_long_short_keeps_highest_confidence
```

### Coverage Targets

| Module | Minimum Coverage | Stretch Target |
|--------|------------------|----------------|
| Domain entities | 95% | 100% |
| Domain services | 95% | 100% |
| Repository interfaces | 95% | 100% |
| Infrastructure implementations | 85% | 90% |
| Interfaces (CLI, API) | 85% | 90% |
| Application services | 90% | 95% |
| **Overall** | **90%** | **95%** |

### Test Environment Strategy

| Environment | Database | Data Sources | Purpose |
|-------------|----------|--------------|---------|
| CI | In-memory | Mock | Fast validation |
| Dev | SQLite | Mock + cached real | Development |
| Staging | PostgreSQL | Cached real | Integration testing |
| Production | PostgreSQL | Live | Real trading |

---

## 18 Quality Gates

Every PR must pass the following gates before merge:

### Gate 1: Pre-Commit (Local)

```
□ make lint            (ruff -- 0 errors)
□ make format-check    (black --check -- 0 reformats)
□ make typecheck       (pyright strict -- 0 errors)
□ make test-quick      (unit + integration tests)
```

### Gate 2: CI (Pull Request)

```
□ Lint check            (ruff)
□ Format check          (black --check, isort --check)
□ Type check            (pyright)
□ Unit tests            (pytest unit/ --cov --cov-fail-under=90)
□ Integration tests     (pytest integration/)
□ Architecture tests    (pytest tests/architecture/)
□ No new architecture violations (compared to main)
```

### Gate 3: Review (Code Review)

```
□ Architecture compliance (follows dependency rules)
□ Test coverage adequate (new code >= 90%)
□ No degradation of existing tests
□ ADR written if significant architectural decision
□ Documentation updated
□ CHANGELOG.md entry added
□ No secrets or credentials in code
□ Error handling follows Constitution standards
□ Type hints complete and correct
```

### Gate 4: Staging (Pre-Release)

```
□ Full test suite passes (all categories)
□ Integration tests pass with PostgreSQL
□ E2E pipeline test passes
□ Performance benchmarks within threshold
□ Security scan passes (no critical findings)
```

### Gate 5: Release (v1 Candidate)

```
□ All quality gates 1–4 pass for all PRs since last release
□ Test coverage >= 90% overall
□ All ADRs documented
□ Portfolio Readiness Checklist passes
□ Hiring Readiness Checklist passes
□ Architecture enforcement tests pass
□ No P0 or P1 bugs open
□ Performance targets met
```

### Quality Gate Violations

| Gate | Failure | Action |
|------|---------|--------|
| Pre-commit | Lint/type error | Fix before commit. No exceptions. |
| CI | Test failure | Fix before merge. No force-merges. |
| Review | Architecture violation | Reject PR. Escalate to Architecture Review Board if disagreement. |
| Staging | Performance regression | Rollback. Investigate. Fix in separate PR. |
| Release | Checklist incomplete | Do not release. Document remaining items with timeline. |

---

## 19 Code Review Workflow

### Review Process

```
1. Author creates PR with description template
2. CI runs automatically (Gate 2)
3. Author assigns reviewer(s)
4. Reviewer performs review (Gate 3)
5. Author addresses feedback
6. Reviewer approves
7. Author merges (squash-merge)
```

### PR Description Template

```markdown
## Description
[What does this PR do? 2-3 sentences]

## Related
- Epic: [Epic X.X]
- Work Package: [WP-XXX]
- ADR: [ADR-NNN if applicable]
- Constitution: [C:section references]
- Audit: [A:finding references]

## Type
[ ] Feature
[ ] Fix
[ ] Refactor
[ ] Test
[ ] Documentation
[ ] Infrastructure

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Documentation
- [ ] Docstrings updated
- [ ] CHANGELOG.md updated
- [ ] README updated (if needed)

## Checklist
- [ ] Architecture compliance verified
- [ ] No new architecture violations
- [ ] Error handling follows standards
- [ ] Logging follows standards
- [ ] Type hints complete
```

### Review Response Times

| Priority | First Response | Approval Target |
|----------|---------------|-----------------|
| Critical | < 2 hours | < 4 hours |
| High | < 4 hours | < 8 hours |
| Medium | < 24 hours | < 48 hours |
| Low | < 48 hours | < 72 hours |

### Review Responsibilities

**Author**:
- Provide clear description with context
- Keep PR size < 400 lines changed
- Respond to feedback within 24 hours
- Update PR with changes

**Reviewer**:
- Verify architecture compliance
- Verify test coverage
- Check for edge cases and error handling
- Verify documentation completeness
- Approve only when all concerns addressed

---

## 20 Definition of Ready

A work package is ready for sprint planning when all criteria are met:

```
□ Work package documented with template (Section 11)
□ Background references Constitution section(s)
□ Background references Audit finding(s) (if applicable)
□ Background references Capability (Section 4)
□ Acceptance criteria are specific and testable
□ Dependencies are identified and unblocked
□ Technical approach is outlined
□ Files likely affected are identified
□ Testing requirements are specified
□ Estimated effort is provided
□ Rollback strategy is documented
□ ADR requirement is determined
```

A work package that does not meet these criteria is **not ready** and must be refined before it enters a sprint. No exceptions.

---

## 21 Definition of Done

Reproduced from the Constitution [C:11] for operational enforcement:

### Architecture
- [ ] Architecture Decision Record written (if significant)
- [ ] Follows dependency direction (Domain → no infra deps)
- [ ] Interfaces defined by consumers
- [ ] No circular dependencies
- [ ] Fits within existing subsystem boundaries
- [ ] Subsystem communication through event bus (not direct calls)

### Testing
- [ ] Unit tests cover all code paths (normal, edge, error)
- [ ] Integration tests cover subsystem boundaries
- [ ] Test coverage >= 90%
- [ ] Tests run in isolation (no network, no shared state)
- [ ] Tests complete in < 30 seconds total
- [ ] Tests are deterministic

### Documentation
- [ ] Docstrings for all public APIs (Google style)
- [ ] README updated if feature changes how system is used
- [ ] CHANGELOG.md entry added
- [ ] CLI --help output updated
- [ ] API documentation updated (if applicable)

### Performance
- [ ] Performance benchmarks established before optimization
- [ ] Feature meets performance expectations defined in subsystem spec
- [ ] No unbounded memory usage
- [ ] Database queries indexed and EXPLAIN-planned

### Security
- [ ] No secrets in code
- [ ] Input validated at all boundaries
- [ ] Parameterized queries used (no SQL injection risk)
- [ ] Authentication/authorization considered (if applicable)

### Observability
- [ ] Structured logging implemented for all new code paths
- [ ] Key metrics emitted (count, duration, errors)
- [ ] Error messages are actionable
- [ ] Correlation ID propagated

### Maintainability
- [ ] Code reviewed by at least one other engineer
- [ ] No duplicated logic
- [ ] Functions < 60 lines, classes < 400 lines
- [ ] Cyclomatic complexity < 10 per function
- [ ] All type hints present and correct

### Developer Experience
- [ ] Feature can be tested locally without external dependencies
- [ ] Feature has a CLI command or API endpoint
- [ ] Configuration documented (if applicable)
- [ ] Migration path documented (if applicable)

---

## 22 Documentation Workflow

### Documentation Types

| Type | Location | Format | Update Trigger | Owner |
|------|----------|--------|----------------|-------|
| Architecture | `docs/architecture/` | Markdown + diagrams | Architecture change | Architect |
| Decisions | `docs/decisions/ADR-*.md` | Markdown (template) | Significant decision | Author |
| User guide | `docs/user/` | Markdown | New feature | PM |
| API reference | Auto-generated from OpenAPI | OpenAPI/Swagger | API change | API dev |
| CLI reference | Auto-generated from argparse | Markdown | CLI change | CLI dev |
| README | `README.md` | Markdown | Major release | All |
| CHANGELOG | `CHANGELOG.md` | Markdown | Every PR | Author |

### Documentation Standards

Each document must include:
- Title and purpose
- Last updated date
- Applies-to version
- Cross-references to related docs

### Documentation Review

- Every PR that adds or modifies a feature must update relevant docs
- Documentation-only PRs are valid and encouraged
- Monthly documentation review identifies stale entries
- Stale entries > 3 months old are flagged in the debt inventory

---

## 23 Release Strategy

### Versioning

TraderOS follows **Semantic Versioning** (MAJOR.MINOR.PATCH):

- **MAJOR** (v1, v2): Breaking changes to public API or architecture
- **MINOR** (v1.1, v1.2): New capabilities, backward-compatible
- **PATCH** (v1.0.1, v1.0.2): Bug fixes, performance improvements

Pre-release tags: `v1.0.0-alpha.1`, `v1.0.0-beta.1`, `v1.0.0-rc.1`

### Release Cadence

| Type | Frequency | Target | Process |
|------|-----------|--------|---------|
| Internal | Weekly | Sprint demo | Tagged `v0.x.x-dev` |
| Alpha | Monthly | Internal testing | Tagged `v0.x.x-alpha` |
| Beta | Quarterly | Limited external | Tagged `v0.x.x-beta` |
| Stable | Per milestone | Public release | Tagged `v1.x.x` |

### Release Process

```
1. Code freeze (48h before target)
   - Only bug fixes and documentation allowed
   - All PRs require explicit release manager approval

2. Staging deployment
   - Full test suite (all categories)
   - E2E pipeline tests
   - Performance benchmarks
   - Security scan

3. Release candidate
   - Tag vX.X.X-rc.N
   - Deploy to staging
   - 24h observation period

4. Release
   - Tag vX.X.X
   - Update CHANGELOG.md
   - Update VERSION file
   - Docker image build and push
   - Release notes published

5. Post-release
   - Monitor for 48h
   - Address any P0 issues immediately (hotfix branch)
   - Update roadmap
```

### Hotfix Process

```
1. Branch from release tag (hotfix/vX.X.X-Y)
2. Minimal fix (no refactoring, no new features)
3. CI must pass
4. Review by at least 2 engineers
5. Merge to main and release tag
6. Cherry-pick to develop branches
```

---

## 24 Portfolio Readiness Checklist

Before TraderOS v1 can be presented as a portfolio-quality codebase:

### Architecture
- [ ] 4-layer architecture enforced by automated tests
- [ ] No infrastructure imports in domain code
- [ ] All repositories have both in-memory and SQLite implementations
- [ ] Event bus operational with 5+ event types
- [ ] Domain entities defined for all 15+ core concepts
- [ ] Architecture dependency direction verified by CI

### Code Quality
- [ ] 90%+ test coverage overall
- [ ] 95%+ test coverage on domain code
- [ ] All tests pass in < 30 seconds
- [ ] Zero lint errors (ruff strict)
- [ ] Zero type errors (pyright strict)
- [ ] All functions < 60 lines
- [ ] Cyclomatic complexity < 10
- [ ] No duplicated code (checked by CI)

### Engineering Infrastructure
- [ ] CI/CD pipeline runs on every push
- [ ] Pre-commit hooks enforced
- [ ] Docker development environment
- [ ] Makefile with test/lint/typecheck/build targets
- [ ] Proper .gitignore (.env, __pycache__, .db, exports)
- [ ] `.env.example` documents all environment variables

### Documentation
- [ ] README explains project purpose, setup, and architecture
- [ ] CHANGELOG.md documents all changes since v0.2
- [ ] All 12 ADRs written and reviewed
- [ ] All public APIs have Google-style docstrings
- [ ] CLI --help output is comprehensive
- [ ] OpenAPI documentation is complete

### Testing
- [ ] Unit tests for all domain services
- [ ] Integration tests for all repository implementations
- [ ] Architecture tests verify dependency direction
- [ ] Property-based tests for critical algorithms
- [ ] Performance benchmarks for critical paths
- [ ] Tests are deterministic and isolated

### Research & Trading
- [ ] Complete O-H-T-R-L workflow operational
- [ ] Knowledge graph with traversal and search
- [ ] Strategy framework with 3+ example strategies
- [ ] Backtesting with cost modeling
- [ ] Paper trading with fill simulation
- [ ] Risk management with position sizing, kill switch
- [ ] Portfolio tracking with performance analytics

### Observability
- [ ] Structured JSON logging enabled everywhere
- [ ] Correlation ID propagated through all subsystems
- [ ] Health check endpoint operational
- [ ] Metrics endpoint with Prometheus format
- [ ] Run manifests generated for every pipeline run
- [ ] Audit trail operational

---

## 25 Hiring Readiness Checklist

Before presenting TraderOS publicly to potential engineering hires:

### Technical Interview Readiness
- [ ] A candidate can clone, `make setup`, `make test` in < 5 minutes
- [ ] Architecture is understandable from directory structure alone
- [ ] ADRs explain why decisions were made, not just what
- [ ] Test suite demonstrates engineering rigor (coverage, isolation, speed)
- [ ] CLI demonstrates product thinking (help output, error messages)

### Candidate Experience
- [ ] README gives clear mental model of the platform
- [ ] First contribution path is documented (CONTRIBUTING.md or equivalent)
- [ ] A meaningful contribution is possible on day 1 (clear starter tasks)
- [ ] Code style is consistent — every file looks like same author
- [ ] PR history shows disciplined engineering practices

### Engineering Signal
- [ ] No file exists that the team is embarrassed to show
- [ ] No test fails without immediate known fix
- [ ] No commit requires oral explanation
- [ ] No architecture decision is undocumented
- [ ] No bug fixable without adding a test
- [ ] Coverage > 90%, tests run in < 30 seconds
- [ ] Every PR has meaningful description and review

### Demo Readiness
- [ ] Full pipeline runs end-to-end on demo data
- [ ] CLI demonstrates all 20+ commands successfully
- [ ] Research workflow demo (observe → hypothesize → test → learn)
- [ ] Backtest demo (strategy selection, execution, results)
- [ ] Paper trading demo (live data, signal generation, fill simulation)
- [ ] Knowledge graph demo (entity creation, traversal, search)

---

## 26 Engineering Dashboard

### Sprint Dashboard — SPRINT 12 (Programme A: Core Loop Integrity, 2026-07-31)

```
SPRINT 12 — CORE LOOP INTEGRITY (2026-07-31)
────────────────────────────────────────────────────────────────────
Scope:          correctness only (Code Freeze — no features/dashboards)
Defects closed: D1-D6, D8, D9 (D7 reclassified by-design) → 8/9
New regressions: +11 invariant tests (tests/test_core_loop_invariants.py)
Blocked:        0 items
Risk count:     1 active (load-sensitive API/orchestrator flake — see
                CORE_LOOP_EVIDENCE.md §4.4; unrelated to diff)

TEST COVERAGE (python3 -m pytest -q -p no:randomly)
────────────────────────────────────────────────────────────────────
Overall:      84.63% (target: 70% gate — exceeded)
Tests:        843 passed (baseline 832 → +11)
Warnings:     environment-dependent, non-fatal

QUALITY
────────────────────────────────────────────────────────────────────
Lint errors:  0 on src/traderos (11 pre-existing errors confined to
              test files: test_dependency_direction, test_audit_integrity,
              test_backup, test_cycle_executor, test_preflight_service)
Type errors:  0 (pyright src/traderos)
Arch violations: 0
Build status: ✅

PROGRAMME A ROADMAP (from STRATEGIC_COMPLETION_BLUEPRINT.md)
────────────────────────────────────────────────────────────────────
A1 Loop correctness:   ✅ COMPLETE (evidence: CORE_LOOP_TRUTH.md,
                        CORE_LOOP_EVIDENCE.md)
A2 Analysis layer:     ⏳ carried forward (out of correctness-only scope)
A3 Refactor for tests: ⏳ carried forward
A4 Hygiene sweep:      ⏳ carried forward
```

### Sprint Dashboard — SPRINT 13 (Programme B: Operational Trust, 2026-07-31)

```
SPRINT 13 — OPERATIONAL TRUST (2026-07-31)
────────────────────────────────────────────────────────────────────
Scope:          survivability only (Code Freeze — no features/UI/commercial)
Findings closed: OT-001…OT-011 → 11/11 (OT-001 live connectivity is a
                 declared remaining risk; structure + pure-frame tests done)
New regressions: +51 tests (tests/test_programme_b_operational_trust.py)
Blocked:        0 items
Risks:          2 declared, not fabricated:
                R-01 OT-001 live Binance WS (needs network + websockets pkg)
                R-02 live Alpaca/Postgres behavior (no credentials/server)

TEST COVERAGE (python3 -m pytest -q -p no:randomly)
────────────────────────────────────────────────────────────────────
Overall:      83.77% (target: 70% gate — exceeded)
Tests:        864 passed (baseline 843 → +21 net; incl. 51 new B tests
                minus removed/consolidated)
Warnings:     environment-dependent, non-fatal

QUALITY
────────────────────────────────────────────────────────────────────
Lint errors:  0 on src/traderos
Type errors:  0 (pyright src/traderos)
Arch violations: 0
Build status: ✅

PROGRAMME B DELIVERABLES (from STRATEGIC_COMPLETION_BLUEPRINT.md)
────────────────────────────────────────────────────────────────────
B0 Trust matrix:   ✅ docs/engineering/OPERATIONAL_TRUST_MATRIX.md
B1 Data trust:     ✅ OT-004 tick validation; OT-007 candle robustness;
                    OT-008 bounded retention
B2 Lifecycle trust: ✅ OT-002 durable journal + manifest; OT-003 outbox;
                    OT-006 serialized events; OT-009 fill guards
B3 Backend/API:    ✅ OT-005 PG migrations (H7); OT-010 bounded health
                    + /healthz + /health
B4 Transport:      ✅ OT-001 BinanceStreamTransport (thin, tested) —
                    LIVE CONNECTIVITY STILL UNVERIFIED (R-01)
B5 Concurrency:    ✅ OT-011 thread-safe sqlite
B6 Evidence:       ✅ docs/engineering/RECOVERY_TRUTH.md,
                    docs/engineering/FAILURE_INJECTION_REPORT.md
PRI (est.):       22 → 70+ per blueprint target; live-connectivity
                    evidence outstanding (R-01/R-02)
```

### Monthly Dashboard — July 2026

```
MONTHLY REVIEW — JULY 2026
────────────────────────────────────────────────────────────────────
PROGRAMME A GATE
Gate:       Core-loop correctness gate — PASSED 2026-07-31
Criterion:  full suite green under deterministic ordering; 84.63%
            coverage; ruff/pyright clean; 8/9 defects closed with
            regression tests; remaining D7 documented by-design.

PROGRAMME B STATUS
Status:     IN PROGRESS — 11/11 OT findings closed as code+tests+evidence
            (OPERATIONAL_TRUST_MATRIX.md); PRI 22 → 70+ estimated.
Next gate:  Controlled live pilot — REQUIRES R-01/R-02 evidence
            (authenticated Binance WS, live Alpaca/Postgres drill).

WORKSTREAM PROGRESS
WS-4 Trading Core:  [██████████████░░░░░░] 70% (Programme B closed;
                     live-connectivity + backtest loop remain)
WS-2 Data & Analysis: [░░░░░░░░░░░░░░░░░░░░] 0% (A2 carried forward)

TECHNICAL RISKS
R-01: Live Binance WebSocket connectivity unverified (no network in
      sandbox; websockets package absent). Structural + pure-frame
      tests pass. Live validation is a deployment-time step.
R-02: Live Alpaca cancel/replace semantics + Postgres failover
      unverified (no credentials/server). Declared, not fabricated.
```

## 27 Weekly Engineering Operating Rhythm

### Monday: Sprint Planning & Refinement

| Time | Activity | Participants | Duration |
|------|----------|--------------|----------|
| 09:00 | Sprint planning (week N+1) | All engineers | 60 min |
| 10:00 | Work package refinement | PM + relevant engineers | 30 min |
| 10:30 | Debt triage | All engineers | 15 min |
| 10:45 | Individual work begins | — | — |

### Tuesday–Thursday: Execution

| Time | Activity | Participants | Duration |
|------|----------|--------------|----------|
| 09:30 | Standup | All engineers | 15 min |
| 15:00 | Pair programming (optional) | 2 engineers | 60 min |
| Async | Code reviews | Reviewer + author | — |

### Friday: Review & Demo

| Time | Activity | Participants | Duration |
|------|----------|--------------|----------|
| 09:00 | Standup + week recap | All engineers | 15 min |
| 14:00 | Sprint demo | All engineers + stakeholders | 30 min |
| 14:30 | Retrospective | All engineers | 30 min |
| 15:00 | Risk register review | PM + Tech Lead | 15 min |

### Daily Standup Template

```
1. What did I complete yesterday?
2. What am I working on today?
3. What is blocking me?
4. What debt did I pay? (must be > 0 most days)
```

---

## 28 Monthly Architecture Review Process

### Schedule

**Last Friday of every month**, 14:00–16:00

### Attendees

- All engineers (mandatory)
- CTO / Architecture Lead (chair)

### Agenda

```
14:00 – Architecture Metrics Review (15 min)
  - Architecture violation count (trend)
  - Migration progress (old modules → new modules)
  - ADR completion status
  - Test coverage by layer

14:15 – New Architecture Decisions (30 min)
  - Review new ADRs written this month
  - Discuss open architecture questions
  - Resolve architecture disagreements

14:45 – Architecture Violation Review (15 min)
  - Review new violations introduced
  - Assign owners for remediation
  - Set deadline for each violation

15:00 – Migration Progress (15 min)
  - Review strangler fig progress
  - Identify stuck migrations
  - Re-prioritize if needed

15:15 – Technical Debt Review (30 min)
  - Review top-10 debt items
  - Re-score debt items
  - Assign new debt items

15:45 – Action Items & Decisions (15 min)
  - Document all decisions
  - Assign action items
  - Publish meeting notes
```

### Architectural Review Criteria

Each month, the review board evaluates:

1. **Are we introducing new architecture violations faster than we fix existing ones?**
   - If yes: Stop feature work. Dedicate sprint to remediation.

2. **Are our ADRs keeping pace with architectural decisions?**
   - If no: Feature work without an ADR is held at review. This is a board
     decision recorded in the sprint log, not a machine gate: per OD-15 no
     principle counts as enforced until it has a check that can fail, so this
     item is governance, and the automated counterpart is
     `python3 scripts/ci/check_docs_drift.py`.

3. **Is the strangler fig pattern progressing?**
   - If no progress for 2 consecutive months: Escalate to CTO.

4. **Are we accumulating debt faster than the 20% budget can handle?**
   - If yes: Increase debt budget to 30% until balance is restored.

---

## 29 Quarterly Technical Debt Review

### Schedule

**Last week of every quarter** (March, June, September, December)

### Process

```
1. Full debt inventory (2 days before review)
   - Run automated debt detection tools
   - Score all debt items
   - Generate debt report

2. Debt review meeting (3 hours)
   - Review debt report
   - Identify systemic patterns
   - Update debt scoring parameters
   - Set debt reduction targets for next quarter

3. Debt reduction planning (1 hour)
   - Allocate debt budget for next quarter
   - Assign priority debt items to workstreams
   - Set quarterly debt reduction target

4. Debt retrospective (1 hour)
   - What debt did we create this quarter?
   - Why was it created?
   - How can we prevent it?
```

### Debt Scoring Review

Each quarter, review the debt scoring parameters:

| Parameter | Review Question | Adjustment Trigger |
|-----------|-----------------|-------------------|
| Severity thresholds | Are severity levels correctly calibrated? | Patterns of mis-scored items |
| Impact criteria | Do our impact criteria reflect actual cost? | Evidence of under/over estimation |
| Age factor | Is age penalty appropriate? | Old debt ignored or over-prioritized |
| Budget allocation | Is 20% sufficient for current debt level? | Debt increasing quarter over quarter |

### Debt Reduction Targets

| Quarter | Target | Measurement |
|---------|--------|-------------|
| Q1 | Reduce critical debt by 50% | Critical items from inventory |
| Q2 | Reduce high debt by 30% | High items from inventory |
| Q3 | Zero critical debt | No critical items in inventory |
| Q4 | Zero high debt | No high items in inventory |

---

## 30 Final 12-Month Execution Timeline

```
Month 1 (Sprints 1–2): Foundation
├── WP-001 Makefile & Tooling [CRITICAL]
├── WP-002 pytest Migration [CRITICAL]
├── WP-003 Linting/Formatting [CRITICAL]
├── WP-004 Type Checking [HIGH]
├── WP-005 Docker [HIGH]
├── WP-006 CI/CD Pipeline [CRITICAL]
└── WP-007 DB Migration Framework [MEDIUM]

Month 2 (Sprints 3–4): Architecture
├── WP-008 Package Restructure [CRITICAL]
├── WP-009 Domain Entities [CRITICAL]
├── WP-010 Repository Interfaces [CRITICAL]
├── WP-011 InMemory Repositories [HIGH]
├── WP-012 SQLite Repositories [HIGH]
├── WP-013 Config v2 [HIGH]
├── WP-014 Error Handling [HIGH]
├── WP-015 Structured Logging [HIGH]
└── WP-016 Event Bus [HIGH]
  🎯 MILESTONE M0: Engineering Foundation Complete
  📋 ADR-002, ADR-003, ADR-004, ADR-005, ADR-007 written

Month 3 (Sprints 5–6): Architecture + Data
├── WP-017 Architecture Tests [CRITICAL]
├── WP-018 MarketDataRepository [HIGH]
├── WP-019 Collector ABC & Registry [HIGH]
├── WP-020 BinanceCollector Port [HIGH]
├── WP-021 YFinanceCollector Port [HIGH]
├── WP-022 MockCollector Port [MEDIUM]
└── WP-023 Data Normalization/Validation [HIGH]

Month 4 (Sprints 7–8): Data + Analysis
├── WP-024 AnalysisService [HIGH]
├── WP-025 Regime Detection [HIGH]
├── WP-026 CorrelationService [MEDIUM]
├── WP-027 SwingDetectionService [HIGH]
├── WP-028 LiquidityZoneService [HIGH]
├── WP-029 SweepDetectionService [MEDIUM]
├── WP-030 BreakoutDetectionService [MEDIUM]
└── WP-031 SessionAnalysisService [LOW]
  🎯 MILESTONE M1: Architecture Framework Complete
  🎯 MILESTONE M2: Data Platform Complete

Month 5 (Sprints 9–10): Research
├── WP-032 ResearchService [HIGH]
├── WP-033 Hypothesis State Machine [HIGH]
├── WP-034 Experiment Config Capture [HIGH]
├── WP-035 AutoObservation Service [MEDIUM]
├── WP-036 KnowledgeGraphService [HIGH]
├── WP-037 Graph Traversal & Search [HIGH]
└── WP-038 Graph Visualization [MEDIUM]
  🎯 MILESTONE M3: Analysis & Liquidity Complete

Month 6 (Sprints 11–12): Research + Strategy
├── WP-039 Strategy ABC & Registry [HIGH]
├── WP-040 Strategy Versioning [MEDIUM]
├── WP-041 Starter Strategy Ports [HIGH]
├── WP-042 SignalService [HIGH]
└── (continued research wrap-up)
  🎯 MILESTONE M4: Research Platform Complete
  📋 ADR-009 written

Month 7 (Sprints 13–14): Trading Core
├── WP-043 RiskService [CRITICAL]
├── WP-044 Position Sizing Methods [HIGH]
├── WP-045 Kill Switch [CRITICAL]
├── WP-046 PortfolioService [HIGH]
└── WP-047 Performance Analytics [MEDIUM]

Month 8 (Sprints 15–16): Trading Core + Execution
├── WP-048 ExecutionService [HIGH]
├── WP-049 BrokerAdapter ABC [HIGH]
├── WP-050 PaperBrokerAdapter [HIGH]
└── (trading core completion)
  🎯 MILESTONE M5: Trading Core Complete

Month 9 (Sprints 17–18): Execution + Backtest
├── WP-051 BacktestingService [HIGH]
├── WP-052 Walk-Forward Optimization [MEDIUM]
├── WP-053 PaperTradingService [HIGH]
├── WP-054 Deviation Analysis [MEDIUM]
└── WP-055 Unified CLI Framework [HIGH]
  🎯 MILESTONE M6: Execution Complete
  📋 ADR-006, ADR-008 written

Month 10 (Sprints 19–20): Platform
├── WP-056 REST API Framework [MEDIUM]
├── WP-057 WebSocket Stream [MEDIUM]
├── WP-058 Web Dashboard [MEDIUM]
├── WP-059 Health Check & Metrics [HIGH]
├── WP-060 Run Manifest Service [MEDIUM]
├── WP-061 Audit Trail Service [MEDIUM]
├── WP-062 Notification Service [LOW]
└── WP-063 VisualizationService Port [MEDIUM]
  🎯 MILESTONE M7: Backtesting & Paper Trading Complete

Month 11 (Sprints 21–22): Stabilization
├── WP-064 Integration Test Suite [HIGH]
├── WP-065 Performance Benchmarks [MEDIUM]
├── WP-066 ADR Completion & Review [HIGH]
├── WP-067 API OpenAPI Documentation [HIGH]
└── (performance optimization, bug fixing)
  📋 ADR-010, ADR-011, ADR-012 written

Month 12 (Sprints 23–24): Release
├── WP-068 Developer Documentation [MEDIUM]
├── WP-069 v1 Release Tag [HIGH]
├── Portfolio Readiness Checklist review
├── Hiring Readiness Checklist review
├── Final quality gate review
└── v1.0.0 tagged and released
  🎯 MILESTONE M8: Platform Complete
  🎯 MILESTONE M9: v1 Release

───────────────────────────────────────────────────────
           TRA DeOS v1.0.0 RELEASED
───────────────────────────────────────────────────────
```

### Timeline Summary

| Quarter | Months | Focus | Milestones | ADRs |
|---------|--------|-------|------------|------|
| Q1 | 1–3 | Foundation & Architecture | M0, M1 | ADR-002–005, ADR-007 |
| Q2 | 4–6 | Data, Analysis, Research | M2, M3, M4 | ADR-009 |
| Q3 | 7–9 | Trading Core, Execution | M5, M6 | ADR-006, ADR-008 |
| Q4 | 10–12 | Platform, Stabilization, Release | M7, M8, M9 | ADR-010–012 |

---

## Appendix: Traceability Matrix

Every work package in this programme is traceable to:

| Trace Target | Example |
|--------------|---------|
| Constitution Section | `C:8.1` (Market Data Engine) |
| Constitution Principle | `C:P3` (Every Decision Traceable) |
| Constitution Subsystem | `C:S8.1` (Market Data Engine spec) |
| Audit Finding | `A:Docker gap` (No Docker) |
| Capability | `CAP-01.01` (CI/CD Pipeline) |
| Measurable Outcome | "test coverage >= 90%" |

This matrix ensures no orphan tasks. Every line of code written in this programme serves a documented, justified purpose.

---

**End of TraderOS v1 Master Execution Programme**

*This document is the operational authority for all engineering execution. It is derived from the TraderOS v1 Engineering Constitution and supersedes all prior plans, backlogs, and roadmaps. It will be reviewed and updated monthly by the Architecture Review Board.*
