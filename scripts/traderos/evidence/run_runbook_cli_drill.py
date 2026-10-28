#!/usr/bin/env python3
"""Sprint 33 evidence: the disaster-recovery runbook commands actually execute.

Every documented ``python -m traderos <verb>`` command in
``runbooks/disaster_recovery.md`` is exercised as a REAL subprocess against the
module entrypoint (``src/traderos/__main__.py``), so a typo, a missing parser
branch, or a broken entrypoint fails this drill instead of the operator during
an outage. Backup/restore round-trips are proven against a scratch SQLite DB.

Proves:
  1. ``db backup`` writes a gzip backup
  2. ``db restore --backup <path>`` round-trips to the backed-up row
  3. ``db restore --latest`` round-trips from the newest backup
  4. ``db restore <path>`` (positional) round-trips
  5. ``db restore`` with no backup fails closed (rc=1, clear message)
  6. ``db list-backups`` lists the created backup
  7. ``db migrate`` + ``db check`` pass on the scratch DB
  8. ``audit query --filter`` returns the durable ``crash.recovery`` entry
  9. ``audit verify`` passes over the durable chain
 10. ``status`` reports mode / kill switch / order acceptance
 11. ``risk status --json`` exposes the ``orders_accepted`` token
 12. ``risk reconcile status`` reports the reconciliation gate
 13. ``run --mode paper`` starts the engine and stays up until signalled

Run:  PYTHONPATH=src python3 scripts/evidence/run_runbook_cli_drill.py
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-10_runbook_cli_drill.log"

_SEED_ROW = "original"


def _cli(workdir: Path, env: dict[str, str], *args: str, timeout: float = 60.0) -> tuple:
    proc = subprocess.run(
        [sys.executable, "-m", "traderos", *args],
        cwd=str(workdir),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _env(workdir: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    env["DB_PATH"] = str(workdir / "data" / "trader.db")
    env["DB_BACKUP_DIR"] = str(workdir / "backups")
    return env


def _seed_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("create table t (id integer primary key, v text)")
    conn.execute("insert into t (v) values (?)", (_SEED_ROW,))
    conn.commit()
    conn.close()


def _corrupt(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute("insert into t (v) values ('corrupted_after')")
    conn.commit()
    conn.close()


def _rows(path: Path) -> list[str]:
    conn = sqlite3.connect(str(path))
    rows = [r[0] for r in conn.execute("select v from t")]
    conn.close()
    return rows


def _backup_file(workdir: Path) -> Path:
    backups = (workdir / "backups").glob("*.sqlite.gz")
    files = sorted(backups, key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def main() -> int:
    lines = ["RUNBOOK-CLI DRILL — Sprint 33 disaster-recovery commands", "via `python -m traderos`"]
    lines.append(f"started {datetime.now(UTC).isoformat()}")

    results: list[tuple[str, bool, str]] = []

    def run_case(name: str, fn) -> None:
        ok, detail = fn()
        results.append((name, ok, detail))
        lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        env = _env(workdir)
        db = Path(env["DB_PATH"])
        os.environ["DB_PATH"] = str(db)
        os.environ["DB_BACKUP_DIR"] = str(workdir / "backups")
        _seed_db(db)

        # 1. db backup
        def case_backup():
            rc, out, _ = _cli(workdir, env, "db", "backup")
            has_backup = list((workdir / "backups").glob("*.sqlite.gz"))
            return (
                rc == 0 and "Backup created" in out and has_backup,
                "db backup writes a gzip backup",
            )

        # 2. db restore --backup <path>
        def case_restore_flag():
            _seed_db(db)
            rc, _, _ = _cli(workdir, env, "db", "backup")
            if rc != 0:
                return False, "backup failed"
            path = _backup_file(workdir)
            _corrupt(db)
            rc, out, _ = _cli(workdir, env, "db", "restore", "--backup", str(path))
            return (
                rc == 0 and "Database restored" in out and _rows(db) == [_SEED_ROW],
                "db restore --backup <path> round-trips to the backed-up row",
            )

        # 3. db restore --latest (newest of two backups wins)
        def case_restore_latest():
            _seed_db(db)
            rc, _, _ = _cli(workdir, env, "db", "backup")
            if rc != 0:
                return False, "backup #1 failed"
            time.sleep(1.1)
            conn = sqlite3.connect(str(db))
            conn.execute("insert into t (v) values ('second_state')")
            conn.commit()
            conn.close()
            rc, _, _ = _cli(workdir, env, "db", "backup")
            if rc != 0:
                return False, "backup #2 failed"
            _corrupt(db)
            rc, out, _ = _cli(workdir, env, "db", "restore", "--latest")
            return (
                rc == 0
                and "Database restored" in out
                and sorted(_rows(db)) == [_SEED_ROW, "second_state"],
                "db restore --latest round-trips from the newest backup",
            )

        # 4. db restore <path> (positional)
        def case_restore_positional():
            _seed_db(db)
            rc, _, _ = _cli(workdir, env, "db", "backup")
            if rc != 0:
                return False, "backup failed"
            path = _backup_file(workdir)
            _corrupt(db)
            rc, out, _ = _cli(workdir, env, "db", "restore", str(path))
            return (
                rc == 0 and "Database restored" in out and _rows(db) == [_SEED_ROW],
                "db restore <path> (positional) round-trips",
            )

        # 5. db restore with no backup fails closed
        def case_restore_noarg():
            rc, out, _ = _cli(workdir, env, "db", "restore")
            return (
                rc == 1 and "No backup specified" in out,
                "db restore with no backup fails closed (rc=1, clear message)",
            )

        # 6. db list-backups
        def case_list_backups():
            rc, out, _ = _cli(workdir, env, "db", "list-backups")
            return (
                rc == 0 and ".sqlite.gz" in out,
                "db list-backups lists the created backup",
            )

        # 7. db migrate + db check (full-recovery step 2/3)
        def case_migrate_check():
            rc1, _, _ = _cli(workdir, env, "db", "migrate")
            rc2, out2, _ = _cli(workdir, env, "db", "check")
            return (
                rc1 == 0 and rc2 == 0 and "Database OK" in out2,
                "db migrate + db check pass on the scratch DB",
            )

        # 8. audit query --filter reads the DURABLE trail (runbook scenario 2)
        def case_audit_query():
            from traderos.infrastructure.database.connection import get_connection
            from traderos.infrastructure.observability import SQLiteAuditService

            conn = get_connection()
            audit = SQLiteAuditService(conn)
            audit.record("crash.recovery", "system", "orchestrator", "post-crash reconciliation")
            audit.record("order.placed", "operator", "broker", "fill")
            conn.close()
            rc, out, _ = _cli(workdir, env, "audit", "query", "--filter", "action=crash.recovery")
            return (
                rc == 0 and "crash.recovery" in out and "order.placed" not in out,
                "audit query --filter returns the durable crash.recovery entry only",
            )

        # 9. audit verify over the durable chain
        def case_audit_verify():
            rc, out, _ = _cli(workdir, env, "audit", "verify")
            return rc == 0 and "PASS" in out, "audit verify passes over the durable chain"

        # 10. status
        def case_status():
            rc, out, _ = _cli(workdir, env, "status")
            return (
                rc == 0
                and "Mode: paper" in out
                and "Kill switch:" in out
                and "Order acceptance" in out,
                "status reports mode / kill switch / order acceptance",
            )

        # 11. risk status --json exposes orders_accepted
        def case_risk_status_json():
            rc, out, _ = _cli(workdir, env, "--json", "risk", "status")
            ok = rc == 0 and "orders_accepted" in out
            try:
                data = json.loads(out)
                ok = ok and "orders_accepted" in data and "trading_halted" in data
            except json.JSONDecodeError:
                ok = False
            return ok, "risk status --json exposes the orders_accepted token"

        # 12. risk reconcile status
        def case_reconcile_status():
            rc, out, _ = _cli(workdir, env, "risk", "reconcile", "status")
            return (
                "Reconciliation gate" in out,
                "risk reconcile status reports the reconciliation gate (fresh instance blocks, rc="
                + str(rc)
                + ")",
            )

        # 13. run --mode paper starts and stays up until signalled
        def case_run():
            try:
                _cli(workdir, env, "run", "--mode", "paper", "--interval", "1", timeout=5.0)
                return False, "engine exited unexpectedly during the window"
            except subprocess.TimeoutExpired:
                return True, "run --mode paper starts the engine and stays up until signalled"

        for name, fn in [
            ("db_backup_writes", case_backup),
            ("db_restore_backup_flag", case_restore_flag),
            ("db_restore_latest", case_restore_latest),
            ("db_restore_positional", case_restore_positional),
            ("db_restore_fails_closed", case_restore_noarg),
            ("db_list_backups", case_list_backups),
            ("db_migrate_and_check", case_migrate_check),
            ("audit_query_filter", case_audit_query),
            ("audit_verify", case_audit_verify),
            ("status_reports_state", case_status),
            ("risk_status_orders_accepted_token", case_risk_status_json),
            ("risk_reconcile_status", case_reconcile_status),
            ("run_starts_engine", case_run),
        ]:
            run_case(name, fn)

    passed = sum(1 for _, ok, _ in results if ok)
    verdict = "PASS" if passed == len(results) else "FAIL"
    lines.append("")
    lines.append(f"VERDICT: {verdict} — {passed}/{len(results)} runbook commands proven")
    lines.append(f"Evidence: {OUT}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
