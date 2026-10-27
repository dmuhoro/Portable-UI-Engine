# Sprint 48 — Launch-readiness: automatic backups, GO-gated readiness, release candidate

**Period:** 2026-08-23
**Objective:** While the G-02 soak window finishes (~2026-08-25T16:48Z), close
the last software gaps so that when the soak closes, the operator's GO review
is a formality — the product is launch-ready.

---

## L1 — Launch-readiness audit (DONE)

- Soak: EU West, batches 001–018 PASS, ~55h left at audit time.
- Found the remaining software gaps (not operator-run): nothing *scheduled*
  backups despite `pg_dump` now being in the image; the readiness gate did not
  verify the G-02/G-03 GO conditions; version still the Sprint-40 cut.

## L2 — Automatic backup scheduler (DONE)

- New `BackupScheduler` (`src/traderos/infrastructure/backup_scheduler.py`),
  mirroring the `ProbeScheduler` thread-loop pattern:
  - Runs the real `create_backup()` (SQLite or Postgres via `DATABASE_URL`)
    every `DB_BACKUP_INTERVAL_SECONDS` (default 3600 = hourly).
  - Fail-closed: every failure is recorded on the instance (`last_error`),
    delivered to `on_failure` (wired to CRITICAL notification), and counted in
    metrics (`backup.scheduled.failed`). Never silent.
  - Wired into `TradingOrchestrator.start/stop/run_forever` alongside the
    probe scheduler; stats surfaced in `get_status()["backups"]`.
  - Factory constructs it with the real `create_backup` + notification/metrics
    wiring; env-gated so local/CI does not back up unintentionally.
- CLI: `traderos db backup-scheduler` reports the scheduler stats.
- README "Key environment variables" documents `DB_BACKUP_INTERVAL_SECONDS` /
  `DB_BACKUP_DIR` / `DB_MAX_BACKUPS` (`.env.example` is gitignored and would
  trip the A4 no-secrets gate, so the reference lives in README).
- Tests: 15 (scheduler behaviors, metrics, real-path, wiring, CLI).

## L3 — GO-gated pilot readiness (DONE)

- `LiveReadinessService.check()` now also verifies the launch-critical GO
  conditions that `pilot readiness --mode live` must reflect:
  - **`allowlist_configured`** (G-03): when `require_allowlist` is set, a
    non-empty `allowed_markets` is required; empty → NOT READY.
  - **`broker_reconcile_clean`** (G-02): order acceptance is blocked until
    broker-state reconciliation completes; a dirty or unqueryable reconcile →
    NOT READY (fail closed).
- Factory passes `risk_service.allowed_markets`, `risk_rails.require_allowlist`,
  and `broker_reconciliation` to the service.
- Tests: 7 new readiness cases.

## L4 — Launch release candidate v1.3.0 (DONE)

- Version bumped 1.2.0 → **1.3.0** across `pyproject.toml`,
  `configs/settings.yaml`, `configs/settings.production.example.yaml`;
  CI version-check gate satisfied.
- `docs/releases/RELEASE_1.3.0_NOTES.md` — launch-candidate release notes.
- `docs/evidence/releases/RELEASE_1.3.0_manifest.json` + `.sig` — signed
  release artifact (committed with the deterministic paper key; the operator
  re-signs with `RELEASE_SIGNING_KEY` for GO, which is the documented step).
- CHANGELOG gains the `## [1.3.0]` release block.

## L5 — Documentation coherence (DONE)

- README: release row → v1.3.0; Backups row → automatic scheduler; risk-rails
  section → transient-broker fail-closed + GO-gated readiness.
- `.env.example` → backup knobs → README "Key environment variables".
- `GAP_READINESS.md` G-04 row → rotation mechanism proven (Sprint 47 already
  did this); Sprint 48 honesty note added.

## Verification

| Check | Result |
|---|---|
| Full suite (`make test`) | **2337 passed / 1 skipped / 100.00% coverage** |
| ruff / black / isort / pyright | clean |
| CI drill set | **20/20 PASS** |
| `BackupScheduler` tests | 15 passed |
| `LiveReadinessService` tests | 21 passed (7 new) |
| CLI db-handler tests | 59 passed (3 new) |
| Orchestrator tests | 16 passed (extended) |
| Version gate | pyproject == settings.yaml == 1.3.0 |

## Honest residuals

- The G-02 soak window itself, managed Vault/KMS rotation, live
  PagerDuty/Slack delivery, orphaned-volume deletion, and the written GO
  review remain **operator-run** (documented in the runbooks + GAP_READINESS).
- The release artifact is signed with the paper key; GO requires re-signing
  with the real `RELEASE_SIGNING_KEY` (documented step).
