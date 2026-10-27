#!/usr/bin/env python3
"""G-07 live gate (CI): block a ``live`` posture unless the documented
GO conditions hold. Fail-closed — any missing check exits non-zero.

Checks (when TRADING_MODE=live):
  1. Secrets conformance: no tracked file contains an Alpaca key literal.
  2. Config validation: LIVE requires ALPACA_API_KEY / ALPACA_SECRET_KEY env.
  3. Live confirmation: LIVE_TRADING_CONFIRMED=true.
  4. Allowlist: risk.require_allowlist=true requires a non-empty
     risk.allowed_markets list.
  5. Production risk rails (WP11): every numeric rail (daily-loss %,
     gross-exposure cap, position-size cap, max positions) explicitly
     configured and within sane bounds, with a mandatory non-empty allowlist.
  6. Release signing: the artifact (default docs/engineering/LIVE_RUN_POLICY.md)
     must carry a valid signature.
  7. GO declaration: GO_CONDITIONS_MET=true, set only by the documented GO
     review (never by code).

Run:  python3 scripts/governance/live_gate.py [--artifact <path>] [--key-var NAME]
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

import yaml  # noqa: E402

from scripts.governance.sign_release import verify as verify_signature  # noqa: E402

_API_KEY_PATTERN = re.compile(r"\bPK[0-9A-Z]{20,}\b")
_TRACKED = {".py", ".yaml", ".yml", ".json", ".toml", ".sh", ".md"}


def _fail(check: str, reason: str) -> None:
    print(f"[FAIL] {check}: {reason}")


def _pass(check: str) -> None:
    print(f"[PASS] {check}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact",
        type=Path,
        default=REPO_ROOT / "docs" / "engineering" / "LIVE_RUN_POLICY.md",
    )
    parser.add_argument("--settings", type=Path, default=REPO_ROOT / "configs" / "settings.yaml")
    parser.add_argument("--key-var", default="RELEASE_SIGNING_KEY")
    args = parser.parse_args(argv)

    mode = os.environ.get("TRADING_MODE", "paper").lower()
    if mode != "live":
        print(f"[PASS] TRADING_MODE={mode} — live gate not required (fail-closed only in live)")
        return 0

    failures = 0

    def check(name: str, ok: bool, reason: str) -> None:
        nonlocal failures
        if ok:
            _pass(name)
        else:
            _fail(name, reason)
            failures += 1

    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True, cwd=REPO_ROOT
    ).stdout.splitlines()
    offenders = [
        rel
        for rel in tracked
        if any(rel.endswith(ext) for ext in _TRACKED)
        and _API_KEY_PATTERN.search((REPO_ROOT / rel).read_text(encoding="utf-8", errors="ignore"))
    ]
    check("secrets conformance", not offenders, f"key literals in tracked files: {offenders}")

    api_key = os.environ.get("ALPACA_API_KEY", "")
    secret_key = os.environ.get("ALPACA_SECRET_KEY", "")
    check(
        "live credentials present",
        bool(api_key and secret_key),
        "ALPACA_API_KEY/ALPACA_SECRET_KEY unset",
    )

    check(
        "live confirmation",
        os.environ.get("LIVE_TRADING_CONFIRMED", "").lower() == "true",
        "LIVE_TRADING_CONFIRMED != true",
    )

    settings = {}
    yaml_path = args.settings
    if yaml_path.exists():
        settings = yaml.safe_load(yaml_path.read_text()) or {}
    require_allowlist = bool(settings.get("risk", {}).get("require_allowlist", False))
    allowed = settings.get("risk", {}).get("allowed_markets", [])
    check(
        "allowlist gate",
        not require_allowlist or bool(allowed),
        "risk.require_allowlist=true but risk.allowed_markets empty",
    )

    from traderos.application.risk_config import validate_production_risk_settings

    rail_problems = validate_production_risk_settings(settings.get("risk", {}))
    check(
        "production risk rails configured (WP11)",
        not rail_problems,
        "; ".join(rail_problems) or "risk rails invalid",
    )

    check(
        "signed release artifact",
        verify_signature(args.artifact, args.key_var) == 0,
        "artifact not signed or invalid",
    )

    from scripts.governance.operator_ack import verify as verify_ack

    check(
        "operator acknowledgment of red-lines",
        verify_ack(args.artifact) == 0,
        "no valid operator acknowledgment for the policy",
    )

    check(
        "GO declared by documented review",
        os.environ.get("GO_CONDITIONS_MET", "").lower() == "true",
        "GO_CONDITIONS_MET != true",
    )

    if failures:
        print(f"\nLIVE GATE: BLOCKED ({failures} failing checks) — fail-closed")
        return 1
    print("\nLIVE GATE: PASS — all documented GO conditions hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
