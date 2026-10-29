#!/usr/bin/env python3
"""G-06 evidence: the credential-free drill suite as one CI job.

Each drill is an executable evidence script that proves a fail-closed rail
against the REAL wiring (real CycleExecutor / RiskService / BrokerAdapter,
real HTTP transports, real governance gate) and exits 0 only on a full PASS.
This runner executes the whole credential-free set as subprocesses, aggregates
the verdicts, writes a date-aware evidence log, and exits non-zero if ANY
drill fails — so a regression that silently weakens a rail stops the build.

Excluded from THIS job (documented, not silently dropped): drills that require
live account credentials, a managed Vault, a Postgres instance, or live
public-market network access. They are intentionally NOT part of the
deterministic CI drill set: the credential-gated ones are operator-run gates,
and the network-gated ones are already exercised by the test suite when the
external feed is reachable. See KEY_GATED.

Run:
    PYTHONPATH=src python3 scripts/evidence/run_ci_drills.py
    PYTHONPATH=src python3 scripts/evidence/run_ci_drills.py --only risk_rails oncall_transport
    PYTHONPATH=src python3 scripts/evidence/run_ci_drills.py --list
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = REPO_ROOT / "docs" / "evidence"
SCRIPTS_DIR = REPO_ROOT / "scripts" / "evidence"

# The credential-free drill set: (short name, script filename). Every script
# must exist on disk, must exit via raise SystemExit(main()), and must pass
# locally without keys, network, or external services.
DRILLS: tuple[tuple[str, str], ...] = (
    ("account", "run_account_drill.py"),
    ("auth_fail_closed", "run_auth_fail_closed_drill.py"),
    ("causal_replay", "run_causal_replay.py"),
    ("firm_ops", "run_firm_ops_drill.py"),
    ("governance", "run_governance_drill.py"),
    ("market_brain", "run_market_brain_drill.py"),
    ("multirestart_replay", "run_multirestart_replay.py"),
    ("oncall_transport", "run_oncall_drill.py"),
    ("operational_health", "run_operational_health_drill.py"),
    ("oracle_conformance", "run_oracle_conformance.py"),
    ("paper_soak", "run_paper_soak.py"),
    ("partial_fill_reconnect", "run_partial_fill_reconnect.py"),
    # Network-free by design: reuses the newest committed frozen snapshot
    # (docs/evidence/frozen/) with no external call; --refresh is the only
    # network path and is never invoked by the deterministic CI job.
    ("real_market_walk_forward", "run_real_market_walk_forward.py"),
    ("rate_limiter_burst", "run_rate_limiter_burst_drill.py"),
    ("risk_rails", "run_risk_rails_drill.py"),
    ("runbook_cli", "run_runbook_cli_drill.py"),
    ("secret_lifecycle", "run_secret_lifecycle_drill.py"),
    ("trigger_alerting", "run_trigger_alerting_drill.py"),
    ("transient_broker_error", "run_transient_broker_error_drill.py"),
    ("walk_forward_evidence", "run_walk_forward_evidence.py"),
)

# Drills that are intentionally OUT of this deterministic CI job: they need
# live account credentials, a managed secret store, a Postgres instance, or
# live public-market network access (real-time streams). Credential/instance-
# gated drills are operator-run gates; the real-time network-gated drill is
# exercised by the normal test suite when the external feed is reachable.
# Keeping this list explicit (and asserting every entry still exists) prevents
# a credential/network-needing drill from silently joining the deterministic
# CI drill set.
KEY_GATED: tuple[str, ...] = (
    "run_cost_adjusted_backtest.py",
    "run_deployment_drill.py",
    "run_postgres_backup_restore_drill.py",
    "run_postgres_parity_drill.py",
    "run_real_binance_stream_drill.py",
    "run_real_paper_soak.py",
    "run_unattended_paper_soak.py",
    "run_vault_rotation_drill.py",
    "run_vault_secret_manager_drill.py",
)

DEFAULT_TIMEOUT_SECONDS = 600.0


@dataclass(frozen=True)
class DrillResult:
    name: str
    ok: bool
    detail: str


def _evidence_path() -> Path:
    date = datetime.now(UTC).date().isoformat()
    return EVIDENCE_DIR / f"{date}_ci_drills.log"


OUT = _evidence_path()


def run_drill(
    name: str,
    *,
    python: str | None = None,
    env: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> DrillResult:
    """Run one drill as a subprocess; FAIL if it times out, crashes, or exits 1.

    PYTHONPATH is set to include the repo's src/ and tests/ so the drills'
    self-bootstrap sys.path insertion is always satisfied (a couple of drills
    import the frozen backtest oracle from tests/).
    """
    script = SCRIPTS_DIR / dict(DRILLS)[name]
    run_env = dict(os.environ)
    if env:
        run_env.update(env)
    pythonpath = os.pathsep.join([str(REPO_ROOT / "src"), str(REPO_ROOT / "tests")])
    if run_env.get("PYTHONPATH"):
        pythonpath = f"{pythonpath}{os.pathsep}{run_env['PYTHONPATH']}"
    run_env["PYTHONPATH"] = pythonpath

    try:
        proc = subprocess.run(
            [python or sys.executable, str(script)],
            cwd=REPO_ROOT,
            env=run_env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return DrillResult(name, False, f"TIMEOUT after {timeout:.0f}s")
    detail = (proc.stdout or "").strip().splitlines()
    summary = detail[-1] if detail else ""
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()
        reason = summary or (tail[-1] if tail else f"exit {proc.returncode}")
        return DrillResult(name, False, reason)
    return DrillResult(name, True, summary)


def run_all(
    names: tuple[str, ...],
    *,
    python: str | None = None,
    env: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[DrillResult]:
    return [run_drill(n, python=python, env=env, timeout=timeout) for n in names]


def aggregate(results: list[DrillResult]) -> int:
    """0 when every drill passed, 1 otherwise — the CI job's exit code."""
    return 0 if results and all(r.ok for r in results) else 1


def write_evidence_log(results: list[DrillResult], out: Path = OUT) -> None:
    lines = [
        "CI DRILL SUITE — G-06 credential-free evidence set",
        f"started {datetime.now(UTC).isoformat()}",
        f"drills {len(results)}",
        "",
    ]
    for r in results:
        lines.append(f"[{'PASS' if r.ok else 'FAIL'}] {r.name}: {r.detail}")
    lines.append("")
    verdict = "PASS" if aggregate(results) == 0 else "FAIL"
    green = sum(1 for r in results if r.ok)
    lines.append(f"VERDICT: {verdict} — {green}/{len(results)} drills green")
    lines.append(f"Evidence: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the credential-free CI drill set.")
    parser.add_argument("--only", nargs="*", default=[], help="Run only these drills by name.")
    parser.add_argument("--list", action="store_true", help="Print the inventory and exit.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument(
        "--no-evidence", action="store_true", help="Skip the aggregate evidence log."
    )
    args = parser.parse_args(argv)

    names = [name for name, _ in DRILLS]
    if args.list:
        for name, script in DRILLS:
            print(f"{name}: {script}")
        excluded = len(KEY_GATED)
        print(f"\n{len(DRILLS)} credential-free drills; {excluded} key-gated drills excluded.")
        return 0

    if args.only:
        available = {name for name, _ in DRILLS}
        unknown = [n for n in args.only if n not in available]
        if unknown:
            print(f"unknown drill name(s): {', '.join(unknown)}", file=sys.stderr)
            return 2
        names = args.only

    results = run_all(tuple(names), timeout=args.timeout)
    for r in results:
        print(f"[{'PASS' if r.ok else 'FAIL'}] {r.name}: {r.detail}")
    passed = sum(1 for r in results if r.ok)
    print(f"\nVERDICT: {'PASS' if aggregate(results) == 0 else 'FAIL'} — {passed}/{len(results)}")
    if not args.no_evidence:
        write_evidence_log(results)
        print(f"Evidence: {OUT}")
    return aggregate(results)


if __name__ == "__main__":
    raise SystemExit(main())
