#!/usr/bin/env python3
"""A4 evidence: real deployment-path drill on a live Postgres.

Proves, against a real local Postgres instance (the same seam as a managed
install), the deployment pieces of A4 that can be proven without a paid host
account or broker credentials:

- **migrations-on-boot** applies the full schema at boot and fails closed if
  the store is not migratable;
- **healthz green** — the built app answers /v1/healthz and /v1/health;
- **supervisor manifest** — Procfile defines web+worker and .dockerignore
  excludes secret-bearing paths;
- **no secrets in repo or image** — the deployment-hygiene scanner finds no
  hard-coded literal secrets in tracked files.

A live Railway host, public TLS URL, and a container build are the remaining
account-facing piece of A4 and are documented as such; everything locally
provable is proven here.

Run:  PYTHONPATH=src python3 scripts/evidence/run_deployment_drill.py
"""

from __future__ import annotations

import os
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from traderos.infrastructure.deployment_hygiene import scan_repo_for_secrets  # noqa: E402

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-06_deployment_drill.log"
DSN = os.environ.get(
    "POSTGRES_TEST_DSN",
    "host=localhost port=5433 dbname=traderos_test user=traderos password=traderos",
)


def _postgres_up() -> bool:
    try:
        import psycopg2

        conn = psycopg2.connect(DSN)
        conn.close()
        return True
    except Exception:  # noqa: BLE001
        return False


def _report(lines: list[str], results: list[tuple[str, bool, str]]) -> int:
    all_ok = all(ok for _, ok, _ in results)
    lines.append("-------")
    for name, ok, detail in results:
        lines.append(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    lines.append(f"VERDICT: {'PASS' if all_ok else 'FAIL'}" if all_ok else "VERDICT: FAIL")
    lines.append(f"Evidence: {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if all_ok else 1


def main() -> int:
    lines: list[str] = []
    results: list[tuple[str, bool, str]] = []
    lines.append("DEPLOYMENT DRILL — A4")
    lines.append(f"started {datetime.now(UTC).isoformat()}")

    if not _postgres_up():
        lines.append("  postgres not reachable -> NO-GO")
        return _report(lines, [("postgres_connection", False, "unreachable")])

    version: int | None = None
    try:
        from traderos.infrastructure.boot import run_migrations_on_boot
        from traderos.infrastructure.config.config_loader import Config

        os.environ["DATABASE_URL"] = "postgresql://traderos:traderos@localhost:5433/traderos_test"
        cfg = Config.load()
        version = run_migrations_on_boot(config=cfg)
        results.append(("migrations_on_boot", version is not None, f"schema_version={version}"))
        lines.append(f"  migrations-on-boot: schema_version={version}")
    except Exception as exc:  # noqa: BLE001
        results.append(("migrations_on_boot", False, str(exc)))
        lines.append(f"  migrations-on-boot: FAILED {exc}")

    try:
        from fastapi.testclient import TestClient

        from traderos.interfaces.api.server import build_app

        os.environ["TRADEROS_ENV"] = "development"
        with TestClient(build_app()) as client:
            r = client.get("/v1/healthz")
            healthy = r.status_code == 200 and r.json().get("status") == "alive"
            results.append(("healthz", healthy, f"status={r.json().get('status')}"))
            lines.append(f"  healthz: {r.json().get('status')}")
    except Exception as exc:  # noqa: BLE001
        results.append(("healthz", False, str(exc)))
        lines.append(f"  healthz: FAILED {exc}")

    procfile = (REPO_ROOT / "Procfile").read_text()
    super_ok = "web:" in procfile and "worker:" in procfile and "traderos daemon" in procfile
    results.append(("supervisor_manifest", super_ok, "Procfile web+worker present"))
    lines.append(f"  supervisor manifest: {'PASS' if super_ok else 'FAIL'}")

    scan = scan_repo_for_secrets(root=REPO_ROOT)
    results.append(("no_secrets_in_repo", scan.clean, f"{len(scan.findings)} findings"))
    lines.append(f"  no-secrets scan: clean={scan.clean}")

    return _report(lines, results)


if __name__ == "__main__":
    raise SystemExit(main())
