# TraderOS v1 Engineering Constitution

> **Version**: 1.0
> **Status**: Ratified
> **Scope**: All engineering decisions within the TraderOS repository
> **Authority**: Supreme — supersedes all prior documents, conventions, and habits

---

## 1 Executive Vision

### One Paragraph

TraderOS is a research-first operating system for systematic traders. It ingests raw market data, transforms it into analyzable structure, enables hypothesis-driven research, executes strategies with disciplined risk management, records every outcome as evidence, and evolves its knowledge graph with every cycle. It is not a trading bot — it is the platform *on which* trading bots, strategies, experiments, and intelligence are built, tested, validated, and retired.

### One Sentence

TraderOS is the engineering platform that makes the scientific method the default mode of trading system development.

### Ten Words

Observe. Analyze. Hypothesize. Test. Execute. Learn. Improve. Repeat. Always.

---

### Mission

Eliminate guesswork from systematic trading by making every decision traceable to evidence, every outcome recordable as data, and every lesson persistable as knowledge.

### Vision

To become the default engineering substrate for quantitative trading research — the way Jupyter is for data exploration, the way Bloomberg is for market data, the way VS Code is for development.

### Engineering Philosophy

**Systems over scripts. Evidence over intuition. Composability over complexity. Architecture before features.**

Every line of code must justify its existence. Every subsystem must be replaceable. Every data point must be traceable. Every failure must be learnable.

### Product Philosophy

TraderOS is a *platform*, not an application. Its value is proportional to the quality of the research it enables, not the quantity of trades it executes. If the platform produces zero trades but produces one validated insight that changes how a trader thinks about a market, it has succeeded.

### Long-term Direction

TraderOS will evolve through four phases:

| Phase | Name | Horizon | Outcome |
|-------|------|---------|---------|
| 1 | Engineering Foundation | 0–12 months | Stable, tested, observable architecture |
| 2 | Research Platform | 6–18 months | Complete hypothesis-to-lesson pipeline |
| 3 | Trading Core | 12–24 months | Paper trading, then live execution |
| 4 | Intelligence Layer | 18–36 months | ML-assisted pattern discovery, knowledge graph inference, adaptive strategies |

All phases overlap. Phase 4 begins only when Phases 1–3 produce reliable data.

---

## 2 Core Principles

### Principle 1: Research First

**Why it exists**: Trading is a probabilistic domain. Without research, every trade is gambling. The platform must default to inquiry, not execution.

**How engineers apply it**:
- Every new feature must answer: "What question does this help a trader answer?"
- No execution path exists without a corresponding research path.
- The knowledge graph is the source of truth, not the trade log.

**Examples of correct implementation**:
- A new indicator is added first to the Analysis Engine, then to the Research Engine for hypothesis testing, and *finally* considered for strategy inclusion.
- Before a strategy goes live, it must have a `hypothesis_id` in its provenance chain.
- The system can run in research-only mode with zero execution capability.

**Examples of violations**:
- Adding execution code before the research pipeline is complete.
- Building a strategy without a testable hypothesis.
- Deleting old data to save space without archiving it for research reproducibility.

---

### Principle 2: Evidence over Opinion

**Why it exists**: Human intuition is biased, noisy, and non-reproducible. The platform exists to replace opinion with data.

**How engineers apply it**:
- Every configuration default must be justified by backtest or research data.
- Every alert must cite its triggering evidence.
- No parameter should exist without a documented rationale.

**Examples of correct implementation**:
- Risk limits are derived from backtest statistics, not gut feelings.
- Strategy parameters are stored alongside their performance metrics.
- The system logs *why* a decision was made, not just what decision was made.

**Examples of violations**:
- Hardcoding thresholds without a documented source.
- Tuning parameters manually on live data without logging the iterations.
- Suppressing logging because "it makes the output cleaner."

---

### Principle 3: Every Decision Traceable

**Why it exists**: When a trade loses money, the team must know exactly why. When a trade wins money, the team must know if it was skill or luck.

**How engineers apply it**:
- Every trade links back to a strategy, a hypothesis, and a signal.
- Every signal links back to the data that produced it.
- Every data point links back to its source and transformation history.

**Examples of correct implementation**:
- Trade records include `signal_id`, `hypothesis_id`, and `strategy_version`.
- The database schema enforces foreign key chains from trade → signal → feature → raw data.
- The system replays historical decisions identically when given the same input data.

**Examples of violations**:
- Deleting raw market data after derived features are computed.
- Running ad-hoc analysis outside the platform that cannot be reproduced.
- Using random seeds that are not recorded alongside experiment results.

---

### Principle 4: No Hidden State

**Why it exists**: Global variables, implicit configuration, and in-memory-only state produce bugs that are impossible to reproduce.

**How engineers apply it**:
- All state must be persisted or explicitly transient with a logged reason.
- Configuration must be immutable during a run.
- The system must be restartable from any checkpoint without side effects.

**Examples of correct implementation**:
- The `Config` object is frozen after initialization.
- All engine state is stored in the database, not in memory.
- A crashed pipeline resumes from its last checkpoint, not from the beginning.

**Examples of violations**:
- Using module-level mutable objects.
- Storing session state in global variables.
- Relying on `os.environ` mutations at runtime.

---

### Principle 5: Small Composable Systems

**Why it exists**: Large monolithic systems cannot be tested, replaced, or understood by a single engineer.

**How engineers apply it**:
- Every subsystem must fit in a single mental model.
- Subsystems communicate through well-defined interfaces, not shared state.
- Any subsystem can be replaced with a different implementation without changing its consumers.

**Examples of correct implementation**:
- The `DataPipeline` produces a `MarketDataFrame` regardless of whether the source is Binance, yfinance, or a CSV file.
- The `RiskEngine` takes a `PortfolioState` and returns a `RiskAssessment` — no direct database access.
- A new liquidity detection algorithm implements the same interface as the existing one.

**Examples of violations**:
- A function that takes 15 parameters.
- Importing from `database.db_manager` inside a visualization module.
- A class that does data collection, analysis, *and* visualization.

---

### Principle 6: Test Before Trust

**Why it exists**: Untested trading code loses real money. There is no argument against this.

**How engineers apply it**:
- No code merges to `main` without tests.
- Tests must cover normal cases, edge cases, and failure cases.
- Tests must execute in isolation without relying on external APIs or network access.

**Examples of correct implementation**:
- All data collectors have mock tests that verify data parsing.
- The RiskEngine has tests for every limit breach scenario.
- Backtest results are verified against hand-calculated expected values.

**Examples of violations**:
- "We'll add tests later."
- Tests that depend on network connectivity.
- Tests that pass because they never assert anything meaningful.

---

### Principle 7: Architecture Before Features

**Why it exists**: Building features on a weak foundation guarantees rewrites. A strong architecture makes features emerge naturally.

**How engineers apply it**:
- No feature is merged without a corresponding architecture decision record.
- Architectural changes are their own work items, separate from feature work.
- Every quarter includes an architecture stabilization sprint.

**Examples of correct implementation**:
- Adding a new data source requires updating the collector interface first, then implementing the collector.
- The message bus is designed and tested before any event producers or consumers are built.
- Performance benchmarks are established before optimization work begins.

**Examples of violations**:
- Adding a new CLI command by copying and pasting an existing one instead of refactoring the CLI framework.
- Building a backtesting engine that cannot be extended to support different order types.
- Using threading for performance without measuring the bottleneck first.

---

### Principle 8: Automation over Manual Work

**Why it exists**: Manual processes are slow, error-prone, and do not scale. Every manual step is a risk.

**How engineers apply it**:
- CI/CD runs all tests, linting, type checking, and security scanning on every push.
- Database migrations are automated and versioned.
- Documentation is generated from code where possible.

**Examples of correct implementation**:
- `pre-commit` hooks enforce formatting and type checking locally.
- A Makefile provides `test`, `lint`, `typecheck`, `build`, and `deploy` targets.
- The research pipeline auto-generates reports from experiment data.

**Examples of violations**:
- Manual deployment steps documented in a README.
- Engineers running linting only before release.
- SQL schema changes applied by hand in production.

---

### Principle 9: Observability by Default

**Why it exists**: A system that cannot be observed cannot be debugged, optimized, or trusted.

**How engineers apply it**:
- Every subsystem emits structured logs with consistent fields.
- Key metrics are exposed via a health endpoint.
- Every run produces a run manifest that records config, inputs, and outputs.

**Examples of correct implementation**:
- All log entries include `timestamp`, `module`, `level`, `run_id`, and `correlation_id`.
- The health endpoint reports system status, last successful run, and error count.
- Grafana dashboards exist for pipeline health and trading performance.

**Examples of violations**:
- Using `print()` for debugging.
- Logging without structured fields (e.g., `f"Price is {price}"` instead of `{"event": "price_update", "value": price}`).
- No health check or monitoring.

---

### Principle 10: Performance is a Feature

**Why it exists**: In trading, latency is not just a UX issue — it is a competitive advantage. But performance must be measured, not guessed.

**How engineers apply it**:
- Every optimization must be justified by a benchmark.
- Critical paths are identified and profiled.
- Backtest performance must be fast enough to enable iterative research.

**Examples of correct implementation**:
- The data pipeline uses vectorized operations (pandas/numpy) instead of loops.
- Database queries are indexed and EXPLAIN-planned.
- A 1-year backtest on 1-hour data completes in under 10 seconds.

**Examples of violations**:
- Premature optimization of non-critical paths.
- Using Python lists instead of numpy arrays for numerical computation.
- Adding caching without measuring the cache hit rate.

---

## 3 Product Definition

### What TraderOS Is

TraderOS is a **Trading Intelligence Platform** — an integrated engineering system for the complete lifecycle of systematic trading research and execution.

Core capabilities:

- **Market Data Ingestion**: Collect, normalize, validate, and store multi-source market data.
- **Market Analysis**: Compute indicators, detect regimes, map liquidity, analyze correlations.
- **Hypothesis-Driven Research**: Formulate observations, design experiments, run tests, record results, extract lessons.
- **Knowledge Management**: Persist every insight in a queryable knowledge graph that grows with use.
- **Strategy Development**: Define, register, parameterize, and version strategies.
- **Backtesting**: Simulate strategies against historical data with realistic costs and constraints.
- **Paper Trading**: Execute strategies against live data in simulation mode.
- **Live Trading**: Execute strategies against real markets with full risk management.
- **Performance Analytics**: Measure, visualize, and compare strategy performance.
- **Risk Management**: Enforce position sizing, drawdown limits, exposure limits, and kill switches.
- **Observability**: Every decision is logged, every metric is tracked, every run is reproducible.

### What TraderOS Is NOT

| Category | TraderOS | NOT |
|----------|----------|-----|
| Trading bot | A platform for building and testing strategies | A single automated trading script |
| Broker | Interfaces with brokers via adapters | A broker itself — no custody of funds |
| Exchange | Consumes exchange data | An exchange — no order matching or settlement |
| Charting software | Generates charts as research output | A real-time charting application (TradingView competitor) |
| Portfolio tracker | Tracks portfolio as part of research | A personal finance app (Mint competitor) |
| Research notebook | Structured, reproducible experiments | A freeform Jupyter notebook |
| Terminal | Provides CLIs for efficient interaction | A read-only data terminal (Bloomberg competitor) |
| Quant platform | Opinionated research-first workflow | A general-purpose quant library (QuantConnect competitor) |

### Unique Identity

TraderOS is the only platform that:

1. **Enforces the scientific method as a workflow** — not just a suggestion.
2. **Persists knowledge, not just trades** — the knowledge graph is a first-class citizen.
3. **Treats every run as an experiment** — reproducible by default.
4. **Separates research from execution** — you cannot trade what you have not researched.
5. **Integrates market structure analysis** — liquidity, sweeps, breakouts, sessions — as core infrastructure, not bolted-on indicators.

---

## 4 Engineering Vision

### Ideal Architecture

The ideal TraderOS architecture is a **modular event-driven monolith** with clearly bounded contexts, communicating through a lightweight message bus, persisted in a relational database, and observable through structured logging and metrics.

```
                    ┌──────────────────────────────┐
                    │     Interface Layer           │
                    │  CLI  │  REST API  │  Dashboard│
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │     Application Layer          │
                    │  Orchestrator  │  Workers      │
                    │  Scheduler    │  Event Bus    │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │     Domain Layer               │
                    │  Research  │  Trading          │
                    │  Analysis  │  Risk             │
                    │  Execution │  Portfolio        │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │     Infrastructure Layer       │
                    │  DB  │  Message Queue  │  Cache│
                    │  Logging │  Metrics    │  FS   │
                    └──────────────────────────────┘
```

### Why Each Layer Exists

**Interface Layer**: Humans and external systems interact through this layer. By isolating it, we ensure that all domain logic is accessible through multiple channels without duplication.

**Application Layer**: Orchestration, scheduling, and event routing belong here — not in domain code. This layer knows about workflows but not about trading logic.

**Domain Layer**: This is the heart of the system. Every trading concept lives here. It has zero infrastructure dependencies — it could run with a different database, message queue, or UI without changing a single line of domain code.

**Infrastructure Layer**: Databases, message queues, file systems, external APIs. Every infrastructure component has an interface in the domain layer and an implementation here. When we replace SQLite with PostgreSQL, we only touch this layer.

### Engineering Philosophy

1. **Dependency Rule**: Dependencies point inward. The domain layer knows nothing about infrastructure. Application layer depends on domain. Interface layer depends on application.

2. **Interface Ownership**: Interfaces are defined by the consumer, not the provider. The domain layer defines the interface it needs; the infrastructure layer implements it.

3. **Eventual Consistency**: Within a run, the system is consistent. Between runs, the system converges. This allows for efficient batch processing during research and real-time processing during execution.

4. **Fail Closed**: When any subsystem cannot determine the correct action, it defaults to the safest option. For risk: reduce position. For execution: cancel order. For data: skip symbol. For research: log warning, continue.

---

## 5 Target System Architecture

```
                              TRADEROS v1 SYSTEM ARCHITECTURE
                              ═══════════════════════════════

 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                             INTERFACE LAYER                                │
 │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌───────────┐  │
 │  │   CLI    │  │ REST API │  │Dashboard │  │ WebSocket  │  │   SDK     │  │
 │  │  (text)  │  │ (REST)   │  │  (web)   │  │  (stream)  │  │ (Python)  │  │
 │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘  └─────┬─────┘  │
 └───────┼─────────────┼─────────────┼───────────────┼───────────────┼───────┘
         │             │             │               │               │
 ┌───────▼─────────────▼─────────────▼───────────────▼───────────────▼───────┐
 │                           APPLICATION LAYER                              │
 │                                                                           │
 │  ┌─────────────────────────────────────────────────────────────────┐     │
 │  │                     EVENT BUS / MESSAGE BROKER                   │     │
 │  │  Topics: market.data │ analysis.result │ signal.generated       │     │
 │  │  │ strategy.evaluated │ order.executed │ research.recorded     │     │
 │  │  │ risk.breach │ system.heartbeat │ knowledge.updated         │     │
 │  └─────────────────────────────────────────────────────────────────┘     │
 │                                                                           │
 │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐     │
 │  │  Orchestrator   │  │   Scheduler    │  │      Workers           │     │
 │  │  Pipeline Mgmt  │  │  Cron-based    │  │  Async Task Executors  │     │
 │  │  Workflow Engine│  │  Interval      │  │  Research Jobs         │     │
 │  └────────────────┘  └────────────────┘  └────────────────────────┘     │
 │                                                                           │
 └───────────────────────────────────────────────────────────────────────────┘
                                    │
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                              DOMAIN LAYER                                 │
 │                                                                           │
 │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                │
 │  │ Market Data   │  │   Analysis    │  │  Liquidity    │                │
 │  │ Engine        │  │   Engine      │  │  Engine       │                │
 │  │ ─ Collect     │  │ ─ Indicators  │  │ ─ Swings      │                │
 │  │ ─ Normalize   │  │ ─ Regimes     │  │ ─ Zones       │                │
 │  │ ─ Validate    │  │ ─ Features    │  │ ─ Sweeps      │                │
 │  │ ─ Store       │  │ ─ Correlate   │  │ ─ Breakouts   │                │
 │  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘                │
 │          │                  │                  │                         │
 │  ┌───────▼──────────────────▼──────────────────▼───────┐                │
 │  │                   Signal Engine                      │                │
 │  │  ┌────────────┐  ┌────────────┐  ┌──────────────┐   │                │
 │  │  │ Strategy   │  │  Signal    │  │  Signal      │   │                │
 │  │  │ Evaluation │──┤ Generation │──┤ Validation   │   │                │
 │  │  └────────────┘  └────────────┘  └──────────────┘   │                │
 │  └──────────────────────────────────────────────────────┘                │
 │          │                                                               │
 │  ┌───────▼───────────────────────────────────────────────────────┐      │
 │  │                      Risk Engine                              │      │
 │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐     │      │
 │  │  │ Position     │  │  Exposure    │  │  Kill Switch     │     │      │
 │  │  │ Sizing       │──┤ Validation   │──┤ Monitoring       │     │      │
 │  │  └──────────────┘  └──────────────┘  └──────────────────┘     │      │
 │  └────────────────────────────────────────────────────────────────┘      │
 │          │                                                               │
 │  ┌───────▼───────────────────────────────────────────────────────┐      │
 │  │                   Portfolio Engine                            │      │
 │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐     │      │
 │  │  │ Portfolio    │  │  Allocation  │  │  Performance     │     │      │
 │  │  │ State        │──┤ Optimizer    │──┤ Analytics        │     │      │
 │  │  └──────────────┘  └──────────────┘  └──────────────────┘     │      │
 │  └────────────────────────────────────────────────────────────────┘      │
 │          │                                                               │
 │  ┌───────▼───────────────────────────────────────────────────────┐      │
 │  │                   Execution Engine                            │      │
 │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐     │      │
 │  │  │ Order        │  │  Broker      │  │  Order           │     │      │
 │  │  │ Management   │──┤ Adapter      │──│  Lifecycle       │     │      │
 │  │  └──────────────┘  └──────────────┘  └──────────────────┘     │      │
 │  └────────────────────────────────────────────────────────────────┘      │
 │                                                                           │
 │  ┌───────────────────────────────────────────────────────────────────┐   │
 │  │                    Research Engine                                │   │
 │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │   │
 │  │  │ Observation  │  │ Hypothesis   │  │  Experiment          │    │   │
 │  │  │ Management   │──┤ Testing      │──│  (Backtest/Paper)    │    │   │
 │  │  └──────────────┘  └──────────────┘  └──────────┬───────────┘    │   │
 │  │  ┌───────────────────────────────────────────────▼───────────┐   │   │
 │  │  │                  Knowledge Graph                          │   │   │
 │  │  │  Obs ──► Hyp ──► Test ──► Result ──► Lesson              │   │   │
 │  │  │  │                                      │                 │   │   │
 │  │  │  └────────────── Connections ────────────┘               │   │   │
 │  │  └──────────────────────────────────────────────────────────┘   │   │
 │  └──────────────────────────────────────────────────────────────────┘   │
 │                                                                           │
 └───────────────────────────────────────────────────────────────────────────┘
                                    │
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                         INFRASTRUCTURE LAYER                             │
 │                                                                           │
 │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
 │  │  PostgreSQL  │  │   Redis      │  │  RabbitMQ/   │  │  Object      │  │
 │  │  (Primary)   │  │  (Cache)     │  │  NATS (Bus)  │  │  Store (S3)  │  │
 │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
 │                                                                           │
 │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
 │  │  Prometheus  │  │   Grafana    │  │  Loki        │  │  Docker /    │  │
 │  │  (Metrics)   │  │  (Dashboards)│  │  (Logs)      │  │  K8s (Deploy)│  │
 │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
 │                                                                           │
 └───────────────────────────────────────────────────────────────────────────┘
```

### Subsystem Dependency Graph

```
MarketDataEngine ─────────────────────────────────────────────────────────┐
    │                                                                     │
    ├──► AnalysisEngine ──► SignalEngine ──► RiskEngine ──► PortfolioEngine ──► ExecutionEngine
    │                                                                     │
    └──► LiquidityEngine ──► SignalEngine                                 │
                                                                          │
ResearchEngine ───────────────────────────────────────────────────────────┤
    │                                                                     │
    └──► KnowledgeGraph (consumes from ALL engines for research logging)  │
                                                                          │
All Engines ──► EventBus ──► VisualizationEngine ──► NotificationEngine   │
All Engines ──► Database (via Repository interfaces)                      │
```

### Key Architectural Decisions

1. **SQLite for development, PostgreSQL for production**: SQLite provides zero-config local development. The repository pattern abstracts storage so the switch is configuration-only.

2. **Event bus as the nervous system**: Every significant action publishes an event. Events are the source of truth for the audit trail. The event schema is versioned.

3. **CLI-first, API-second, Dashboard-third**: The CLI is the primary interface because it enables scripting, automation, and headless operation. The REST API enables integration. The dashboard provides visualization.

4. **No direct database access from domain code**: All persistence goes through repository interfaces. This enables testing with in-memory stores and production with PostgreSQL.

5. **Research is not a feature — it is a layer**: The Research Engine and Knowledge Graph are not optional modules. They are the foundation upon which trading features are built.

---

## 6 Domain Model

### Entity Catalog

#### Market

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `symbol` | str | Normalized symbol (e.g., `BTCUSDT`) |
| `asset_class` | enum | crypto, forex, equity, futures |
| `exchange` | str | Source exchange |
| `status` | enum | active, inactive, error |

**Purpose**: Represents a tradeable market. Every data point, signal, and trade is associated with a market.

**Responsibilities**: Identity, classification, lifecycle.

**Relationships**: Has many Candles, Indicators, Signals, Trades.

**Lifecycle**: Created on first data collection. Deactivated when exchange drops the symbol. Never deleted — deactivated markets preserve historical research.

**Owner**: Market Data Engine.

**Persistence**: `markets` table.

---

#### Candle

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `market_id` | UUID | FK → markets |
| `timestamp` | datetime | Start of candle period |
| `open` | decimal | Open price |
| `high` | decimal | High price |
| `low` | decimal | Low price |
| `close` | decimal | Close price |
| `volume` | decimal | Volume |
| `trades` | int | Trade count (if available) |
| `timeframe` | str | e.g., `1h`, `1d` |
| `source` | str | Collector ID |

**Purpose**: The fundamental unit of market data. Every computation starts here.

**Responsibilities**: Price discovery, volume tracking.

**Relationships**: Owned by Market. Consumed by Analysis Engine and Liquidity Engine.

**Lifecycle**: Inserted in batches by the data pipeline. Never modified after insertion. If data is corrected, a new candle with corrected flag is inserted.

**Owner**: Market Data Engine.

**Persistence**: `candles` table. Partitioned by symbol and timeframe. Indexed on (market_id, timestamp, timeframe).

---

#### Indicator

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `market_id` | UUID | FK → markets |
| `timestamp` | datetime | Computation time |
| `name` | str | Indicator name (e.g., `sma_20`) |
| `value` | decimal | Computed value |
| `parameters` | json | Parameters used for computation |

**Purpose**: A computed value derived from candle data. Indicators are the bridge between raw data and trading signals.

**Responsibilities**: Feature extraction, regime classification.

**Relationships**: Owned by Market. Consumed by Signal Engine.

**Lifecycle**: Recalculated on each pipeline run. Historical values are preserved for backtesting reproducibility.

**Owner**: Analysis Engine.

**Persistence**: `indicators` table.

---

#### LiquidityZone

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `market_id` | UUID | FK → markets |
| `timestamp` | datetime | Detection time |
| `zone_type` | enum | support, resistance |
| `price_level` | decimal | Zone price |
| `strength` | int | 1–5 strength score |
| `swing_high` | decimal | Associated swing high |
| `swing_low` | decimal | Associated swing low |
| `parameters` | json | Detection parameters |

**Purpose**: Represents a price level where significant liquidity exists. Used to predict price reactions.

**Responsibilities**: Market structure mapping.

**Relationships**: Owned by Market. Consumed by Signal Engine.

**Lifecycle**: Recalculated on each pipeline run. Historical zones preserved for research.

**Owner**: Liquidity Engine.

**Persistence**: `liquidity_zones` table.

---

#### Signal

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `market_id` | UUID | FK → markets |
| `timestamp` | datetime | Generation time |
| `signal_type` | enum | entry, exit, alert |
| `direction` | enum | long, short, neutral |
| `strength` | decimal | 0.0–1.0 confidence |
| `price` | decimal | Signal price |
| `source` | str | Engine that generated it |
| `indicators_used` | json | Indicator values at signal time |
| `hypothesis_id` | UUID | FK → hypotheses (optional) |

**Purpose**: A recommendation to enter, exit, or monitor a position. Signals are advisory — they become orders only after risk validation.

**Responsibilities**: Decision recommendation.

**Relationships**: Owned by Signal Engine. Consumed by Risk Engine. Optionally linked to hypothesis.

**Lifecycle**: Created by Signal Engine. Validated by Risk Engine. Either escalated to order or rejected (rejection logged).

**Owner**: Signal Engine.

**Persistence**: `signals` table.

---

#### Hypothesis

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `observation_id` | UUID | FK → observations |
| `content` | str | Hypothesis statement |
| `status` | enum | proposed, testing, confirmed, rejected, inconclusive |
| `created_at` | datetime | Creation time |
| `updated_at` | datetime | Last update time |
| `tags` | json | Categorization tags |

**Purpose**: A testable proposition about market behavior. The unit of research progress.

**Responsibilities**: Research organization, experiment linking.

**Relationships**: Owned by Observation. Has many Experiments.

**Lifecycle**: Proposed → Testing → Confirmed/Rejected/Inconclusive. Never deleted.

**Owner**: Research Engine.

**Persistence**: `hypotheses` table.

---

#### Experiment

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `hypothesis_id` | UUID | FK → hypotheses |
| `type` | enum | backtest, paper_trade, live_trade |
| `configuration` | json | Full experiment config |
| `start_time` | datetime | Experiment start |
| `end_time` | datetime | Experiment end |
| `status` | enum | running, completed, failed, cancelled |

**Purpose**: A controlled test of a hypothesis. Encapsulates everything needed to reproduce the test.

**Responsibilities**: Reproducibility, result generation.

**Relationships**: Owned by Hypothesis. Produces Results.

**Lifecycle**: Running → Completed/Failed/Cancelled. Immutable after completion.

**Owner**: Research Engine.

**Persistence**: `experiments` table.

---

#### Trade

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `signal_id` | UUID | FK → signals |
| `experiment_id` | UUID | FK → experiments (optional) |
| `market_id` | UUID | FK → markets |
| `direction` | enum | long, short |
| `entry_price` | decimal | Execution price |
| `exit_price` | decimal | Exit price (null if open) |
| `quantity` | decimal | Position size |
| `entry_time` | datetime | Entry timestamp |
| `exit_time` | datetime | Exit timestamp (null if open) |
| `pnl` | decimal | Realized PnL (null if open) |
| `pnl_pct` | decimal | Percentage return |
| `status` | enum | open, closed, cancelled |
| `exit_reason` | str | Manual, stop_loss, take_profit, signal |

**Purpose**: The atomic unit of trading activity. Every trade is a documented decision with full provenance.

**Responsibilities**: Performance measurement, audit trail.

**Relationships**: Owned by Portfolio. Linked to Signal and optionally Experiment.

**Lifecycle**: Open → Closed. Trades cannot be deleted — they can be voided (with reason) for data correction.

**Owner**: Portfolio Engine.

**Persistence**: `trades` table.

---

#### Position

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `market_id` | UUID | FK → markets |
| `direction` | enum | long, short, flat |
| `quantity` | decimal | Current size |
| `entry_price` | decimal | Average entry |
| `current_price` | decimal | Mark-to-market |
| `unrealized_pnl` | decimal | Floating PnL |
| `opened_at` | datetime | Position open time |

**Purpose**: Represents the current state of exposure in a market. Computed dynamically from open trades.

**Responsibilities**: Current exposure tracking.

**Relationships**: Owned by Portfolio. Composed of Trades.

**Lifecycle**: Created when first trade opens. Updated with each trade. Closed when quantity reaches zero.

**Owner**: Portfolio Engine.

**Persistence**: In-memory during session, checkpointed to `positions` table.

---

#### Portfolio

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `name` | str | Portfolio name |
| `total_capital` | decimal | Allocated capital |
| `used_margin` | decimal | Currently used |
| `free_margin` | decimal | Available |
| `total_pnl` | decimal | Cumulative PnL |
| `last_updated` | datetime | Last computation |

**Purpose**: The aggregate view of all positions and capital. The unit of risk management.

**Responsibilities**: Capital allocation, risk aggregation, performance reporting.

**Relationships**: Has many Positions. Has a RiskProfile.

**Lifecycle**: Created on first run. Persisted across sessions.

**Owner**: Portfolio Engine.

**Persistence**: `portfolios` table.

---

#### RiskProfile

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `portfolio_id` | UUID | FK → portfolios |
| `max_drawdown` | decimal | Maximum allowed drawdown |
| `max_position_size` | decimal | Per-market limit |
| `max_correlation` | decimal | Correlation limit |
| `max_exposure` | decimal | Total portfolio limit |
| `position_sizing_method` | str | kelly, fixed, volatility |
| `is_active` | bool | Whether this profile is active |

**Purpose**: Defines the risk constraints for a portfolio. Multiple profiles can exist for different market conditions.

**Responsibilities**: Risk parameter definition.

**Relationships**: Owned by Portfolio. Consumed by Risk Engine.

**Lifecycle**: Created by user. Activated/deactivated as needed.

**Owner**: Risk Engine.

**Persistence**: `risk_profiles` table.

---

#### Lesson

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `result_id` | UUID | FK → results |
| `content` | str | Lesson narrative |
| `tags` | json | Categorization tags |
| `actionable` | bool | Whether lesson suggests a change |
| `applied` | bool | Whether the lesson was applied |

**Purpose**: The output of the research loop. A lesson is knowledge extracted from an experiment result.

**Responsibilities**: Knowledge preservation, decision influence.

**Relationships**: Owned by Result. Feeds into Knowledge Graph.

**Lifecycle**: Created by researcher (human or system). Reviewed periodically for actionability.

**Owner**: Research Engine.

**Persistence**: `lessons` table.

---

#### KnowledgeNode

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `entity_type` | str | observation, hypothesis, experiment, result, lesson |
| `entity_id` | UUID | FK to the specific entity |
| `connections` | json | Array of { target_id, relationship, strength } |
| `embedding` | vector | Semantic embedding (future) |

**Purpose**: The unified graph structure connecting all research entities. Enables discovery of non-obvious relationships.

**Responsibilities**: Graph traversal, relationship discovery.

**Relationships**: Links all research entities into a directed graph.

**Lifecycle**: Created/updated when any research entity is created. Re-indexed periodically.

**Owner**: Knowledge Graph.

**Persistence**: `knowledge_graph` table.

---

## 7 System Boundaries

### Inside TraderOS

| Capability | Boundary |
|------------|----------|
| Market data collection | Inside — collectors are core infrastructure |
| Data normalization | Inside — all data must be normalized to canonical format |
| Data storage | Inside — the database is part of the system |
| Technical analysis | Inside — indicators, regimes, features |
| Market structure analysis | Inside — liquidity, sweeps, breakouts, sessions |
| Correlation analysis | Inside — cross-asset relationships |
| Strategy definition and registration | Inside — strategy framework |
| Signal generation | Inside — based on strategy + analysis |
| Risk validation | Inside — risk engine |
| Portfolio management | Inside — positions, capital, allocation |
| Backtesting | Inside — historical simulation |
| Paper trading | Inside — simulated execution against live data |
| Order management | Inside — order lifecycle tracking |
| Research workflow | Inside — O-H-T-R-L pipeline |
| Knowledge graph | Inside — graph storage and querying |
| Performance analytics | Inside — metrics, visualization |
| CLI | Inside — primary interface |
| REST API | Inside — secondary interface |
| Event bus | Inside — inter-subystem communication |
| Structured logging | Inside — all logging |
| Configuration | Inside — YAML + env + DB |
| Scheduling | Inside — for recurring tasks |

### Outside TraderOS

| Capability | Boundary | Reason |
|------------|----------|--------|
| Order execution at broker | Outside — broker handles matching | TraderOS is not a broker |
| Fund custody | Outside — client funds stay at broker | TraderOS is not a custodian |
| Real-time market data feeds (raw) | Outside — feed handlers are external | Specialized infrastructure |
| Risk monitoring at broker level | Outside — broker has own risk systems | Redundant, but must reconcile |
| Tax reporting | Outside — specialized software | Not a core engineering concern |
| AI/ML model training | Outside — specialized frameworks (PyTorch, etc.) | TraderOS consumes models but does not train them |
| Team collaboration | Outside — Slack, Notion, Linear | TraderOS exports data to these |
| Deployment infrastructure | Outside — K8s, Docker, cloud | TraderOS is deployable but not a deployment platform |
| Data warehousing/analytics | Outside — Snowflake, BigQuery | Data can be exported |
| Authentication/Authorization | Inside — first-class concern | Required for API and multi-user |
| Frontend dashboard framework | Inside — but UI is thin; logic is in API | Dashboard is a consumer, not a provider |

### Boundary Enforcement Rules

1. **No external service calls from domain code**. All external calls go through repository/adapter interfaces defined in the domain layer and implemented in the infrastructure layer.

2. **No direct database access from interface code**. CLI, API, and Dashboard go through application services, never through database connections.

3. **No infrastructure imports in domain code**. `import sqlite3` in domain code is a violation. Domain code imports repository interfaces.

4. **No circular dependencies** between domains. Research never depends on Trading. Trading depends on Research (for hypothesis linkage). This direction is intentional.

5. **No orphaned data**. Every entity that references another must use foreign keys or be verifiable via referential integrity checks.

---

## 8 Subsystem Specifications

### 8.1 Market Data Engine

**Purpose**: The single source of truth for all market data entering the system.

**Responsibilities**:
- Collect data from multiple sources (exchange APIs, file imports, live feeds)
- Normalize all data to canonical schema (OHLCV + metadata)
- Validate data integrity (gaps, outliers, sequence checks)
- Store normalized data in the time-series store
- Provide query interfaces for historical and real-time data

**Inputs**: Raw exchange data, CSV files, WebSocket feeds.

**Outputs**: Normalized `Candle` objects published to the event bus.

**Dependencies**: Exchange APIs (ccxt, yfinance), database.

**Interfaces**:
```python
class MarketDataRepository(ABC):
    @abstractmethod
    def get_candles(self, market_id: UUID, timeframe: str,
                    start: datetime, end: datetime) -> list[Candle]: ...

    @abstractmethod
    def insert_candles(self, candles: list[Candle]) -> int: ...

class DataCollector(ABC):
    @abstractmethod
    def collect(self, symbol: str, timeframe: str,
                start: datetime, end: datetime) -> list[Candle]: ...

    @abstractmethod
    def validate(self, candles: list[Candle]) -> ValidationResult: ...

    @abstractmethod
    def normalize(self, raw: Any) -> list[Candle]: ...
```

**Failure modes**:
- Exchange API down → fall back to last known data, log warning, emit alert event
- Data gap detected → impute or skip, log gap details, emit gap event
- Invalid data (negative price, zero volume) → discard, log, emit validation event

**Testing strategy**:
- Mock exchanges return predefined candle sets
- Test gap detection with intentionally sparse data
- Test normalization with raw data from each exchange format
- Test validation rejects obviously bad data

**Performance expectations**:
- 1 year of 1-hour data for 10 symbols collected and stored in < 30 seconds
- Query 100,000 candles in < 100ms
- Streaming ingestion handles 10 symbols at 1-second resolution

**Completion criteria**:
- [ ] Collector interface defined with 2+ implementations
- [ ] Normalization pipeline handles crypto and forex
- [ ] Validation rejects gap > 5% and price < 0
- [ ] Repository pattern implemented with SQLite and PostgreSQL support
- [ ] 95%+ test coverage
- [ ] Performance benchmarks met

---

### 8.2 Analysis Engine

**Purpose**: Transform raw price data into analyzable market features and regimes.

**Responsibilities**:
- Compute technical indicators (moving averages, volatility, momentum, etc.)
- Classify market regimes (trending, ranging, volatile, quiet)
- Extract features for strategy consumption
- Persist all computed values for reproducibility

**Inputs**: Candle data from Market Data Engine.

**Outputs**: Indicator values, regime classification, feature vectors.

**Dependencies**: Market Data Repository, numpy, pandas.

**Interfaces**:
```python
class AnalysisEngine:
    def compute_indicators(self, candles: list[Candle],
                           windows: list[int]) -> dict[str, list[float]]: ...

    def detect_regime(self, indicators: dict) -> Regime: ...

    def extract_features(self, candles: list[Candle],
                         indicators: dict) -> FeatureVector: ...
```

**Failure modes**:
- Insufficient data for window → return None for that window, log warning
- Division by zero (zero volatility) → return 0, log edge case
- NaN/inf values → clean before returning, log count

**Testing strategy**:
- Test indicators against hand-calculated expected values
- Test regime detection with synthetic trending, ranging, and volatile data
- Test edge cases: single candle, missing data, constant prices

**Performance expectations**:
- Compute 20 indicators for 100,000 candles in < 1 second
- Regime detection in < 10ms per symbol

**Completion criteria**:
- [ ] All legacy indicators ported to new interface
- [ ] Regime detection accuracy > 90% on labeled test data
- [ ] Feature extraction produces deterministic output
- [ ] 95%+ test coverage
- [ ] Performance benchmarks met

---

### 8.3 Liquidity Engine

**Purpose**: Map market structure — identify where liquidity resides and where it is likely to be taken.

**Responsibilities**:
- Detect swing highs and swing lows
- Cluster swing points into support/resistance zones
- Detect liquidity sweeps (stop runs)
- Detect breakouts from consolidation
- Analyze per-session market behavior

**Inputs**: Candle data.

**Outputs**: LiquidityZone list, SweepEvent list, BreakoutEvent list, SessionStats.

**Dependencies**: Market Data Repository.

**Interfaces**:
```python
class LiquidityEngine:
    def detect_swings(self, candles: list[Candle],
                      window: int) -> list[SwingPoint]: ...

    def map_zones(self, swings: list[SwingPoint],
                  threshold: float) -> list[LiquidityZone]: ...

    def detect_sweeps(self, candles: list[Candle],
                      swings: list[SwingPoint]) -> list[SweepEvent]: ...

    def detect_breakouts(self, candles: list[Candle],
                         params: BreakoutParams) -> list[BreakoutEvent]: ...

    def analyze_sessions(self, candles: list[Candle],
                         session_defs: dict) -> list[SessionStats]: ...
```

**Failure modes**:
- No swing points found → empty zones, log low volatility
- Zone clustering fails (bad threshold) → log, use default threshold
- Session boundary edge cases at midnight → floor to date boundaries

**Testing strategy**:
- Test swing detection on known chart patterns
- Test zone clustering with controlled swing data
- Test sweep detection with bars that exceed and retrace
- Test breakout detection with consolidation sequences

**Performance expectations**:
- Full liquidity analysis on 100,000 candles in < 2 seconds

**Completion criteria**:
- [ ] All swing detection, zone mapping, sweep detection, breakout detection ported
- [ ] Session analysis handles all global timezones
- [ ] Zones include strength scoring (1–5)
- [ ] 90%+ test coverage
- [ ] Performance benchmarks met

---

### 8.4 Strategy Engine

**Purpose**: Define, register, version, and evaluate trading strategies.

**Responsibilities**:
- Provide a strategy definition framework (ABC + decorators)
- Manage strategy registry and metadata
- Evaluate all registered strategies against current market state
- Version strategies for reproducibility

**Inputs**: FeatureVector, LiquidityZone list, current market state.

**Outputs**: Strategy evaluation results (signal + metadata).

**Dependencies**: Analysis Engine, Liquidity Engine, Signal Engine.

**Interfaces**:
```python
class Strategy(ABC):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @abstractmethod
    def evaluate(self, market_state: MarketState) -> Signal | None: ...

    @abstractmethod
    def get_parameters(self) -> dict: ...

    @abstractmethod
    def set_parameters(self, params: dict): ...

class StrategyRegistry:
    def register(self, strategy: type[Strategy]): ...
    def get(self, name: str) -> Strategy: ...
    def list(self) -> list[StrategyMeta]: ...
```

**Failure modes**:
- Strategy raises exception → catch, log, return None signal, emit error event
- Strategy depends on missing indicator → log dependency, skip evaluation
- Duplicate strategy name → reject registration, log conflict

**Testing strategy**:
- Test each starter strategy against known market conditions
- Test registry operations (register, list, get, remove)
- Test strategy versioning produces different evaluations
- Test error handling for malformed strategies

**Performance expectations**:
- Evaluate 10 strategies on 1 symbol in < 10ms
- Strategy load time < 100ms for 50 strategies

**Completion criteria**:
- [ ] Strategy ABC defined with full interface
- [ ] Registry implements decorator registration
- [ ] Strategy versioning (semver) enforced
- [ ] 3+ starter strategies ported and tested
- [ ] 95%+ test coverage

---

### 8.5 Signal Engine

**Purpose**: Transform strategy evaluations into validated trading signals.

**Responsibilities**:
- Collect evaluations from all active strategies
- Apply signal generation rules (confidence thresholds, cooldowns)
- Deduplicate conflicting signals (long vs. short)
- Publish validated signals for risk processing

**Inputs**: Strategy evaluation results.

**Outputs**: Validated Signal objects.

**Dependencies**: Strategy Engine, Market Data Engine.

**Interfaces**:
```python
class SignalEngine:
    def process_evaluations(self, evaluations: list[Evaluation],
                            market_state: MarketState) -> list[Signal]: ...

    def validate_signal(self, signal: Signal,
                        market_state: MarketState) -> ValidationResult: ...

    def deduplicate(self, signals: list[Signal]) -> list[Signal]: ...
```

**Failure modes**:
- Conflicting signals → lower-confidence signal is suppressed (logged)
- Signal for inactive market → reject, log
- Signal at stale price (> 1 bar old) → reject, log staleness

**Testing strategy**:
- Test signal generation with known strategy outputs
- Test deduplication with conflicting long/short signals
- Test confidence threshold filtering
- Test stale price rejection

**Performance expectations**:
- Process 100 signals in < 5ms

**Completion criteria**:
- [ ] Signal generation pipeline complete
- [ ] Deduplication logic tested with conflicts
- [ ] Staleness detection implemented
- [ ] 95%+ test coverage

---

### 8.6 Risk Engine

**Purpose**: Ensure no trade is executed without passing all risk checks.

**Responsibilities**:
- Calculate position size based on method (Kelly, fixed fraction, volatility-adjusted)
- Validate exposure limits (per-market, per-portfolio)
- Monitor drawdown limits
- Execute kill switch when limits are breached
- Log every risk decision with reasoning

**Inputs**: Signal, Portfolio state, RiskProfile.

**Outputs**: RiskAssessment (approved/rejected + reason + position size).

**Dependencies**: Portfolio Engine, Market Data Engine.

**Interfaces**:
```python
class RiskEngine:
    def assess_signal(self, signal: Signal,
                      portfolio: Portfolio,
                      risk_profile: RiskProfile) -> RiskAssessment: ...

    def calculate_position_size(self, signal: Signal,
                                portfolio: Portfolio,
                                method: str) -> decimal: ...

    def check_exposure(self, signal: Signal,
                       portfolio: Portfolio,
                       limits: ExposureLimits) -> ExposureCheck: ...

    def check_drawdown(self, portfolio: Portfolio,
                       max_drawdown: decimal) -> DrawdownCheck: ...

    def check_correlation(self, signal: Signal,
                          portfolio: Portfolio,
                          max_correlation: decimal) -> CorrelationCheck: ...

    def evaluate_kill_switch(self, portfolio: Portfolio,
                             risk_profile: RiskProfile) -> KillSwitchStatus: ...
```

**Failure modes**:
- Position size calculation fails → return minimum position, log error
- Kill switch active → reject all signals, log
- Missing risk profile → use conservative defaults, log warning
- Correlation data stale → use most recent available, log

**Testing strategy**:
- Test every position sizing method against known inputs
- Test every breach condition (drawdown, exposure, correlation)
- Test kill switch activation and deactivation
- Test edge cases: zero capital, zero volatility, empty portfolio

**Performance expectations**:
- Risk assessment in < 5ms per signal

**Completion criteria**:
- [ ] Position sizing supports 3+ methods
- [ ] All limit checks implemented and tested
- [ ] Kill switch behavior documented and tested
- [ ] Every rejection includes a human-readable reason
- [ ] 95%+ test coverage

---

### 8.7 Portfolio Engine

**Purpose**: Maintain the complete, accurate state of the trading portfolio.

**Responsibilities**:
- Track all open positions and their PnL
- Record all completed trades
- Compute portfolio-level metrics (total PnL, Sharpe, drawdown)
- Manage capital allocation

**Inputs**: Trade execution events, market data updates.

**Outputs**: Portfolio snapshot, position updates, trade records.

**Dependencies**: Market Data Engine (for mark-to-market prices).

**Interfaces**:
```python
class PortfolioEngine:
    def get_portfolio(self) -> Portfolio: ...
    def get_positions(self) -> list[Position]: ...
    def open_trade(self, trade: Trade) -> Position: ...
    def close_trade(self, trade_id: UUID) -> Trade: ...
    def mark_to_market(self, prices: dict[str, decimal]) -> Portfolio: ...
    def compute_metrics(self) -> PortfolioMetrics: ...
```

**Failure modes**:
- Duplicate trade → reject, log conflict
- Trade for unknown market → reject, log
- Mark-to-market with stale price → use last price, log

**Testing strategy**:
- Test trade lifecycle (open → add → reduce → close)
- Test mark-to-market with known position and price
- Test portfolio metrics against hand-calculated values
- Test edge cases: empty portfolio, single trade, multiple positions

**Performance expectations**:
- Portfolio computation in < 1ms
- Support 100+ concurrent positions

**Completion criteria**:
- [ ] Complete trade lifecycle implemented
- [ ] Mark-to-market working with all asset classes
- [ ] Portfolio metrics match known calculations
- [ ] 95%+ test coverage

---

### 8.8 Execution Engine

**Purpose**: Execute trading signals as orders through broker adapters.

**Responsibilities**:
- Receive validated signals from Risk Engine
- Construct orders (market, limit, stop, etc.)
- Route orders through appropriate broker adapter
- Track order lifecycle (submitted → partial → filled → cancelled)
- Handle order failures and retries

**Inputs**: RiskAssessment (approved), market data.

**Outputs**: Order lifecycle events, Trade objects.

**Dependencies**: Risk Engine, Broker Adapter(s), Market Data Engine.

**Interfaces**:
```python
class ExecutionEngine:
    def execute_signal(self, assessment: RiskAssessment) -> Order: ...
    def cancel_order(self, order_id: UUID) -> bool: ...
    def get_order_status(self, order_id: UUID) -> OrderStatus: ...
    def get_open_orders(self, market_id: UUID | None) -> list[Order]: ...

class BrokerAdapter(ABC):
    @abstractmethod
    def submit_order(self, order: Order) -> OrderResult: ...
    @abstractmethod
    def cancel_order(self, broker_order_id: str) -> bool: ...
    @abstractmethod
    def get_order_status(self, broker_order_id: str) -> OrderStatus: ...
    @abstractmethod
    def get_balance(self) -> Balance: ...
```

**Failure modes**:
- Broker API down → queue order, retry with backoff, emit alert
- Order rejected by broker → log reason, emit rejection event
- Partial fill → continue tracking, log fill details
- Network timeout → retry once, then fail, log

**Testing strategy**:
- Mock broker adapter returns controlled responses
- Test order lifecycle transitions
- Test retry logic with transient failures
- Test partial fill handling
- Test all order types

**Performance expectations**:
- Order submission in < 100ms (including broker latency)
- Order status check in < 50ms

**Completion criteria**:
- [ ] Order lifecycle state machine implemented
- [ ] Broker adapter interface defined
- [ ] 1+ broker adapter implemented (paper trading first)
- [ ] Retry logic with exponential backoff
- [ ] 90%+ test coverage

---

### 8.9 Research Engine

**Purpose**: Enforce the scientific method as a software workflow.

**Responsibilities**:
- Manage the O-H-T-R-L (Observation → Hypothesis → Test → Result → Lesson) lifecycle
- Link every experiment to a hypothesis and every hypothesis to an observation
- Ensure reproducibility by capturing full experiment configuration
- Provide query interfaces for research discovery

**Inputs**: User input (via CLI/API), system observations (auto-generated).

**Outputs**: Research entities (Observations, Hypotheses, Experiments, Results, Lessons).

**Dependencies**: Knowledge Graph, Backtesting Engine, Paper Trading Engine.

**Interfaces**:
```python
class ResearchEngine:
    def create_observation(self, symbol: str, content: str,
                           tags: list[str]) -> Observation: ...
    def create_hypothesis(self, observation_id: UUID,
                          content: str) -> Hypothesis: ...
    def create_experiment(self, hypothesis_id: UUID,
                          config: ExperimentConfig) -> Experiment: ...
    def record_result(self, experiment_id: UUID,
                      metrics: dict, artifacts: list[str]) -> Result: ...
    def record_lesson(self, result_id: UUID,
                      content: str, actionable: bool) -> Lesson: ...
    def get_workflow(self, entity_id: UUID) -> WorkflowTrace: ...
    def search(self, query: str) -> list[ResearchEntity]: ...
```

**Failure modes**:
- Orphan entity (e.g., hypothesis with no observation) → reject creation
- Experiment with invalid config → reject, log validation errors
- Duplicate research (exact same config run twice) → warn, allow (reproducibility check)

**Testing strategy**:
- Test complete O-H-T-R-L workflow
- Test validation rules for each entity type
- Test search across all research entities
- Test workflow trace from leaf to root

**Performance expectations**:
- Research entity creation in < 10ms
- Workflow trace in < 50ms

**Completion criteria**:
- [ ] O-H-T-R-L workflow fully implemented
- [ ] Experiment configuration captured completely
- [ ] Search across all research entities
- [ ] 95%+ test coverage

---

### 8.10 Knowledge Graph

**Purpose**: Connect every piece of knowledge into a traversable, queryable graph.

**Responsibilities**:
- Maintain directed graph of all research entities
- Store entity connections (references, relationships, similarity)
- Support graph traversal queries (path finding, influence chains)
- Enable discovery of non-obvious relationships (future: ML-powered)

**Inputs**: Research entity creation events, user-defined connections.

**Outputs**: Graph query results, relationship maps.

**Dependencies**: Research Engine.

**Interfaces**:
```python
class KnowledgeGraph:
    def add_node(self, entity: ResearchEntity): ...
    def add_edge(self, source_id: UUID, target_id: UUID,
                 relationship: str, weight: float): ...
    def get_connections(self, entity_id: UUID,
                        depth: int) -> list[Connection]: ...
    def find_path(self, source_id: UUID,
                  target_id: UUID) -> list[Connection]: ...
    def search(self, query: str,
               entity_type: str | None) -> list[ResearchEntity]: ...
    def get_insights(self, entity_id: UUID) -> list[Insight]: ...
```

**Failure modes**:
- Circular reference → detect and reject or cap depth
- Missing node → log orphan edge, continue
- Too many results → paginate, log count

**Testing strategy**:
- Test graph construction with known entities
- Test traversal depth limiting
- Test path finding between connected and unconnected nodes
- Test search indexing

**Performance expectations**:
- Node insertion in < 5ms
- Depth-3 traversal in < 50ms on 10,000 nodes
- Full-text search in < 100ms

**Completion criteria**:
- [ ] Graph data model implemented
- [ ] CRUD operations for nodes and edges
- [ ] Traversal with configurable depth
- [ ] Path finding between any two nodes
- [ ] 90%+ test coverage

---

### 8.11 Backtesting Engine

**Purpose**: Simulate strategy performance against historical data with maximum realism.

**Responsibilities**:
- Replay historical candle data through strategy evaluation pipeline
- Execute simulated orders with configurable costs (commission, spread, slippage)
- Track simulated portfolio state
- Compute comprehensive performance metrics
- Persist results for comparison and research

**Inputs**: Strategy, symbol range, date range, configuration.

**Outputs**: BacktestResult (metrics + equity curve + trade log).

**Dependencies**: Strategy Engine, Risk Engine, Portfolio Engine, Market Data Engine.

**Interfaces**:
```python
class BacktestingEngine:
    def run(self, strategy_name: str, symbol: str,
            start: datetime, end: datetime,
            config: BacktestConfig) -> BacktestResult: ...

    def compare(self, result_ids: list[UUID]) -> ComparisonReport: ...

    def walk_forward(self, strategy_name: str, symbol: str,
                     windows: list[tuple[datetime, datetime]],
                     config: WalkForwardConfig) -> WalkForwardResult: ...
```

**Failure modes**:
- Insufficient historical data → abort with clear message
- Strategy error during backtest → log error, skip that bar, continue
- Numerical overflow (extreme PnL) → cap, log warning

**Testing strategy**:
- Test backtest against known data with known expected results
- Test commission, spread, and slippage impact
- Test walk-forward optimization
- Test edge cases: zero bars, single bar, constant price

**Performance expectations**:
- 1 year of 1-hour data backtest in < 5 seconds
- Walk-forward with 10 windows in < 60 seconds
- Equity curve computation vectorized (no loops)

**Completion criteria**:
- [ ] Backtest pipeline matches live execution pipeline exactly
- [ ] Commission/spread/slippage modeled
- [ ] Performance metrics match standard definitions (Sharpe, Sortino, Calmar, etc.)
- [ ] Walk-forward optimization implemented
- [ ] 95%+ test coverage
- [ ] Performance benchmarks met

---

### 8.12 Paper Trading Engine

**Purpose**: Execute strategies against live market data in simulation mode, bridging backtesting and live trading.

**Responsibilities**:
- Receive live market data from Market Data Engine
- Run strategy evaluation on each bar
- Execute simulated orders with realistic fills
- Track paper portfolio in real-time
- Compare paper results with backtest expectations

**Inputs**: Live market data, strategy definitions, paper portfolio.

**Outputs**: Paper trades, paper portfolio state, deviation reports.

**Dependencies**: Market Data Engine, Strategy Engine, Risk Engine, Portfolio Engine.

**Interfaces**:
```python
class PaperTradingEngine:
    def start_session(self, config: PaperTradingConfig) -> UUID: ...
    def stop_session(self, session_id: UUID): ...
    def on_market_data(self, candles: list[Candle]): ...
    def get_state(self) -> PaperTradingState: ...
    def get_deviation_report(self) -> DeviationReport: ...
```

**Failure modes**:
- Market data gap → pause paper trading, log, resume on data recovery
- Strategy error → disable that strategy, alert, continue with others
- Fill simulation edge case → log, use conservative fill

**Testing strategy**:
- Test paper trading session lifecycle
- Test fill simulation with realistic market conditions
- Test deviation detection between paper and backtest
- Test overnight/gap handling

**Performance expectations**:
- Sub-100ms processing per bar (including strategy evaluation)
- Real-time monitoring dashboard updates in < 1s

**Completion criteria**:
- [ ] Paper trading session management complete
- [ ] Fill simulation matches real exchange behavior within configurable tolerance
- [ ] Backtest-to-paper deviation reporting implemented
- [ ] 90%+ test coverage

---

### 8.13 Visualization Engine

**Purpose**: Transform data into insight through visual representation.

**Responsibilities**:
- Generate price charts with indicators and liquidity zones
- Generate correlation heatmaps
- Generate equity curves and performance dashboards
- Generate research knowledge graph visualizations
- Export to multiple formats (PNG, SVG, HTML)

**Inputs**: Market data, analysis results, portfolio state.

**Outputs**: Chart images, interactive HTML, data exports.

**Dependencies**: All engines (as data sources).

**Interfaces**:
```python
class VisualizationEngine:
    def price_chart(self, symbol: str, indicators: list[str],
                    zones: bool) -> Chart: ...
    def correlation_heatmap(self, symbols: list[str]) -> Chart: ...
    def equity_curve(self, portfolio_id: UUID) -> Chart: ...
    def knowledge_graph(self, entity_id: UUID, depth: int) -> Chart: ...
    def export(self, chart: Chart, format: str, path: str): ...
```

**Failure modes**:
- Missing data for chart → render partial chart with annotation
- Memory limit for large datasets → downsample, log
- Export directory not writable → log error, suggest fallback

**Testing strategy**:
- Test chart generation with known data produces expected output
- Test export formats render correctly
- Test memory-efficient downsampling

**Performance expectations**:
- Single chart generation in < 2 seconds
- Correlation heatmap for 20 symbols in < 3 seconds

**Completion criteria**:
- [ ] All legacy chart types ported
- [ ] Knowledge graph visualization implemented
- [ ] Export supports PNG, SVG, HTML
- [ ] 85%+ test coverage

---

### 8.14 Notification Engine

**Purpose**: Deliver timely, relevant notifications to users without noise.

**Responsibilities**:
- Send alerts for significant events (risk breach, strategy error, fill confirmation)
- Aggregate notifications to prevent spam
- Support multiple channels (CLI, terminal, webhook, email)
- Respect user notification preferences

**Inputs**: Notification events from all engines.

**Outputs**: Delivered notifications.

**Dependencies**: Event Bus.

**Interfaces**:
```python
class NotificationEngine:
    def send(self, notification: Notification) -> bool: ...
    def register_channel(self, name: str, channel: NotificationChannel): ...
    def get_history(self, since: datetime) -> list[Notification]: ...

class NotificationChannel(ABC):
    @abstractmethod
    def deliver(self, notification: Notification) -> bool: ...
```

**Failure modes**:
- Channel delivery failure → try alternative channel, log
- Rate limit exceeded → queue, delay, log

**Testing strategy**:
- Test each notification channel with mock delivery
- Test rate limiting and aggregation
- Test notification history

**Performance expectations**:
- Notification delivery in < 100ms per channel

**Completion criteria**:
- [ ] Multi-channel notification framework implemented
- [ ] Rate limiting and aggregation working
- [ ] 90%+ test coverage

---

### 8.15 API Layer

**Purpose**: Expose all system capabilities through a well-documented, versioned REST API.

**Responsibilities**:
- Provide CRUD operations for all domain entities
- Expose engine execution endpoints (run analysis, start backtest)
- Stream real-time data via WebSocket
- Authenticate and authorize requests
- Document all endpoints (OpenAPI)

**Inputs**: HTTP requests, WebSocket connections.

**Outputs**: HTTP responses, WebSocket messages.

**Dependencies**: Application Layer (orchestrators).

**Failure modes**:
- Invalid request → 400 with structured error response
- Not found → 404
- Internal error → 500 with correlation_id for debugging
- Rate limit exceeded → 429

**Testing strategy**:
- Test every endpoint with valid and invalid inputs
- Test authentication/authorization
- Test WebSocket connectivity and message format
- Test API versioning

**Performance expectations**:
- < 50ms response time for 95% of requests
- WebSocket < 10ms message latency
- Support 100+ concurrent connections

**Completion criteria**:
- [ ] All domain entities exposed via REST
- [ ] OpenAPI documentation auto-generated
- [ ] Authentication implemented
- [ ] WebSocket for real-time data
- [ ] 90%+ test coverage

---

### 8.16 Dashboard

**Purpose**: Provide a visual, real-time view of the trading system.

**Responsibilities**:
- Display portfolio state and PnL
- Show current positions and orders
- Visualize performance metrics
- Display research knowledge graph
- Provide system health monitoring

**Inputs**: API Layer.

**Outputs**: Web UI.

**Dependencies**: API Layer.

**Failure modes**:
- API unavailable → show cached data with staleness indicator
- Large datasets → paginate, lazy load

**Testing strategy**:
- Component tests for each dashboard widget
- Integration tests against mock API

**Performance expectations**:
- Initial load in < 2 seconds
- Real-time updates in < 1 second

**Completion criteria**:
- [ ] Portfolio overview page
- [ ] Positions and orders view
- [ ] Performance charts
- [ ] Research graph explorer
- [ ] System health page

---

### 8.17 CLI

**Purpose**: Provide the fastest, most scriptable interface to the system.

**Responsibilities**:
- Expose all system commands
- Support scripting and automation (non-interactive mode)
- Provide tabular output (default) and JSON output (for piping)
- Support configuration via flags and environment variables

**Commands**:
```
traderos data collect [symbols...] [--timeframe] [--days]
traderos data list
traderos analyze [symbols...]
traderos liquidity [symbols...]
traderos research obs [--symbol] [--content] [--tags]
traderos research hyp <obs_id> <content>
traderos research test <hyp_id> [--strategy] [--params]
traderos research trace <entity_id>
traderos strategy list
traderos strategy run <name> <symbol> [--params]
traderos backtest <strategy> <symbol> [--start] [--end]
traderos paper start [--config]
traderos paper stop
traderos paper status
traderos portfolio
traderos risk limits [--set]
traderos run [--pipeline]    # Run the full pipeline
```

**Failure modes**:
- Invalid command → print help
- Missing arguments → print usage
- Command failure → non-zero exit code, error message
- Connection failure → clear error, suggest --help

**Testing strategy**:
- Test every command with valid and invalid inputs
- Test JSON output format is parseable
- Test non-interactive mode exits cleanly
- Test --help output completeness

**Performance expectations**:
- Command parsing in < 10ms
- Response display in < 100ms (excluding computation)

**Completion criteria**:
- [ ] All commands implemented
- [ ] JSON output mode for all commands
- [ ] Tabulate formatting for human-readable output
- [ ] 90%+ test coverage
- [ ] Man page generated from CLI help

---

### 8.18 Infrastructure

**Purpose**: All the plumbing that keeps the system running.

**Sub-components**:

| Component | Technology | Purpose |
|-----------|------------|---------|
| Database | SQLite (dev) / PostgreSQL (prod) | Primary persistence |
| Cache | Redis (optional) | Strategy parameter cache, session state |
| Message Bus | RabbitMQ or NATS | Event distribution |
| Object Store | Local FS / S3 | Chart exports, experiment artifacts |
| Metrics | Prometheus | System and trading metrics |
| Visualizations | Grafana | Operational dashboards |
| Logging | Loki / Structured JSON | Centralized logging |
| Deployment | Docker / Docker Compose / K8s | Containerized deployment |
| CI/CD | GitHub Actions | Automated testing and deployment |

**Failure modes**:
- Database unavailable → graceful degradation, cache reads
- Message bus unavailable → direct execution (degraded mode)
- Object store unavailable → store locally, queue sync

**Testing strategy**:
- Integration tests with Docker Compose
- Infrastructure-as-code versioned in repository

**Completion criteria**:
- [ ] Dockerfile and docker-compose.yml for development
- [ ] Database migrations framework
- [ ] Structured logging implemented
- [ ] Health check endpoint
- [ ] CI/CD pipeline running

---

## 9 Execution Pipeline

### Complete System Flow

```
                                EXECUTION PIPELINE
                                ═══════════════════

  PHASE 1: DATA INGESTION
  ───────────────────────────────────────────────────────────────────
  External APIs ──► Collectors ──► Normalization ──► Validation ──► Store
       │                │               │               │
       │                │               │               └──► Emit: data.validated
       │                │               └──► Emit: data.normalized
       │                └──► Emit: data.collected
       └──► Emit: data.raw

  Input:    Raw exchange data
  Output:   Normalized, validated Candles in database
  Failure:  Collector error → log, try next source, emit alert
            Validation error → log, quarantine bad data, emit alert
  Metrics:  candles_collected, candles_validated, validation_errors,
            collection_duration_ms

  PHASE 2: ANALYSIS
  ───────────────────────────────────────────────────────────────────
  Candles ──► Indicators ──► Regime Detection ──► Feature Extraction ──► Store
    │            │                │                       │
    │            │                └──► Emit: regime.detected
    │            └──► Emit: indicator.computed
    └──► Emit: analysis.started

  Input:    Normalized candles
  Output:   Indicators, regimes, features stored in database
  Failure:  Insufficient data → skip symbol, log
            Computation error → log, continue with next indicator
  Metrics:  indicators_computed, regimes_classified, analysis_duration_ms

  PHASE 3: LIQUIDITY MAPPING
  ───────────────────────────────────────────────────────────────────
  Candles ──► Swing Detection ──► Zone Mapping ──► Sweep/Breakout Detection ──► Store
    │            │                    │                        │
    │            │                    └──► Emit: liquidity.zones_mapped
    │            └──► Emit: liquidity.swings_detected
    └──► Emit: liquidity.started

  Input:    Normalized candles
  Output:   Liquidity zones, sweep events, breakout events, session stats
  Failure:  No swings found → empty zones, log low volatility
            Zone clustering error → use defaults, log
  Metrics:  zones_mapped, sweeps_detected, breakouts_detected,
            liquidity_duration_ms

  PHASE 4: STRATEGY EVALUATION
  ───────────────────────────────────────────────────────────────────
  Features + Zones + Regimes ──► Strategy Evaluation ──► Signal Generation
        │              │               │                       │
        │              │               └──► Emit: strategy.evaluated
        │              └──► Emit: signal.candidates
        └──► Emit: evaluation.started

  Input:    Features, liquidity zones, current regime
  Output:   Candidate signals from all strategies
  Failure:  Strategy error → disable strategy for this bar, log, continue
            No signals → log, continue
  Metrics:  strategies_evaluated, signals_candidates, evaluation_duration_ms

  PHASE 5: RISK VALIDATION
  ───────────────────────────────────────────────────────────────────
  Signals ──► Position Sizing ──► Exposure Check ──► Kill Switch Check ──► Validation
    │              │                    │                    │
    │              │                    │                    └──► Emit: risk.kill_switch
    │              │                    └──► Emit: risk.exposure_breach
    │              └──► Emit: risk.position_sized
    └──► Emit: risk.validation_started

  Input:    Candidate signals, portfolio state, risk profile
  Output:   Approved signals (with position size) or rejection reasons
  Failure:  All signals rejected → log, emit risk.summary
            Position sizing error → use minimum, log
  Metrics:  signals_approved, signals_rejected, rejection_reasons,
            risk_duration_ms

  PHASE 6: PORTFOLIO DECISION
  ───────────────────────────────────────────────────────────────────
  Approved Signals ──► Portfolio Impact Assessment ──► Final Decision
       │                        │
       │                        └──► Emit: portfolio.decision
       └──► Emit: portfolio.decision_started

  Input:    Approved signals, current portfolio state
  Output:   Final execution decisions (which orders to place)
  Failure:  Portfolio constraint violated → reject signal, log
  Metrics:  decisions_made, decisions_rejected, portfolio_duration_ms

  PHASE 7: EXECUTION
  ───────────────────────────────────────────────────────────────────
  Decisions ──► Order Construction ──► Broker Adapter ──► Order Lifecycle ──► Trade
      │               │                    │                    │
      │               │                    │                    └──► Emit: trade.executed
      │               │                    └──► Emit: order.submitted
      │               └──► Emit: order.created
      └──► Emit: execution.started

  Input:    Execution decisions
  Output:   Executed trades
  Failure:  Broker reject → log reason, alert
            Partial fill → log, continue tracking
            Timeout → retry once, then fail
  Metrics:  orders_submitted, orders_filled, orders_rejected,
            execution_duration_ms, slippage_bps

  PHASE 8: TRADE LOGGING
  ───────────────────────────────────────────────────────────────────
  Trades ──► Store ──► Update Portfolio ──► Update Positions ──► Emit: trade.logged

  Input:    Executed trades
  Output:   Updated trades, positions, portfolio in database
  Failure:  Database error → queue in memory, retry on next cycle
  Metrics:  trades_logged, positions_updated, logging_duration_ms

  PHASE 9: RESEARCH LOGGING
  ───────────────────────────────────────────────────────────────────
  All Events ──► Research Engine ──► Create Observations ──► Link to Hypotheses
       │               │                       │
       │               │                       └──► Emit: research.recorded
       │               └──► Emit: research.observation_created
       └──► Emit: research.logging_started

  Input:    All pipeline events (system observations)
  Output:   Auto-generated observations in research database
  Failure:  Research engine error → log, continue (research is non-critical path)
  Metrics:  observations_created, research_logging_duration_ms

  PHASE 10: KNOWLEDGE GRAPH UPDATE
  ───────────────────────────────────────────────────────────────────
  Research Entities ──► Graph Update ──► Relationship Discovery ──► Store ──► Emit: knowledge.updated

  Input:    All research entities created this cycle
  Output:   Updated knowledge graph
  Failure:  Graph update error → log, retry on next cycle
  Metrics:  nodes_added, edges_added, graph_update_duration_ms

  PHASE 11: PERFORMANCE ANALYTICS
  ───────────────────────────────────────────────────────────────────
  Portfolio + Trades + Research ──► Metrics Computation ──► Visualization ──► Store
       │                                │                        │
       │                                └──► Emit: analytics.computed
       └──► Emit: analytics.started

  Input:    Current system state
  Output:   Performance metrics, updated charts
  Failure:  Metrics computation error → log, use previous metrics
  Metrics:  performance_duration_ms

  PHASE 12: LEARNING
  ───────────────────────────────────────────────────────────────────
  Performance Data ──► Deviation Analysis ──► Lesson Extraction ──► Store ──► Emit: learning.updated
       │                     │                        │
       │                     └──► Emit: learning.anomaly_detected
       └──► Emit: learning.started

  Input:    Performance metrics, backtest vs paper deviation
  Output:   Auto-generated lessons, improvement suggestions
  Failure:  Learning engine error → log, skip automatic lesson generation
  Metrics:  lessons_generated, anomalies_detected, learning_duration_ms

  PHASE 13: PUBLISH
  ───────────────────────────────────────────────────────────────────
  All Results ──► Aggregate Report ──► Notifications ──► Dashboard Update

  Input:    All pipeline results
  Output:   Run summary, notifications, updated dashboard
  Failure:  Notification error → log, continue
  Metrics:  notifications_sent, dashboard_updated, publish_duration_ms
```

### Pipeline Orchestration

The pipeline supports three execution modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| `realtime` | Runs on each new candle | Live trading and paper trading |
| `batch` | Runs on historical data range | Backtesting and research |
| `catchup` | Runs on missed candles, then switches to realtime | Recovery after downtime |

Each mode uses the same engine code — only the data source and scheduling differ.

---

## 10 Engineering Standards

### 10.1 Python Standards

| Standard | Requirement |
|----------|-------------|
| Version | Python 3.11+ |
| Formatting | Black (line length 100) |
| Import sorting | isort (Black-compatible profile) |
| Linting | ruff (all rules enabled except by explicit exclusion) |
| Type checking | pyright strict mode |
| Testing | pytest with coverage reporting |
| Pre-commit | All of the above as pre-commit hooks |

### 10.2 Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Packages | short, lowercase, no underscores | `analysis_engine` |
| Modules | short, lowercase, underscores | `indicator_calculator.py` |
| Classes | PascalCase | `MarketDataEngine` |
| Functions | snake_case | `compute_moving_average()` |
| Variables | snake_case | `current_price` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Private members | _prefix | `_internal_method()` |
| Protected members | single _ prefix | `_validate()` |
| Type variables | short, PascalCase | `T`, `EngineType` |
| Enums | PascalCase members | `Regime.TRENDING_BULLISH` |
| Database tables | snake_case, plural | `market_data` |
| Database columns | snake_case | `price_level` |
| UUID columns | `_id` suffix | `market_id` |
| Boolean columns | `is_` prefix | `is_active` |

### 10.3 Architecture Standards

| Standard | Requirement |
|----------|-------------|
| Layer separation | Domain → Application → Interface → Infrastructure (dependency direction) |
| Package structure | `domain/`, `application/`, `infrastructure/`, `interfaces/` per bounded context |
| Interface ownership | Defined by consumer, implemented by provider |
| Dependency injection | Required for all infrastructure dependencies |
| No circular imports | Enforced by `ruff` or import linter |
| No global state | Singleton only for Config (frozen after init) |
| No `from X import *` | Explicit imports only |
| Maximum function lines | 60 lines (excluding docstrings) |
| Maximum class lines | 400 lines |
| Maximum method parameters | 5 |

### 10.4 Testing Standards

| Standard | Requirement |
|----------|-------------|
| Framework | pytest |
| Coverage target | 90%+ (overall), 80%+ (per module) |
| Test types | Unit (80%), Integration (15%), End-to-End (5%) |
| Test isolation | No network calls, no shared state, no test interdependencies |
| Naming | `test_<module>_<behavior>` |
| Structure | Arrange-Act-Assert (Given-When-Then) |
| Fixtures | Use pytest fixtures, not setUp/tearDown |
| Mocking | Use `unittest.mock` or `pytest-mock` |
| Fakes | In-memory implementations of repositories for speed |
| Performance tests | Separate from unit tests, run on CI nightly |

### 10.5 Logging Standards

| Standard | Requirement |
|----------|-------------|
| Library | `structlog` or standard `logging` with JSON formatter |
| Level | DEBUG (development), INFO (production), WARNING (concern), ERROR (failure), CRITICAL (system down) |
| Fields | `timestamp`, `level`, `module`, `function`, `run_id`, `correlation_id`, `message`, `extra` |
| Format | JSON structured (machine-parseable) |
| Sensitive data | Never log passwords, keys, or personal data |
| Rate limiting | No more than 1 log per second per source for repetitive events |
| Correlation ID | Generated at pipeline start, propagated to all subsystems |

### 10.6 Documentation Standards

| Standard | Requirement |
|----------|-------------|
| Docstrings | Google style for all public APIs |
| README | Updated with every significant change |
| Architecture | Updated when architecture changes |
| ADRs | Written for every significant architectural decision |
| Inline comments | Explain *why*, not *what* (the code explains *what*) |
| Changelog | Every PR updates CHANGELOG.md |

### 10.7 Typing Standards

| Standard | Requirement |
|----------|-------------|
| Type hints | Required for all function signatures (parameters and return types) |
| No `Any` | Except for truly dynamic code (generic serialization, etc.) |
| Use `|` syntax | `str | None` instead of `Optional[str]` |
| `Protocol` | Use for structural subtyping |
| `TypedDict` | Use for structured dicts |
| `dataclass` | Use for data containers |
| No type: ignore | Except in tests for deliberate runtime checks |

### 10.8 Configuration Standards

| Standard | Requirement |
|----------|-------------|
| Format | YAML for structured config, env vars for secrets |
| Precedence | CLI flags > env vars > YAML config > defaults |
| Validation | Config validated on load, errors reported with field names |
| Immutability | Config is frozen after initialization |
| Schema | Documented schema with descriptions and types |
| Environment | `.env.example` checked in, `.env` in `.gitignore` |

### 10.9 Database Standards

| Standard | Requirement |
|----------|-------------|
| Migrations | Versioned, automated, tested |
| Schema | Documented for all tables |
| Indexes | Indexed on all FK columns and query-critical columns |
| Constraints | FK constraints with CASCADE/ SET NULL as appropriate |
| Connections | Connection pool with configurable limits |
| Timeouts | Query timeout configurable per operation |
| No raw SQL in domain code | SQL only in repository implementations |

### 10.10 Error Handling Standards

| Standard | Requirement |
|----------|-------------|
| Custom exceptions | Defined per bounded context |
| Exception hierarchy | Base exception per context, specific exceptions below |
| Catch specificity | No bare `except:` or `except Exception` |
| Log and re-raise | Only at subsystem boundaries |
| Fail closed | On uncertainty, take the safest action |
| Error responses | Structured JSON with code, message, and correlation_id |

### 10.11 Git Standards

| Standard | Requirement |
|----------|-------------|
| Branch naming | `type/short-description` (e.g., `feat/paper-trading`, `fix/swing-detection`) |
| Types | `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf` |
| Commit messages | Conventional Commits format |
| Commits per PR | Multiple small commits, squash-merged to main |
| PR size | < 400 lines changed. Larger PRs must be split |
| PR reviews | Required for all PRs to main |
| CI pass | Required before merge |

### 10.12 Security Standards

| Standard | Requirement |
|----------|-------------|
| Secret storage | Never in code. Environment variables or secret manager. |
| API keys | Loaded at runtime, never logged, never committed |
| SQL injection | Prevented by parameterized queries (never string formatting) |
| Input validation | All user input validated at boundary (CLI, API) |
| Authentication | Required for API and dashboard |
| Authorization | Role-based access (admin, researcher, viewer) |

### 10.13 Performance Standards

| Standard | Requirement |
|----------|-------------|
| Benchmarks | Defined for all critical paths |
| Profiling | Required before optimization |
| Vectorization | numpy/pandas preferred over Python loops |
| Memory | No unbounded data structures. Batch processing for large datasets. |
| Caching | Explicit, measured, documented |
| Async | For I/O-bound operations |
| Database queries | Indexed, EXPLAIN-planned |

### 10.14 Observability Standards

| Standard | Requirement |
|----------|-------------|
| Health endpoint | `GET /health` returns system status |
| Metrics endpoint | `GET /metrics` returns Prometheus-format metrics |
| Run manifest | Every pipeline run produces a manifest (config, inputs, outputs, duration) |
| Traceability | Every trade, signal, and decision has a correlation_id chain |
| Alerts | Critical events trigger alerts (risk breach, system down, data stale) |

---

## 11 Definition of Done

No feature is complete until every requirement in every category passes.

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

## 12 Decision Framework

Before writing any code, every engineer must answer these questions:

### Purpose

1. **Why does this exist?**
   - What problem does it solve?
   - What evidence do we have that this problem exists?
   - What happens if we don't build it?

2. **Who is the user?**
   - Human trader? Automated system? Another subsystem?
   - What is their workflow? How does this fit?

3. **What question does this answer?**
   - Every feature should help answer a question about markets, strategies, or performance.
   - If it does not answer a question, it should not be built.

### Architecture

4. **Does it belong here?**
   - Which subsystem does this belong to?
   - Does the proposed location respect the dependency direction?
   - If it spans subsystems, is the boundary in the right place?

5. **Does it preserve the architecture?**
   - Does it introduce a new dependency direction?
   - Does it require changes to existing interfaces?
   - Does it create a circular dependency?

6. **Can it be replaced?**
   - If we need to swap this implementation in 6 months, can we?
   - Is it behind an interface?
   - Are the interface boundaries correct?

### Design

7. **Will it scale?**
   - How does it behave with 10× the data? 100×?
   - Where is the bottleneck?
   - What is the asymptotic complexity?

8. **Can it be tested?**
   - Can we test it without external dependencies?
   - Are the edge cases enumerable?
   - Can we test failure modes?

9. **Does it simplify the system?**
   - Does this make the system easier to understand?
   - Does it reduce duplication?
   - Does it remove accidental complexity?

10. **Is the default correct?**
    - What happens when nothing is configured?
    - What happens when data is missing?
    - What happens on error?

### Integrity

11. **Can we observe it?**
    - Are the right metrics in place?
    - Is logging sufficient to debug failures?
    - Is there a health check?

12. **Is it secure?**
    - Where does user input enter?
    - Are secrets handled correctly?
    - Is there an injection risk?

13. **Is it fast enough?**
    - Not "is it fast" — "is it fast enough for its purpose?"
    - What is the acceptable threshold?
    - How do we measure it?

### Completion

14. **Is this the smallest possible change?**
    - Can we deliver value in a smaller increment?
    - What is the Minimum Viable Change?

15. **When is it done?**
    - What does "done" look like?
    - Can we define the acceptance criteria before starting?

---

## 13 Engineering Roadmap

### Milestone 0: Engineering Stabilization

**Objective**: Make the existing codebase maintainable, testable, and observable before adding new functionality.

**Deliverables**:
- CI/CD pipeline (GitHub Actions): lint, typecheck, test on every push
- pre-commit hooks for Black, isort, ruff, pyright
- pytest migration from unittest (all 7 existing tests passing)
- Test coverage reporting (target: current coverage baseline + 10%)
- Dockerfile and docker-compose.yml for development
- Structured logging implemented across all modules
- .env.example updated with all documented variables
- All existing code passes ruff with no errors
- All existing code passes pyright strict mode

**Dependencies**: None.

**Acceptance Criteria**:
- `make lint` passes with zero errors
- `make typecheck` passes with zero errors
- `make test` runs in < 30 seconds
- `make docker-dev` builds and starts the system
- CI pipeline green on every PR

**Definition of Success**: An engineer can clone the repo, run `make setup`, `make test`, and have a fully functional development environment in < 5 minutes.

---

### Milestone 1: Core Architecture

**Objective**: Establish the modular architecture with clear bounded contexts, interfaces, and dependency rules.

**Deliverables**:
- Package restructuring into `traderos/` namespace package
- Bounded context separation: `market_data/`, `analysis/`, `liquidity/`, `signal/`, `risk/`, `portfolio/`, `execution/`, `research/`, `knowledge/`
- Repository interfaces for all persistence
- In-memory repository implementations for testing
- Event bus framework with typed events
- Configuration system v2 (validation, schema, immutability)
- Migration from single `main.py` to `Orchestrator` class
- Domain entity models (dataclasses) for all entities in Section 6
- Error hierarchy for each bounded context

**Dependencies**: Milestone 0.

**Acceptance Criteria**:
- Every bounded context has zero infrastructure imports in domain code
- Every repository has at least one implementation (in-memory for testing)
- Event bus has typed events with schema validation
- `Orchestrator` can run the full pipeline
- All existing tests pass with new architecture
- Architecture tests enforce dependency direction

**Definition of Success**: The architecture is proven by a working pipeline that uses the new structure. A new engineer can understand the system boundaries by reading the package structure.

---

### Milestone 2: Research Platform

**Objective**: Make the Research Engine and Knowledge Graph production-quality.

**Deliverables**:
- Research Engine with full O-H-T-R-L workflow
- Knowledge Graph with persistence and traversal
- Research CLI complete with all commands
- Research REST API endpoints
- Knowledge graph visualization
- Auto-observation generation from pipeline events
- Research search (full-text + graph)
- Experiment configuration capture and replay
- Research report generation

**Dependencies**: Milestone 1.

**Acceptance Criteria**:
- Complete O-H-T-R-L workflow works via CLI
- Knowledge graph supports depth-5 traversal in < 100ms on 1,000 nodes
- Full-text search returns results in < 200ms
- Auto-observations generated on every pipeline run
- All entities traced from trade → signal → strategy → experiment → hypothesis → observation

**Definition of Success**: A trader can observe a market pattern, formulate a hypothesis, design an experiment, run a backtest, record the result, extract a lesson, and see it all in the knowledge graph — without leaving the CLI.

---

### Milestone 3: Trading Core

**Objective**: Make the Strategy, Signal, Risk, and Portfolio engines production-quality.

**Deliverables**:
- Strategy framework with versioning and parameter management
- 3+ starter strategies fully ported and tested
- Signal Engine with generation, validation, and deduplication
- Risk Engine with all position sizing methods and limit checks
- Portfolio Engine with complete trade lifecycle
- Comprehensive backtesting with realistic costs
- Backtest-to-live parity verification framework
- Strategy performance comparison dashboard

**Dependencies**: Milestone 1, Milestone 2 (for research linkage).

**Acceptance Criteria**:
- Backtest results match known expected values within 0.1%
- Risk Engine rejects signals that violate any limit
- Portfolio tracks all trades correctly through full lifecycle
- Strategy versioning produces deterministic, reproducible results
- All risk checks have documented test cases

**Definition of Success**: A strategy can be defined, registered, parameterized, backtested, compared, and linked to a research hypothesis — all with audit-trail quality provenance.

---

### Milestone 4: Execution Layer

**Objective**: Build the bridge from research to real markets.

**Deliverables**:
- Execution Engine with order lifecycle state machine
- Broker adapter interface
- Paper trading adapter (simulated fills)
- At least one live broker adapter (e.g., Alpaca, Interactive Brokers)
- Order management CLI and API
- Order status tracking and notification
- Fallback and retry logic
- Execution analytics (fill rates, slippage, latency)

**Dependencies**: Milestone 3.

**Acceptance Criteria**:
- Paper trading fills match expected distribution within configurable tolerance
- Order lifecycle state machine handles all transitions
- Broker adapter can be swapped without changing execution logic
- Retry logic with exponential backoff works correctly
- Execution latency measured and meeting targets

**Definition of Success**: A strategy evaluated by the research pipeline can be paper-traded against live data with fills that are statistically indistinguishable from a real broker.

---

### Milestone 5: Paper Trading

**Objective**: Run the complete pipeline in paper trading mode with live data.

**Deliverables**:
- Paper trading session management
- Live data streaming via WebSocket
- Real-time strategy evaluation
- Paper portfolio tracking with mark-to-market
- Backtest-to-paper deviation analysis
- Paper trading dashboard
- Paper trading alerts
- Session persistence and recovery

**Dependencies**: Milestone 4.

**Acceptance Criteria**:
- Paper trading runs 24/7 without memory leaks
- Deviation reports show statistically significant differences between backtest and paper
- Session recovery after restart reproduces state exactly
- Dashboard updates in < 1s after each bar

**Definition of Success**: The system can run unattended for 30 days, producing daily deviation reports that allow a trader to assess strategy readiness for live trading.

---

### Milestone 6: Intelligence Layer

**Objective**: Add ML-assisted pattern discovery and knowledge graph inference.

**Deliverables**:
- Pattern discovery service (anomaly detection in market data)
- Knowledge graph embedding generation
- Similar strategy discovery
- Automated hypothesis suggestion from observed anomalies
- Research assistant (suggest related observations, hypotheses, experiments)
- Vector storage for semantic search
- ML model integration framework (consume models from external training)

**Dependencies**: Milestone 2, Milestone 5.

**Acceptance Criteria**:
- Pattern discovery finds statistically significant patterns in historical data
- Knowledge graph embeddings enable meaningful similarity search
- Automated hypothesis suggestions lead to validatable experiments ≥ 20% of the time
- ML model integration framework is model-framework-agnostic

**Definition of Success**: The system can analyze its own research history and suggest new research directions that a trader finds valuable enough to pursue.

---

### Milestone 7: Platform Layer

**Objective**: Make TraderOS accessible to users beyond the founding team.

**Deliverables**:
- REST API v1 with full OpenAPI documentation
- Dashboard v1 with portfolio, research, and system health views
- User authentication and authorization
- Multi-portfolio support
- SDK package (pip-installable)
- Plugin system for community strategies
- Documentation site
- Deployment guide (Docker, K8s, cloud)

**Dependencies**: Milestone 5, Milestone 6.

**Acceptance Criteria**:
- API v1 is feature-complete and documented
- Dashboard is usable by non-technical traders
- SDK enables third-party strategy development
- Deployment guide enables one-command cloud deployment
- 99.9% uptime in staging environment

**Definition of Success**: A new user can install TraderOS, configure data sources, define a strategy, run a backtest, and see results — all through the dashboard — in under 30 minutes.

---

### Milestone 8: Production Readiness

**Objective**: Make TraderOS production-grade for live trading.

**Deliverables**:
- Load testing and performance optimization
- Disaster recovery procedures
- Monitoring and alerting for production
- Security audit and remediation
- Compliance documentation (if applicable)
- Live trading with real capital (small scale)
- Post-trade analytics and reconciliation
- Incident response runbook

**Dependencies**: Milestone 5, Milestone 7.

**Acceptance Criteria**:
- System handles 2× expected production load
- Disaster recovery restores within 1 hour
- Security audit passes with zero critical findings
- Live trading reconciles with broker statements within 0.1%
- Incident response runbook covers all known failure modes

**Definition of Success**: TraderOS manages real capital with the same reliability and auditability as a Bloomberg terminal.

---

## 14 Engineering KPIs

### Code Quality KPIs

| KPI | Target | Measurement | Frequency |
|-----|--------|-------------|-----------|
| Test coverage | >= 90% | pytest --cov | Every PR |
| Type check pass rate | 100% | pyright | Every PR |
| Lint pass rate | 100% | ruff | Every PR |
| Architecture violations | 0 | Import linter | Every PR |
| Cyclomatic complexity | < 10 avg | radon | Weekly |
| Duplication | < 5% | radon or similar | Monthly |

### Delivery KPIs

| KPI | Target | Measurement | Frequency |
|-----|--------|-------------|-----------|
| Build success rate | > 95% | CI pipeline | Per push |
| Deployment frequency | Weekly | Git tags | Monthly |
| PR lead time | < 48 hours | PR open → merged | Monthly |
| PR size | < 400 lines | PR stats | Monthly |
| Bug escape rate | < 5% | Bugs found in prod / total bugs | Monthly |

### Research KPIs

| KPI | Target | Measurement | Frequency |
|-----|--------|-------------|-----------|
| Research velocity | 10+ experiments/week | DB query | Weekly |
| Hypothesis→lesson rate | > 30% | lessons / hypotheses | Monthly |
| Knowledge graph size | Growing | Node count | Monthly |
| Backtest reproducibility | 100% | Same config → same result | Every backtest |

### Trading KPIs

| KPI | Target | Measurement | Frequency |
|-----|--------|-------------|-----------|
| Backtest accuracy | < 5% paper deviation | Paper vs backtest PnL | Daily |
| Strategy reliability | > 99% uptime | Strategy execution success | Daily |
| Signal-to-order rate | > 80% | orders / signals | Daily |
| System availability | > 99.5% | Health check | Monthly |

### Performance KPIs

| KPI | Target | Measurement | Frequency |
|-----|--------|-------------|-----------|
| Pipeline run time | < 5 min (batch) | Timer | Every run |
| Strategy evaluation | < 10ms per strategy | Timer | Every run |
| Risk assessment | < 5ms per signal | Timer | Every run |
| Database query p95 | < 50ms | Query logging | Weekly |
| Memory usage | < 2GB steady state | Resource monitor | Continuous |

---

## 15 Technical Debt Strategy

### Debt Categories

| Category | Examples | Severity |
|----------|----------|----------|
| **Architecture** | Wrong layer, circular dependency, no interface | Critical |
| **Testing** | Missing tests, flaky tests, low coverage | High |
| **Performance** | N+1 queries, no index, O(n²) in hot path | High |
| **Observability** | No logging, print debugging, no metrics | Medium |
| **Documentation** | Missing docstrings, stale comments, no ADR | Medium |
| **Code quality** | Long functions, duplicated code, no types | Low |
| **Configuration** | Hardcoded values, magic numbers, missing env vars | Medium |

### Debt Scoring

```
Score = Severity × Impact × Age

Severity:
  Critical = 5, High = 4, Medium = 3, Low = 1

Impact:
  Blocks work = 5, Slows work = 3, Annoying = 1

Age:
  > 6 months = 3, > 1 month = 2, < 1 month = 1
```

Score thresholds:
- **> 30**: Must fix this sprint
- **15–30**: Schedule within 2 sprints
- **5–15**: Schedule within 4 sprints
- **< 5**: Accept, monitor

### Debt Prioritization

1. Architecture debt is always highest priority.
2. Testing debt that allows bugs to reach production is second.
3. Performance debt affecting current research velocity is third.
4. All other debt is background — fixed as encountered.

### Debt Review Cadence

- **Weekly**: 15-minute debt review during sprint planning. Review top-5 scored items.
- **Quarterly**: Full debt inventory. Re-score all items. Identify systemic patterns.
- **Per-PR**: New debt must not exceed debt paid down. (If you add a shortcut, fix two shortcuts.)

### Debt Budget

Each sprint allocates:
- **20%** of capacity to debt reduction (mandatory)
- **10%** of capacity to architecture improvement (mandatory)
- Remaining 70% for feature work

Violations (exceeding 70% feature work) require CTO approval.

---

## 16 Architecture Decision Records

### Required ADRs

| # | Title | Purpose | Priority |
|---|-------|---------|----------|
| ADR-001 | Research-First over Execution-First | (Exists) Document why research precedes execution | Completed |
| ADR-002 | Modular Monolith with Extraction Path | Document why not microservices now and how to extract later | Immediate |
| ADR-003 | Event Bus as Nervous System | Document the role of events in system communication | Immediate |
| ADR-004 | Repository Pattern for Persistence | Document why domain code never accesses DB directly | Immediate |
| ADR-005 | SQLite Dev / PostgreSQL Prod | Document database strategy and migration path | Immediate |
| ADR-006 | CLI-First Interface Strategy | Document why CLI is primary, API secondary, dashboard tertiary | Immediate |
| ADR-007 | Structured Logging as Default | Document logging standards and why JSON format | Milestone 0 |
| ADR-008 | Backtest-to-Live Parity | Document how paper trading bridges backtesting and live trading | Milestone 3 |
| ADR-009 | Knowledge Graph as Research Backbone | Document why all research entities form a traversable graph | Milestone 2 |
| ADR-010 | Deprecation Strategy | Document how features and APIs are deprecated and removed | Milestone 7 |
| ADR-011 | Plugin System Architecture | Document strategy for third-party extensions | Milestone 7 |
| ADR-012 | ML Model Integration Boundary | Document how ML models enter and leave the system | Milestone 6 |

---

## 17 Hiring Standard

### Portfolio Quality Definition

A "portfolio-quality" codebase is one that demonstrates:

1. **Professional Consistency**: Every file looks like it was written by the same person on the same day. Naming, formatting, structure, and patterns are uniform across the entire repository.

2. **Architectural Integrity**: The architecture is visible in the code. Package names, module organization, and import patterns communicate the system design. A new engineer can understand the architecture by reading the imports.

3. **Test-Driven Reliability**: Tests are not an afterthought — they are the foundation. Coverage > 90%, tests run in seconds, and test failures are immediately actionable.

4. **Production Readiness**: The system has been operated long enough to prove its reliability. Logging is useful. Metrics exist. Failures are handled gracefully. Recovery is documented.

5. **Research Provenance**: Every result in the system can be traced back to its source data and configuration. No result is orphaned. No data is unexplained.

6. **Review Readiness**: Every line has been reviewed. Every PR has a meaningful description. Every commit tells a story. The git history is a narrative, not a dump.

### The Standard

Before TraderOS is presented publicly:

- **No file** should exist that the team is embarrassed to show.
- **No test** should fail without an immediate known fix.
- **No commit** should require an oral explanation.
- **No architecture decision** should be undocumented.
- **No bug** should be fixable without a test.
- **No feature** should be buildable without an ADR (if significant).

An engineer joining the team should be able to:
1. Clone the repo and run the full test suite in < 30 seconds.
2. Understand the system architecture in < 30 minutes by reading the package structure and ADRs.
3. Make a meaningful contribution on their first day.
4. Deploy the system on their second day.

---

## 18 Final Engineering Constitution

### Preamble

We, the engineers of TraderOS, establish this Constitution as the supreme engineering authority for this repository.

All code written, all architectures designed, all decisions made, and all features delivered shall conform to the principles, standards, and structures defined herein.

### Article I: The Philosophy

Every line of code serves a purpose. Every design decision has a rationale. Every trade executed has a traceable chain of evidence. We build systems, not scripts. We prefer evidence over intuition. We optimize for longevity, not speed. We design for five years from now, not five minutes from now.

### Article II: The Architecture

The architecture recognizes four sacred layers: Domain, Application, Interface, Infrastructure. Dependency flows inward. The Domain knows nothing of the outside world. The Infrastructure serves the Domain, not the reverse. Any violation of this direction is a constitutional crisis.

### Article III: The Method

The scientific method is the default workflow. Observe before hypothesize. Hypothesize before test. Test before execute. Execute before learn. Learn before improve. No feature exists that does not serve this cycle.

### Article IV: The Evidence

Every claim requires evidence. Every parameter requires justification. Every configuration requires documentation. "Because it felt right" is not an acceptable rationale. "Because the backtest showed" is the minimum standard.

### Article V: The Integrity

A system that cannot be tested cannot be trusted. A system that cannot be observed cannot be debugged. A system that cannot be reproduced cannot be improved. Testing, observability, and reproducibility are not optional — they are the cost of entry.

### Article VI: The Standards

The standards in this document are not guidelines. They are requirements. Every PR is measured against them. Every engineer is accountable to them. They exist because shortcuts compound and integrity decays.

### Article VII: The Debt

Technical debt is acknowledged and managed, not ignored and accumulated. 20% of every sprint is dedicated to its reduction. No feature work exceeds 70% of capacity. The system must improve with age, not degrade.

### Article VIII: The Future

This Constitution is not static. It will be amended as the platform grows and the domain evolves. But amendments are not casual — they require the same rigor as architectural decisions. Every amendment must be proposed, debated, documented, and ratified.

### Article IX: The Commitment

Every engineer working on TraderOS commits to:
1. Upholding these principles in every PR.
2. Holding peers accountable to these standards.
3. Documenting decisions that shape the architecture.
4. Paying down debt encountered during feature work.
5. Leaving the codebase better than they found it.

### Article X: The Legacy

TraderOS will become the standard platform for systematic trading research. This Constitution is the foundation upon which that legacy is built. Every commit, every PR, every decision either reinforces that foundation or weakens it. There is no neutral action.

---

**Ratified by the TraderOS Engineering Organization**

**This document is the highest engineering authority in this repository. All prior documents, conventions, and practices are subordinate.**
