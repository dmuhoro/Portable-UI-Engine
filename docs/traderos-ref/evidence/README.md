# Programme Ω — Execution Evidence

This directory holds **raw, timestamped execution records** for Programme Ω
(the genuine-run evidence programme). Each file is captured directly from a
real command run — never simulated, never narrated.

## Conventions

1. **Redaction.** Any credential that appears in a captured command is masked
   as `***REDACTED***` before the log is saved. Secrets are never committed.
2. **Fidelity.** Files are the actual command + stdout/exit code; timestamps
   are captured at run time. No post-hoc embellishment.
3. **Status labels.** An evidence file's header states `STATUS: DONE` or
   `STATUS: PARTIAL` and, if partial, the exact blocker (e.g. missing live
   credentials of a human-owned step).

## Index

| File | Programme step | Status |
|---|---|---|
| `2026-08-23_vault_rotation_drill.log` | Secret rotation cadence (real Vault, G-04) | **DONE** (5/5 PASS: changed-secret pickup, version bump, value-redacted audit, rotate_all, fail-closed missing key) |
| `2026-08-23_transient_broker_error_drill.log` | Transient broker error (503/429) reconcile-survival drill | **DONE** (5/5 PASS: 503 fails closed not crash, 429 retries→clean reject, 400 fail-fast, reconcile recovers) |
| `2026-08-22_sigterm_startup_drain.log` | SIGTERM-under-load HA flake root-cause + close | **DONE** (VERDICT PASS: late-handler-install window found + fixed + regression test; 44/44 x10 under load) |
| `2026-08-22_rate_limiter_burst_drill.log` | Rate-limiter burst / load-shedding drill | **DONE** (13/13 PASS: broker-path + HTTP 429s + headers, breaker stays closed, traffic resumes) |
| `2026-08-22_postgres_backup_restore_drill.log` | Live Postgres backup→restore drill (post-migration) | **DONE** (VERDICT PASS, schema v9 round-trip intact; orphaned volume surfaced) |
| `2026-08-02_dry_run_paper_rehearsal.log` | Pilot dry-run rehearsal | **DONE** (real Alpaca paper account, workflow READY / exit 0) |
| `2026-08-02_backup_restore_drill.log` | Backup → restore drill | **DONE** (SHA-256 round-trip equal) |
| `2026-08-02_rollback_drill.log` | Deployment rollback drill | **DONE** (6→3→6, integrity ok) |
