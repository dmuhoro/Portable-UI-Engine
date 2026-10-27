# Progress Ledger

Chronological table of work shipped, sourced from git history. One row per session/sprint reflecting commits and independent verification.

| date | commit(s) | what shipped | what broke (if anything) | what was claimed vs. what you independently verified |
|---|---|---|---|---|
| 2026-10-01 | 09abade | release(v1.3.3): honest deployment of the soak — docs, runbook, version pin | — | Git history; shipped per commit. |
| 2026-10-01 | b55e5ce | release(v1.3.3): signed provenance manifest (11 artifacts, head acc30e4) | — | Git history; shipped per commit. |
| 2026-10-02 | 4b32ce0 | feat(frontend): add Vercel static deploy config for dashboard (L1) | — | Git history; shipped per commit. |
| 2026-10-03 | dbf7b28 | fix(B-1): a str timestamp made the LIVE data-gap breaker unreachable | — | Git history; shipped per commit. |
| 2026-10-03 | 1b839dc | fix(broker): key order idempotency on intent, not request shape | — | Git history; shipped per commit. |
| 2026-10-03 | efd6130 | docs(audit): 2026-10-03 sprint, foundations and doctrine audits | — | Git history; shipped per commit. |
| 2026-10-03 | 4db7ea1 | fix(reconcile): order acceptance is a latch, not a startup flag | — | Git history; shipped per commit. |
| 2026-10-03 | 8c2765b | fix(risk): position sizing may not invent a win rate | — | Git history; shipped per commit. |
| 2026-10-03 | 7b33e1f | ci: configure CodeRabbit review layer with repository doctrine | — | Git history; shipped per commit. |
| 2026-10-03 | 13e55fb | ci: add OD-14 docs-drift gate and fix the three drifts it found | — | Git history; shipped per commit. |
| 2026-10-03 | 1aec0ec | docs: write down the test strategy the suite has been living | — | Git history; shipped per commit. |
| 2026-10-03 | cbd43a8 | docs: record G-08 — the system can no longer size positions | — | Git history; shipped per commit. |
| 2026-10-03 | 8fd258a | docs(adr): ADR-009 — Decimal at the boundary, scaled integers in SQLite | — | Git history; shipped per commit. |
| 2026-10-03 | 417a182 | feat(money): exact Decimal<->scaled-integer conversion with a float tripwire | — | Git history; shipped per commit. |
| 2026-10-04 | 0b1fdb8 | fix: VaR derivation, perf targets, evidence contract, and CHANGELOG | — | Git history; shipped per commit. |
| 2026-10-05 | c2fcd19 | docs: add session 2026-10-05 entry — Alpaca credentials activate CI drill suite | — | Git history; shipped per commit. |
| 2026-10-05 | 2c48026 | fix(pg): bound read transactions in PostgresUserRepository (fail closed) | — | Git history; shipped per commit. |
| 2026-10-05 | 622fd33 | fix(pg): bound read transactions across all postgres repositories | — | Git history; shipped per commit. |
| 2026-10-05 | 911d473 | fix(pg): bound read transactions in remaining postgres repositories | — | Git history; shipped per commit. |
| 2026-10-05 | 2e225c3 | fix(sqlite): typed use-after-close error; stop orphaned health writes crashing the run | — | Git history; shipped per commit. |
| 2026-10-05 | 132334d | fix(migrate): verify the version marker against the schema instead of trusting it | — | Git history; shipped per commit. |
| 2026-10-05 | e370654 | fix(factory): resolve a connection for the postgres account repo instead of passing None | — | Git history; shipped per commit. |
| 2026-10-05 | 4738088 | fix(api): add RISK_MEASUREMENT_SCOPE so the research risk endpoint exists | — | Git history; shipped per commit. |
| 2026-10-05 | 9021735 | feat(db): refuse destructive SQL and stray remote connections during tests | — | Git history; shipped per commit. |
| 2026-10-05 | f703e45 | chore(docker): bind the test postgres to loopback only | — | Git history; shipped per commit. |
| 2026-10-05 | 00f4ead | test(security): close the leak surface the existing hygiene test missed | — | Git history; shipped per commit. |
| 2026-10-05 | 6b8008e | fix(db): make the remote-database interlock fail closed, and stop the suite dialling production | — | Git history; shipped per commit. |
| 2026-10-05 | 99b4675 | fix(db): an explicit Config must not be overridden by the ambient DATABASE_URL | — | Git history; shipped per commit. |
| 2026-10-05 | a8fd0db | fix(research): give every research row a real identity | — | Git history; shipped per commit. |
| 2026-10-05 | 40c551e | fix(database): restore cursor iteration and an honest database_url type | — | Git history; shipped per commit. |
| 2026-10-06 | Phase 0 (this session) | Identified/confirmed RISK_MEASUREMENT_SCOPE exists in market.py; test collection clean (0 errors); full suite run (excl. flaky perf benchmark) shows 2588 passed, 16 skipped, 0 failed. | None observed in this run. | Claimed regression from import mismatch was a red herring at HEAD c2fcd19 - constant exists; independently verified via `pytest --collect-only` (no errors) and full suite summary. |

Evidence: Phase 0 full summary in /tmp/pytest_main.txt (2588 passed, 16 skipped, 0 failed).
