#!/usr/bin/env python3
"""G-07 evidence: governance gate drill — signing + operator ack + live gate.

Records standing evidence that the governance stack is mechanically enforced:
  1. the release artifact (LIVE_RUN_POLICY.md) can be signed + verified
  2. an operator acknowledgment of the red-lines can be recorded + verified
  3. the live gate FAILS CLOSED in live posture without the GO declaration,
     and PASSES only when every documented GO condition holds (env-only drill)

Run:  PYTHONPATH=src python3 scripts/evidence/run_governance_drill.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.governance.operator_ack import ack as operator_ack  # noqa: E402
from scripts.governance.operator_ack import verify as verify_ack  # noqa: E402
from scripts.governance.sign_release import sign as sign_artifact  # noqa: E402
from scripts.governance.sign_release import verify as verify_signature  # noqa: E402

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-04_sprint27_governance_drill.log"

DRILL_KEY = "governance-drill-key-not-a-secret"


def main() -> int:
    lines: list[str] = []
    lines.append("GOVERNANCE DRILL — G-07 signing + operator ack + live gate")
    lines.append(f"started {datetime.now(UTC).isoformat()}")
    lines.append(f"drill key: {DRILL_KEY} (in-process only, never persisted)")

    tmp = tempfile.mkdtemp()
    old_env = {
        k: os.environ.get(k)
        for k in (
            "RELEASE_SIGNING_KEY",
            "RELEASE_SIG_DIR",
            "OPERATOR_ACK_DIR",
            "OPERATOR_NAME",
            "OPERATOR_ROLE",
            "TRADING_MODE",
            "RISK_DAILY_LOSS_PCT",
            "RISK_MAX_GROSS_EXPOSURE",
            "RISK_MAX_POSITION_SIZE",
            "RISK_MAX_POSITIONS_TOTAL",
            "RISK_MAX_DATA_STALENESS_SECONDS",
            "RISK_ALLOWED_MARKETS",
            "RISK_REQUIRE_ALLOWLIST",
        )
    }
    for k in old_env:
        if k.startswith("RISK_"):
            os.environ.pop(k, None)
    os.environ["RELEASE_SIGNING_KEY"] = DRILL_KEY
    os.environ["RELEASE_SIG_DIR"] = str(Path(tmp) / "sigs")
    os.environ["OPERATOR_ACK_DIR"] = str(Path(tmp) / "acks")
    os.environ["OPERATOR_NAME"] = "Drill Operator"
    os.environ["OPERATOR_ROLE"] = "on-call"
    os.environ["TRADING_MODE"] = "paper"

    results: list[tuple[str, bool]] = []
    try:
        artifact = REPO_ROOT / "docs" / "engineering" / "LIVE_RUN_POLICY.md"
        results.append(("release_signing", sign_artifact(artifact, "RELEASE_SIGNING_KEY") == 0))
        results.append(("release_verify", verify_signature(artifact, "RELEASE_SIGNING_KEY") == 0))
        results.append(("operator_ack", operator_ack(artifact) == 0))
        results.append(("operator_ack_verify", verify_ack(artifact) == 0))

        os.environ["TRADING_MODE"] = "live"
        os.environ["GO_CONDITIONS_MET"] = "false"
        os.environ["LIVE_TRADING_CONFIRMED"] = "true"
        os.environ["ALPACA_API_KEY"] = "PK" + "GOVERNANCEDRILLKEY1234567890"
        os.environ["ALPACA_SECRET_KEY"] = "governancedrillsecret123456"

        # WP11: a live PASS now also requires explicit production risk rails —
        # the drill supplies them in a temp settings file (never the committed
        # one), so the gate is proven to enforce the full documented GO set.
        drill_settings = Path(tmp) / "settings.yaml"
        drill_settings.write_text(
            "risk:\n"
            "  daily_loss_pct: 0.02\n"
            "  max_gross_exposure: 1.0\n"
            "  max_position_size: 0.25\n"
            "  max_positions_total: 10\n"
            "  require_allowlist: true\n"
            "  allowed_markets:\n"
            "    - AAPL\n"
        )

        from scripts.governance.live_gate import main as gate

        blocked = gate(["--artifact", str(artifact), "--settings", str(drill_settings)]) == 1
        results.append(("live_gate_fails_closed_without_go", blocked))

        os.environ["GO_CONDITIONS_MET"] = "true"
        passed = gate(["--artifact", str(artifact), "--settings", str(drill_settings)]) == 0
        results.append(("live_gate_passes_with_go_and_ack", passed))
    finally:
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    ok = sum(1 for _, b in results if b)
    verdict = "PASS" if ok == len(results) else "FAIL"
    lines.append("")
    for name, passed in results:
        lines.append(f"[{'PASS' if passed else 'FAIL'}] {name}")
    lines.append("")
    lines.append(
        f"VERDICT: {verdict} — governance stack {ok}/{len(results)} enforced "
        "(signing, operator ack, fail-closed live gate)"
    )
    lines.append(f"Evidence: {OUT}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
