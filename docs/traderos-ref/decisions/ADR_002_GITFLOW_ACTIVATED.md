# ADR-002

## Decision

TraderOS operates a GitFlow branch strategy from Sprint 14 onward.

- `main` — production, protected. Receives code only via `release/*` PRs.
- `develop` — integration branch (created at commit `1205b6f`, 2026-07-31). Receives `feature/*`, `fix/*`, and `wp/*` branches via PR.
- No direct pushes to `main` or `develop`; all merges via PR with gates G1-G6 passing.
- Releases: `develop` reaches release criteria, cut `release/vX.Y.Z`, run release checklist, tag semver, merge to `main` and `develop`.

## Reason

The documented workflow (`.ai/context/11_workflow-rules.md`) mandated GitFlow from the start, and `.github/workflows/ci.yml` already targeted `main` and `develop` — but `develop` was never created. Prior programmes (Sprint 9, Programme Omega, Programme A, Programme B) committed directly to `main`, a deviation that had no recorded approval. This ADR records the activation of the intended strategy and closes the deviation.

The pre-existing `sprint-2-paper-trading` branch (tip `454f8e8`) is an abandoned divergent line; its history diverges at `ae2c789`. Its tip is preserved for archival on origin but it is not part of the active GitFlow.

## Status

Accepted
