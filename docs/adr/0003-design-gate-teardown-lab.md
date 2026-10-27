# ADR 0003: Design Gate via Teardown Lab

## Status
Accepted

## Context
Need objective, evidence-based quality bar for "elite" design.

## Decision
Create `apps/teardown-lab` implementing rubric v1 with:
- Visual hierarchy, typography, spacing, color/contrast
- Interaction states, motion, a11y
- Keyboard/focus, screen reader
- Responsiveness, tokens, API clarity, performance
Enforce via `tools/design-lint` as design gate.

## Consequences
- Objective scoring with evidence
- Catches regressions early
- Teaches and enforces standards
- Required for PRs affecting UI
