# Portable UI Engine - Constitution

## Core Principles
1. **Evidence First** - Every claim must have verifiable evidence. No unverified assertions.
2. **Fail Closed** - When in doubt, refuse. Never silently degrade or allow unsafe behavior.
3. **Token-Driven** - Design tokens are the single source of truth. No hardcoded magic values.
4. **Accessible by Default** - WCAG AA compliance is non-negotiable. Keyboard navigation, screen readers, reduced motion all required.
5. **Shadow DOM Integrity** - Maintain style isolation. Respect encapsulation boundaries.
6. **Zero Bloat** - Keep packages/engine lean. Apps may be heavier, engine must stay portable.
7. **Traceable** - All work has ADRs, sprint docs, evidence, atomic commits.
8. **Mechanical Gates** - Rules enforced by tooling/CI, not just prompts.

## Quality Gates
- Lint must pass
- Tests must pass  
- Build must succeed
- Axe/contrast checks pass for components
- Bundle size monitored
- No secrets committed
- All changes go through PR (never merged directly)
