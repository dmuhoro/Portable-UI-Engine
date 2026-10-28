#!/usr/bin/env python3
"""G-04 evidence: secret ROTATION cadence against a real HashiCorp Vault.

The G-04 open item is "rotation cadence against a managed Vault/KMS not yet
exercised (local dev Vault proven)". This drill proves the rotation MECHANISM
against a real Vault (dev server), so the only thing left for a managed
instance is pointing the same code at the managed address with real keys — the
rotator logic is identical.

Proves, through the real ``SecretRotator`` + ``VaultSecretProvider`` wiring:

1. **Rotator reads from Vault, not env** — a key that exists ONLY in Vault
   resolves through the rotator to its real value.
2. **Rotation picks up a changed secret** — after the Vault value is changed
   (write a new KV-v2 version), ``rotator.rotate(key)`` returns the NEW value
   and bumps the version.
3. **Value-redacted access audit** — every read and rotation records
   ``secret.accessed`` / ``secret.rotated`` to the durable audit trail with the
   raw value absent (``value_redacted: true``), never written.
4. **Rotate-all** — ``rotate_all`` rotates every tracked secret and returns the
   count.
5. **Fail-closed on a missing key** — a key absent from Vault resolves to None
   (data outcome, not an outage).

PASS requires all checks green. This drill never fabricates data: if Vault is
unreachable it exits NO-GO. It is operator-run (needs a real Vault instance);
against a managed Vault/KMS, set VAULT_ADDR/VAULT_TOKEN to the managed address
and run the same script — see the checklist in docs/runbooks/SECRET_ROTATION.md.

Requires a running dev Vault with the keys written:
    docker run --rm -d -p 8200:8200 -e VAULT_DEV_ROOT_TOKEN_ID=traderos-dev-root \
        hashicorp/vault server -dev
    export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=traderos-dev-root
    curl -XPOST -H "X-Vault-Token: $VAULT_TOKEN" \
        --data '{"data":{"value":"ALPACA_V3K_VAL"}}' \
        $VAULT_ADDR/v1/secret/data/ALPACA_API_KEY

Run:  PYTHONPATH=src python3 scripts/evidence/run_vault_rotation_drill.py
"""

from __future__ import annotations

import os
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

OUT = (
    REPO_ROOT
    / "docs"
    / "evidence"
    / (f"{datetime.now(UTC).date().isoformat()}_vault_rotation_drill.log")
)

VAULT_ADDR = os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.environ.get("VAULT_TOKEN", "traderos-dev-root")
ROTATE_KEY = "ALPACA_API_KEY"
VALUE_V1 = "ALPACA_V3K_VAL"
VALUE_V2 = "ALPACA_V3K_VAL_ROTATED"


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


def _vault_reachable() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 8200), timeout=2):
            return True
    except OSError:
        return False


def _vault_write(value: str) -> None:
    """Write a new KV-v2 version of ROTATE_KEY to the real Vault."""
    req = urllib.request.Request(
        f"{VAULT_ADDR}/v1/secret/data/{ROTATE_KEY}",
        data=__import__("json").dumps({"data": {"value": value}}).encode(),
        method="POST",
        headers={"X-Vault-Token": VAULT_TOKEN, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=5):
        pass


def _vault_delete() -> None:
    """Remove ROTATE_KEY entirely (to prove fail-closed on a missing key)."""
    req = urllib.request.Request(
        f"{VAULT_ADDR}/v1/secret/metadata/{ROTATE_KEY}",
        method="DELETE",
        headers={"X-Vault-Token": VAULT_TOKEN},
    )
    try:
        with urllib.request.urlopen(req, timeout=5):
            pass
    except urllib.error.HTTPError:
        pass


def main() -> int:
    lines: list[str] = []
    results: list[tuple[str, bool, str]] = []
    lines.append("SECRET ROTATION CADENCE DRILL — real HashiCorp Vault (G-04)")
    lines.append(f"started {datetime.now(UTC).isoformat()} addr={VAULT_ADDR}")

    if not _vault_reachable():
        lines.append("  vault not reachable -> NO-GO")
        results.append(("vault_connection", False, f"unreachable at {VAULT_ADDR}"))
        return _report(lines, results)

    from traderos.infrastructure.resilience import reset_all_breakers
    from traderos.infrastructure.secrets import SecretRotator
    from traderos.infrastructure.secrets import VaultSecretProvider

    reset_all_breakers()

    class _Audit:
        """In-memory durable-audit stand-in with a redaction check."""

        def __init__(self) -> None:
            self.records: list[dict] = []
            self.redaction_violations = 0

        def record(self, action: str, actor: str, subject: str, detail: str = ""):
            self.records.append({"action": action, "subject": subject, "detail": detail})
            # The audit must never carry the secret value itself.
            if VALUE_V1 in detail or VALUE_V2 in detail:
                self.redaction_violations += 1

    audit = _Audit()
    rotator = SecretRotator(audit=audit)  # pyright: ignore[reportArgumentType]
    rotator.add_provider(VaultSecretProvider(url=VAULT_ADDR, token=VAULT_TOKEN, mount="secret"))

    # ---- 1. read from Vault (not env) ---------------------------------
    try:
        value = rotator.get(ROTATE_KEY)
        ok1 = value == VALUE_V1
        lines.append(
            f"check1: rotator resolved {ROTATE_KEY} from Vault -> "
            f"{'matched' if ok1 else 'mismatch'}"
        )
        results.append(
            ("read_from_vault_not_env", ok1, f"resolved={value is not None} (expected {VALUE_V1})")
        )
    except Exception as exc:  # noqa: BLE001
        results.append(("read_from_vault_not_env", False, str(exc)))

    # ---- 2. rotation picks up a changed secret ------------------------
    try:
        _vault_write(VALUE_V2)
        time.sleep(0.2)
        ok_rotate = rotator.rotate(ROTATE_KEY)
        new_value = rotator.get(ROTATE_KEY)
        stats = rotator.stats
        version = stats["versions"].get(ROTATE_KEY, 0)
        ok2 = ok_rotate and new_value == VALUE_V2 and version >= 2
        lines.append(
            f"check2: rotate after Vault write -> ok={ok_rotate} "
            f"new_value_matched={new_value == VALUE_V2} version={version}"
        )
        results.append(
            (
                "rotation_picks_up_changed_secret",
                ok2,
                f"new={new_value == VALUE_V2} version={version}",
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(("rotation_picks_up_changed_secret", False, str(exc)))

    # ---- 3. value-redacted access + rotation audit ----------------------
    try:
        reads = [r for r in audit.records if r["action"] == "secret.accessed"]
        rotates = [r for r in audit.records if r["action"] == "secret.rotated"]
        ok_reads = len(reads) >= 2
        ok_rotates = len(rotates) >= 1
        ok_redacted = audit.redaction_violations == 0
        lines.append(
            f"check3: audit -> accesses={len(reads)} rotations={len(rotates)} "
            f"redaction_violations={audit.redaction_violations}"
        )
        results.append(
            (
                "value_redacted_audit",
                ok_reads and ok_rotates and ok_redacted,
                (
                    f"accesses={len(reads)} rotations={len(rotates)} "
                    f"redaction_violations={audit.redaction_violations}"
                ),
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(("value_redacted_audit", False, str(exc)))

    # ---- 4. rotate_all returns the count --------------------------------
    try:
        count = rotator.rotate_all()
        lines.append(f"check4: rotate_all -> count={count}")
        results.append(("rotate_all_counts", count >= 1, f"rotated {count} tracked secret(s)"))
    except Exception as exc:  # noqa: BLE001
        results.append(("rotate_all_counts", False, str(exc)))

    # ---- 5. fail-closed on a missing key --------------------------------
    try:
        _vault_delete()
        time.sleep(0.2)
        missing = rotator.get("ALPACA_SECRET_KEY_THAT_DOES_NOT_EXIST")
        ok5 = missing is None
        lines.append(f"check5: missing key -> resolved={missing is not None}")
        results.append(
            (
                "missing_key_fail_closed",
                ok5,
                "absent key resolves to None (data outcome, not an outage)",
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(("missing_key_fail_closed", False, str(exc)))

    # Leave Vault clean for the next run.
    try:
        _vault_write(VALUE_V1)
    except Exception:  # noqa: BLE001, S110 — cleanup only, verdict already decided
        pass

    return _report(lines, results)


if __name__ == "__main__":
    raise SystemExit(main())
