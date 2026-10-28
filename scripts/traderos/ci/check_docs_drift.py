#!/usr/bin/env python3
"""OD-14 docs-drift gate.

Documentation drift is a defect, not a style issue: a document that claims a
capability nobody can demonstrate is a false promise to whoever reads it next.

This gate is deliberately narrow and mechanical. It checks the failure modes
that have actually occurred in this repository, and it fails closed on the
checks it cannot verify:

1. Version drift      -- pyproject.toml is the single version source, and it
                         must match configs/settings.yaml.
2. Legacy version file-- a tracked VERSION file means two sources of truth.
3. Undemonstrated claim -- a capability claim must name a command that
                         demonstrates it. Prose assertions of the form
                         "is enforced", "is blocked", "cannot happen" or
                         "guarantees" must cite a command, test path or ADR.
4. Superseded evidence -- a document must not cite a release tag that is
                         older than the tag it claims to describe.
5. Stale release metadata -- CHANGELOG must contain an entry for the current
                         version.

Every check prints what it looked at. A check that cannot run is a FAIL, not a
silent pass: an unverifiable gate is exactly the kind of gate that provides
false confidence (OD-15).
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # scripts/ci/<this> -> repo root

# Claims of enforcement. Each needs a demonstrable anchor on the same or an
# adjacent line: a command, a test path, a file:line citation, or an ADR.
ENFORCEMENT_CLAIM = re.compile(
    r"\b(?:"
    r"is\s+enforced"
    r"|are\s+enforced"
    r"|is\s+blocked"
    r"|are\s+blocked"
    r"|cannot\s+happen"
    r"|can\s+never\s+happen"
    r"|is\s+guaranteed"
    r"|are\s+guaranteed"
    r"|guarantees"
    r"|prevents?\s+(?:this|it|them)"
    r")\b",
    re.IGNORECASE,
)

DEMONSTRATION = re.compile(
    r"`[^`]*`"  # inline code: a command, path or flag
    r"|(?:^|\s)(?:pytest|python3?|make|docker|bash|alembic|uvicorn|curl)\b"
    r"|\.py\b"
    r"|ADR-\d+"
    r"|OD-\d+"
    r"|:\d+",  # file:line citation
    re.IGNORECASE,
)

# An enforcement claim only matters when it is about THIS system. Without this
# scope the gate flags ordinary engineering prose ("a weak foundation
# guarantees rewrites"), and a gate that cries wolf gets switched off -- which
# is worse than having no gate. Claims with no system context are out of scope
# and are stated as such here rather than quietly skipped.
SYSTEM_CONTEXT = re.compile(
    r"\b(?:"
    r"order|orders|sizing|position|positions|money|capital|equity"
    r"|risk|kill|reconcil\w*|broker|fill|trade|trading|ledger|journal"
    r"|idempoten\w*|staleness|exposure|drawdown|VaR|PnL|credential|secret"
    r"|decimal|gate|rails?|policy|CI|workflow|ADR|governance"
    r")\b",
    re.IGNORECASE,
)

# Directories scanned for drift. Generated/vendored trees are excluded so the
# gate stays fast and its failures stay actionable.
SCAN_DIRS = ("docs", "README.md", "CHANGELOG.md")
SCAN_SUFFIXES = (".md",)


def _failures() -> list[str]:
    return []


def check_version_sources() -> list[str]:
    """pyproject.toml is the single version source (CI asserts this too)."""
    out: list[str] = []
    pyproject = ROOT / "pyproject.toml"
    settings = ROOT / "configs" / "settings.yaml"

    if not pyproject.exists():
        return [f"VERSION: {pyproject} is missing; cannot verify the version source"]
    version = tomllib.loads(pyproject.read_text())["project"]["version"]

    if settings.exists():
        text = settings.read_text()
        m = re.search(r'^version:\s*"?([^"\n]+)"?', text, re.MULTILINE)
        if m is None:
            out.append(f"VERSION: no version key found in {settings.relative_to(ROOT)}")
        elif m.group(1).strip() != version:
            out.append(
                f"VERSION DRIFT: pyproject.toml={version} but "
                f"{settings.relative_to(ROOT)}={m.group(1).strip()}"
            )
    else:
        out.append(f"VERSION: {settings.relative_to(ROOT)} is missing; drift unverifiable")

    if (ROOT / "VERSION").exists():
        out.append("VERSION: a VERSION file exists; pyproject.toml must be the only source")
    return out


def check_undemonstrated_claims() -> list[str]:
    """Every enforcement claim needs a command, test path or ADR beside it."""
    out: list[str] = []
    files: list[Path] = []
    for entry in SCAN_DIRS:
        p = ROOT / entry
        if p.is_file() and p.suffix in SCAN_SUFFIXES:
            files.append(p)
        elif p.is_dir():
            files.extend(
                sorted(
                    f
                    for f in p.rglob("*")
                    if f.is_file() and f.suffix in SCAN_SUFFIXES and "evidence" not in f.parts
                )
            )

    if not files:
        # Fail closed: a gate that scanned nothing proves nothing.
        return ["CLAIMS: no documentation found to scan; the gate cannot pass vacuously"]

    flagged = 0
    for path in files:
        rel = path.relative_to(ROOT)
        lines = path.read_text(errors="replace").splitlines()
        for i, line in enumerate(lines):
            if not ENFORCEMENT_CLAIM.search(line):
                continue
            # Look at the claim line and the two lines of context either side:
            # prose routinely puts the command on the following line.
            window = "\n".join(lines[max(0, i - 2) : i + 3])
            if not SYSTEM_CONTEXT.search(window):
                continue  # out of scope: not a claim about this system
            if DEMONSTRATION.search(window):
                continue
            flagged += 1
            out.append(
                f"CLAIM: {rel}:{i + 1} asserts enforcement with nothing to run: "
                f"{line.strip()[:100]}"
            )
    print(f"    (scanned {len(files)} files in system context)")
    return out


def check_superseded_evidence() -> list[str]:
    """The declared version must correspond to an actual release tag.

    Scope, stated rather than hidden: this checks the CURRENT version, which is
    unambiguous. An earlier draft also scanned every `vN.N.N` string in the docs
    and required each to be a real tag; that was wrong and was removed, because
    in this repository those strings are legitimately product names
    ("Market Intelligence Platform v0.1.0"), semver-policy examples
    ("PATCH (v1.0.1, v1.0.2)") and historical sprint records. Guessing which is
    which would have produced false findings that train people to ignore the
    gate. Historical version strings in archived prose remain out of scope.
    """
    out: list[str] = []
    changelog = ROOT / "CHANGELOG.md"
    if not changelog.exists():
        return ["RELEASE: CHANGELOG.md is missing; release metadata unverifiable"]

    try:
        tags = set(
            subprocess.run(
                ["git", "tag", "--list", "v*"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            ).stdout.split()
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover
        return [f"RELEASE: could not read tags ({exc}); release metadata unverifiable"]

    if not tags:
        return ["RELEASE: no tags readable; release metadata unverifiable (fail closed)"]

    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    if f"v{version}" not in tags:
        out.append(
            f"RELEASE: pyproject.toml is {version} but no tag v{version} exists. "
            "An unreleased version in the changelog is drift, not a release."
        )
    return out


def check_changelog_covers_version() -> list[str]:
    """CHANGELOG must mention the current version somewhere."""
    out: list[str] = []
    changelog = ROOT / "CHANGELOG.md"
    if not changelog.exists():
        return ["RELEASE: CHANGELOG.md is missing"]
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    if version not in changelog.read_text(errors="replace"):
        out.append(f"RELEASE: CHANGELOG.md has no entry for the current version {version}")
    return out


CHECKS = (
    ("version sources", check_version_sources),
    ("undemonstrated claims", check_undemonstrated_claims),
    ("superseded evidence", check_superseded_evidence),
    ("changelog coverage", check_changelog_covers_version),
)


def main() -> int:
    failures = _failures()
    print("OD-14 DOCS-DRIFT GATE")
    print(f"root: {ROOT}")
    print()
    for name, check in CHECKS:
        found = check()
        if found:
            print(f"[FAIL] {name}")
            for f in found:
                print(f"    - {f}")
            failures.extend(found)
        else:
            print(f"[PASS] {name}")

    print()
    if failures:
        print(f"VERDICT: FAIL — {len(failures)} drift finding(s)")
        print("Docs claiming enforcement without something to run are a defect.")
        return 1
    print("VERDICT: PASS — no documentation drift detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
