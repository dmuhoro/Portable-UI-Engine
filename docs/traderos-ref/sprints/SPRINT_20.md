# Sprint 20 — Programme Ω: First genuine execution evidence

**Period:** 2026-08-02
**Objective:** Deliver the repository's first genuine, command-logged execution
records (Programme Ω). Fix the confirmed bootstrap `ConfigError` so
`pilot dry-run` works from a fresh checkout; run the operator dry-run
rehearsal against a **real Alpaca paper account**; run real backup→restore and
migration-rollback drills with checksums and integrity checks; update the
governance docs **evidence-only**. No feature work, no new abstractions.

**Reference docs:** `docs/engineering/NEXT_STEPS_TO_COMPLETION.md`,
`docs/AUDIT_GROUND_TRUTH.md` §10, `docs/engineering/FINISH_LINE_DASHBOARD.md`.

---

## Work Package Register

| Layer | Deliverable | Gate |
|-------|-------------|------|
| Ω-1 | Bootstrap fix — `Config.load()` auto-creates runtime dirs | regression test green |
| Ω-2 | Real `pilot dry-run` rehearsal against Alpaca paper account | operator workflow `READY`, exit 0 |
| Ω-3 | Backup→restore drill (populated DB) | SHA-256 round-trip equal, integrity ok |
| Ω-4 | Migration rollback drill | 6→3→6, integrity ok |
| Ω-5 | Governance evidence-only update | docs reflect only proven facts |
| Final | Full suite + lint/typecheck + sprint record + CHANGELOG + push | **1266 passed, 1 skipped**; ruff//pyright clean |

## Work Completed

### Ω-1 — Bootstrap fix
- `Config.load()` now calls `_ensure_runtime_dirs()` creating `data_dir`,
  `exports_dir` and the `db_path` directory before `validate()`. Strict
  validation for all other fields preserved.
- Regression test: `tests/test_infrastructure.py::test_load_creates_missing_db_directory`.

### Ω-2 — Genuine dry-run rehearsal (real Alpaca paper account)
- Confirmed credentials against live paper edge (`/account 200`, `/positions []`, `/orders []`).
- Installed `alpaca-py 0.43.5` (user-site); `pilot dry-run` workflow driven with
  `dry_run=True`, reconciliation + `LIVE_TRADING_CONFIRMED=true` from a **real** broker.
- Result: genuine `account_balance 100,000.00`, `can_accept_orders=True`, all
  operator steps PASS (prep-hook, broker, market-data, paper, performance,
  controlled-live with live execution disabled, session report); strategy
  promotion SKIPPED (operator decision); exit **0**.

### Ω-3 — Backup → restore drill
- Populated DB (schema v6 + marker row), `traderos db backup`, deleted live DB,
  `traderos db restore`. Verified **SHA-256 of restored == original**
  (`b91b07a…`), marker preserved, `PRAGMA integrity_check` ok.

### Ω-4 — Migration rollback drill
- `traderos db migrate` (v6) → `db rollback --target 3` (v3, 21 tables, integrity
  ok) → `db migrate` (v6, 24 tables, integrity ok).

### Real defects surfaced & fixed by the genuine run
- `AlpacaBrokerAdapter.get_open_orders()` used `get_orders(status="open")`
  (incompatible with alpaca-py 0.43.5) → now `GetOrdersRequest(QueryOrderStatus.OPEN)`;
  test mock + assertion updated.
- `factory.py` only built `PaperTradingService` in `PAPER` mode, so the LIVE-mode
  operator workflow hard-failed at `BROKER_CHECK/PAPER_TRADING`; now built in
  `LIVE` too (harmless under `dry_run=True`), enabling a complete rehearsal.

### Ω-5 — Governance evidence-only update
- `NEXT_STEPS_TO_COMPLETION.md` Ω trackers → DONE with pointers to evidence logs.
- `docs/evidence/README.md` index updated.
- `FINISH_LINE_DASHBOARD.md` — Deployment Readiness 72→74; PRI note records the
  real paper drill; residual blockers (replay CLOSURE-12, real-money pilot,
  Binance R-01, Postgres R-02) stated honestly.
- `AUDIT_GROUND_TRUTH.md` §10 delta added.

## Verification

- `make ci` equivalent gates: `ruff check .` **0 errors**; `black --check` /
  `isort --check` clean; `pyright` strict **0 errors**; **full suite 1266 passed,
  1 skipped** (matches Sprint-19 baseline).
- Evidence logs: `docs/evidence/2026-08-02_*.log` (secrets redacted; verified no
  key/secret fragments in any committed file).
