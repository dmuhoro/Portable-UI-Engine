# Cold Incident Drill — TraderOS

## Purpose

Simulate a complete system outage from a clean slate and verify that TraderOS can be restored to a known-good state using only documented procedures and backup artifacts.

---

## Prerequisites

- Backup tarball from a prior session (`backups/*.sqlite.gz` or PostgreSQL dump)
- Access to the operations runbook (`docs/runbooks/OPERATIONS.md`)
- Clean environment with no prior state (empty `data/` directory)

---

## Drill Steps

### Phase 1 — Teardown (5 min)

1. Kill all running TraderOS processes
   ```bash
   pkill -f traderos
   ```
2. Wipe the working state
   ```bash
   rm -rf data/ backups/__tmp__
   ```
3. Confirm no database exists
   ```bash
   ls data/*.sqlite 2>/dev/null && echo "FAIL: residual state" || echo "OK: clean"
   ```

### Phase 2 — Restore (10 min)

1. Deploy the target version
   ```bash
   git checkout <target-tag>
   pip install -e .
   ```
2. Restore from backup per runbook
   ```bash
   traderos db restore <path-to-backup>
   ```
3. Verify audit chain integrity
   ```bash
   traderos audit verify   # or equivalent CLI
   ```

### Phase 3 — Startup (10 min)

1. Run preflight check
   ```bash
   traderos risk check
   ```
2. Confirm kill switch is reset
3. Start the trading engine
   ```bash
   traderos daemon start
   ```

### Phase 4 — Verification (10 min)

1. Verify broker reconciliation matches
   ```bash
   traderos risk reconcile status
   ```
2. Confirm trading cycles are executing
   ```bash
   tail -f data/logs/cycle.log
   ```
3. Run the full test suite
   ```bash
   make test-coverage
   ```

---

## Success Criteria

- All phases complete within 35 minutes
- Audit chain verification passes with zero breaks
- Preflight gate passes on first attempt
- Trading cycles resume without manual intervention
- `make test-coverage` reports 100% pass rate
