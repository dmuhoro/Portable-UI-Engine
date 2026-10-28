# Sprint 22 — Postgres reproducibility: environment-independent CI signal

**Period:** 2026-08-02
**Objective:** Make the full test suite (1223+ tests, 90%+ coverage) pass
identically in **any** environment — with or without a reachable Postgres —
eliminating the last unverified/unreproducible claim in TraderOS's CI signal.
Confirmed by an independent cold-environment audit against `d52f0bd`: 51 test
errors, 100% traced to one root cause (Postgres unreachable at
`localhost:5433`, no skip guard), zero application-logic defects.

**Scope (per directive):** only `tests/`, the CI workflow, and two named
governance docs. No new services, ports, or abstractions — a test-harness and
CI-configuration fix, not an architecture change.

**Reference docs:** `docs/AUDIT_GROUND_TRUTH.md` §7 (new delta),
`docs/engineering/NEXT_STEPS_TO_COMPLETION.md`.

---

## Work Package Register

| ID | Work package | Gate |
|----|--------------|------|
| WP-N1 | Postgres-reproducibility guard + honest skip | both-full-suite runs green, only skip count differs |
| WP-N0 | Prior single-environment claim | folded (not reproducible) |
| WP-N2 | Audit-doc consolidation | single canonical `docs/AUDIT_GROUND_TRUTH.md` |

## Work Completed

### WP-N1 — Reachability guard + honest skip
- Added a short-timeout reachability probe (`psycopg2.connect` +
  `connect_timeout=3`, caught as `psycopg2.Error`) at the top of:
  - `tests/test_postgres_repositories.py`
  - `tests/test_observability_postgres.py`
  - `tests/test_observability_postgres_services.py`
  - and on the `TestV004Postgres` class in `tests/test_migration_v004.py`
    (its sqlite `TestV004Sqlite` still runs with no Postgres).
- When unreachable, tests **skip** with an explicit, honest reason
  (`Postgres not reachable at <dsn> — skipped, not passed`), visibly distinct
  from a pass. When reachable they run for real.
- Read `POSTGRES_TEST_DSN` (default `localhost:5433`). Verified rather than
  assumed that `.github/workflows/ci.yml` (test job) provisions that Postgres
  (`postgres:16` → host `5433`, db `traderos_test`) and documented it so CI
  exercises the **pass** path, not the skip path.

### Evidence (both environments, attached)
- **WITH Postgres** (`docs/evidence/2026-08-02_postgres_with_pg.log`):
  `1274 passed, 1 skipped` — 0 failures, 0 errors; PG tests ran for real.
- **WITHOUT Postgres** (`docs/evidence/2026-08-02_postgres_without_pg.log`):
  `1219 passed, 56 skipped` — 0 failures, 0 errors; 55 PG-backing items skipped.
- Only the skip count differs (55); both re-runnable from a cold checkout.

### Governance consolidation (WP-N1/WP-N0/WP-N2)
- WP-N2: merged `docs/engineering/AUDIT_GROUND_TRUTH.md` **verbatim** into the
  canonical `docs/AUDIT_GROUND_TRUTH.md` (new §7 delta + appendix), deleted the
  redundant engineering copy via `git rm`, repointed internal sprint links.
- WP-N1/WP-N0: `docs/engineering/NEXT_STEPS_TO_COMPLETION.md` — WP-N1 marked
  DONE with the two attached runs, WP-N0 folded, WP-N2 closed.

### Gate
- `1274 passed / 1219 passed` both **0 failures, 0 errors**, coverage 93%+;
  `ruff` 0 errors on the changed test files; black/isort clean; `ci.yml`
  parses as valid YAML. No source (`src/`) changes in this sprint.
