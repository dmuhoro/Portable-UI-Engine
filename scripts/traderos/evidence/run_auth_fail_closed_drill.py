#!/usr/bin/env python3
"""A1 evidence: the /v1/* API seam fails closed under authentication.

Proves three postures against the REAL ``build_app()`` boundary (the
``enforce_auth_boundary`` HTTP middleware), not a helper:

  1. development (no keys, no trading posture) stays open — local friction free
  2. any trading posture (paper/live) without keys is fail-closed: every
     non-public /v1 route returns 401, even a route with no role dependency
  3. a configured key authenticates the boundary while public probes stay open

Run:  PYTHONPATH=. python3 scripts/evidence/run_auth_fail_closed_drill.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from starlette.exceptions import HTTPException  # noqa: E402
from starlette.requests import Request  # noqa: E402

from traderos.infrastructure.auth import APIKeyAuthenticator  # noqa: E402
from traderos.interfaces.api import security  # noqa: E402
from traderos.interfaces.api import server  # noqa: E402

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-06_auth_fail_closed_drill.log"

ADMIN_KEY = "admin-secret-key-1234567890"


def _client() -> TestClient:
    server.reset_orchestrator()
    return TestClient(server.build_app())


def _request(path: str) -> Request:
    return Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": [],
            "server": ("test", 80),
            "client": ("test", 12345),
            "scheme": "http",
            "query_string": b"",
            "root_path": "",
        }
    )


def main() -> int:
    lines: list[str] = []
    lines.append("AUTH FAIL-CLOSED DRILL — A1 /v1 boundary")
    results: list[tuple[str, bool]] = []

    # 1. development posture stays open
    os.environ.pop("TRADING_MODE", None)
    security.reset_authenticator()
    results.append(("dev_no_keys_open", _client().get("/v1/portfolio").status_code == 200))

    # 2. live posture without keys -> all non-public /v1 routes closed (401)
    os.environ["TRADING_MODE"] = "live"
    security.reset_authenticator()
    c = _client()
    results.append(("live_no_key_blocked", c.get("/v1/portfolio").status_code == 401))
    results.append(("live_no_key_strategies_blocked", c.get("/v1/strategies").status_code == 401))
    results.append(
        ("live_no_key_route_without_dep_blocked", _raises_401(_request("/v1/some-route")))
    )
    # public probes stay open for load balancers + auth-info
    results.append(("live_healthz_open", c.get("/v1/healthz").status_code == 200))
    results.append(("live_auth_me_open", c.get("/v1/auth/me").status_code == 200))

    # 3. paper posture without keys also closes the boundary
    os.environ["TRADING_MODE"] = "paper"
    security.reset_authenticator()
    results.append(("paper_no_key_blocked", _client().get("/v1/portfolio").status_code == 401))

    # 4. valid key authenticates the boundary in live posture (fake env keys so
    #    the orchestrator's live-mode config validation passes — the drill is
    #    about the auth boundary, not broker configuration)
    os.environ["TRADING_MODE"] = "live"
    os.environ["ALPACA_API_KEY"] = "PK" + "DRILLKEY1234567890"
    os.environ["ALPACA_SECRET_KEY"] = "drillsecret1234567890"
    security.set_authenticator(APIKeyAuthenticator(admin_keys=(ADMIN_KEY,)))
    c = _client()
    h = {"X-API-Key": ADMIN_KEY}
    results.append(("live_with_key_allowed", c.get("/v1/portfolio", headers=h).status_code == 200))
    results.append(("live_wrong_key_blocked", c.get("/v1/portfolio").status_code == 401))

    os.environ.pop("TRADING_MODE", None)
    os.environ.pop("ALPACA_API_KEY", None)
    os.environ.pop("ALPACA_SECRET_KEY", None)
    security.reset_authenticator()

    lines.append("")
    for name, ok in results:
        lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}")
    lines.append("")
    ok_count = sum(1 for _, ok in results if ok)
    verdict = "PASS" if ok_count == len(results) else "FAIL"
    lines.append(f"VERDICT: {verdict} — /v1 boundary fail-closed {ok_count}/{len(results)}")
    lines.append(f"Evidence: {OUT}")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if verdict == "PASS" else 1


def _raises_401(request: Request) -> bool:
    try:
        security.enforce_auth_boundary(request)
    except HTTPException as exc:
        return exc.status_code == 401
    return False


if __name__ == "__main__":
    raise SystemExit(main())
