# Sprint 42 — Durability completion: knowledge graph, migration v009, persisted backtest history

**Period:** 2026-08-20
**Objective:** Close the remaining software-closeable durability gaps on the
road to GO, following Sprint 41's research-store durability work. Three gaps
closed without touching the execution/order path: (1) the **knowledge graph**
was in-memory-only and lost on restart — now wired to durable SQLite and
Postgres repos; (2) the Postgres store lacked a **canonical schema** for the
research and knowledge tables the repos read/write — added **migration v009**;
(3) **backtest results were computed on the fly and never persisted** — now
recorded through the strategy catalog and surfaced via a new
`GET /v1/backtest/history` endpoint.

---

## 1. Durable knowledge graph

**Problem:** `KnowledgeGraphService` was wired to `InMemoryKnowledgeNodeRepository`
and `InMemoryKnowledgeEdgeRepository` (`factory.py`), so the research knowledge
graph was **lost on every restart** — the same data-loss gap closed for the
research store in Sprint 41.

**Closure:**
- Added **`postgres/knowledge.py`** — `PostgresKnowledgeNodeRepository` and
  `PostgresKnowledgeEdgeRepository` (positional row access to match the
  psycopg2 convention; node/edge CRUD + `get_by_label`, `get_by_type`,
  `search`, `get_by_source`, `get_by_target`, `get_neighbors`).
- Wired the factory to use Postgres repos on the PG backend, SQLite repos
  (`SQLiteKnowledge*`, already implemented) on SQLite, and in-memory only when
  no DB is present.
- Knowledge data now survives restart/crash on both durable backends.

## 2. Migration v009 — canonical research + knowledge tables

**Problem:** the Postgres repos for research (Sprint 41) and knowledge (this
sprint) self-create their tables, but the migration set did not include them —
so a fresh Postgres schema applied only through migrations lacked the
`experiments`, `experiment_results`, `knowledge_nodes`, and `knowledge_edges`
tables the repos expect. v001 created a legacy `research_tests` /
`research_results` pair the current repo contract does not use.

**Closure:** added **`migrations/v009_research_knowledge.py`** (VERSION 9) that
creates the canonical `experiments`, `experiment_results`, `knowledge_nodes`,
and `knowledge_edges` tables on every backend (idempotent `CREATE TABLE IF NOT
EXISTS`), with a matching `down()`.

- Verified on a fresh Postgres 16: `migrate()` reaches schema version **9** and
  all four tables exist.
- Updated every schema-version assertion across the suite (down-path test,
  `test_programme_b_operational_trust`) from 8 → 9.
- Updated the CI `deploy-check` gate: `grep "Schema version: 9"`.

## 3. Persisted backtest history

**Problem:** both `POST /v1/backtest` and `POST /v1/research/backtest`
computed metrics and returned them on the fly; **nothing persisted the
results**, so a strategy's backtest history was empty even after runs.

**Closure:**
- Added `StrategyCatalogService.record_backtest(...)` — persists a
  `BacktestResult` (metrics + equity curve + period) through the durable
  `backtest_results` repo; returns `None` when no repo is wired (honest, not a
  silent claim).
- Added `StrategyCatalogService.history(strategy, limit)` — recent persisted
  results for a strategy.
- Wired both API backtest handlers to record results, returning a `recorded`
  flag so consumers know whether the result was retained.
- Added **`GET /v1/backtest/history?strategy=&limit=`** endpoint (404 for
  unknown strategy).

## 4. Slice 4 — real Binance feed on the deployed instance (honest outcome)

**What was done:** `BINANCE_ENABLED=true` and `BINANCE_STREAMING=true` set on
the Railway production instance; three deploys shipped. The first feedless
deploy exposed a real bug: the A2 transports lazily import `websockets`, which
no dependency group shipped — so an explicitly-enabled stream **silently**
failed to wire while healthz stayed green. Fixed properly:

- New `streaming` extra (`websockets==17.0.1`) in pyproject + Dockerfile install.
- Both streaming seams in the factory now log a loud warning when an
  explicitly-enabled feed fails to wire (no silent drops); two new tests pin it.
- Deployed orchestrator started (`POST /v1/orchestrator/start`) — running, paper mode.

**What did NOT close:** the deployed instance still serves no BTCUSDT candles.
Evidence chain: local drill 8/8 PASS against live Binance; deployed REST
backfill returns empty (404 fail-closed, not 503) AND the WS stream stays
silent → outbound Binance (REST + WSS) is unreachable from Railway's egress
region (geo-restriction is the consistent explanation; Kenya egress works).
Fixing it is a **dashboard operator action** (move the service region to an
EU zone, e.g. eu-west/eu-central, then redeploy + start the orchestrator) —
not automatable via the Railway CLI, so it is recorded here rather than
faked. G-03-style honesty: no fabricated market data is served in the
meantime; the endpoint fails closed with 404.

## 5. Verification

| Check | Result |
|---|---|
| `pytest` (full suite) | **2270 passed, 7 skipped, 100.00%** coverage (gate 100) |
| `ruff check .` | All checks passed |
| `black --check .` | 370 files left unchanged |
| `pyright` (strict, `src/traderos`) | 0 errors, 0 warnings |
| `pre-commit --all-files` | all hooks Passed |
| Postgres knowledge repo tests | 4 new tests (51 total in the PG repo file), pass against PG 16 |
| Migration v009 | applies on fresh Postgres to schema version 9; all 4 tables present |
| Backtest history tests | endpoint + catalog unit tests pass |
| No-silent-drop streaming tests | 2 new tests prove both factory seams warn loudly on wire failure |

## 6. Governance / honesty notes

- The execution/order path was **not touched** — real order execution remains
  tested last per directive.
- Slice 4's code path (streaming extra + loud wire-failure warnings) is
  complete and locally proven (8/8 live-feed drill); activating the deployed
  instance remains an operator dashboard step — move the service to an EU
  region so Binance egress works, then redeploy and start the orchestrator.
- GO for real capital remains **NO-GO** until the exit tests in
  `GAP_READINESS.md` are met (G-02 paper soak, G-01 edge proof, operator gates).
