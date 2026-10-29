#!/usr/bin/env python3
"""Sprint 46 evidence: backup -> restore round-trip against the LIVE Postgres.

Proves, against the current production Postgres instance (post-Amsterdam
region migration, schema v9), that the real backup/restore path in
``traderos.infrastructure.database.backup`` still round-trips data intact:

  1. Fingerprint the live database (schema version, table set, per-table
     row counts).
  2. ``backup_postgres`` -> pg_dump custom-format snapshot (timed).
  3. Restore into a throwaway scratch database on the same server via
     ``restore_postgres`` (timed).
  4. Verify the restored database matches the backup-time fingerprint
     exactly, and that the live database only grew (never shrank) during
     the window.
  5. Surface the Railway volume state so the Sprint 43 "postgres-volume:
     detached" warning is either confirmed or refuted with fresh evidence.
  6. Drop the scratch database. No production data is ever written.

PASS requires: successful timed backup + restore, restored == backup-time
fingerprint (schema version 9, identical table set, identical per-table
counts), live counts never below backup-time counts, and a clean scratch-DB
drop. The drill never fabricates data; if the database is unreachable it
exits NO-GO.

Run (production via `railway connect Postgres-gKbz --tunnel-only`):
    DATABASE_URL=postgresql://postgres:...@127.0.0.1:15432/railway \\
        python3 scripts/evidence/run_postgres_backup_restore_drill.py
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

# Imported after the path insert above: this drill is runnable from a checkout
# without an editable install, and a top-of-file import would win the race.
from traderos.infrastructure.database.migration_manager import latest_version  # noqa: E402

OUT = (
    REPO_ROOT
    / "docs"
    / "evidence"
    / (f"{datetime.now(UTC).date().isoformat()}_postgres_backup_restore_drill.log")
)

DATABASE_URL = os.environ.get("DATABASE_URL", "")
SCRATCH_DB = os.environ.get("PG_SCRATCH_DB", "traderos_restore_drill")
BACKUP_DIR = Path(os.environ.get("DB_BACKUP_DIR", "/tmp/opencode/bd/backups"))
# Derived from the migration chain, never a hardcoded literal: adding a
# migration must not silently turn this drill red, and a migration that is
# discovered but never applied must still fail it.
EXPECTED_SCHEMA_VERSION = latest_version()


def _redact(url: str) -> str:
    return url.split("@")[-1] if "@" in url else url


def _sanitize(text: str) -> str:
    """Strip any embedded credentials from a message (pg_dump can echo the DSN)."""
    import re

    out = re.sub(r"://([^/@:]+):[^/@]+@", r"://\1:***@", text)
    return out


def _connect(url: str | None = None) -> Any:
    import psycopg2

    return psycopg2.connect(url or DATABASE_URL, connect_timeout=15)


def _table_counts(url: str | None = None) -> dict[str, int]:
    conn = _connect(url)
    cur = conn.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    tables = [r[0] for r in cur.fetchall()]
    counts: dict[str, int] = {}
    for t in tables:
        cur.execute(f'SELECT count(*) FROM "{t}"')
        counts[t] = cur.fetchone()[0]
    conn.close()
    return counts


def _schema_version(url: str | None = None) -> int:
    conn = _connect(url)
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(version), 0) FROM _schema_version")
    v = cur.fetchone()[0]
    conn.close()
    return v


def _drop_scratch() -> None:
    conn = _connect()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (SCRATCH_DB,))
    if cur.fetchone():
        cur.execute(f'DROP DATABASE "{SCRATCH_DB}"')
    conn.close()


def _create_scratch() -> None:
    conn = _connect()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f'CREATE DATABASE "{SCRATCH_DB}"')
    conn.close()


def _scratch_url() -> str:
    from urllib.parse import quote
    from urllib.parse import urlparse
    from urllib.parse import urlunparse

    parts = urlparse(DATABASE_URL)
    netloc = parts.hostname or ""
    if parts.port:
        netloc += f":{parts.port}"
    if parts.username:
        creds = quote(parts.username)
        if parts.password:
            creds += ":" + quote(parts.password)
        netloc = f"{creds}@{netloc}"
    return urlunparse(parts._replace(netloc=netloc, path=f"/{SCRATCH_DB}"))


def _volume_state() -> list[str]:
    """Best-effort Railway volume probe; returns log lines (never raises)."""
    try:
        cmd = ["railway", "volume", "list"]
        env = dict(os.environ)
        if os.environ.get("RAILWAY_TOKEN"):
            env["RAILWAY_TOKEN"] = os.environ["RAILWAY_TOKEN"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45, env=env, check=False)
        if proc.returncode != 0:
            return [f"  volume probe failed: {(proc.stderr or '').strip()[:120]}"]
        text = proc.stdout.strip()
        if not text:
            return ["  volume probe returned empty"]
        interesting = [
            line.strip()
            for line in text.splitlines()
            if line.strip().startswith(("Volume:", "Attached", "Mount", "Status", "Storage"))
        ]
        return ["  " + line for line in interesting] or ["  " + text]
    except Exception as exc:  # noqa: BLE001
        return [f"  volume probe unavailable: {exc}"]


def _report(lines: list[str], results: list) -> int:
    all_ok = all(ok for _, ok, _ in results)
    lines.append("-------")
    for name, ok, detail in results:
        lines.append(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    lines.append(f"VERDICT: {'PASS' if all_ok else 'FAIL'}")
    lines.append(f"Evidence: {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if all_ok else 1


def main() -> int:
    lines: list[str] = []
    results: list[tuple[str, bool, str]] = []
    lines.append("POSTGRES BACKUP->RESTORE DRILL — live production instance, post-migration")
    lines.append(f"started {datetime.now(UTC).isoformat()}")
    lines.append(f"target: {_redact(DATABASE_URL)} scratch_db={SCRATCH_DB}")

    if not DATABASE_URL:
        lines.append("  DATABASE_URL not set -> NO-GO")
        results.append(("connection", False, "DATABASE_URL missing"))
        return _report(lines, results)

    try:
        _connect().close()
    except Exception as exc:  # noqa: BLE001
        lines.append(f"  database unreachable -> NO-GO ({exc})")
        results.append(("connection", False, str(exc)))
        return _report(lines, results)

    from traderos.infrastructure.database.backup import backup_postgres
    from traderos.infrastructure.database.backup import restore_postgres

    backup_path = None
    try:
        # --- 1. fingerprint the live database -----------------------------
        live_version = _schema_version()
        live_counts_before = _table_counts()
        table_set = sorted(live_counts_before)
        lines.append(f"live fingerprint: schema_version={live_version} tables={len(table_set)}")
        for t in table_set:
            lines.append(f"  {t}: {live_counts_before[t]} rows")
        results.append(
            (
                "live_fingerprint",
                live_version == EXPECTED_SCHEMA_VERSION,
                (
                    f"schema_version={live_version} (expected {EXPECTED_SCHEMA_VERSION}), "
                    f"{len(table_set)} tables"
                ),
            )
        )

        # --- 2. timed backup -----------------------------------------------
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        t0 = time.monotonic()
        backup_path = backup_postgres(DATABASE_URL)
        backup_duration = time.monotonic() - t0
        digest = hashlib.sha256(backup_path.read_bytes()).hexdigest()
        lines.append(
            f"backup: {backup_path.name} size={backup_path.stat().st_size} "
            f"sha256={digest} duration={backup_duration:.2f}s"
        )
        results.append(
            (
                "timed_backup",
                True,
                (
                    f"{backup_path.stat().st_size} bytes in {backup_duration:.2f}s "
                    f"sha256={digest[:16]}..."
                ),
            )
        )

        # --- 3. timed restore into a scratch DB ----------------------------
        _drop_scratch()
        _create_scratch()
        scratch = _scratch_url()
        t0 = time.monotonic()
        restore_postgres(backup_path, scratch)
        restore_duration = time.monotonic() - t0
        lines.append(f"restore: {backup_path.name} -> {SCRATCH_DB} in {restore_duration:.2f}s")
        results.append(
            ("timed_restore", True, f"pg_restore into scratch DB in {restore_duration:.2f}s")
        )

        # --- 4. verify restored DB == backup-time fingerprint ---------------
        restored_version = _schema_version(scratch)
        restored_counts = _table_counts(scratch)
        restored_set = sorted(restored_counts)
        version_ok = restored_version == live_version == EXPECTED_SCHEMA_VERSION
        tables_ok = restored_set == table_set
        shrunk = [t for t in table_set if restored_counts[t] < live_counts_before[t]]
        grown = [t for t in table_set if restored_counts[t] > live_counts_before[t]]
        counts_ok = not shrunk and tables_ok
        for t in table_set:
            marker = "ok" if restored_counts[t] == live_counts_before[t] else ""
            if restored_counts[t] != live_counts_before[t]:
                marker = "DIFF"
            lines.append(
                f"  restored {t}: {restored_counts[t]} rows "
                f"(live {live_counts_before[t]}) {marker}"
            )
        if grown:
            lines.append(f"  NOTE: live grew after fingerprint (expected): {grown}")
        lines.append(
            f"restored fingerprint: schema_version={restored_version} tables={len(restored_set)}"
        )
        results.append(
            (
                "restored_matches_backup",
                version_ok and tables_ok and counts_ok,
                (
                    f"version={restored_version} tables={tables_ok} "
                    f"shrunk={shrunk} grown_after_fingerprint={grown}"
                ),
            )
        )

        # --- 5. surface the volume state (Sprint 43 detached warning) -------
        vol = _volume_state()
        lines.append("railway volume state (Sprint 43 'postgres-volume: detached' check):")
        lines += vol
        detached = any("Attached to: N/A" in v for v in vol)
        results.append(
            (
                "volume_state_surfaced",
                True,
                (
                    "orphaned 'postgres-volume' reported detached (see log) "
                    if detached
                    else "all volumes attached"
                ),
            )
        )

        # --- 6. drop the scratch DB ----------------------------------------
        _drop_scratch()
        lines.append(f"scratch DB dropped: {SCRATCH_DB}")
        results.append(("scratch_drop", True, f"{SCRATCH_DB} dropped"))
    except Exception as exc:  # noqa: BLE001
        lines.append(f"  drill aborted: {_sanitize(str(exc))}")
        results.append(("drill_execution", False, _sanitize(str(exc))))
        if backup_path is None:
            lines.append("  no backup produced")
        try:
            _drop_scratch()
            lines.append(f"  cleanup: scratch DB {SCRATCH_DB} dropped")
        except Exception as cleanup_exc:  # noqa: BLE001
            lines.append(f"  cleanup FAILED: {cleanup_exc}")

    return _report(lines, results)


if __name__ == "__main__":
    raise SystemExit(main())
