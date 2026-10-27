# ADR-011: One Owner Per Table — the Migration and the Repository Cannot Disagree

**Status:** Accepted
**Date:** 2026-10-05
**Driver:** `Constitution.md` §"enforcement goes at the real boundary" and §"no
claim of capability without a named command"; the 90-minute suite hang and the
51-failure full-suite run that followed it.

## Context

Two independent defects were found while chasing a symptom that looked like one
problem: a full test run hung with no failing test to point at.

**1. The hang was a lock wait, not slow tests.** `pg_stat_activity` showed five
backends in `idle in transaction` and one blocked on
`DROP TABLE IF EXISTS operator_workflow CASCADE`. psycopg2 opens a transaction
on the first statement, so a connection that is opened and never closed is not a
slow resource leak — it is a session that holds locks forever. The leak sites
were real:

- `cli/main.py` `_historical_candles_for_backtest` opened a connection, handed it
  to a cache repository, and returned without closing.
- `cli/main.py` `_build_audit_service` did the same for every `audit`,
  `audit query`, and `audit verify` invocation.
- `build_orchestrator` opened the durable connection and passed it to roughly
  twenty repositories, none of which owned it, with no way for any caller to
  release it.

**2. `v001_initial.py` and the repositories declared different schemas for the
same tables.** `observations` was declared `id SERIAL PRIMARY KEY` by the
migration and `id TEXT PRIMARY KEY` by `PostgresObservationRepository`. The
domain entity is `Observation.id: uuid.UUID`, and the repository writes
`str(entity.id)` — so the repository was right and the migration was wrong.

Because every one of these uses `CREATE TABLE IF NOT EXISTS`, the first owner to
run wins and the second is silently ignored. On a fresh PostgreSQL database the
outcome depends on construction order:

- repository first → `observations.id` is TEXT, then v001's
  `hypotheses.observation_id INTEGER REFERENCES observations(id)` cannot be
  implemented. PostgreSQL raises `DatatypeMismatch` and **aborts v001
  mid-migration**, so `hypotheses` is never created, the version marker is never
  written, and every subsequent migration is skipped.

That single ambiguity presented as ~25 unrelated API test failures, each with a
confusing error pointing at a different subsystem.

## Decision

**The migration and the repository must declare the same schema, and the
repository wins where they disagree.**

`observations`, `hypotheses`, `research_tests`, `research_results`, `lessons`,
and `liquidity_zones` are now declared in `v001_initial.py` to match their
repository DDL exactly: TEXT uuid keys, TEXT ISO-8601 timestamps, TEXT tags
holding a JSON array.

The reasoning is that the repository is closer to the truth. It is written
against the domain entities, and it is what production code actually executes
when it persists a row. Where the migration and the repository disagree about a
type, the migration is the copy that has no consumer to contradict.

This is deliberately *not* "delete the repository DDL". That would be the
cleaner end state, but it would require every repository constructor to depend
on migrations having run first, and several of them are constructed before
`migrate()` is called. Both owners are retained, and they are now required to
agree. A future migration that renames a column must change both, and the
migration is the wrong place to discover the disagreement at runtime.

## Consequences

- `hypotheses` and `lessons` are created on a fresh PostgreSQL database, so the
  migration chain completes and the version marker is written.
- `schema_drift()` keeps its meaning: it verifies tables exist, which is now a
  real check rather than one that passed because a repository had created the
  table behind the migration's back.
- The dual ownership remains a hazard, and this ADR does not remove it — it makes
  the two owners consistent and documents why. Eliminating it means having
  migrations be the only DDL source, which is a larger change than the defect
  warranted and should be its own ADR.

## Connection Ownership

Because the orchestrator's connection is shared and unowned, three things are now
explicit rather than implicit:

- `TradingOrchestrator.close()` releases it, and the orchestrator is a context
  manager. It is idempotent and a no-op for an in-memory orchestrator.
- `AsyncDaemonController.close()` closes the orchestrator it wraps; `stop()` only
  halts the loop, because the connection is a separate resource with a separate
  lifetime.
- The CLI's three former leak sites close in a `finally`, and the audit service is
  a context manager (`_AuditServiceHandle`) so releasing it cannot be forgotten.

A harness-level backstop also exists: `conftest.py` terminates backends in
`idle in transaction` at each test boundary. It is scoped to that state
specifically — not all backends — because a connection mid-query is `active` and
an idle one has already committed. Terminating everything on the database
manufactured a failure in the money test's scratch-database setup
(`server closed the connection unexpectedly`), which is a worse outcome than the
hang it was meant to prevent.

## Verification

```
# The FK that could not be implemented is now created:
PYTHONPATH=src python3 -m pytest tests/test_money_storage_types.py -v

# No backend is left idle-in-transaction after a PostgreSQL-heavy run:
docker exec traderos-pg-test psql -U traderos -d postgres \
  -c "SELECT count(*) FROM pg_stat_activity
      WHERE datname='traderos_test' AND state LIKE 'idle%'"
```

Both the ownership fix and the schema fix were proved by negative control: the
previous `connection.py` fails 9 of the affected tests with `DATABASE_URL` set,
and the previous `v001_initial.py` reproduces the `DatatypeMismatch` that
skipped the migration chain.