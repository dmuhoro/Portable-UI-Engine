# Deployment Rollback Drill — TraderOS

## Purpose

Validate that a faulty deployment can be detected and rolled back within the incident-response SLO (15 min for SEV-1) with zero data loss.

---

## Drill Scenario

Version `v2` is deployed. After 2 trading cycles, a spike in `circuit_breaker.tripped` is detected. The on-call engineer determines `v2` introduced a faulty kill-switch integration and initiates rollback to `v1`.

---

## Rollback Steps

### Phase 1 — Contain (3 min)

1. Trip the kill switch manually (if not already)
   ```bash
   traderos risk kill
   ```
2. Verify no new orders being accepted
   ```bash
   traderos risk status | grep "orders_accepted"
   ```
3. Snapshot current database and logs
   ```bash
   cp data/traderos.sqlite data/traderos_pre_rollback.sqlite
   ```

### Phase 2 — Rollback Code (5 min)

```bash
# Record the faulty version
git log --oneline -1 > data/rolled_back_from.txt

# Rollback to previous release tag
git checkout v1

# Reinstall
pip install -e .
```

### Phase 3 — Verify Rollback (5 min)

1. Run preflight gate
   ```bash
   traderos risk check
   ```
2. Confirm kill switch is reset and `can_trade()` returns true
3. Verify audit chain passes
4. Reconcile broker state with persisted state

### Phase 4 — Resume (5 min)

1. Restart the daemon
   ```bash
   traderos daemon start
   ```
2. Monitor first 3 cycles for anomalies
   ```bash
   traderos metrics watch --cycles 3
   ```

---

## Success Criteria

- Rollback complete within 15 minutes (SEV-1 SLO)
- Zero data loss — no trades or audit entries missing
- Preflight gate passes on first attempt
- No manual database patching required
