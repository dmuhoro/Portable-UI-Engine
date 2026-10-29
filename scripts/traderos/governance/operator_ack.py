#!/usr/bin/env python3
"""G-07 operator acknowledgement: record the operator's written acceptance of
the live-run red-lines before any real capital moves.

The GO definition (LIVE_RUN_POLICY §8.5) requires the policy to be *reviewed
and acknowledged in writing by the operator; red-lines and kill authority
agreed*. A config flag is not proof of a human decision — this tool writes an
explicit, timestamped, HMAC-signed acknowledgment record under
``docs/evidence/operator/`` (or ``OPERATOR_ACK_DIR``) and the live gate refuses
to pass unless a valid acknowledgment for the committed policy digest exists.

Run:
    OPERATOR_NAME="Jane" OPERATOR_ROLE="on-call" \
    python3 scripts/governance/operator_ack.py ack --policy docs/engineering/LIVE_RUN_POLICY.md
    python3 scripts/governance/operator_ack.py verify --policy docs/engineering/LIVE_RUN_POLICY.md
    python3 scripts/governance/operator_ack.py status --policy docs/engineering/LIVE_RUN_POLICY.md
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

RED_LINES = [
    "any unplanned order -> stop and reconcile before re-arm",
    "kill-switch trip or daily-loss cap -> flatten, zero exposure, no auto re-arm",
    "data-gap breaker -> trading blocked while feed is absent/stale",
    "gross exposure breach -> new orders refused + alert",
    "supervision unclean-death -> do not resume until broker truth reconciled",
    "unreconciled startup -> order acceptance blocked (fail-closed)",
    "only an operator can re-arm, after clean reconciliation + fresh readiness pass",
]


def _ack_dir() -> Path:
    return Path(
        os.environ.get("OPERATOR_ACK_DIR", str(REPO_ROOT / "docs" / "evidence" / "operator"))
    )


def _key() -> bytes:
    key = os.environ.get("RELEASE_SIGNING_KEY", "")
    if not key:
        print("FATAL: RELEASE_SIGNING_KEY is not set", file=sys.stderr)
        raise SystemExit(1)
    return key.encode()


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ack_path(policy: Path) -> Path:
    return _ack_dir() / (policy.name + ".operator-ack.json")


def _record() -> dict:
    return {
        "schema_version": 1,
        "policy": "LIVE_RUN_POLICY.md",
        "operator_name": os.environ.get("OPERATOR_NAME", ""),
        "operator_role": os.environ.get("OPERATOR_ROLE", ""),
        "red_lines_acknowledged": RED_LINES,
        "acknowledged_at": datetime.now(UTC).isoformat(),
        "policy_sha256": "",
        "signature": "",
    }


def ack(policy: Path) -> int:
    if not policy.is_file():
        print(f"FATAL: policy not found: {policy}", file=sys.stderr)
        return 1
    name = os.environ.get("OPERATOR_NAME", "").strip()
    role = os.environ.get("OPERATOR_ROLE", "").strip()
    if not name or not role:
        print("FATAL: OPERATOR_NAME and OPERATOR_ROLE must be set", file=sys.stderr)
        return 1
    rec = _record()
    rec["operator_name"] = name
    rec["operator_role"] = role
    rec["policy_sha256"] = _digest(policy)
    body = json.dumps(
        {k: v for k, v in rec.items() if k != "signature"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    rec["signature"] = hmac.new(_key(), body, hashlib.sha256).hexdigest()
    out = _ack_path(policy)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=2) + "\n")
    print(f"ACK recorded: {out}")
    print(f"  operator={name} ({role}) policy_sha256={rec['policy_sha256'][:16]}...")
    print(f"  red-lines acknowledged: {len(RED_LINES)}")
    return 0


def verify(policy: Path) -> int:
    out = _ack_path(policy)
    if not out.is_file():
        print(f"FAIL: no operator acknowledgment for {policy.name}", file=sys.stderr)
        return 1
    rec = json.loads(out.read_text())
    signature = str(rec.get("signature", ""))
    expected_body = json.dumps(
        {k: v for k, v in rec.items() if k != "signature"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    expected_sig = hmac.new(_key(), expected_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        print("FAIL: acknowledgment signature invalid", file=sys.stderr)
        return 1
    if rec.get("policy_sha256") != _digest(policy):
        print("FAIL: acknowledgment was made against a different policy digest", file=sys.stderr)
        return 1
    if not rec.get("operator_name") or not rec.get("operator_role"):
        print("FAIL: acknowledgment missing operator identity", file=sys.stderr)
        return 1
    print(
        f"OK: {policy.name} operator acknowledgment valid "
        f"({rec.get('operator_name')} {rec.get('acknowledged_at')})"
    )
    return 0


def status(policy: Path) -> int:
    out = _ack_path(policy)
    if not out.is_file():
        print(f"STATUS: no operator acknowledgment recorded for {policy.name}")
        return 1
    rec = json.loads(out.read_text())
    print(f"STATUS: acknowledged by {rec.get('operator_name')} ({rec.get('operator_role')})")
    print(f"  at {rec.get('acknowledged_at')}")
    print(f"  policy_sha256={rec.get('policy_sha256')}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("ack", "verify", "status"):
        p = sub.add_parser(name)
        p.add_argument("--policy", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.cmd == "ack":
        return ack(args.policy)
    if args.cmd == "verify":
        return verify(args.policy)
    return status(args.policy)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
