#!/usr/bin/env bash
# Independent clean-tree verification. Prefer a local clone so the check does
# not depend on GitHub availability; fall back to remote when REMOTE=1.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BRANCH="${BRANCH:-$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)}"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

echo "=== CLEAN CLONE VERIFICATION ==="
echo "Branch: $BRANCH"
echo "Temp:   $TMPDIR"

if [[ "${REMOTE:-0}" == "1" ]]; then
  git clone --branch "$BRANCH" https://github.com/dmuhoro/Portable-UI-Engine.git "$TMPDIR/repo"
else
  git clone --local --shared "$ROOT" "$TMPDIR/repo"
  git -C "$TMPDIR/repo" checkout "$BRANCH"
fi

cd "$TMPDIR/repo"
npm ci
node packages/tokens/scripts/build-tokens.js
npm run check:version
npm run lint
node tools/design-lint/index.mjs
npm run test:negative-gate
npm test
npm run build
test -s dist/engine.js
test -s dist/engine.min.js
echo "=== CLEAN CLONE VERIFICATION: PASS ==="
