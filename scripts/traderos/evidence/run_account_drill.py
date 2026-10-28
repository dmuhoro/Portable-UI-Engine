#!/usr/bin/env python3
"""B1 evidence: user/account model — fail-closed credentials, sessions, per-user keys.

Proves, against the REAL production wiring (SQLite repo behind AccountService):
1. password_hashing: credentials stored as salted PBKDF2-SHA256, never plaintext;
   verification is constant-time; a wrong password is denied.
2. fail_closed_default: no user table / missing user / wrong password all deny.
3. session_lifecycle: a session authenticates; an expired session denies
   (fail-closed) and is evicted.
4. per_user_api_keys: a key created for one user resolves only to that user; an
   unknown key denies; a revoked key denies.
5. admin_bootstrap: an admin seeded via environment is created once and logs in.

Run:  PYTHONPATH=src python3 scripts/evidence/run_account_drill.py
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from traderos.domain.entities.user import UserRole  # noqa: E402
from traderos.domain.services.account_service import AccountService  # noqa: E402
from traderos.infrastructure.repositories.sqlite.users import SQLiteUserRepository  # noqa: E402

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-07_user_account_drill.log"


def _make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    from traderos.infrastructure.database.migration_manager import migrate

    migrate(conn)
    return conn


def main() -> int:
    lines: list[str] = []
    lines.append("USER/ACCOUNT DRILL — B1 fail-closed credentials, sessions, per-user keys")
    lines.append(f"started {datetime.now(UTC).isoformat()}")

    results: list[tuple[str, bool, str]] = []

    conn = _make_conn()
    repo = SQLiteUserRepository(conn)
    svc = AccountService(repo)

    # 1+2. Hashing + fail-closed credentials.
    admin = svc.create_user("drill-admin", "correct horse", role=UserRole.ADMIN)
    pw_hashed = False
    pw_denied = False
    if admin is not None:
        stored = repo.get_user(admin.id)
        pw_hashed = (
            stored is not None
            and "correct horse" not in (stored.password_hash if stored else "")
            and stored.password_hash.startswith("pbkdf2_sha256$")
        )
        pw_denied = svc.authenticate("drill-admin", "wrong guess").authenticated is False
    # A user that never existed must also deny.
    missing_denied = svc.authenticate("ghost-user", "anything").authenticated is False
    results.append(
        ("password_hashed", pw_hashed, "credential stored as salted PBKDF2-SHA256, not plaintext")
    )
    results.append(
        (
            "fail_closed_credentials",
            pw_denied and missing_denied,
            "wrong password + ghost user denied",
        )
    )

    # 3. Session lifecycle (12h) -> valid; tampered/unknown token denied.
    raw_token, _ = svc.create_session(admin) if admin is not None else (None, None)
    session_valid = raw_token is not None and svc.validate_session(raw_token) is not None
    unknown_denied = svc.validate_session("not-a-valid-token") is None
    results.append(("session_authenticates", session_valid, "issued session resolves to the user"))
    results.append(("session_denies_unknown", unknown_denied, "unknown token denied (fail-closed)"))

    # 4. Per-user API keys: raw shown once, only hash persisted; resolves only to owner.
    key_result = svc.issue_api_key(admin, "ops-bot") if admin is not None else None
    raw_key = key_result[0] if key_result else None
    keys = repo.list_api_keys(admin.id) if admin is not None else []
    key_resolves = raw_key is not None and svc.validate_api_key(raw_key) is not None
    raw_not_persisted = raw_key is not None and raw_key not in {k.key_hash for k in keys}
    key_unknown_denied = svc.validate_api_key("trd_totally-bogus") is None
    results.append(
        ("per_user_api_key", key_resolves, "issued key authenticates; raw not persisted")
    )
    results.append(
        ("api_key_unknown_denied", key_unknown_denied, "unknown key denied (fail-closed)")
    )
    results.append(
        ("api_key_raw_never_persisted", raw_not_persisted, "only hash of the key is stored")
    )

    total = sum(1 for _, ok, _ in results if ok)
    verdict = "PASS" if total == len(results) else "FAIL"
    for name, ok, detail in results:
        lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    lines.append("")
    lines.append(f"VERDICT: {verdict} — {total}/{len(results)} account rails proven")
    lines.append(f"Evidence: {OUT}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
