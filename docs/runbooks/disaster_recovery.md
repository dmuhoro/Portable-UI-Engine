# Disaster Recovery Runbook

## Overview

This runbook describes procedures for recovering the TraderOS platform from various failure scenarios.

## Supported Backends

- **SQLite** (development, single-user)
- **PostgreSQL** (production, multi-user via Railway)

## Prerequisites

- PostgreSQL client tools (`pg_dump`, `pg_restore`) for Postgres recovery
- Access to backup storage (default: `./backups/`)
- Environment variables configured (or `.env` file)

## Recovery Scenarios

### 1. Database Corruption

**Symptoms:** Application crashes with `DatabaseError`, queries fail, checksum errors.

**SQLite:**
```bash
# Restore from latest backup
python -m traderos db restore --backup backups/sqlite_latest.sqlite.gz

# Verify integrity
python -m traderos db check
```

**PostgreSQL:**
```bash
# List available backups
python -m traderos db list-backups

# Restore from specific backup
python -m traderos db restore --backup backups/postgres_20260101_120000.dump
```

### 2. Application Crash During Trading

**Symptoms:** Process terminated unexpectedly, open orders may be in flight.

**Automatic Recovery:**
1. On restart, `DaemonController.recover_from_crash()` runs automatically
2. `OrderReconciliationService.reconcile_orders()` matches local trade state against broker
3. Open orders are cancelled or filled based on broker state
4. Positions are reconciled

**Manual Verification:**
```bash
# Check crash recovery status
curl http://localhost:8000/v1/orchestrator/status | jq .crash_recovered

# Review audit log for crash events
python -m traderos audit query --filter "action=crash.recovery"
```

### 3. Kill Switch Engaged

**Symptoms:** Trading stopped, `can_trade()` returns false, circuit breaker open.

**Automatic:**
- Circuit auto-resets after cooldown period (default: 300s)
- Daily loss limit resets at UTC midnight

**Manual Override:**
```bash
# Reset kill switch
python -m traderos risk reset

# Check kill switch status
curl http://localhost:8000/v1/risk/kill-switch
```

### 4. Broker Connection Failure

**Symptoms:** Orders not executing, reconciliation detects orphaned orders.

**Procedure:**
1. Verify broker API credentials
2. Check broker status page
3. If broker-side orders exist but local state is lost:
   - Reconciliation will detect `orphaned_broker` orders
   - Manual intervention required to reconcile positions

### 5. Full System Recovery

**Steps:**
```bash
# 1. Restore database from latest backup
python -m traderos db restore --latest

# 2. Run pending migrations
python -m traderos db migrate

# 3. Verify data integrity
python -m traderos db check

# 4. Start application
python -m traderos run --mode live

# 5. Verify crash recovery completed
python -m traderos status
```

## Backup Rotation

- SQLite backups: gzip-compressed, kept for 30 days (configurable via `DB_MAX_BACKUPS`)
- Postgres backups: custom format dumps via `pg_dump -Fc`, kept for 30 days
- Backups stored in `./backups/` (configurable via `DB_BACKUP_DIR`)

## Testing Recovery

Run the recovery test suite:
```bash
python -m pytest tests/test_backup.py -v
```
