#!/usr/bin/env bash
set -e
TMPDIR=$(mktemp -d)
cd "$TMPDIR"
git clone --branch chore/ci-bootstrap https://github.com/dmuhoro/Portable-UI-Engine.git repo
cd repo
npm ci
npm run lint
npm run test
npm run build
echo "=== CLEAN CLONE VERIFICATION: PASS ==="
