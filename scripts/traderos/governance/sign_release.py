#!/usr/bin/env python3
"""G-07 release signing: attach and verify a signature for a release artifact.

Sign:     python3 scripts/governance/sign_release.py sign --artifact <path> [--key-var NAME]
Verify:   python3 scripts/governance/sign_release.py verify --artifact <path> [--key-var NAME]

- The signature is HMAC-SHA256 over the artifact digest with a key from the
  environment (default env var ``RELEASE_SIGNING_KEY``).
- The key is never printed and never written to disk. If the key is absent in
  ``sign`` mode a deterministic *paper* key is used (drill only) and the output
  says so; ``verify`` fails closed on any mismatch or missing signature.
- Signature files live under ``docs/evidence/releases/`` as
  ``<artifact>.sig`` containing ``<digest_hex>:<hmac_hex>``.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _sig_dir() -> Path:
    return Path(
        os.environ.get("RELEASE_SIG_DIR", str(REPO_ROOT / "docs" / "evidence" / "releases"))
    )


PAPER_KEY = "paper-signing-key-for-drills-only"


def _key(key_var: str, required: bool) -> bytes:
    key = os.environ.get(key_var)
    if key:
        return key.encode()
    if required:
        print(f"FATAL: environment variable {key_var} is not set", file=sys.stderr)
        raise SystemExit(1)
    return PAPER_KEY.encode()


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sig_path(artifact: Path) -> Path:
    return _sig_dir() / (artifact.name + ".sig")


def sign(artifact: Path, key_var: str) -> int:
    if not artifact.is_file():
        print(f"FATAL: artifact not found: {artifact}", file=sys.stderr)
        return 1
    key = _key(key_var, required=False)
    used_paper = key != os.environ.get(key_var, "").encode()
    digest = _digest(artifact)
    mac = hmac.new(key, digest.encode(), hashlib.sha256).hexdigest()
    sig_dir = _sig_dir()
    sig_dir.mkdir(parents=True, exist_ok=True)
    out = _sig_path(artifact)
    out.write_text(f"{digest}:{mac}\n")
    print(f"signed {artifact.name} digest={digest[:16]}... -> {out}")
    if used_paper:
        print("WARNING: used the deterministic paper key (env signing key absent) — drill only")
    return 0


def verify(artifact: Path, key_var: str) -> int:
    sig_file = _sig_path(artifact)
    if not sig_file.is_file():
        print(f"FAIL: no signature file {sig_file}", file=sys.stderr)
        return 1
    try:
        stored_digest, stored_mac = sig_file.read_text().strip().split(":", 1)
    except ValueError:
        print(f"FAIL: malformed signature file {sig_file}", file=sys.stderr)
        return 1
    key = _key(key_var, required=True)
    digest = _digest(artifact)
    expected = hmac.new(key, digest.encode(), hashlib.sha256).hexdigest()
    if digest != stored_digest or not hmac.compare_digest(expected, stored_mac):
        print("FAIL: signature does not match the artifact", file=sys.stderr)
        return 1
    print(f"OK: {artifact.name} signature valid")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("sign", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--artifact", type=Path, required=True)
        p.add_argument("--key-var", default="RELEASE_SIGNING_KEY")
    args = parser.parse_args(argv)
    if args.cmd == "sign":
        return sign(args.artifact, args.key_var)
    return verify(args.artifact, args.key_var)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
