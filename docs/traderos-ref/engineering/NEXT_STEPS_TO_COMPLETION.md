# TraderOS — Next Steps to Completion

**Tracked from:** 2026-08-02 · **Programme Ω:** Execution-Evidence delivery

## Programme Ω — definition

**Goal.** Produce the first genuine, command-logged execution records the
repository has ever contained: a real pilot dry-run rehearsal, a real
backup→restore drill, and a real rollback drill — each with attached raw
evidence in `docs/evidence/`. No simulated `PASS`. A correctly-labelled
`PARTIAL` beats a false `DONE`.

**Acceptance criteria (Ω-DoD).**
1. `pilot dry-run` succeeds from a genuinely fresh checkout with **zero
   manual setup steps**.
2. At least one real, timestamped, command-logged execution record exists in
   `docs/evidence/` for each of: dry-run rehearsal, backup/restore, rollback.
3. `AUDIT_GROUND_TRUTH.md`, this file, and `FINISH_LINE_DASHBOARD.md` state
   only what is genuinely proven.
4. The reported result is the honest status of each evidence type, with the
   exact blocker (if any) that prevents `DONE`.

## Programme Ω — result (2026-08-02)

| Gate | Status | Blocker (if any) |
|---|---|---|
| Ω-1 Bootstrap fix | **DONE** | — |
| Ω-2 Pilot dry-run rehearsal (real Alpaca paper) | **DONE** (workflow READY / exit 0) | — (paper account; real-money live still requires operator-controlled pilot) |
| Ω-3 Backup→restore | **DONE** (SHA-256 round-trip equal) | — |
| Ω-4 Rollback | **DONE** (6→3→6, integrity `ok`) | — |
| Ω-5 Governance update | **DONE** | — |

## Work package tracker

| ID | Work package | Status | Evidence |
|---|---|---|---|
| Ω-1 | Bootstrap fix (auto-create runtime dirs in `Config.load`) | **DONE** | regression test added; verified in fresh dir |
| Ω-2 | Run `pilot dry-run` rehearsal for real (broker/paper wired) | **DONE** | `docs/evidence/2026-08-02_dry_run_paper_rehearsal.log` (real Alpaca paper account) |
| Ω-3 | Backup → restore drill (populated DB, timed, checksums) | **DONE** | `docs/evidence/2026-08-02_backup_restore_drill.log` |
| Ω-4 | Rollback drill (prior migration, timed, verified) | **DONE** | `docs/evidence/2026-08-02_rollback_drill.log` |
| Ω-5 | Governance evidence-only update | **DONE** | this file + `AUDIT_GROUND_TRUTH.md` §Δ + `FINISH_LINE_DASHBOARD.md`

> Status cells are updated only from actual evidence (Task 4); never from aspiration.

---

## Postgres-reproducibility & audit-consolidation programme (2026-08-02)

Single, focused follow-on programme: make the full test suite pass identically
with **or** without a reachable Postgres, so the CI "green" signal is
unambiguous in any environment. Scoped by directive to `tests/`, the CI
workflow, and governance docs only — no new services/ports/abstractions.

| ID | Work package | Status | Evidence |
|----|--------------|--------|----------|
| WP-N1 | Postgres-reproducibility: reachability guard + honest skip | **DONE** | `docs/evidence/2026-08-02_postgres_with_pg.log` (with PG: **1274 passed, 1 skipped, 0 fail/err**); `docs/evidence/2026-08-02_postgres_without_pg.log` (without PG: **1219 passed, 56 skipped, 0 fail/err**). 55 Postgres-backing tests skip (not silently pass) when PG is unreachable; CI (`ci.yml` test job) provisions PG so the pass path runs for real |
| WP-N0 | Prior claim "passes only with Postgres" (single-environment) | **FOLDED** | Not reproducible → superseded by WP-N1; removed from coming claims. No single-environment result is treated as sufficient evidence |
| WP-N2 | Audit-doc consolidation | **CLOSED** | `docs/engineering/AUDIT_GROUND_TRUTH.md` merged verbatim into canonical `docs/AUDIT_GROUND_TRUTH.md` (new §7 delta + appendix), redundant file deleted, internal links repointed; the task-4 cross-check is in that §7 |

**Self-check (Task 4):** every claim above survives a cold checkout **both** with
and without a reachable Postgres — both attached runs show 0 failures, 0
errors; only the skip count differs.
