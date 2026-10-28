#!/usr/bin/env python3
"""Generate a release manifest: version, date, HEAD, and sha256 of the
release-defining files.

    python3 scripts/governance/release_manifest.py --version 1.3.1

The manifest is the artifact that gets signed (``sign_release.py``), so it must
be reproducible and honest: it records the *committed* HEAD the artifact set was
cut from and the digest of each file. Write to a path (default under
``docs/evidence/releases/``), then sign it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The files that define a release. Keep this list explicit — a release
# manifest that silently omits a changed file is a false provenance claim.
DEFAULT_ARTIFACTS = [
    "pyproject.toml",
    "configs/settings.yaml",
    "configs/settings.production.example.yaml",
    "Dockerfile",
    "railway.toml",
    "railway.soak.toml",
    "src/traderos/application/factory.py",
    "src/traderos/application/orchestrator.py",
    "src/traderos/infrastructure/alpaca_broker.py",
    "scripts/evidence/run_real_paper_soak.py",
    "scripts/evidence/run_unattended_paper_soak.py",
]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="release version, e.g. 1.3.1")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output path (default docs/evidence/releases/RELEASE_<v>_manifest.json)",
    )
    parser.add_argument("--date", default=None, help="ISO date (default: today UTC)")
    parser.add_argument("--artifacts", nargs="*", default=DEFAULT_ARTIFACTS, help="files to hash")
    args = parser.parse_args(argv)

    out = args.out or (
        REPO_ROOT / "docs" / "evidence" / "releases" / f"RELEASE_{args.version}_manifest.json"
    )
    date = args.date or datetime.now(UTC).date().isoformat()

    files: dict[str, str] = {}
    for rel in args.artifacts:
        path = REPO_ROOT / rel
        if not path.is_file():
            print(f"FATAL: artifact missing: {rel}")
            return 1
        files[rel] = _digest(path)

    head = _head()
    manifest = {
        "release": args.version,
        "date": date,
        "head": head,
        "artifact_files": files,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(files)} artifacts, head={head[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
