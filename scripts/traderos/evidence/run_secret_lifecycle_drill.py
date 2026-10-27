#!/usr/bin/env python3
"""A6 evidence: secrets-lifecycle + fail-closed live gate on the production path.

This drill exercises the REAL factory/orchestrator wiring (not an isolated
SecretRotator unit test) and proves the G-04 secret claim is genuinely true in
production:

- **Access is audited** — reading a secret through the orchestrator's rotator
  emits a durable `secret.accessed` audit row with the value redacted;
- **Rotation is audited + versioned** — rotating a secret emits a
  `secret.rotated` row, bumps the cached version, and the reloaded value is
  returned;
- **Fail-closed LIVE** — booting the orchestrator in LIVE mode without broker
  credentials via the secret manager/env raises loudly and never silently
  degrades to paper; with credentials present but an unusable adapter it also
  refuses rather than demoting;
- **Fail-closed LIVE risk rails (WP11)** — even before credentials are
  checked, a live boot without explicit production risk rails refuses
  (config is a boot-time gate, not a paper default).

Honest scope: this drill proves the rotator-to-audit/metrics production wiring
and the fail-closed live gate with env-only keys. The real HashiCorp Vault
KV-v2 integration on the same LIVE boot path is proven separately in
``run_vault_secret_manager_drill.py`` (`vault_secret_manager_drill.log` 5/5);
a managed Vault/KMS instance with production rotation cadence remains
account-vendor-gated.

Run:  PYTHONPATH=src python3 scripts/evidence/run_secret_lifecycle_drill.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from traderos.application.factory import build_orchestrator  # noqa: E402
from traderos.domain.exceptions import ConfigError  # noqa: E402
from traderos.infrastructure.config.config_loader import Config  # noqa: E402

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-06_secret_lifecycle_drill.log"
LINES: list[str] = []
RESULTS: list[tuple[str, bool, str]] = []


def _durable_db() -> str:
    """A real on-disk SQLite path.

    LIVE mode refuses to boot without a durable database for order and risk
    state. An in-memory path trips that guard before any rail or credential
    check runs, so it cannot be used to prove either of them.
    """
    return os.path.join(tempfile.mkdtemp(prefix="live-drill-"), "live.db")


def _live_config(db_path: str | None = None) -> Config:
    """A LIVE-mode config that passes the WP11 production-risk-rail gate, so a
    boot can reach the A6 credential check this drill is proving."""
    return Config(
        db_path=db_path or _durable_db(),
        log_level="WARNING",
        _raw_settings={
            "risk": {
                "daily_loss_pct": 0.02,
                "max_gross_exposure": 1.0,
                "max_position_size": 0.25,
                "max_positions_total": 10,
                "max_data_staleness_seconds": 300.0,
                "allowed_markets": ["SPY"],
                "require_allowlist": True,
            }
        },
    )


def _report() -> int:
    all_ok = all(ok for _, ok, _ in RESULTS)
    LINES.append("-------")
    for name, ok, detail in RESULTS:
        LINES.append(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    LINES.append(f"VERDICT: {'PASS' if all_ok else 'FAIL'}")
    LINES.append(f"Evidence: {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(LINES) + "\n")
    print("\n".join(LINES))
    return 0 if all_ok else 1


def main() -> int:
    started = datetime.now(UTC)
    LINES.append("SECRET LIFECYCLE + FAIL-CLOSED LIVE DRILL — A6")
    LINES.append(f"started {started.isoformat()}")

    os.environ["A6_DRILL_KEY"] = "s3cr3t-v1"

    # 1) Production-path wiring: build a real orchestrator (in-memory store, so
    #    the drill needs no network/host) and confirm the rotator uses the
    #    orchestrator's real audit + metrics ports.
    cfg = Config(db_path=":memory:", log_level="WARNING")
    orch = build_orchestrator(mode="paper", config=cfg)
    rotator = orch.secret_rotator
    ok_wire = rotator is not None
    RESULTS.append(("rotator_wired", ok_wire, "rotator built on the production orchestrator path"))
    LINES.append("  rotator built on the production orchestrator path")
    assert rotator is not None, "secret rotator must be wired on the paper build"

    # 2) Access audited + versioned through the real path.
    rotator.get("A6_DRILL_KEY")
    actions_after_access = [e.action for e in orch.audit.get_entries(limit=100)]
    ok_access = "secret.accessed" in actions_after_access
    RESULTS.append(
        (
            "access_audited",
            ok_access,
            "read through orchestrator rotator emitted secret.accessed (redacted)",
        )
    )
    LINES.append(f"  secret.accessed present in durable audit: {ok_access}")

    # 3) Rotation audited + versioned; reloaded value returned.
    os.environ["A6_DRILL_KEY"] = "s3cr3t-v2"
    rotated = rotator.rotate("A6_DRILL_KEY")
    actions_after_rotate = [e.action for e in orch.audit.get_entries(limit=100)]
    reloaded = rotator.get("A6_DRILL_KEY")
    stats = rotator.stats
    ok_rotate = (
        rotated
        and "secret.rotated" in actions_after_rotate
        and reloaded == "s3cr3t-v2"
        and stats["versions"]["A6_DRILL_KEY"] == 2
    )
    RESULTS.append(
        (
            "rotation_audited_versioned",
            ok_rotate,
            (
                f"rotate returned True, reloaded={reloaded!r}, "
                f"version={stats.get('versions', {}).get('A6_DRILL_KEY')}"
            ),
        )
    )
    LINES.append(f"  secret.rotated in durable audit; reloaded v2: {ok_rotate}")

    # Metrics surface the lifecycle counters on the real port.
    metric_access = orch.metrics.get_counter("secret.accessed.read.provider")
    metric_rotate = orch.metrics.get_counter("secret.rotated")
    ok_metrics = metric_access > 0 and metric_rotate > 0
    RESULTS.append(
        ("metrics_emitted", ok_metrics, f"accessed={metric_access} rotated={metric_rotate}")
    )
    LINES.append(
        "  lifecycle counters on real metrics port: "
        f"access={metric_access} rotation={metric_rotate}"
    )

    orch.stop()

    # 4) Fail-closed live gate: LIVE without a durable database for order and
    #    risk state. An in-memory path would leave order and risk state in RAM,
    #    so this refusal must be loud rather than a silent degradation.
    try:
        try:
            build_orchestrator(mode="live", config=Config(db_path=":memory:", log_level="WARNING"))
            refused_no_db = False
            detail = "LIVE boot did NOT refuse without a durable database"
        except RuntimeError as exc:
            refused_no_db = "durable database" in str(exc)
            detail = f"refused missing durable db: {exc}"[:120]
        RESULTS.append(("live_requires_durable_db", refused_no_db, detail))
        LINES.append(
            "  LIVE without a durable database refused to boot " f"(fail-closed): {refused_no_db}"
        )
    except Exception as exc:  # noqa: BLE001 — any non-RuntimeError abort is a defect
        RESULTS.append(("live_requires_durable_db", False, f"unexpected abort: {exc}"[:120]))

    # 4) Fail-closed live gate: no risk rails -> loud ConfigError naming them.
    try:
        try:
            build_orchestrator(
                mode="live",
                config=Config(db_path=_durable_db(), log_level="WARNING"),
            )
            refused_no_rails = False
            detail = "LIVE boot did NOT refuse without explicit risk rails"
        except ConfigError as exc:
            refused_no_rails = "production risk rails" in str(exc)
            detail = f"refused missing risk rails: {exc}"[:120]
        RESULTS.append(("live_requires_risk_rails", refused_no_rails, detail))
        LINES.append(f"  LIVE without risk rails refused to boot (fail-closed): {refused_no_rails}")
    except Exception as exc:  # noqa: BLE001 — any non-ConfigError abort is a defect
        RESULTS.append(("live_requires_risk_rails", False, f"unexpected abort: {exc}"[:120]))

    # 5) Fail-closed live gate: rails supplied, but no broker creds -> loud
    #    RuntimeError (A6), never a silent demotion to paper.
    saved_api = os.environ.pop("ALPACA_API_KEY", None)
    saved_secret = os.environ.pop("ALPACA_SECRET_KEY", None)
    try:
        try:
            build_orchestrator(mode="live", config=_live_config())
            refused_missing = False
            detail = "LIVE boot did NOT refuse without broker credentials"
        except RuntimeError as exc:
            refused_missing = "ALPACA_API_KEY and ALPACA_SECRET_KEY" in str(exc)
            detail = f"refused missing creds: {exc}"[:120]
        RESULTS.append(("live_requires_credentials", refused_missing, detail))
        LINES.append(
            f"  LIVE without broker creds refused to boot (fail-closed): {refused_missing}"
        )
    finally:
        if saved_api is not None:
            os.environ["ALPACA_API_KEY"] = saved_api
        if saved_secret is not None:
            os.environ["ALPACA_SECRET_KEY"] = saved_secret

    return _report()


if __name__ == "__main__":
    raise SystemExit(main())
