# Sprint 33 — Disaster-recovery runbook commands execute via `python -m traderos` (DR-01)

This sprint makes every command documented in `runbooks/disaster_recovery.md`
actually executable, and proves each one with a new CI-registered evidence
drill. Before this sprint the runbook told an operator to run `python -m
traderos ...` commands that the console-script-only CLI could not execute: the
module entrypoint did not exist, `audit verify` was a positional argument the
parser could not route, `audit query`/`run`/`status` had no parser branch, and
`db restore --latest` was not implemented. A runbook whose commands cannot run
is worse than none during an outage.

- **Module entrypoint:** `src/traderos/__main__.py` so `python -m traderos`
  matches the `traderos` console script exactly.
- **`audit`:** `verify` is a proper subcommand; new `audit query --filter`
  reads the **durable** audit trail (the same SQLite/Postgres service the
  daemon records into) and filters on `action`/`actor`/`resource`/`detail`
  (substring, comma-separated keys, JSON or text). A missing audit schema
  fails closed with a clear "run `db migrate`" message instead of a silent
  empty result.
- **`run`:** alias of `daemon start` with `--interval`/`--mode`.
- **`status`:** reports mode, running state, market count, crash-recovery
  state, kill switch, and reconciled order acceptance (`orders_accepted`) plus
  the health summary; JSON support.
- **`risk status`:** adds the `orders_accepted` output token and `--json`;
  **`risk reconcile status`** reports the reconciliation gate without running
  a reconcile (plain `risk reconcile` still runs one).
- **`db restore`:** accepts a positional path, `--backup <path>`, and the
  runbook's `--latest` (newest backup wins); with no backup it fails closed
  with a clear message rather than defaulting.

## Ground truth (verified, not assumed)

- `runbooks/disaster_recovery.md` commands: `python -m traderos db
  restore --backup <path>`, `db restore --latest`, `db migrate`, `db check`,
  `db list-backups`, `audit query --filter "action=crash.recovery"`, `risk
  reset`, `run --mode live`, `status` (runbooks/disaster_recovery.md:27, 36,
  39, 58, 72, 94-106).
- The console entrypoint existed (`traderos` in `pyproject.toml [project.
  scripts]`) but `python -m traderos` failed: no `src/traderos/__main__.py`.
- The daemon records crash-recovery and kill-switch events into a **durable**
  audit (`SQLiteAuditService`/`PostgresAuditService`, `factory.py:145-157`,
  `daemon_controller.py:216` records `crash.recovery`), while the CLI `audit`
  commands previously built a fresh in-memory `AuditService` — so the runbook's
  "review the audit log" step would always return nothing on the one process
  that mattered. DR-01 closes that false gate by reading the same durable
  service the factory wires (`_build_audit_service` mirrors `factory.py:122`
  plus the `145-157` backend branch).

## Work Completed

### WP1 — module entrypoint + parser/handler wiring
- New `src/traderos/__main__.py` calls `traderos.interfaces.cli.main.main`.
- `audit`: `verify` moved to a real subparser; `query` subcommand with
  `--filter`/`--limit`; dispatch routes `audit_cmd` (`verify`/`query`/none).
- New `run` and `status` verbs with `--mode`; `db restore` gains positional
  `backup`, `--backup <path>` (`backup_flag`), and `--latest`;
  `risk reconcile` gains an optional `status` verb; `risk status` gains
  `--json` output with `orders_accepted`.
- `src/traderos/interfaces/cli/main.py` handlers: `cmd_run`, `cmd_status`,
  `cmd_audit_query`, `_build_audit_service`, `_read_audit`.

### WP2 — durable audit reads (DR-01 false-gate closure)
- `cmd_audit`/`cmd_audit_query`/`cmd_audit_verify` now read the configured
  SQLite/Postgres audit service via `_build_audit_service()` — the same
  backend selection as the factory. If the schema is missing, the CLI fails
  closed: `Audit trail unavailable: <e>. Run python -m traderos db migrate
  first.` with rc=1, never a silent "no entries".
- Tests: `tests/test_cli.py` updated to the `_build_audit_service` seam
  (text/JSON/no-entries) plus `test_audit_trail_unavailable_fails_closed`.

### WP3 — evidence drill + CI registration
- New `scripts/evidence/run_runbook_cli_drill.py` (13 cases) runs every
  documented command as a real `python -m traderos` subprocess against a
  scratch SQLite DB, including a `db backup`→corrupt→`restore --backup`/
  `--latest`/positional round-trip, the fail-closed no-arg restore, and a
  durable `crash.recovery` entry recorded via `SQLiteAuditService` that
  `audit query --filter` must return (and exclude `order.placed`).
- Registered as `runbook_cli` in the credential-free CI drill set
  (`run_ci_drills.py`); the drill inventory test and the `--list` count updated
  (16 drills).

## Belt-and-suspenders checks
- Full suite on the final state: **1658 passed / 7 skipped**, coverage
  **76.6%** (gate 70%).
- CI drill suite: **16/16 PASS**, including the new `runbook_cli` drill
  (`docs/evidence/2026-08-10_runbook_cli_drill.log`).
- Static checks clean: `ruff check .` 0, `pyright` 0 errors, `black --check`
  and `isort --check` clean on changed files.
- Real-path smoke: `python -m traderos audit` reads the durable trail
  (daemon/kill-switch entries present), `audit verify` PASS, `db restore
  --latest` round-trips a scratch DB to its pre-corruption row, `run --mode
  paper` starts the engine and shuts down gracefully on SIGTERM.

## Not done (honest)
- The CLI audit read requires the DB to be migrated (schema present); an
  unmigrated DB yields the explicit fail-closed message above — the operator
  must `db migrate` first, exactly as the runbook's full-recovery flow already
  sequences it.
- `risk reconcile status` reports the gate but does not run a reconcile by
  design; a fresh instance correctly reports `blocked` (no reconciliation has
  run), which is the honest state rather than a fabricated allow.
- Closing DR-01 makes the documented commands runnable; it does not change the
  still-open G-01/G-02 real-broker and real-market exit gates, which remain
  operator-run.
