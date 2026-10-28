# ADR 0001: Monorepo Structure

## Status
Accepted

## Context
Portable UI Engine needs to scale to support tokens, primitives, design gate tools, and showcase apps while keeping the core library portable and zero-dependency.

## Decision
Adopt a monorepo with:
- `packages/engine` - Core web components library (distributable, Shadow DOM, zero runtime deps)
- `packages/tokens` - W3C Design Tokens, generators, CSS/TS outputs
- `apps/*` - Showcase applications (docs, teardown-lab, run-theater, commit-garden, pattern-foundry)
- `tools/*` - Internal tooling (design-lint)
- `design/` - AI Studio briefs and directions

## Consequences
- Clear separation of concerns
- Engine remains lightweight and CDN-friendly
- Apps can consume shared packages
- Easier to enforce boundaries and gates
- Requires workspace tooling
