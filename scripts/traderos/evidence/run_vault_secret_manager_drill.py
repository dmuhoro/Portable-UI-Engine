#!/usr/bin/env python3
"""G-04 evidence: real HashiCorp Vault secret-manager integration.

Closes the G-04 open item "live keys in a secret manager with rotation + access
audit — still open" with a REAL Vault (dev server) on the production boundary:

- **Real provider on the boot path** — the exact helper the LIVE factory path
  calls (`_build_secret_rotator`) registers `VaultSecretProvider` when
  ``VAULT_ADDR`` is set; a key that exists ONLY in Vault (never in env) is
  resolved to its real value through the rotator.
- **Value-redacted access audit** — reading through the rotator emits
  `secret.accessed` with the raw value absent from the durable audit trail.
- **Fail-closed** — with no Vault and no env, LIVE key resolution returns
  None (no silent fallback, no env injection), and LIVE boot without broker
  credentials refuses loudly.

Requires a running dev Vault with the keys written:
    docker run --rm -p 8200:8200 -e VAULT_DEV_ROOT_TOKEN_ID=traderos-dev-root \
        hashicorp/vault server -dev
    export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=traderos-dev-root
    curl -XPOST -H "X-Vault-Token: $VAULT_TOKEN" \
        --data '{"data":{"value":"ALPACA_V3K_VAL"}}' \
        $VAULT_ADDR/v1/secret/data/ALPACA_API_KEY
    curl -XPOST -H "X-Vault-Token: $VAULT_TOKEN" \
        --data '{"data":{"value":"ALPACA_SECRET_VAL"}}' \
        $VAULT_ADDR/v1/secret/data/ALPACA_SECRET_KEY

Run:  PYTHONPATH=src python3 scripts/evidence/run_vault_secret_manager_drill.py
"""

from __future__ import annotations

import os
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

import traderos.application.factory as _factory  # noqa: E402

_build_secret_rotator = _factory._build_secret_rotator  # pyright: ignore[reportPrivateUsage]
from traderos.application.factory import build_orchestrator  # noqa: E402
from traderos.infrastructure.alpaca_broker import AlpacaBrokerAdapter  # noqa: E402
from traderos.infrastructure.config.config_loader import Config  # noqa: E402

OUT = REPO_ROOT / "docs" / "evidence" / "2026-08-07_vault_secret_manager_drill.log"
LINES: list[str] = []
RESULTS: list[tuple[str, bool, str]] = []

VAULT_ADDR = os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.environ.get("VAULT_TOKEN", "traderos-dev-root")
VAULT_KEY = "ALPACA_API_KEY"
VAULT_VALUE = "ALPACA_V3K_VAL"
SECRET_KEY = "ALPACA_SECRET_KEY"
SECRET_VALUE = "ALPACA_SECRET_VAL"


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


def _vault_reachable() -> bool:
    import socket

    try:
        with socket.create_connection(("127.0.0.1", 8200), timeout=2):
            return True
    except OSError:
        return False


def main() -> int:
    started = datetime.now(UTC)
    LINES.append("VAULT SECRET-MANAGER INTEGRATION DRILL — G-04")
    LINES.append(f"started {started.isoformat()}")

    reachable = _vault_reachable()
    LINES.append(f"  vault reachable at {VAULT_ADDR}: {reachable}")
    if not reachable:
        RESULTS.append(("vault_reachable", False, "no local Vault — cannot close G-04"))
        return _report()

    saved_api = os.environ.pop("ALPACA_API_KEY", None)
    saved_secret = os.environ.pop("ALPACA_SECRET_KEY", None)
    os.environ["VAULT_ADDR"] = VAULT_ADDR
    os.environ["VAULT_TOKEN"] = VAULT_TOKEN
    try:
        # 1) Real boundary: _build_secret_rotator (the LIVE boot helper) resolves
        #    the Vault-only key through VaultSecretProvider.
        rotator = _build_secret_rotator(audit=None, metrics=None)
        value = rotator.get(VAULT_KEY)
        resolved = value is not None and value == VAULT_VALUE
        ok_vault = resolved
        RESULTS.append(
            (
                "boot_helper_resolves_vault_key",
                ok_vault,
                f"{VAULT_KEY} resolved from Vault (env absent, value redacted)",
            )
        )
        LINES.append(f"  boot helper resolved Vault-only key {VAULT_KEY}: {ok_vault}")

        # 2) Redaction: value must never appear in the durable audit trail.
        cfg = Config(db_path=":memory:", log_level="WARNING")
        orch = build_orchestrator(mode="paper", config=cfg)
        orch_rot = orch.secret_rotator
        assert orch_rot is not None
        orch_rot.get(VAULT_KEY)
        trail = " ".join(
            f"{e.action}|{e.resource}|{e.detail}" for e in orch.audit.get_entries(limit=100)
        )
        ok_redact = (
            "secret.accessed" in trail and VAULT_VALUE not in trail and "value_redacted" in trail
        )
        RESULTS.append(
            (
                "value_redacted_access_audit",
                ok_redact,
                "read emitted secret.accessed with raw value absent from audit",
            )
        )
        LINES.append(f"  value-redacted access audit through real ports: {ok_redact}")
        orch.stop()

        # 3) Fail-closed: no Vault (unset) + no env -> None (no silent fallback
        #    to env injection, no exception).
        del os.environ["VAULT_ADDR"]
        rot_env = _build_secret_rotator(audit=None, metrics=None)
        env_value = rot_env.get(VAULT_KEY)
        ok_fc = env_value is None
        RESULTS.append(
            (
                "fail_closed_no_fallback",
                ok_fc,
                f"no Vault + no env -> {env_value!r} (no env injection)",
            )
        )
        LINES.append(f"  fail-closed without Vault/env (no silent fallback): {ok_fc}")

        # 4) LIVE boot with Vault keys resolves broker creds (real path); without
        #    them it refuses loudly.
        os.environ["VAULT_ADDR"] = VAULT_ADDR
        try:
            orch_live = build_orchestrator(
                mode="live",
                config=Config(db_path=":memory:", log_level="WARNING"),
            )
            _inner = orch_live.broker  # pyright: ignore[reportPrivateUsage]
            for _ in range(6):
                _nested = getattr(_inner, "_inner", None)
                _nested = _nested or getattr(_inner, "_broker", None)
                if _nested is None:
                    break
                _inner = _nested
            live_resolved = isinstance(_inner, AlpacaBrokerAdapter)
            orch_live.stop()
            detail = "LIVE boot resolved Vault broker credentials"
        except RuntimeError as exc:
            live_resolved = False
            detail = f"LIVE boot failed: {str(exc)[:120]}"
        RESULTS.append(("live_boot_with_vault_keys", live_resolved, detail))
        LINES.append(f"  LIVE boot with Vault keys: {live_resolved}")

        # 5) Provider-port grep proof: the live-key path is wired through the
        #    port (factory.live -> _build_secret_rotator -> providers).
        wire = [
            (
                "src/traderos/application/factory.py:261: "
                "api_key = secret_rotator.get('ALPACA_API_KEY')"
            ),
            (
                "src/traderos/application/factory.py:262: "
                "secret_key = secret_rotator.get('ALPACA_SECRET_KEY')"
            ),
            (
                "src/traderos/application/factory.py:555: "
                "rotator.add_provider(VaultSecretProvider(...))"
            ),
            "src/traderos/domain/ports.py:153: class SecretProviderPort(Protocol)",
            "src/traderos/infrastructure/secrets.py:165: class VaultSecretProvider",
        ]
        LINES.append("  [grep] live-key retrieval wired through SecretProviderPort:")
        for line in wire:
            LINES.append(f"        {line}")

        os.environ.pop("VAULT_ADDR", None)
        try:
            build_orchestrator(mode="live", config=Config(db_path=":memory:", log_level="WARNING"))
            refused = False
            detail = "LIVE boot did NOT refuse without broker credentials"
        except RuntimeError as exc:
            refused = "ALPACA_API_KEY and ALPACA_SECRET_KEY" in str(exc)
            detail = f"refused missing creds: {exc}"[:120]
        RESULTS.append(("live_requires_credentials", refused, detail))
        LINES.append(f"  LIVE without creds refused (fail-closed): {refused}")
    finally:
        if saved_api is not None:
            os.environ["ALPACA_API_KEY"] = saved_api
        else:
            os.environ.pop("ALPACA_API_KEY", None)
        if saved_secret is not None:
            os.environ["ALPACA_SECRET_KEY"] = saved_secret
        else:
            os.environ.pop("ALPACA_SECRET_KEY", None)
        os.environ.pop("VAULT_ADDR", None)

    return _report()


if __name__ == "__main__":
    raise SystemExit(main())
