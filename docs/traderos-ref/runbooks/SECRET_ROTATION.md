# Secret Rotation — Operator Runbook (G-04: managed Vault/KMS)

**Purpose:** run the real `SecretRotator` + `VaultSecretProvider` rotation path
against a **managed** Vault/KMS with live keys, so the G-04 item "rotation
cadence against a managed Vault/KMS instance" is closed with production
evidence — not just the local-dev Vault proven by the drills.

## What is already proven (local dev Vault)

- `scripts/evidence/run_vault_secret_manager_drill.py` — 5/5 PASS: real
  provider on the boot path, value-redacted access audit, fail-closed on no
  Vault/no env.
- `scripts/evidence/run_vault_rotation_drill.py` — 5/5 PASS (Sprint 47): the
  rotator picks up a **changed** KV-v2 secret on `rotate()` (version bumps),
  `rotate_all()` counts, reads/rotations are value-redacted in the audit trail,
  a missing key fails closed to `None` (data outcome, not an outage).

The rotation *mechanism* is therefore proven. The remaining step is running
the **same code** against a managed instance — the provider and rotator are
identical; only the address/token differ.

## Operator steps (managed Vault)

1. **Provision a managed Vault or KMS-backed KV store** (e.g. Vault Enterprise,
   Cloud KMS-backed Vault, or a managed HashiCorp Vault as a Service).
2. **Create the KV-v2 mount** and store the production secret under the same
   key names the app resolves (`ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, plus any
   broker/admin keys). Values are written via the provider's own secret-owner
   workflow — never via this repo, never committed.
3. **Grant a scoped token/app-role** to the TraderOS service with read access
   to that mount only (least privilege). The token lives in Railway env as
   `VAULT_TOKEN` (itself a secret, not committed).
4. **Set on the deployed service:** `VAULT_ADDR`, `VAULT_TOKEN` (and
   `SECRET_ROTATION_INTERVAL` if a non-default cadence is wanted; default
   86400s = daily).
5. **Run the rotation drill against the managed address:**
   ```bash
   VAULT_ADDR=https://<managed-vault-addr> VAULT_TOKEN=<token> \
       PYTHONPATH=src python3 scripts/evidence/run_vault_rotation_drill.py
   ```
   The drill writes/rotates/reads a test key named `ALPACA_API_KEY` and
   restores the original value afterwards. On a managed instance, prefer a
   throwaway drill key (`PG_SCRATCH`-style): either write a disposable key and
   point the drill at it, or run it in a scratch Vault namespace. **The drill
   must not rotate a live broker key out from under a running daemon** — run it
   against a dedicated drill key or during a maintenance window.
6. **Verify rotation cadence in production:** trigger one real rotation
   (update the secret in Vault, then `POST /v1/...` or restart the rotator's
   interval loop) and confirm via `/v1/orchestrator/status` that the rotator
   version map advances and the audit trail records `secret.rotated` with
   `value_redacted: true` (no raw value ever persisted).
7. **Record evidence:** save the drill stdout to
   `docs/evidence/<date>_vault_rotation_drill.log` and note the managed
   instance in `GAP_READINESS.md` G-04 row.

## Acceptance (closes the G-04 open item)

- `run_vault_rotation_drill.py` VERDICT PASS against the managed address.
- A real rotation in production advances the version and writes a
  value-redacted `secret.rotated` audit entry.
- Access audit shows reads with no raw values.

## Fail-closed guarantees (unchanged, re-verified by drills)

- Missing/forbidden key (4xx) → `None` (data outcome, next provider or None).
- Vault outage (5xx/network/timeout/corrupt body) → `VaultFetchError` →
  `VAULT_CB` opens → `CircuitOpenError` fast-fail. Never a silent demotion to
  a lower-trust source.
- No `VAULT_ADDR`/`VAULT_TOKEN` and no env value → LIVE key resolution returns
  None and LIVE boot refuses loudly.
